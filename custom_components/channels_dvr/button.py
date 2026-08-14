"""Button entities for Channels DVR M3U source refreshes."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import slugify

from .api import ChannelsDVRError
from .coordinator import ChannelsDVRConfigEntry, ChannelsDVRCoordinator
from .entity import ChannelsDVREntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ChannelsDVRConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up one refresh button per M3U source."""
    coordinator = entry.runtime_data
    async_add_entities(
        ChannelsDVRRefreshSourceButton(coordinator, source)
        for source in coordinator.sources
    )


class ChannelsDVRRefreshSourceButton(ChannelsDVREntity, ButtonEntity):
    """Button that refreshes the playlist of one M3U source."""

    _attr_icon = "mdi:playlist-refresh"

    def __init__(self, coordinator: ChannelsDVRCoordinator, source: str) -> None:
        """Initialize the button for a source."""
        super().__init__(coordinator)
        self._source = source
        self._attr_name = f"Refresh {source} M3U"
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_refresh_{slugify(source)}"
        )

    async def async_press(self) -> None:
        """Trigger the M3U refresh on the server."""
        try:
            await self.coordinator.client.refresh_source(self._source)
        except ChannelsDVRError as err:
            raise HomeAssistantError(
                f"Failed to refresh M3U source {self._source}: {err}"
            ) from err
