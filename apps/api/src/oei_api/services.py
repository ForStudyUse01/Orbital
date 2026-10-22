from __future__ import annotations

import math
import secrets
from datetime import UTC, date, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .demo_data import EVENTS, NOW, OBJECTS, TIMELINE, positions
from .models import Workspace, WorkspaceShare
from .schemas import (
    ConcentrationCell,
    DistributionBin,
    EventComparison,
    Overview,
    PersistencePoint,
    ResponseMeta,
    SnapshotManifest,
    SourceCitation,
    WorkspaceCreate,
    WorkspaceRead,
    WorkspaceUpdate,
)

SOURCES = [
    SourceCitation(name="Space-Track", url="https://www.space-track.org", role="Canonical orbital history"),
    SourceCitation(name="CelesTrak", url="https://celestrak.org", role="Current catalog validation"),
    SourceCitation(name="GCAT", url="https://planet4589.org/space/gcat", role="Lifecycle metadata"),
    SourceCitation(name="NASA HOOSF", url="https://orbitaldebris.jsc.nasa.gov", role="Fragmentation events"),
]


def meta(*warnings: str) -> ResponseMeta:
    age = (datetime.now(UTC) - NOW).total_seconds() / 3600
    return ResponseMeta(
        release_id=settings.release_id,
        generated_at=datetime.now(UTC),
        data_as_of=NOW,
        freshness_hours=max(0, round(age, 2)),
        sources=SOURCES,
        warnings=[
            (
                "Development release uses deterministic synthetic orbital records; "
                "connect provider credentials before scientific use."
            ),
            *warnings,
        ],
    )


def overview() -> Overview:
    latest = TIMELINE[-1]
    prior = TIMELINE[-2]
    return Overview(
        total_objects=latest["total"],
        active_payloads=latest["active_payload"],
        inactive_payloads=latest["inactive_payload"],
        debris=latest["debris"],
        rocket_bodies=latest["rocket_body"],
        tracked_regimes=6,
        modeled_over_1cm=1_568_450,
        change_yoy_percent=round((latest["total"] / prior["total"] - 1) * 100, 1),
    )


def filtered_timeline(start: int = 1957, end: int = 2026) -> list[dict]:
    return [point for point in TIMELINE if start <= point["date"].year <= end]


def distribution(dimension: str) -> list[DistributionBin]:
    if dimension == "category":
        labels = [
            ("Active payloads", "active_payload"),
            ("Inactive payloads", "inactive_payload"),
            ("Debris", "debris"),
            ("Rocket bodies", "rocket_body"),
            ("Unknown", "unknown"),
        ]
        total = len(OBJECTS)
        return [
            DistributionBin(
                label=label,
                count=sum(obj.category == key for obj in OBJECTS),
                share=round(sum(obj.category == key for obj in OBJECTS) / total, 4),
            )
            for label, key in labels
        ]
    if dimension == "regime":
        total = len(OBJECTS)
        return [
            DistributionBin(
                label=regime,
                count=sum(o.regime == regime for o in OBJECTS),
                share=round(sum(o.regime == regime for o in OBJECTS) / total, 4),
            )
            for regime in ["LEO", "MEO", "GEO", "GTO_HEO", "SUPER_GEO", "OTHER"]
        ]
    bins = [
        (0, 400),
        (400, 600),
        (600, 800),
        (800, 1000),
        (1000, 2000),
        (2000, 10000),
        (10000, 40000),
        (40000, 100000),
    ]
    total = len(OBJECTS)
    return [
        DistributionBin(
            label=f"{low:,}–{high:,} km",
            count=sum(low <= obj.altitude_km < high for obj in OBJECTS),
            share=round(sum(low <= obj.altitude_km < high for obj in OBJECTS) / total, 4),
        )
        for low, high in bins
    ]


def concentration() -> list[ConcentrationCell]:
    cells: list[ConcentrationCell] = []
    altitude_bins = list(range(200, 2001, 200))
    inclination_bins = list(range(0, 181, 15))
    for alt in altitude_bins[:-1]:
        for inc in inclination_bins[:-1]:
            count = sum(alt <= obj.altitude_km < alt + 200 and inc <= obj.inclination_deg < inc + 15 for obj in OBJECTS)
            r1 = 6378.137 + alt
            r2 = r1 + 200
            shell_volume = 4 / 3 * math.pi * (r2**3 - r1**3)
            cells.append(
                ConcentrationCell(
                    altitude_start_km=alt,
                    altitude_end_km=alt + 200,
                    inclination_start_deg=inc,
                    inclination_end_deg=inc + 15,
                    count=count,
                    normalized_density=count / shell_volume,
                )
            )
    return cells


def snapshot(snapshot_date: date) -> SnapshotManifest:
    year = snapshot_date.year
    resolution = "annual" if year < 2000 else "monthly"
    if any(abs((snapshot_date - event.date).days) <= 180 for event in EVENTS):
        resolution = "weekly"
    snapshot_positions = positions(snapshot_date)
    return SnapshotManifest(
        snapshot_date=snapshot_date,
        resolution=resolution,
        positions=snapshot_positions,
        object_count=len(snapshot_positions),
        excluded_from_positioning=sum(obj.quality == "metadata_only" for obj in OBJECTS),
    )


def event_comparison(event_id: str) -> EventComparison:
    event = next((item for item in EVENTS if item.id == event_id), None)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return EventComparison(
        event=event,
        windows={
            "30_days": {
                "before": 14210,
                "after": 14210 + round(event.fragments_catalogued * 0.51),
                "change_percent": 8.6,
            },
            "90_days": {
                "before": 14180,
                "after": 14180 + round(event.fragments_catalogued * 0.73),
                "change_percent": 12.2,
            },
            "365_days": {
                "before": 14020,
                "after": 14020 + round(event.fragments_catalogued * 0.91),
                "change_percent": 15.4,
            },
        },
        affected_altitude_band=f"{event.altitude_km - 100}–{event.altitude_km + 100} km",
        affected_regime="LEO",
    )


def persistence() -> list[PersistencePoint]:
    result: list[PersistencePoint] = []
    profiles = {
        "active_payload": (0.996, 4500),
        "inactive_payload": (0.992, 1800),
        "debris": (0.987, 8400),
        "rocket_body": (0.994, 2100),
        "unknown": (0.980, 300),
    }
    for category, (retention, initial) in profiles.items():
        for month in range(0, 361, 12):
            probability = retention**month
            result.append(
                PersistencePoint(
                    months=month,
                    survival_probability=round(probability, 4),
                    at_risk=max(0, int(initial * probability)),
                    category=category,
                )
            )
    return result


def _workspace_read(workspace: Workspace) -> WorkspaceRead:
    share_token = workspace.share.token if workspace.share and not workspace.share.revoked_at else None
    return WorkspaceRead(
        id=workspace.id,
        owner_id=workspace.owner_id,
        name=workspace.name,
        notes=workspace.notes,
        state=workspace.state,
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
        share_token=share_token,
    )


async def list_workspaces(session: AsyncSession, owner_id: str) -> list[WorkspaceRead]:
    result = await session.execute(
        select(Workspace).where(Workspace.owner_id == owner_id).order_by(Workspace.updated_at.desc())
    )
    return [_workspace_read(item) for item in result.scalars().all()]


async def create_workspace(session: AsyncSession, owner_id: str, payload: WorkspaceCreate) -> WorkspaceRead:
    workspace = Workspace(owner_id=owner_id, name=payload.name, notes=payload.notes, state=payload.state.model_dump())
    session.add(workspace)
    await session.commit()
    await session.refresh(workspace)
    return _workspace_read(workspace)


async def get_owned_workspace(session: AsyncSession, owner_id: str, workspace_id: str) -> Workspace:
    workspace = await session.get(Workspace, workspace_id)
    if not workspace or workspace.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


async def update_workspace(
    session: AsyncSession, owner_id: str, workspace_id: str, payload: WorkspaceUpdate
) -> WorkspaceRead:
    workspace = await get_owned_workspace(session, owner_id, workspace_id)
    workspace.name, workspace.notes, workspace.state = (
        payload.name,
        payload.notes,
        payload.state.model_dump(),
    )
    await session.commit()
    await session.refresh(workspace)
    return _workspace_read(workspace)


async def delete_workspace(session: AsyncSession, owner_id: str, workspace_id: str) -> None:
    workspace = await get_owned_workspace(session, owner_id, workspace_id)
    await session.delete(workspace)
    await session.commit()


async def share_workspace(session: AsyncSession, owner_id: str, workspace_id: str) -> WorkspaceRead:
    workspace = await get_owned_workspace(session, owner_id, workspace_id)
    if workspace.share:
        workspace.share.revoked_at = None
        workspace.share.token = secrets.token_urlsafe(24)
    else:
        workspace.share = WorkspaceShare(token=secrets.token_urlsafe(24))
    await session.commit()
    await session.refresh(workspace)
    return _workspace_read(workspace)


async def revoke_share(session: AsyncSession, owner_id: str, workspace_id: str) -> WorkspaceRead:
    workspace = await get_owned_workspace(session, owner_id, workspace_id)
    if workspace.share:
        workspace.share.revoked_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(workspace)
    return _workspace_read(workspace)


async def shared_workspace(session: AsyncSession, token: str) -> WorkspaceRead:
    result = await session.execute(
        select(WorkspaceShare).where(WorkspaceShare.token == token, WorkspaceShare.revoked_at.is_(None))
    )
    share = result.scalar_one_or_none()
    if not share:
        raise HTTPException(status_code=404, detail="Shared workspace not found or revoked")
    return _workspace_read(share.workspace)
