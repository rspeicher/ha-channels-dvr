"""Base entity for the Channels DVR integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ChannelsDVRCoordinator


class ChannelsDVREntity(CoordinatorEntity[ChannelsDVRCoordinator]):
    """Defines a Channels DVR entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: ChannelsDVRCoordinator) -> None:
        """Initialize a Channels DVR entity."""
        super().__init__(coordinator=coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name="Channels DVR",
            manufacturer="Fancy Bits, LLC",
            model="Channels DVR Server",
            sw_version=coordinator.server_info.get("version"),
            configuration_url=str(coordinator.client.base_url),
        )
