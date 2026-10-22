import json
from datetime import date

import pytest

from oei_api.demo_data import positions
from oei_pipeline.publication import publish_snapshot
from oei_pipeline.quality import validate_snapshot_records
from oei_pipeline.storage import LocalArtifactStore


def sample_records() -> list[dict]:
    return [item.model_dump(mode="json") for item in positions(date(2026, 9, 1), limit=10)]


def test_publication_writes_pointer_last_and_valid_artifacts(tmp_path) -> None:
    manifest = publish_snapshot(
        LocalArtifactStore(tmp_path),
        "test-release",
        date(2026, 9, 1),
        "monthly",
        sample_records(),
        {"fixture": "abc123"},
    )
    pointer = json.loads((tmp_path / "current.json").read_text(encoding="utf-8"))
    assert pointer["release_id"] == manifest.release_id
    assert pointer["row_count"] == 10
    assert (tmp_path / pointer["artifacts"]["arrow"]["key"]).exists()
    assert (tmp_path / pointer["artifacts"]["parquet"]["key"]).exists()


def test_duplicate_catalog_ids_reject_publication() -> None:
    records = sample_records()
    records[1]["norad_id"] = records[0]["norad_id"]
    issues = validate_snapshot_records(records)
    assert any(issue.code == "duplicate_catalog_id" and issue.fatal for issue in issues)


def test_artifact_store_rejects_path_escape(tmp_path) -> None:
    with pytest.raises(ValueError, match="escapes"):
        LocalArtifactStore(tmp_path).put_bytes("../outside", b"x", "text/plain")


def test_development_snapshot_exercises_forty_thousand_points() -> None:
    assert len(positions(date(2026, 9, 1))) == 40_000
