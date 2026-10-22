from datetime import UTC, datetime, timedelta

import pytest

from oei_pipeline.analytics import choose_snapshot_record, classify_regime, derive_orbit


def test_iss_like_orbit_is_leo() -> None:
    orbit = derive_orbit(15.5, 0.0004, 51.64)
    assert orbit.regime == "LEO"
    assert 380 < orbit.perigee_km < 450
    assert 90 < orbit.period_minutes < 95


@pytest.mark.parametrize(
    ("perigee", "apogee", "eccentricity", "inclination", "expected"),
    [
        (400, 410, 0.001, 51, "LEO"),
        (20000, 20200, 0.01, 55, "MEO"),
        (35780, 35790, 0.001, 0.2, "GEO"),
        (200, 36000, 0.7, 28, "GTO_HEO"),
        (40000, 45000, 0.02, 5, "SUPER_GEO"),
    ],
)
def test_regime_boundaries(
    perigee: float, apogee: float, eccentricity: float, inclination: float, expected: str
) -> None:
    assert classify_regime(perigee, apogee, eccentricity, inclination) == expected


def test_snapshot_selection_marks_stale() -> None:
    target = datetime(2026, 1, 1, tzinfo=UTC)
    record = {"epoch": target - timedelta(days=45), "id": 1}
    selected, quality = choose_snapshot_record([record], target)
    assert selected == record
    assert quality == "stale"
