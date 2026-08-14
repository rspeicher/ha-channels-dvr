"""Binary sensor entities for Channels DVR."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    """Set up Channels DVR binary sensors."""
    async_add_entities([ChannelsDVRPlayingBinarySensor(entry.runtime_data)])


class ChannelsDVRPlayingBinarySensor(ChannelsDVREntity, BinarySensorEntity):
    """Whether anything is currently streaming from the server."""

    _attr_translation_key = "playing"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator: ChannelsDVRCoordinator) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_playing"

    @property
    def is_on(self) -> bool:
        """Return True when at least one stream is active."""
        return bool(self.coordinator.data.streams)
