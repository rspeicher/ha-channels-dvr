"""Async client for the Channels DVR server API.

This module is intentionally free of Home Assistant imports so it can be
tested (and potentially reused) on its own.

The full file list endpoint (GET /dvr/files) is deliberately unsupported:
its response is enormous (~85MB) and has crashed servers.
"""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp
from yarl import URL

REQUEST_TIMEOUT = 10


class ChannelsDVRError(Exception):
    """Base exception for Channels DVR client errors."""


class ChannelsDVRConnectionError(ChannelsDVRError):
    """Raised when the Channels DVR server cannot be reached."""


class ChannelsDVRClient:
    """Minimal client for the Channels DVR local API."""

    def __init__(
        self,
        host: str,
        port: int,
        *,
        ssl: bool = False,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the client with a caller-owned aiohttp session."""
        scheme = "https" if ssl else "http"
        self.base_url = URL(f"{scheme}://{host}:{port}")
        self._session = session

    async def _request(self, method: str, path: str) -> Any:
        """Perform a request and return the decoded JSON body (if any)."""
        url = self.base_url.joinpath(*path.split("/"))
        try:
            async with asyncio.timeout(REQUEST_TIMEOUT):
                response = await self._session.request(method, url)
                response.raise_for_status()
                if response.content_type == "application/json":
                    return await response.json()
                return await response.text()
        except (TimeoutError, aiohttp.ClientError) as err:
            raise ChannelsDVRConnectionError(
                f"Error communicating with Channels DVR at {self.base_url}: {err}"
            ) from err

    async def get_status(self) -> dict[str, Any]:
        """Return server info: version, os, arch, subscription, etc."""
        return await self._request("GET", "status")

    async def get_dvr(self) -> dict[str, Any]:
        """Return top-level DVR state, including the activity map."""
        return await self._request("GET", "dvr")

    async def get_lineups(self) -> dict[str, str]:
        """Return the map of device IDs to bound guide lineups."""
        return await self._request("GET", "dvr/lineups")

    async def refresh_source(self, name: str) -> None:
        """Trigger a playlist refresh for an M3U source."""
        await self._request("POST", f"providers/m3u/sources/{name}/refresh")
