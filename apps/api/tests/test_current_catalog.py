from datetime import UTC, datetime

import httpx
import pytest

from oei_api import current_catalog as catalog


def row():
    return dict(
        NORAD_CAT_ID=25544,
        OBJECT_NAME="ISS",
        OBJECT_ID="1998-067A",
        EPOCH="2026-09-22T00:00:00",
        MEAN_MOTION=15.49,
        ECCENTRICITY=0.0004,
        INCLINATION=51.64,
        RA_OF_ASC_NODE=120,
        ARG_OF_PERICENTER=40,
        MEAN_ANOMALY=80,
        EPHEMERIS_TYPE=0,
        CLASSIFICATION_TYPE="U",
        ELEMENT_SET_NO=999,
        REV_AT_EPOCH=12345,
        BSTAR=0.0001,
        MEAN_MOTION_DOT=0.00001,
        MEAN_MOTION_DDOT=0,
    )


def test_real_propagation_deduplication_and_validation():
    target = datetime(2026, 9, 22, tzinfo=UTC)
    result = catalog.build_snapshot([row(), row(), {"NORAD_CAT_ID": "bad"}], target)
    assert result["object_count"] == 1
    position = result["positions"][0]
    assert position["norad_id"] == 25544
    assert position["category"] == "active_payload"
    assert 1.03 < sum(position[k] ** 2 for k in ("x", "y", "z")) ** 0.5 < 1.1
    assert catalog.build_snapshot([row()], datetime(2027, 1, 1, tzinfo=UTC))["positions"] == []


@pytest.mark.asyncio
async def test_failure_is_not_synthetic(monkeypatch, tmp_path):
    monkeypatch.setattr(catalog, "CACHE", tmp_path / "missing.json")
    monkeypatch.setattr(catalog, "_catalog", None)
    monkeypatch.setattr(catalog, "_result", None)
    monkeypatch.setattr(catalog, "_retry_at", float("inf"))
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as error:
        await catalog.current_snapshot()
    assert error.value.status_code == 503


@pytest.mark.asyncio
async def test_cached_response_has_real_provenance(monkeypatch):
    now = datetime.now(UTC)
    record = row()
    record["EPOCH"] = now.replace(tzinfo=None).isoformat()
    monkeypatch.setattr(catalog, "_catalog", dict(rows=[record], retrieved_at=now.isoformat(), checksum="a" * 64))
    monkeypatch.setattr(catalog, "_result", None)
    result = await catalog.current_snapshot()
    assert result["meta"]["synthetic"] is False
    assert result["data"]["positions"]
    assert await catalog.current_snapshot() is result


@pytest.mark.asyncio
async def test_failed_refresh_retains_cached_catalog(monkeypatch):
    now = datetime.now(UTC)
    record = row()
    record["EPOCH"] = now.replace(tzinfo=None).isoformat()
    from datetime import timedelta

    monkeypatch.setattr(
        catalog,
        "_catalog",
        dict(rows=[record], retrieved_at=(now - timedelta(hours=13)).isoformat(), checksum="b" * 64),
    )
    monkeypatch.setattr(catalog, "_result", None)
    monkeypatch.setattr(catalog, "_retry_at", 0)

    async def unavailable(*args, **kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx.AsyncClient, "get", unavailable)
    result = await catalog.current_snapshot()
    assert result["meta"]["synthetic"] is False
    assert any("STALE" in warning for warning in result["meta"]["warnings"])


@pytest.mark.asyncio
async def test_successful_download_publishes_atomic_cache(monkeypatch, tmp_path):
    now = datetime.now(UTC)
    record = row()
    record["EPOCH"] = now.replace(tzinfo=None).isoformat()
    monkeypatch.setattr(catalog, "CACHE", tmp_path / "active.json")
    monkeypatch.setattr(catalog, "_catalog", None)
    monkeypatch.setattr(catalog, "_result", None)
    monkeypatch.setattr(catalog, "_retry_at", 0)

    async def download(*args, **kwargs):
        return httpx.Response(200, json=[record], request=httpx.Request("GET", catalog.URL))

    monkeypatch.setattr(httpx.AsyncClient, "get", download)
    result = await catalog.current_snapshot()
    assert result["data"]["object_count"] == 1
    assert result["data"]["positions"][0]["name"] == "ISS"
    assert catalog.CACHE.exists()
    assert not catalog.CACHE.with_suffix(".tmp").exists()
    assert result["meta"]["freshness_hours"] == 0
