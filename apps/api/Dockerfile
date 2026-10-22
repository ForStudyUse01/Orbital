FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

RUN pip install --no-cache-dir uv==0.11.19
WORKDIR /app
COPY apps/api/pyproject.toml apps/api/uv.lock ./
RUN uv sync --frozen --no-dev
COPY apps/api ./
EXPOSE 8000
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn oei_api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
