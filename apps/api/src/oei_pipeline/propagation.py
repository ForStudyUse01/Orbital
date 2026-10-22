from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sgp4 import omm
from sgp4.api import Satrec, jday

from .analytics import EARTH_RADIUS_KM, derive_orbit


def _epoch(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def latest_per_catalog_id(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[int, dict[str, Any]] = {}
    for row in rows:
        catalog_id = int(row["NORAD_CAT_ID"])
        previous = latest.get(catalog_id)
        if previous is None or _epoch(row["EPOCH"]) > _epoch(previous["EPOCH"]):
            latest[catalog_id] = row
    return list(latest.values())


def propagate_omm_rows(
    rows: list[dict[str, Any]], target: datetime
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    target = target.astimezone(UTC)
    jd, fraction = jday(target.year, target.month, target.day, target.hour, target.minute, target.second)
    positions: list[dict[str, Any]] = []
    quarantine: list[dict[str, Any]] = []
    for row in latest_per_catalog_id(rows):
        catalog_id = int(row["NORAD_CAT_ID"])
        age_days = (target - _epoch(row["EPOCH"])).total_seconds() / 86_400
        if age_days > 90:
            quarantine.append({"norad_id": catalog_id, "reason": "element_too_stale", "age_days": age_days})
            continue
        try:
            satellite = Satrec()
            omm.initialize(satellite, row)
            error, coordinates, _velocity = satellite.sgp4(jd, fraction)
            regime = derive_orbit(
                float(row["MEAN_MOTION"]), float(row["ECCENTRICITY"]), float(row["INCLINATION"])
            ).regime
        except (KeyError, TypeError, ValueError) as exc:
            quarantine.append({"norad_id": catalog_id, "reason": "invalid_omm", "detail": str(exc)})
            continue
        if error:
            quarantine.append({"norad_id": catalog_id, "reason": "sgp4_error", "code": error})
            continue
        object_type = str(row.get("OBJECT_TYPE", "UNKNOWN")).upper()
        category = "debris" if object_type == "DEBRIS" else "rocket_body" if object_type == "ROCKET BODY" else "unknown"
        positions.append(
            {
                "norad_id": catalog_id,
                "x": coordinates[0] / EARTH_RADIUS_KM,
                "y": coordinates[1] / EARTH_RADIUS_KM,
                "z": coordinates[2] / EARTH_RADIUS_KM,
                "category": category,
                "regime": regime,
            }
        )
    return positions, quarantine
