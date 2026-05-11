"""Config flow for Muller Intuitiv integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, CONF_HOME_ID, CONF_ACCESS_TOKEN, CONF_REFRESH_TOKEN, CONF_EXPIRES_IN, CONF_EXPIRES_AT
from .api import (
    MullerIntuitivApi,
    MullerIntuitivAuthError,
    MullerIntuitivApiError,
    MullerIntuitivTimeoutError,
    MullerIntuitivConnectionError,
)

_LOGGER = logging.getLogger(__name__)

class MullerIntuitivConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Muller Intuitiv."""

    VERSION = 1

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            api = MullerIntuitivApi(session)

            try:
                # Attempt login
                tokens = await api.login(user_input[CONF_USERNAME], user_input[CONF_PASSWORD])
                
                # Fetch homes data to get the home_id
                home_data = await api.get_homes_data()
                home_id = home_data.get("id")
                home_name = home_data.get("name", "Muller Intuitiv Home")

                if not home_id:
                    errors["base"] = "no_home_found"
                else:
                    await self.async_set_unique_id(home_id)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=home_name,
                        data={
                            CONF_USERNAME: user_input[CONF_USERNAME],
                            CONF_PASSWORD: user_input[CONF_PASSWORD],
                            CONF_HOME_ID: home_id,
                            CONF_ACCESS_TOKEN: tokens.get("access_token"),
                            CONF_REFRESH_TOKEN: tokens.get("refresh_token"),
                            CONF_EXPIRES_IN: tokens.get("expires_in"),
                            CONF_EXPIRES_AT: tokens.get("expires_at"),
                        },
                    )

            except MullerIntuitivAuthError:
                errors["base"] = "invalid_auth"
            except (MullerIntuitivTimeoutError, MullerIntuitivConnectionError):
                errors["base"] = "cannot_connect"
            except MullerIntuitivApiError:
                errors["base"] = "api_error"
            except Exception as ex:
                _LOGGER.exception("Unexpected exception: %s", ex)
                errors["base"] = "unknown"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }
        )

        return self.async_show_form(
            step_id="user", data_schema=data_schema, errors=errors
        )
