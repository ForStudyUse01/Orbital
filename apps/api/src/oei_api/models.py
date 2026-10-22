from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(80), unique=True)
    homepage_url: Mapped[str] = mapped_column(String(500))
    license_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    attribution: Mapped[str] = mapped_column(Text)
    restricted: Mapped[bool] = mapped_column(Boolean, default=False)


class CatalogObject(Base):
    __tablename__ = "objects"

    norad_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    international_designator: Mapped[str | None] = mapped_column(String(32), index=True)
    name: Mapped[str] = mapped_column(String(240), index=True)
    source_classification: Mapped[str | None] = mapped_column(String(80), nullable=True)
    normalized_classification: Mapped[str] = mapped_column(String(40), index=True)
    operational_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    launch_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    decay_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)


class ObjectAlias(Base):
    __tablename__ = "object_aliases"
    __table_args__ = (UniqueConstraint("source_id", "alias", name="uq_object_alias_source_alias"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    norad_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("objects.norad_id", ondelete="CASCADE"), index=True)
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("sources.id"))
    alias: Mapped[str] = mapped_column(String(240))
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)


class ObjectSourceRecord(Base):
    __tablename__ = "object_source_records"
    __table_args__ = (UniqueConstraint("source_id", "norad_id", "source_epoch", name="uq_source_object_epoch"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("sources.id"), index=True)
    norad_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("objects.norad_id"), index=True)
    source_epoch: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    source_classification: Mapped[str | None] = mapped_column(String(80), nullable=True)
    checksum: Mapped[str] = mapped_column(String(64))
    raw_key: Mapped[str] = mapped_column(String(600))


class DatasetRelease(Base):
    __tablename__ = "dataset_releases"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    status: Mapped[str] = mapped_column(String(24), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    transformation_version: Mapped[str] = mapped_column(String(80))
    classifier_version: Mapped[str] = mapped_column(String(80))
    source_checksums: Mapped[dict] = mapped_column(JSON, default=dict)
    quality_statistics: Mapped[dict] = mapped_column(JSON, default=dict)
    manifest_key: Mapped[str | None] = mapped_column(String(600), nullable=True)


class Snapshot(Base):
    __tablename__ = "snapshots"
    __table_args__ = (UniqueConstraint("release_id", "snapshot_date", "resolution", name="uq_release_snapshot"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    release_id: Mapped[str] = mapped_column(String(80), ForeignKey("dataset_releases.id"), index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, index=True)
    resolution: Mapped[str] = mapped_column(String(16))
    object_count: Mapped[int] = mapped_column(Integer)
    excluded_count: Mapped[int] = mapped_column(Integer, default=0)
    parquet_key: Mapped[str] = mapped_column(String(600))
    arrow_key: Mapped[str] = mapped_column(String(600))


class EnvironmentMetric(Base):
    __tablename__ = "environment_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    snapshot_id: Mapped[str] = mapped_column(String(36), ForeignKey("snapshots.id", ondelete="CASCADE"), index=True)
    metric: Mapped[str] = mapped_column(String(80), index=True)
    dimension: Mapped[str | None] = mapped_column(String(80), nullable=True)
    dimension_value: Mapped[str | None] = mapped_column(String(120), nullable=True)
    value: Mapped[float] = mapped_column(Float)


class ConcentrationBin(Base):
    __tablename__ = "concentration_bins"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    snapshot_id: Mapped[str] = mapped_column(String(36), ForeignKey("snapshots.id", ondelete="CASCADE"), index=True)
    altitude_start_km: Mapped[int] = mapped_column(Integer)
    altitude_end_km: Mapped[int] = mapped_column(Integer)
    inclination_start_deg: Mapped[int] = mapped_column(Integer)
    inclination_end_deg: Mapped[int] = mapped_column(Integer)
    catalog_count: Mapped[int] = mapped_column(Integer)
    population_share: Mapped[float] = mapped_column(Float)
    shell_density: Mapped[float] = mapped_column(Float)


class EventRecord(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("sources.id"))
    name: Mapped[str] = mapped_column(String(240))
    event_date: Mapped[date] = mapped_column(Date, index=True)
    event_type: Mapped[str] = mapped_column(String(80))
    assessed_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class EventObject(Base):
    __tablename__ = "event_objects"
    __table_args__ = (UniqueConstraint("event_id", "norad_id", "role", name="uq_event_object_role"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    event_id: Mapped[str] = mapped_column(String(100), ForeignKey("events.id", ondelete="CASCADE"), index=True)
    norad_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("objects.norad_id"), index=True)
    role: Mapped[str] = mapped_column(String(32))


class ModeledPopulationEstimate(Base):
    __tablename__ = "modeled_population_estimates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    release_id: Mapped[str] = mapped_column(String(80), ForeignKey("dataset_releases.id"), index=True)
    source_id: Mapped[str] = mapped_column(String(36), ForeignKey("sources.id"))
    estimate_date: Mapped[date] = mapped_column(Date)
    size_band: Mapped[str] = mapped_column(String(40))
    estimated_count: Mapped[int] = mapped_column(BigInteger)
    methodology_note: Mapped[str] = mapped_column(Text)


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    job_type: Mapped[str] = mapped_column(String(40), index=True)
    status: Mapped[str] = mapped_column(String(24), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    release_id: Mapped[str | None] = mapped_column(String(80), ForeignKey("dataset_releases.id"), nullable=True)
    published: Mapped[bool] = mapped_column(Boolean, default=False)
    statistics: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class DataQualityIssue(Base):
    __tablename__ = "data_quality_issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    ingestion_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ingestion_runs.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(80), index=True)
    severity: Mapped[str] = mapped_column(String(16), index=True)
    norad_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    message: Mapped[str] = mapped_column(Text)
    quarantined_record_key: Mapped[str | None] = mapped_column(String(600), nullable=True)


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    owner_id: Mapped[str] = mapped_column(String(128), index=True)
    name: Mapped[str] = mapped_column(String(120))
    notes: Mapped[str] = mapped_column(Text, default="")
    state: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    share: Mapped["WorkspaceShare | None"] = relationship(
        back_populates="workspace", cascade="all, delete-orphan", uselist=False, lazy="selectin"
    )


class WorkspaceShare(Base):
    __tablename__ = "workspace_shares"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), unique=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    workspace: Mapped[Workspace] = relationship(back_populates="share", lazy="selectin")
