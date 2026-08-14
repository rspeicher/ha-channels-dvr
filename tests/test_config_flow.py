"""Tests for the Channels DVR config flow."""

from unittest.mock import patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.channels_dvr.api import ChannelsDVRConnectionError
from custom_components.channels_dvr.const import DOMAIN
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_SSL, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

USER_INPUT = {
    CONF_HOST: "dvr.local",
    CONF_PORT: 8089,
    CONF_SSL: False,
    CONF_VERIFY_SSL: True,
}


async def test_user_flow_success(hass: HomeAssistant) -> None:
    """A reachable server creates a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with (
        patch(
            "custom_components.channels_dvr.config_flow.ChannelsDVRClient.get_status",
            return_value={"version": "2026.08.07.0346"},
        ),
        patch(
            "custom_components.channels_dvr.async_setup_entry", return_value=True
        ) as mock_setup,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Channels DVR (dvr.local)"
    assert result["data"] == USER_INPUT
    assert len(mock_setup.mock_calls) == 1


async def test_user_flow_cannot_connect(hass: HomeAssistant) -> None:
    """An unreachable server shows an error and allows retry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.channels_dvr.config_flow.ChannelsDVRClient.get_status",
        side_effect=ChannelsDVRConnectionError("boom"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_user_flow_duplicate_aborts(hass: HomeAssistant) -> None:
    """Configuring the same host and port twice aborts."""
    MockConfigEntry(domain=DOMAIN, data=USER_INPUT).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], USER_INPUT
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
