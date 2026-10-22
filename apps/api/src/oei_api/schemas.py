from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

ObjectCategory = Literal["active_payload", "inactive_payload", "debris", "rocket_body", "unknown"]
OrbitalRegime = Literal["LEO", "MEO", "GEO", "GTO_HEO", "SUPER_GEO", "OTHER"]


class SourceCitation(BaseModel):
    name: str
    url: str
    role: str


class ResponseMeta(BaseModel):
    release_id: str
    generated_at: datetime
    data_as_of: datetime
    synthetic: bool = True
    freshness_hours: float
    sources: list[SourceCitation]
    warnings: list[str] = Field(default_factory=list)


class Overview(BaseModel):
    total_objects: int
    active_payloads: int
    inactive_payloads: int
    debris: int
    rocket_bodies: int
    tracked_regimes: int
    modeled_over_1cm: int
    change_yoy_percent: float


class TimelinePoint(BaseModel):
    date: date
    total: int
    active_payload: int
    inactive_payload: int
    debris: int
    rocket_body: int
    unknown: int


class DistributionBin(BaseModel):
    label: str
    count: int
    share: float


class ConcentrationCell(BaseModel):
    altitude_start_km: int
    altitude_end_km: int
    inclination_start_deg: int
    inclination_end_deg: int
    count: int
    normalized_density: float


class OrbitalObject(BaseModel):
    norad_id: int
    name: str
    international_designator: str
    category: ObjectCategory
    regime: OrbitalRegime
    country: str
    launch_date: date
    decay_date: date | None = None
    altitude_km: float
    perigee_km: float
    apogee_km: float
    inclination_deg: float
    period_minutes: float
    eccentricity: float
    quality: Literal["current", "stale", "metadata_only"] = "current"


class Position(BaseModel):
    norad_id: int
    x: float
    y: float
    z: float
    category: ObjectCategory
    regime: OrbitalRegime


class SnapshotManifest(BaseModel):
    snapshot_date: date
    resolution: Literal["annual", "monthly", "weekly", "current"]
    positions: list[Position]
    object_count: int
    excluded_from_positioning: int


class Event(BaseModel):
    id: str
    name: str
    date: date
    event_type: str
    assessed_cause: str
    parent_norad_ids: list[int]
    fragments_catalogued: int
    fragments_remaining: int
    altitude_km: int
    inclination_deg: float
    description: str
    deep_replay: bool = False


class EventComparison(BaseModel):
    event: Event
    windows: dict[str, dict[str, float | int]]
    affected_altitude_band: str
    affected_regime: OrbitalRegime


class PersistencePoint(BaseModel):
    months: int
    survival_probability: float
    at_risk: int
    category: ObjectCategory


class WorkspaceState(BaseModel):
    primary_date: str = "2026-09-01"
    comparison_date: str | None = "2020-01-01"
    categories: list[ObjectCategory] = Field(default_factory=list)
    regimes: list[OrbitalRegime] = Field(default_factory=list)
    selected_objects: list[int] = Field(default_factory=list, max_length=100)
    selected_events: list[str] = Field(default_factory=list, max_length=50)
    chart_order: list[str] = Field(default_factory=list, max_length=20)
    camera: dict[str, float] = Field(default_factory=dict)
    rendering_mode: Literal["objects", "density"] = "objects"


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    notes: str = Field(default="", max_length=20_000)
    state: WorkspaceState

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return " ".join(value.split())


class WorkspaceUpdate(WorkspaceCreate):
    pass


class WorkspaceRead(WorkspaceCreate):
    model_config = ConfigDict(from_attributes=True)

    id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    share_token: str | None = None


class Envelope(BaseModel):
    data: Any
    meta: ResponseMeta
