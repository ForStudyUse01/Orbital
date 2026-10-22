from __future__ import annotations

import os
from pathlib import Path
from typing import Protocol

import boto3


class ArtifactStore(Protocol):
    def put_bytes(self, key: str, content: bytes, content_type: str) -> None: ...


class LocalArtifactStore:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def put_bytes(self, key: str, content: bytes, content_type: str) -> None:
        del content_type
        destination = (self.root / key).resolve()
        if self.root not in destination.parents:
            raise ValueError("Artifact key escapes the configured storage root")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(f"{destination.suffix}.tmp")
        temporary.write_bytes(content)
        temporary.replace(destination)


class R2ArtifactStore:
    def __init__(self, endpoint: str, bucket: str, access_key: str, secret_key: str) -> None:
        self.bucket = bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="auto",
        )

    def put_bytes(self, key: str, content: bytes, content_type: str) -> None:
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content,
            ContentType=content_type,
            CacheControl="public, max-age=31536000, immutable" if key.startswith("releases/") else "no-cache",
        )


def artifact_store_from_environment(local_root: Path) -> ArtifactStore:
    values = {
        "endpoint": os.getenv("R2_ENDPOINT"),
        "bucket": os.getenv("R2_BUCKET"),
        "access_key": os.getenv("R2_ACCESS_KEY_ID"),
        "secret_key": os.getenv("R2_SECRET_ACCESS_KEY"),
    }
    if all(values.values()):
        return R2ArtifactStore(**values)  # type: ignore[arg-type]
    return LocalArtifactStore(local_root)
