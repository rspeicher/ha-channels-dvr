"""DataUpdateCoordinator for Channels DVR."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SSL, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ChannelsDVRClient, ChannelsDVRConnectionError, ChannelsDVRError
from .const import (
    ACTIVITY_KEY_RE,
    ACTIVITY_POSITION_RE,
    DOMAIN,
    LOGGER,
    M3U_PREFIX,
    SCAN_INTERVAL,
    TITLE_YEAR_RE,
)

type ChannelsDVRConfigEntry = ConfigEntry[ChannelsDVRCoordinator]


@dataclass(frozen=True)
class FileMetadata:
    """Metadata about the file behind a stream, from GET /dvr/files/{id}."""

    content_type: str
    title: str | None = None
    series_title: str | None = None
    season: int | None = None
    episode: int | None = None
    duration: int | None = None
    library: str | None = None
    year: int | None = None


@dataclass(frozen=True)
class StreamInfo:
    """A single active stream reported by the server."""

    session_key: str
    description: str
    file_id: int | None
    client: str | None
    position: int | None = None
    media: FileMetadata | None = None


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
        position: int | None = None
        if match := ACTIVITY_KEY_RE.search(key):
            file_id = int(match.group(1))
            client = match.group(2)
        if match := ACTIVITY_POSITION_RE.search(description):
            hours, minutes, seconds = match.groups()
            position = (
                int(hours or 0) * 3600 + int(minutes or 0) * 60 + int(float(seconds))
            )
        streams.append(
            StreamInfo(
                session_key=key,
                description=description,
                file_id=file_id,
                client=client,
                position=position,
            )
        )
    return streams


def parse_file_metadata(file: dict[str, Any]) -> FileMetadata:
    """Reduce a /dvr/files/{id} response to the fields exposed as attributes."""
    airing = file.get("Airing") or {}
    categories = airing.get("Categories") or []

    if "Episode" in categories:
        content_type = "episode"
    elif "Movie" in categories:
        content_type = "movie"
    else:
        content_type = "video"

    title = airing.get("Title")
    series_title = None
    if content_type == "episode":
        series_title = title
        title = airing.get("EpisodeTitle") or title
    elif title:
        title = TITLE_YEAR_RE.sub("", title)

    import_path = file.get("ImportPath")
    duration = file.get("Duration")

    return FileMetadata(
        content_type=content_type,
        title=title,
        series_title=series_title,
        season=airing.get("SeasonNumber"),
        episode=airing.get("EpisodeNumber"),
        duration=round(duration) if duration is not None else None,
        library=import_path.rsplit("/", 1)[-1] if import_path else None,
        year=airing.get("ReleaseYear"),
    )


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
        self._file_cache: dict[int, FileMetadata | None] = {}

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

        streams = [
            replace(stream, media=await self._async_file_metadata(stream.file_id))
            for stream in parse_activity(dvr.get("activity") or {})
        ]

        # Keep only metadata for files that are still streaming, so the cache
        # stays bounded by the number of concurrent streams.
        active_ids = {stream.file_id for stream in streams}
        self._file_cache = {
            file_id: metadata
            for file_id, metadata in self._file_cache.items()
            if file_id in active_ids
        }

        return ChannelsDVRData(streams=streams, dvr=dvr)

    async def _async_file_metadata(self, file_id: int | None) -> FileMetadata | None:
        """Return cached metadata for a file, fetching it on first sight.

        Metadata is best-effort: a lookup failure is logged and cached as None
        for as long as the stream stays active, never failing the update.
        """
        if file_id is None:
            return None
        if file_id not in self._file_cache:
            try:
                file = await self.client.get_file(file_id)
                self._file_cache[file_id] = parse_file_metadata(file)
            except ChannelsDVRError as err:
                LOGGER.warning("Could not fetch metadata for file %s: %s", file_id, err)
                self._file_cache[file_id] = None
        return self._file_cache[file_id]
