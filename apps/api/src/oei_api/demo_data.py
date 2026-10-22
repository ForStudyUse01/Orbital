from __future__ import annotations

import math
import random
from datetime import UTC, date, datetime

from .schemas import Event, OrbitalObject, Position

NOW = datetime(2026, 9, 21, 12, 0, tzinfo=UTC)

CATEGORIES = ["active_payload", "inactive_payload", "debris", "rocket_body", "unknown"]
REGIMES = ["LEO", "MEO", "GEO", "GTO_HEO", "SUPER_GEO", "OTHER"]


def timeline() -> list[dict]:
    points = []
    for year in range(1957, 2027):
        t = year - 1957
        constellation = max(0, year - 2018) ** 2 * 165
        active = int(1 + t * 24 + max(0, year - 2013) ** 2 * 41 + constellation)
        inactive = int(t * 33 + max(0, year - 1990) * 14)
        debris = int(t * 91 + max(0, year - 2007) * 145 + max(0, year - 2021) * 210)
        rockets = int(t * 31)
        unknown = max(1, int(t * 0.8))
        points.append(
            {
                "date": date(year, 1, 1),
                "total": active + inactive + debris + rockets + unknown,
                "active_payload": active,
                "inactive_payload": inactive,
                "debris": debris,
                "rocket_body": rockets,
                "unknown": unknown,
            }
        )
    return points


TIMELINE = timeline()

EVENTS = [
    Event(
        id="fengyun-1c-2007",
        name="Fengyun-1C destruction",
        date=date(2007, 1, 11),
        event_type="fragmentation",
        assessed_cause="Intentional anti-satellite test",
        parent_norad_ids=[25730],
        fragments_catalogued=3532,
        fragments_remaining=2793,
        altitude_km=850,
        inclination_deg=98.6,
        description=("A high-altitude polar-orbit fragmentation that produced a persistent debris cohort."),
        deep_replay=True,
    ),
    Event(
        id="iridium-cosmos-2009",
        name="Iridium 33–Cosmos 2251 collision",
        date=date(2009, 2, 10),
        event_type="collision",
        assessed_cause="Accidental collision",
        parent_norad_ids=[24946, 22675],
        fragments_catalogued=2372,
        fragments_remaining=1321,
        altitude_km=790,
        inclination_deg=86.4,
        description="The first accidental hypervelocity collision between two intact satellites.",
        deep_replay=True,
    ),
    Event(
        id="cosmos-1408-2021",
        name="Cosmos 1408 destruction",
        date=date(2021, 11, 15),
        event_type="fragmentation",
        assessed_cause="Intentional anti-satellite test",
        parent_norad_ids=[13552],
        fragments_catalogued=1785,
        fragments_remaining=364,
        altitude_km=480,
        inclination_deg=82.6,
        description=("A lower-LEO breakup whose fragments initially intersected heavily used orbital bands."),
        deep_replay=True,
    ),
]


def objects(count: int = 850) -> list[OrbitalObject]:
    rng = random.Random(42164)
    results: list[OrbitalObject] = []
    category_weights = [0.39, 0.08, 0.42, 0.10, 0.01]
    regime_weights = [0.78, 0.06, 0.07, 0.06, 0.02, 0.01]
    countries = ["US", "CIS", "PRC", "ESA", "IND", "JPN", "OTHER"]
    for index in range(count):
        category = rng.choices(CATEGORIES, category_weights)[0]
        regime = rng.choices(REGIMES, regime_weights)[0]
        if regime == "LEO":
            altitude = max(180.0, min(1950.0, rng.gauss(620, 245)))
        elif regime == "MEO":
            altitude = rng.uniform(2_100, 28_000)
        elif regime == "GEO":
            altitude = rng.gauss(35_786, 65)
        elif regime == "GTO_HEO":
            altitude = rng.uniform(8_000, 34_500)
        elif regime == "SUPER_GEO":
            altitude = rng.uniform(36_100, 60_000)
        else:
            altitude = rng.uniform(2_000, 60_000)
        eccentricity = rng.uniform(0, 0.02) if regime in {"LEO", "MEO", "GEO"} else rng.uniform(0.1, 0.72)
        delta = altitude * eccentricity
        inclination = rng.choice([rng.gauss(53, 4), rng.gauss(98, 2), rng.uniform(0, 120)])
        launched = date(rng.randint(1960, 2026), rng.randint(1, 12), 1)
        results.append(
            OrbitalObject(
                norad_id=10000 + index,
                name=f"OEI {category.replace('_', ' ').upper()} {index + 1}",
                international_designator=f"{launched.year}-{index % 999:03d}{chr(65 + index % 24)}",
                category=category,
                regime=regime,
                country=rng.choice(countries),
                launch_date=launched,
                altitude_km=round(altitude, 2),
                perigee_km=round(max(90, altitude - delta), 2),
                apogee_km=round(altitude + delta, 2),
                inclination_deg=round(max(0, min(180, inclination)), 3),
                period_minutes=round(84.0 * ((6378 + altitude) / 6558) ** 1.5, 2),
                eccentricity=round(eccentricity, 7),
                quality="current" if rng.random() > 0.04 else "stale",
            )
        )
    return results


OBJECTS = objects()


def positions(snapshot_date: date, limit: int = 40_000) -> list[Position]:
    seed = snapshot_date.toordinal()
    rng = random.Random(seed)
    result: list[Position] = []
    for index in range(limit):
        obj = OBJECTS[index % len(OBJECTS)]
        radial_jitter = rng.uniform(-0.006, 0.006)
        radius = 1.0 + obj.altitude_km / 6378.137 + radial_jitter
        phase = (index * 0.61803398875 + seed * 0.0027) * math.tau
        inc = math.radians(obj.inclination_deg + rng.uniform(-0.3, 0.3))
        x = radius * math.cos(phase)
        y = radius * math.sin(phase) * math.sin(inc)
        z = radius * math.sin(phase) * math.cos(inc)
        result.append(Position(norad_id=10000 + index, x=x, y=y, z=z, category=obj.category, regime=obj.regime))
    return result
