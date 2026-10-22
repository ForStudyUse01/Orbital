from __future__ import annotations

import csv
import io
from datetime import UTC, date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from . import services
from .auth import Principal, require_admin, require_user
from .current_catalog import current_object, current_snapshot
from .db import get_session
from .demo_data import EVENTS, OBJECTS
from .schemas import Envelope, WorkspaceCreate, WorkspaceUpdate

router = APIRouter(prefix="/api/v1")
Session = Annotated[AsyncSession, Depends(get_session)]
User = Annotated[Principal, Depends(require_user)]
Admin = Annotated[Principal, Depends(require_admin)]


@router.get("/environment/current", response_model=Envelope)
async def get_current_environment() -> dict:
    return await current_snapshot()


@router.get("/overview", response_model=Envelope)
async def get_overview() -> Envelope:
    return Envelope(data=services.overview(), meta=services.meta())


@router.get("/timeline", response_model=Envelope)
async def get_timeline(
    start: int = Query(1957, ge=1957, le=2026), end: int = Query(2026, ge=1957, le=2026)
) -> Envelope:
    if start > end:
        raise HTTPException(status_code=422, detail="start must not be after end")
    return Envelope(data=services.filtered_timeline(start, end), meta=services.meta())


@router.get("/distribution", response_model=Envelope)
async def get_distribution(
    dimension: Literal["altitude", "category", "regime"] = "altitude",
) -> Envelope:
    return Envelope(data=services.distribution(dimension), meta=services.meta())


@router.get("/concentration", response_model=Envelope)
async def get_concentration() -> Envelope:
    return Envelope(
        data=services.concentration(),
        meta=services.meta("Concentration describes catalog records, not collision risk."),
    )


@router.get("/snapshots", response_model=Envelope)
async def get_snapshots() -> Envelope:
    dates = [date(year, 1, 1).isoformat() for year in range(1957, 2000)]
    dates += [
        date(year, month, 1).isoformat()
        for year in range(2000, 2027)
        for month in range(1, 13)
        if date(year, month, 1) <= date(2026, 9, 1)
    ]
    return Envelope(data=dates, meta=services.meta())


@router.get("/snapshots/{snapshot_date}/manifest", response_model=Envelope)
async def get_snapshot(snapshot_date: date) -> Envelope:
    if not date(1957, 1, 1) <= snapshot_date <= date(2026, 9, 21):
        raise HTTPException(status_code=404, detail="Snapshot is outside the available range")
    return Envelope(data=services.snapshot(snapshot_date), meta=services.meta())


@router.get("/objects/search", response_model=Envelope)
async def search_objects(q: str = Query("", max_length=80), limit: int = Query(20, ge=1, le=100)) -> Envelope:
    needle = q.casefold().strip()
    matches = [item for item in OBJECTS if not needle or needle in item.name.casefold() or needle in str(item.norad_id)]
    return Envelope(data=matches[:limit], meta=services.meta())


@router.get("/objects/{norad_id}", response_model=Envelope)
async def get_object(norad_id: int, source: Literal["demo", "current"] = "demo") -> Envelope:
    if source == "current":
        release = await current_snapshot()
        item = await current_object(norad_id)
        if not item:
            raise HTTPException(status_code=404, detail="Object not found in the current catalog")
        release["meta"]["warnings"].append("Current object detail is derived from CelesTrak GP elements.")
        return Envelope(data=item, meta=release["meta"])
    item = next((obj for obj in OBJECTS if obj.norad_id == norad_id), None)
    if not item and 10_000 <= norad_id < 50_000:
        template = OBJECTS[(norad_id - 10_000) % len(OBJECTS)]
        item = template.model_copy(update={"norad_id": norad_id, "name": f"Demo {template.name}"})
    if not item:
        raise HTTPException(status_code=404, detail="Object not found")
    return Envelope(data=item, meta=services.meta())


@router.get("/objects/{norad_id}/history", response_model=Envelope)
async def get_object_history(norad_id: int) -> Envelope:
    item = next((obj for obj in OBJECTS if obj.norad_id == norad_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Object not found")
    history = [
        {
            "date": f"{year}-01-01",
            "altitude_km": round(item.altitude_km + (year - 2026) * 0.65, 2),
            "inclination_deg": item.inclination_deg,
            "quality": item.quality,
        }
        for year in range(max(item.launch_date.year, 2000), 2027)
    ]
    return Envelope(data=history, meta=services.meta())


@router.get("/events", response_model=Envelope)
async def get_events() -> Envelope:
    return Envelope(data=EVENTS, meta=services.meta())


@router.get("/events/{event_id}", response_model=Envelope)
async def get_event(event_id: str) -> Envelope:
    event = next((item for item in EVENTS if item.id == event_id), None)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return Envelope(data=event, meta=services.meta())


@router.get("/events/{event_id}/comparison", response_model=Envelope)
async def get_event_comparison(event_id: str) -> Envelope:
    return Envelope(data=services.event_comparison(event_id), meta=services.meta())


@router.get("/persistence", response_model=Envelope)
async def get_persistence() -> Envelope:
    return Envelope(
        data=services.persistence(),
        meta=services.meta("Survival estimates are right-censored for objects still tracked."),
    )


@router.get("/methodology", response_model=Envelope)
async def methodology() -> Envelope:
    return Envelope(
        data={
            "population": "Distinct catalog IDs present in a validated snapshot.",
            "concentration": "Counts in altitude–inclination bins; not a collision probability.",
            "persistence": ("First valid observation to confirmed decay, with active records right-censored."),
            "regimes": {
                "LEO": "apogee ≤ 2,000 km",
                "MEO": "perigee > 2,000 km and apogee < 35,586 km",
                "GEO": "35,786 ± 200 km, e ≤ 0.05, i ≤ 15°",
            },
            "limitations": [
                "Public catalog excludes classified and untracked objects.",
                "Markers are visually enlarged.",
                "The service is not an operational risk system.",
            ],
        },
        meta=services.meta(),
    )


@router.get("/releases", response_model=Envelope)
async def releases() -> Envelope:
    return Envelope(
        data=[
            {
                "id": services.settings.release_id,
                "status": "current",
                "published_at": services.NOW.isoformat(),
                "quality": "validated-demo",
            }
        ],
        meta=services.meta(),
    )


@router.get("/exports/timeline.{format}")
async def export_timeline(format: Literal["csv", "json"]):
    rows = services.filtered_timeline()
    if format == "json":
        return {"data": rows, "meta": services.meta().model_dump(mode="json")}
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    headers = {"Content-Disposition": "attachment; filename=oei-population-timeline.csv"}
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers=headers)


@router.get("/workspaces", response_model=Envelope)
async def workspaces(session: Session, principal: User) -> Envelope:
    return Envelope(data=await services.list_workspaces(session, principal.user_id), meta=services.meta())


@router.post("/workspaces", response_model=Envelope, status_code=201)
async def create_workspace(payload: WorkspaceCreate, session: Session, principal: User) -> Envelope:
    return Envelope(
        data=await services.create_workspace(session, principal.user_id, payload),
        meta=services.meta(),
    )


@router.put("/workspaces/{workspace_id}", response_model=Envelope)
async def update_workspace(workspace_id: str, payload: WorkspaceUpdate, session: Session, principal: User) -> Envelope:
    return Envelope(
        data=await services.update_workspace(session, principal.user_id, workspace_id, payload),
        meta=services.meta(),
    )


@router.delete("/workspaces/{workspace_id}", status_code=204)
async def delete_workspace(workspace_id: str, session: Session, principal: User) -> Response:
    await services.delete_workspace(session, principal.user_id, workspace_id)
    return Response(status_code=204)


@router.post("/workspaces/{workspace_id}/share", response_model=Envelope)
async def share_workspace(workspace_id: str, session: Session, principal: User) -> Envelope:
    return Envelope(
        data=await services.share_workspace(session, principal.user_id, workspace_id),
        meta=services.meta(),
    )


@router.delete("/workspaces/{workspace_id}/share", response_model=Envelope)
async def revoke_workspace_share(workspace_id: str, session: Session, principal: User) -> Envelope:
    return Envelope(
        data=await services.revoke_share(session, principal.user_id, workspace_id),
        meta=services.meta(),
    )


@router.get("/shared/{token}", response_model=Envelope)
async def shared_workspace(token: str, session: Session) -> Envelope:
    return Envelope(data=await services.shared_workspace(session, token), meta=services.meta())


@router.get("/admin/ingestion-runs", response_model=Envelope)
async def ingestion_runs(_principal: Admin) -> Envelope:
    return Envelope(
        data=[
            {
                "id": "demo-seed",
                "status": "succeeded",
                "started_at": services.NOW.isoformat(),
                "published": True,
            }
        ],
        meta=services.meta(),
    )


@router.get("/admin/quality", response_model=Envelope)
async def quality(_principal: Admin) -> Envelope:
    return Envelope(
        data={"status": "passing", "duplicate_ids": 0, "invalid_orbits": 0, "warnings": 1},
        meta=services.meta(),
    )


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "time": datetime.now(UTC).isoformat()}


@router.get("/ready")
async def ready(session: Session) -> dict:
    await session.execute(text("SELECT 1"))
    return {"status": "ready"}
