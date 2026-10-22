import time
from collections import defaultdict, deque
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse

from .config import settings
from .db import create_schema
from .router import router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    if settings.app_env != "production":
        await create_schema()
    yield


if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, environment=settings.app_env, traces_sample_rate=0.1)

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Analytics API for Earth's tracked artificial orbital environment.",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.web_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "If-None-Match"],
)
app.add_middleware(GZipMiddleware, minimum_size=1_024)

requests_by_ip: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def security_and_rate_limit(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > 2_000_000:
        return ORJSONResponse(status_code=413, content={"detail": "Request body is too large"})
    if request.url.path.startswith("/api/"):
        now = time.monotonic()
        ip = request.client.host if request.client else "unknown"
        window = requests_by_ip[ip]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= 180:
            return ORJSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
        window.append(now)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.method == "GET" and request.url.path.startswith("/api/v1/"):
        response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    return response


app.include_router(router)


@app.get("/")
async def root() -> dict:
    return {"name": settings.app_name, "docs": "/docs", "health": "/api/v1/health"}
