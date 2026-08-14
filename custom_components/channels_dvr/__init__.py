"""The Channels DVR integration."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import ChannelsDVRConfigEntry, ChannelsDVRCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.BUTTON, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ChannelsDVRConfigEntry) -> bool:
    """Set up Channels DVR from a config entry."""
    coordinator = ChannelsDVRCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: ChannelsDVRConfigEntry
) -> bool:
    """Unload a Channels DVR config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
