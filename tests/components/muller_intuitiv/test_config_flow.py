"""Tests for the Muller Intuitiv config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResultType

from custom_components.muller_intuitiv.const import (
    CONF_ACCESS_TOKEN,
    CONF_EXPIRES_AT,
    CONF_EXPIRES_IN,
    CONF_HOME_ID,
    CONF_REFRESH_TOKEN,
    DOMAIN,
)
from custom_components.muller_intuitiv.exceptions import (
    MullerIntuitivAuthError,
    MullerIntuitivConnectionError,
)

pytestmark = pytest.mark.usefixtures("enable_custom_integrations")


async def test_user_flow_creates_entry_without_password(hass):
    """Test a successful user flow stores tokens but not the password."""
    with (
        patch(
            "custom_components.muller_intuitiv.config_flow.MullerIntuitivApi.login",
            AsyncMock(
                return_value={
                    "access_token": "access-token",
                    "refresh_token": "refresh-token",
                    "expires_in": 3600,
                    "expires_at": 1234567890,
                }
            ),
        ),
        patch(
            "custom_components.muller_intuitiv.config_flow.MullerIntuitivApi.get_homes_data",
            AsyncMock(return_value={"id": "home-id", "name": "Home"}),
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_USERNAME: "user@example.com", CONF_PASSWORD: "secret"},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Home"
    assert result["data"] == {
        CONF_USERNAME: "user@example.com",
        CONF_HOME_ID: "home-id",
        CONF_ACCESS_TOKEN: "access-token",
        CONF_REFRESH_TOKEN: "refresh-token",
        CONF_EXPIRES_IN: 3600,
        CONF_EXPIRES_AT: 1234567890,
    }
    assert CONF_PASSWORD not in result["data"]


async def test_user_flow_invalid_auth(hass):
    """Test invalid credentials are reported as an auth error."""
    with patch(
        "custom_components.muller_intuitiv.config_flow.MullerIntuitivApi.login",
        AsyncMock(side_effect=MullerIntuitivAuthError),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_USERNAME: "user@example.com", CONF_PASSWORD: "bad-password"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_user_flow_cannot_connect(hass):
    """Test connection errors are reported as cannot_connect."""
    with patch(
        "custom_components.muller_intuitiv.config_flow.MullerIntuitivApi.login",
        AsyncMock(side_effect=MullerIntuitivConnectionError),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={CONF_USERNAME: "user@example.com", CONF_PASSWORD: "secret"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
