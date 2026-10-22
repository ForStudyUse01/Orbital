from __future__ import annotations

import argparse
import asyncio
import json
import os
from dataclasses import asdict
from datetime import UTC, date, datetime
from pathlib import Path

import httpx

from oei_api.demo_data import positions

from .propagation import propagate_omm_rows
from .providers import SpaceTrackClient, fetch_celestrak_group, fetch_celestrak_satcat
from .publication import publish_snapshot
from .storage import artifact_store_from_environment


async def sync_current(output: Path) -> None:
    store = artifact_store_from_environment(output)
    async with httpx.AsyncClient(follow_redirects=True) as client:
        artifacts = [await fetch_celestrak_group(client), await fetch_celestrak_satcat(client)]
        username = os.getenv("SPACE_TRACK_USERNAME")
        password = os.getenv("SPACE_TRACK_PASSWORD")
        space_track = await SpaceTrackClient(username, password).latest_gp(client) if username and password else None
        if space_track:
            artifacts.append(space_track)
    retrieved_at = datetime.now(UTC)
    manifest = {"retrieved_at": retrieved_at.isoformat(), "artifacts": []}
    for artifact in artifacts:
        key = f"raw/{artifact.source}/{retrieved_at:%Y/%m/%d}/{artifact.sha256}.bin"
        store.put_bytes(key, artifact.content, artifact.content_type)
        manifest["artifacts"].append(
            {"source": artifact.source, "sha256": artifact.sha256, "bytes": len(artifact.content), "key": key}
        )
    manifest_content = json.dumps(manifest, indent=2).encode()
    store.put_bytes(f"ingestion/{retrieved_at:%Y%m%dT%H%M%SZ}.json", manifest_content, "application/json")
    store.put_bytes("ingestion/latest.json", manifest_content, "application/json")
    if space_track:
        records, quarantine = propagate_omm_rows(json.loads(space_track.content), retrieved_at)
        release_id = f"current-{retrieved_at:%Y%m%dT%H%M%SZ}"
        release = publish_snapshot(
            store,
            release_id,
            retrieved_at.date(),
            "current",
            records,
            {artifact.source: artifact.sha256 for artifact in artifacts},
        )
        quality_content = json.dumps(
            {"release_id": release.release_id, "accepted": len(records), "quarantined": quarantine}, indent=2
        ).encode()
        store.put_bytes(f"releases/{release_id}/quality.json", quality_content, "application/json")


def fixture_release(output: Path, release_id: str, snapshot_date: date) -> None:
    store = artifact_store_from_environment(output)
    records = [item.model_dump(mode="json") for item in positions(snapshot_date)]
    manifest = publish_snapshot(
        store,
        release_id,
        snapshot_date,
        "current",
        records,
        {"development-fixture": "deterministic-seed-42164"},
    )
    print(json.dumps(asdict(manifest), indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="OEI ingestion and release utilities")
    subparsers = parser.add_subparsers(dest="command", required=True)
    sync = subparsers.add_parser("sync-current", help="Download immutable current-source inputs")
    sync.add_argument("--output", type=Path, default=Path("data/raw"))
    fixture = subparsers.add_parser("fixture-release", help="Publish a validated deterministic release")
    fixture.add_argument("--output", type=Path, default=Path("data/public"))
    fixture.add_argument("--release-id", default="demo-2026.09")
    fixture.add_argument("--date", type=date.fromisoformat, default=date.today())
    args = parser.parse_args()
    if args.command == "sync-current":
        asyncio.run(sync_current(args.output))
    else:
        fixture_release(args.output, args.release_id, args.date)


if __name__ == "__main__":
    main()
