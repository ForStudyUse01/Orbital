from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

EARTH_RADIUS_KM = 6378.137
EARTH_MU_KM3_S2 = 398600.4418

Regime = Literal["LEO", "MEO", "GEO", "GTO_HEO", "SUPER_GEO", "OTHER"]


@dataclass(frozen=True)
class DerivedOrbit:
    semi_major_axis_km: float
    perigee_km: float
    apogee_km: float
    period_minutes: float
    regime: Regime


def derive_orbit(mean_motion_rev_day: float, eccentricity: float, inclination_deg: float) -> DerivedOrbit:
    if mean_motion_rev_day <= 0 or not 0 <= eccentricity < 1 or not 0 <= inclination_deg <= 180:
        raise ValueError("Orbital elements are outside supported Earth-orbit ranges")
    angular_rate = mean_motion_rev_day * 2 * math.pi / 86400
    semi_major = (EARTH_MU_KM3_S2 / angular_rate**2) ** (1 / 3)
    perigee = semi_major * (1 - eccentricity) - EARTH_RADIUS_KM
    apogee = semi_major * (1 + eccentricity) - EARTH_RADIUS_KM
    period = 1440 / mean_motion_rev_day
    return DerivedOrbit(
        semi_major,
        perigee,
        apogee,
        period,
        classify_regime(perigee, apogee, eccentricity, inclination_deg),
    )


def classify_regime(perigee_km: float, apogee_km: float, eccentricity: float, inclination_deg: float) -> Regime:
    mean_altitude = (perigee_km + apogee_km) / 2
    if apogee_km <= 2000:
        return "LEO"
    if abs(mean_altitude - 35786) <= 200 and eccentricity <= 0.05 and inclination_deg <= 15:
        return "GEO"
    if perigee_km > 35986:
        return "SUPER_GEO"
    if eccentricity >= 0.25 or (perigee_km < 35586 <= apogee_km):
        return "GTO_HEO"
    if perigee_km > 2000 and apogee_km < 35586:
        return "MEO"
    return "OTHER"


def choose_snapshot_record(records: list[dict], target: datetime) -> tuple[dict | None, str]:
    candidates = [row for row in records if row["epoch"] <= target]
    if not candidates:
        return None, "missing"
    selected = max(candidates, key=lambda row: row["epoch"])
    age_days = (target - selected["epoch"]).total_seconds() / 86400
    if age_days <= 30:
        return selected, "current"
    if age_days <= 90:
        return selected, "stale"
    return None, "too_stale"
