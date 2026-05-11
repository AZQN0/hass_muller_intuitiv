"""DataUpdateCoordinator for Muller Intuitiv."""
import logging
from datetime import timedelta
import time

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MullerIntuitivApi, MullerIntuitivAuthError, MullerIntuitivApiError
from .const import DOMAIN, CONF_HOME_ID

_LOGGER = logging.getLogger(__name__)

class MullerIntuitivDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Muller Intuitiv data."""

    def __init__(self, hass: HomeAssistant, api: MullerIntuitivApi, entry):
        """Initialize."""
        self.api = api
        self.entry = entry
        self.home_id = entry.data[CONF_HOME_ID]

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
        )

    async def _async_update_data(self):
        """Fetch data from API endpoint."""
        try:
            # Check if token needs refresh (simplified check)
            # In a real scenario, we might track expiration time
            # For simplicity, if we get an auth error, we try to refresh and retry once
            try:
                rooms = await self.api.get_home_status(self.home_id)
            except MullerIntuitivAuthError:
                _LOGGER.info("Token expired or invalid, attempting to refresh...")
                refresh_token = self.entry.data.get("refresh_token")
                if not refresh_token:
                    raise UpdateFailed("No refresh token available")
                
                new_tokens = await self.api.refresh_token(refresh_token)
                
                # Update config entry with new tokens
                new_data = {**self.entry.data}
                new_data["access_token"] = new_tokens.get("access_token")
                new_data["refresh_token"] = new_tokens.get("refresh_token")
                new_data["expires_in"] = new_tokens.get("expires_in")
                self.hass.config_entries.async_update_entry(self.entry, data=new_data)
                
                # Retry fetch
                rooms = await self.api.get_home_status(self.home_id)
                
            return {room["id"]: room for room in rooms}

        except MullerIntuitivApiError as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}")
