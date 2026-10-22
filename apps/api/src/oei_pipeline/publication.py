from __future__ import annotations

import hashlib
import io
import json
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from typing import Any

import pyarrow as pa
import pyarrow.ipc as ipc
import pyarrow.parquet as pq

from .quality import require_passing, validate_arrow, validate_snapshot_records
from .storage import ArtifactStore


@dataclass(frozen=True)
class ReleaseManifest:
    release_id: str
    snapshot_date: str
    resolution: str
    row_count: int
    created_at: str
    transformation_version: str
    classifier_version: str
    source_checksums: dict[str, str]
    artifacts: dict[str, dict[str, str | int]]


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def publish_snapshot(
    store: ArtifactStore,
    release_id: str,
    snapshot_date: date,
    resolution: str,
    records: list[dict[str, Any]],
    source_checksums: dict[str, str],
) -> ReleaseManifest:
    require_passing(validate_snapshot_records(records))
    table = pa.Table.from_pylist(records)
    parquet_buffer = io.BytesIO()
    pq.write_table(table, parquet_buffer, compression="zstd")
    arrow_buffer = io.BytesIO()
    with ipc.new_file(arrow_buffer, table.schema) as writer:
        writer.write_table(table)
    parquet_content = parquet_buffer.getvalue()
    arrow_content = arrow_buffer.getvalue()
    require_passing(validate_arrow(arrow_content, len(records)))

    prefix = f"releases/{release_id}/snapshots/{snapshot_date.isoformat()}"
    parquet_key = f"{prefix}/snapshot.parquet"
    arrow_key = f"{prefix}/positions.arrow"
    store.put_bytes(parquet_key, parquet_content, "application/vnd.apache.parquet")
    store.put_bytes(arrow_key, arrow_content, "application/vnd.apache.arrow.file")

    manifest = ReleaseManifest(
        release_id=release_id,
        snapshot_date=snapshot_date.isoformat(),
        resolution=resolution,
        row_count=len(records),
        created_at=datetime.now(UTC).isoformat(),
        transformation_version="1.0.0",
        classifier_version="1.0.0",
        source_checksums=source_checksums,
        artifacts={
            "parquet": {"key": parquet_key, "sha256": _digest(parquet_content), "bytes": len(parquet_content)},
            "arrow": {"key": arrow_key, "sha256": _digest(arrow_content), "bytes": len(arrow_content)},
        },
    )
    manifest_content = json.dumps(asdict(manifest), indent=2, sort_keys=True).encode()
    immutable_manifest_key = f"releases/{release_id}/manifest.json"
    store.put_bytes(immutable_manifest_key, manifest_content, "application/json")
    # The mutable pointer is published last, so readers never observe a partial release.
    store.put_bytes("current.json", manifest_content, "application/json")
    return manifest
