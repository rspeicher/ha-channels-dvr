"""DataUpdateCoordinator for Channels DVR."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SSL, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ChannelsDVRClient, ChannelsDVRConnectionError
from .const import ACTIVITY_KEY_RE, DOMAIN, LOGGER, M3U_PREFIX, SCAN_INTERVAL

type ChannelsDVRConfigEntry = ConfigEntry[ChannelsDVRCoordinator]


@dataclass(frozen=True)
class StreamInfo:
    """A single active stream reported by the server."""

    session_key: str
    description: str
    file_id: int | None
    client: str | None


@dataclass(frozen=True)
class ChannelsDVRData:
    """Data fetched by the coordinator on each refresh."""

    streams: list[StreamInfo]
    dvr: dict[str, Any]


def parse_activity(activity: dict[str, str]) -> list[StreamInfo]:
    """Parse the /dvr activity map into StreamInfo records.

    Keys that don't match the expected format still count as a stream;
    they just carry no parsed file ID or client address.
    """
    streams = []
    for key, description in sorted(activity.items()):
        file_id: int | None = None
        client: str | None = None
        if match := ACTIVITY_KEY_RE.search(key):
            file_id = int(match.group(1))
            client = match.group(2)
        streams.append(
            StreamInfo(
                session_key=key,
                description=description,
                file_id=file_id,
                client=client,
            )
        )
    return streams


class ChannelsDVRCoordinator(DataUpdateCoordinator[ChannelsDVRData]):
    """Poll the Channels DVR server for activity."""

    config_entry: ChannelsDVRConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ChannelsDVRConfigEntry) -> None:
        """Initialize the coordinator and its API client."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_{entry.data[CONF_HOST]}",
            update_interval=SCAN_INTERVAL,
        )
        self.client = ChannelsDVRClient(
            entry.data[CONF_HOST],
            entry.data[CONF_PORT],
            ssl=entry.data[CONF_SSL],
            session=async_get_clientsession(
                hass, verify_ssl=entry.data[CONF_VERIFY_SSL]
            ),
        )
        self.server_info: dict[str, Any] = {}
        self.sources: list[str] = []

    async def _async_setup(self) -> None:
        """Fetch server info and enumerate M3U sources once at setup."""
        try:
            self.server_info = await self.client.get_status()
            lineups = await self.client.get_lineups()
        except ChannelsDVRConnectionError as err:
            raise UpdateFailed(err) from err
        self.sources = sorted(
            device_id.removeprefix(M3U_PREFIX)
            for device_id in lineups
            if device_id.startswith(M3U_PREFIX)
        )

    async def _async_update_data(self) -> ChannelsDVRData:
        """Fetch the DVR state and parse active streams."""
        try:
            dvr = await self.client.get_dvr()
        except ChannelsDVRConnectionError as err:
            raise UpdateFailed(err) from err
        return ChannelsDVRData(
            streams=parse_activity(dvr.get("activity") or {}),
            dvr=dvr,
        )
