import pytest
from httpx import ASGITransport, AsyncClient

from oei_api.main import app


@pytest.mark.asyncio
async def test_overview_has_provenance() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["total_objects"] > 0
    assert len(body["meta"]["sources"]) >= 3
    assert body["meta"]["synthetic"] is True


@pytest.mark.asyncio
async def test_invalid_timeline_range_is_rejected() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/timeline?start=2020&end=2000")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_local_vite_origin_is_allowed() -> None:
    origin = "http://127.0.0.1:5173"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/overview", headers={"Origin": origin})

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


@pytest.mark.asyncio
async def test_every_demo_scene_object_has_a_detail_record() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/objects/49999?source=demo")

    assert response.status_code == 200
    assert response.json()["data"]["norad_id"] == 49999
    assert response.json()["data"]["name"].startswith("Demo ")
