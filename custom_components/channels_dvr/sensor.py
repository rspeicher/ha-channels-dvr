"""Sensor entities for Channels DVR."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import ChannelsDVRConfigEntry, ChannelsDVRCoordinator
from .entity import ChannelsDVREntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ChannelsDVRConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Channels DVR sensors."""
    async_add_entities([ChannelsDVRActiveStreamsSensor(entry.runtime_data)])


class ChannelsDVRActiveStreamsSensor(ChannelsDVREntity, SensorEntity):
    """Number of streams currently playing from the server."""

    _attr_translation_key = "active_streams"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:play-network"

    def __init__(self, coordinator: ChannelsDVRCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_active_streams"

    @property
    def native_value(self) -> int:
        """Return the number of active streams."""
        return len(self.coordinator.data.streams)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose per-stream detail for automations and templates."""
        return {
            "streams": [
                {
                    "description": stream.description,
                    "file_id": stream.file_id,
                    "client": stream.client,
                }
                for stream in self.coordinator.data.streams
            ]
        }
