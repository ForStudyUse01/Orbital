"""Current CelesTrak active subset. Never silently substitute synthetic records."""

import asyncio
import hashlib
import json
import logging
import math
import time
from datetime import UTC, date, datetime
from pathlib import Path

import httpx
from fastapi import HTTPException
from sgp4 import omm
from sgp4.api import Satrec, jday
from sgp4.propagation import gstime

from oei_pipeline.analytics import EARTH_RADIUS_KM, derive_orbit

URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=JSON"
CACHE = Path(__file__).resolve().parents[4] / "data/raw/current-active.json"
_lock = asyncio.Lock()
_catalog = None
_result = None
_result_at = 0.0
_retry_at = 0.0


def build_snapshot(rows: list[dict], target: datetime) -> dict:
    """SGP4 TEME -> approximate Earth-fixed coordinates, then Three.js y-up."""
    jd, fr = jday(target.year, target.month, target.day, target.hour, target.minute, target.second)
    theta = gstime(jd + fr)
    ct, st = math.cos(theta), math.sin(theta)
    latest = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            ident = int(row["NORAD_CAT_ID"])
            epoch = datetime.fromisoformat(row["EPOCH"].replace("Z", "+00:00")).replace(tzinfo=UTC)
            if ident <= 0 or ident > 999999999:
                continue
            if ident not in latest or epoch > latest[ident][0]:
                latest[ident] = (epoch, row)
        except (KeyError, ValueError, TypeError):
            continue
    positions = []
    for ident, (epoch, row) in latest.items():
        try:
            if abs((target - epoch).total_seconds()) > 30 * 86400:
                continue
            orbit = derive_orbit(float(row["MEAN_MOTION"]), float(row["ECCENTRICITY"]), float(row["INCLINATION"]))
            satellite = Satrec()
            normalized = {**row, "EPOCH": epoch.replace(tzinfo=None).isoformat(timespec="microseconds")}
            omm.initialize(satellite, normalized)
            error, (x, y, z), _ = satellite.sgp4(jd, fr)
            if error or not all(math.isfinite(v) for v in (x, y, z)):
                continue
            if math.sqrt(x * x + y * y + z * z) < EARTH_RADIUS_KM:
                continue
            # The bundled equirectangular map has longitude zero on +X.
            positions.append(
                dict(
                    norad_id=ident,
                    name=str(row.get("OBJECT_NAME", ident)),
                    epoch=epoch.isoformat(),
                    x=round((ct * x + st * y) / EARTH_RADIUS_KM, 7),
                    y=round(z / EARTH_RADIUS_KM, 7),
                    z=round((st * x - ct * y) / EARTH_RADIUS_KM, 7),
                    category="active_payload",
                    regime=orbit.regime,
                )
            )
        except (KeyError, ValueError, TypeError, OverflowError):
            continue
    return dict(
        snapshot_date=target.date().isoformat(),
        position_time=target.isoformat(),
        resolution="current",
        positions=positions,
        object_count=len(latest),
        excluded_from_positioning=len(latest) - len(positions),
        coordinate_frame="Earth-fixed (approximate)",
    )


async def current_snapshot() -> dict:
    global _catalog, _result, _result_at, _retry_at
    async with _lock:
        now = datetime.now(UTC)
        if _result is not None and time.monotonic() - _result_at < 60:
            return _result
        if _catalog is None and CACHE.exists():
            try:
                candidate = json.loads(await asyncio.to_thread(CACHE.read_text, encoding="utf-8"))
                stamp = datetime.fromisoformat(candidate["retrieved_at"])
                if stamp.tzinfo is None or not isinstance(candidate["checksum"], str):
                    raise ValueError("Invalid cache provenance")
                if isinstance(candidate["rows"], list) and candidate["rows"]:
                    _catalog = candidate
            except (ValueError, KeyError, OSError, TypeError):
                pass
        age = (now - datetime.fromisoformat(_catalog["retrieved_at"])).total_seconds() if _catalog else math.inf
        failed = False
        if age >= 10800 and time.monotonic() >= _retry_at:
            _retry_at = time.monotonic() + 900
            try:
                async with httpx.AsyncClient(timeout=45, follow_redirects=True) as client:
                    response = await client.get(URL)
                    response.raise_for_status()
                rows = response.json()
                if not isinstance(rows, list) or not rows or len(rows) > 100000:
                    raise ValueError("Invalid upstream catalog")
                validation = await asyncio.to_thread(build_snapshot, rows, now)
                if len(validation["positions"]) < len(rows) * 0.8:
                    raise ValueError("Catalog failed orbital validation")
                if _catalog and len(rows) < len(_catalog["rows"]) * 0.8:
                    raise ValueError("Unexpected catalog population drop")
                candidate = dict(
                    rows=rows, retrieved_at=now.isoformat(), checksum=hashlib.sha256(response.content).hexdigest()
                )
                CACHE.parent.mkdir(parents=True, exist_ok=True)
                temporary = CACHE.with_suffix(".tmp")
                await asyncio.to_thread(temporary.write_text, json.dumps(candidate), encoding="utf-8")
                temporary.replace(CACHE)
                _catalog = candidate
                age = 0
            except (httpx.HTTPError, ValueError, OSError, TypeError) as exc:
                logging.getLogger(__name__).warning("Current catalog refresh failed: %s", exc)
                failed = True
        if not _catalog:
            raise HTTPException(
                503, "CelesTrak is unavailable and no validated live cache exists. Try later or select Demo history."
            )
        snapshot = await asyncio.to_thread(build_snapshot, _catalog["rows"], now)
        warnings = [
            "Active-satellite subset only; excludes the full debris and rocket-body population.",
            "SGP4 estimates at the displayed time, not live radar observations. Other analytics remain demo data.",
        ]
        if age >= 10800 or failed:
            warnings.append("Using cached elements; upstream refresh is pending or unavailable.")
        if age > 43200:
            warnings.append("STALE: source download is over 12 hours old.")
        if snapshot["excluded_from_positioning"]:
            warnings.append("Invalid, decayed or over-30-day-old elements were excluded from positioning.")
        _result = dict(
            data=snapshot,
            meta=dict(
                release_id="celestrak-active-" + _catalog["checksum"][:12],
                generated_at=now.isoformat(),
                data_as_of=_catalog["retrieved_at"],
                synthetic=False,
                freshness_hours=round(age / 3600, 2),
                sources=[dict(name="CelesTrak active satellites", url=URL, role="Current GP orbital elements")],
                warnings=warnings,
            ),
        )
        _result_at = time.monotonic()
        return _result


async def current_object(norad_id: int) -> dict | None:
    """Return searchable details for an object in the validated current cache."""
    await current_snapshot()
    if not _catalog:
        return None
    row = None
    for item in _catalog["rows"]:
        try:
            if int(item.get("NORAD_CAT_ID", -1)) == norad_id:
                row = item
                break
        except (TypeError, ValueError):
            continue
    if row is None:
        return None
    try:
        epoch = datetime.fromisoformat(str(row["EPOCH"]).replace("Z", "+00:00")).replace(tzinfo=UTC)
        orbit = derive_orbit(float(row["MEAN_MOTION"]), float(row["ECCENTRICITY"]), float(row["INCLINATION"]))
        designator = str(row.get("OBJECT_ID") or "UNKNOWN")
        launch_year = int(designator[:4]) if len(designator) >= 4 and designator[:4].isdigit() else epoch.year
        return dict(
            norad_id=norad_id,
            name=str(row.get("OBJECT_NAME") or f"NORAD {norad_id}"),
            international_designator=designator,
            category="active_payload",
            regime=orbit.regime,
            country="Not supplied by current GP source",
            launch_date=date(launch_year, 1, 1).isoformat(),
            altitude_km=round((orbit.perigee_km + orbit.apogee_km) / 2, 2),
            perigee_km=round(orbit.perigee_km, 2),
            apogee_km=round(orbit.apogee_km, 2),
            inclination_deg=float(row["INCLINATION"]),
            period_minutes=round(orbit.period_minutes, 2),
            eccentricity=float(row["ECCENTRICITY"]),
            quality="current" if abs((datetime.now(UTC) - epoch).total_seconds()) <= 3 * 86400 else "stale",
        )
    except (KeyError, TypeError, ValueError, OverflowError):
        return None
