"""Diagnostics support for Muller Intuitiv."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_ACCESS_TOKEN, CONF_REFRESH_TOKEN

# Keys to redact for privacy
REDACT_KEYS = {
    CONF_ACCESS_TOKEN,
    CONF_REFRESH_TOKEN,
    "access_token",
    "refresh_token",
    "username",
    "password",
    "id",
}

async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    return {
        "entry": async_redact_data(entry.as_dict(), REDACT_KEYS),
        "coordinator_data": async_redact_data(coordinator.data, REDACT_KEYS),
        "last_update_success": coordinator.last_update_success,
        "update_interval": coordinator.update_interval.total_seconds(),
        "api_base_url": coordinator.api._session.base_url if hasattr(coordinator.api, "_session") else None,
    }