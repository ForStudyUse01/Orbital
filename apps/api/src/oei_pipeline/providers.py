from __future__ import annotations

import hashlib
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class DownloadedArtifact:
    source: str
    content: bytes
    content_type: str
    sha256: str


async def fetch_celestrak_satcat(client: httpx.AsyncClient) -> DownloadedArtifact:
    url = "https://celestrak.org/pub/satcat.csv"
    response = await client.get(url, timeout=60)
    response.raise_for_status()
    return DownloadedArtifact(
        "celestrak-satcat",
        response.content,
        response.headers.get("content-type", "text/csv"),
        hashlib.sha256(response.content).hexdigest(),
    )


async def fetch_celestrak_group(client: httpx.AsyncClient, group: str = "active") -> DownloadedArtifact:
    url = "https://celestrak.org/NORAD/elements/gp.php"
    response = await client.get(url, params={"GROUP": group, "FORMAT": "CSV"}, timeout=60)
    response.raise_for_status()
    return DownloadedArtifact(
        f"celestrak-gp-{group}",
        response.content,
        response.headers.get("content-type", "text/csv"),
        hashlib.sha256(response.content).hexdigest(),
    )


class SpaceTrackClient:
    def __init__(self, username: str, password: str) -> None:
        self.username = username
        self.password = password

    async def latest_gp(self, client: httpx.AsyncClient) -> DownloadedArtifact:
        login = await client.post(
            "https://www.space-track.org/ajaxauth/login",
            data={"identity": self.username, "password": self.password},
        )
        login.raise_for_status()
        response = await client.get(
            "https://www.space-track.org/basicspacedata/query/class/gp/decay_date/null-val/orderby/norad_cat_id/format/json",
            timeout=120,
        )
        response.raise_for_status()
        return DownloadedArtifact(
            "space-track-gp",
            response.content,
            response.headers.get("content-type", "application/json"),
            hashlib.sha256(response.content).hexdigest(),
        )
