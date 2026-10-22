from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pyarrow as pa
import pyarrow.ipc as ipc


@dataclass(frozen=True)
class QualityIssue:
    code: str
    message: str
    record_id: int | None = None
    fatal: bool = True


def validate_snapshot_records(records: list[dict[str, Any]]) -> list[QualityIssue]:
    issues: list[QualityIssue] = []
    seen: set[int] = set()
    for record in records:
        norad_id = int(record["norad_id"])
        if norad_id in seen:
            issues.append(QualityIssue("duplicate_catalog_id", "Snapshot contains a duplicate catalog ID", norad_id))
        seen.add(norad_id)
        radius = (float(record["x"]) ** 2 + float(record["y"]) ** 2 + float(record["z"]) ** 2) ** 0.5
        if not 1.0 <= radius <= 20.0:
            issues.append(QualityIssue("position_out_of_range", "Normalized geocentric radius is invalid", norad_id))
        if record.get("category") not in {"active_payload", "inactive_payload", "debris", "rocket_body", "unknown"}:
            issues.append(QualityIssue("invalid_category", "Normalized object category is invalid", norad_id))
    if not records:
        issues.append(QualityIssue("empty_snapshot", "Snapshot contains no positional records"))
    return issues


def validate_arrow(content: bytes, expected_rows: int) -> list[QualityIssue]:
    try:
        table = ipc.open_file(pa.BufferReader(content)).read_all()
    except (pa.ArrowInvalid, OSError) as exc:
        return [QualityIssue("invalid_arrow", f"Arrow validation failed: {exc}")]
    if table.num_rows != expected_rows:
        return [QualityIssue("arrow_row_count", "Arrow row count differs from the curated snapshot")]
    return []


def require_passing(issues: list[QualityIssue]) -> None:
    fatal = [issue for issue in issues if issue.fatal]
    if fatal:
        summary = "; ".join(f"{issue.code}: {issue.message}" for issue in fatal[:10])
        raise ValueError(f"Dataset publication rejected: {summary}")
