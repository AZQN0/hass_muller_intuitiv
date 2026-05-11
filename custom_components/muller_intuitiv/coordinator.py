"""DataUpdateCoordinator for Muller Intuitiv."""
import logging
from datetime import timedelta
import time
from typing import Dict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    MullerIntuitivApi,
    MullerIntuitivAuthError,
    MullerIntuitivApiError,
    MullerIntuitivTimeoutError,
    MullerIntuitivConnectionError,
)
from .const import DOMAIN, CONF_HOME_ID, CONF_EXPIRES_AT, DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)

class MullerIntuitivDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Muller Intuitiv data."""

    def __init__(self, hass: HomeAssistant, api: MullerIntuitivApi, entry) -> None:
        """Initialize."""
        self.api = api
        self.entry = entry
        self.home_id: str = entry.data[CONF_HOME_ID]

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_UPDATE_INTERVAL),
        )

    async def _async_update_data(self) -> Dict[str, dict]:
        """Fetch data from API endpoint."""
        try:
            # Check if token needs refresh based on expiration time
            expires_at = self.entry.data.get(CONF_EXPIRES_AT, 0)
            current_time = int(time.time())

            # Refresh token if it expires within 5 minutes
            if current_time >= (expires_at - 300):
                _LOGGER.info("Token expired or expiring soon, attempting to refresh...")
                refresh_token = self.entry.data.get("refresh_token")
                if not refresh_token:
                    raise UpdateFailed("No refresh token available - please reconfigure integration")

                try:
                    new_tokens = await self.api.refresh_token(refresh_token)

                    # Update config entry with new tokens
                    new_data = {**self.entry.data}
                    new_data["access_token"] = new_tokens.get("access_token")
                    new_data["refresh_token"] = new_tokens.get("refresh_token")
                    new_data["expires_in"] = new_tokens.get("expires_in")
                    new_data[CONF_EXPIRES_AT] = new_tokens.get("expires_at")
                    self.hass.config_entries.async_update_entry(self.entry, data=new_data)

                    # Update API client with new token
                    self.api.set_token(new_data["access_token"])

                except MullerIntuitivAuthError as err:
                    if "expired" in str(err).lower() or "invalid" in str(err).lower():
                        _LOGGER.error("Refresh token expired or invalid - reconfiguration required: %s", err)
                        raise UpdateFailed("Authentication tokens expired - please reconfigure the integration")
                    else:
                        raise UpdateFailed(f"Token refresh failed: {err}") from err

            try:
                # Get device status (what API calls "rooms" are actually heating devices)
                devices_data = await self.api.get_home_status(self.home_id)

                # Process each heating device and create meaningful names
                for device in devices_data:
                    device_id = device.get("id")
                    muller_type = device.get("muller_type", "Unknown")

                    # Create user-friendly names
                    short_id = device_id[-4:] if device_id else "XXXX"

                    # Different naming based on device features
                    if device.get("therm_measured_temperature") is not None:
                        # Device with temperature sensor
                        device_name = f"{muller_type} Thermostat {short_id}"
                    else:
                        # Device without temperature sensor (relay/actuator only)
                        device_name = f"{muller_type} Heater {short_id}"

                    device["name"] = device_name

            except MullerIntuitivAuthError:
                # If we still get auth error after checking expiration, try refresh once more
                _LOGGER.info("Authentication failed, attempting emergency token refresh...")
                refresh_token = self.entry.data.get("refresh_token")
                if not refresh_token:
                    raise UpdateFailed("No refresh token available - please reconfigure integration")

                try:
                    new_tokens = await self.api.refresh_token(refresh_token)

                    # Update config entry with new tokens
                    new_data = {**self.entry.data}
                    new_data["access_token"] = new_tokens.get("access_token")
                    new_data["refresh_token"] = new_tokens.get("refresh_token")
                    new_data["expires_in"] = new_tokens.get("expires_in")
                    new_data[CONF_EXPIRES_AT] = new_tokens.get("expires_at")
                    self.hass.config_entries.async_update_entry(self.entry, data=new_data)

                    # Update API client with new token
                    self.api.set_token(new_data["access_token"])

                    # Retry fetch with device processing
                    devices_data = await self.api.get_home_status(self.home_id)

                    # Process each heating device and create meaningful names
                    for device in devices_data:
                        device_id = device.get("id")
                        muller_type = device.get("muller_type", "Unknown")

                        # Create user-friendly names
                        short_id = device_id[-4:] if device_id else "XXXX"

                        # Different naming based on device features
                        if device.get("therm_measured_temperature") is not None:
                            # Device with temperature sensor
                            device_name = f"{muller_type} Thermostat {short_id}"
                        else:
                            # Device without temperature sensor (relay/actuator only)
                            device_name = f"{muller_type} Heater {short_id}"

                        device["name"] = device_name

                except MullerIntuitivAuthError as err:
                    if "expired" in str(err).lower() or "invalid" in str(err).lower():
                        _LOGGER.error("Emergency token refresh failed - tokens expired: %s", err)
                        raise UpdateFailed("Authentication tokens expired - please reconfigure the integration")
                    else:
                        _LOGGER.error("Emergency token refresh failed: %s", err)
                        raise UpdateFailed(f"Authentication failed: {err}") from err
                
            return {device["id"]: device for device in devices_data}

        except (MullerIntuitivApiError, MullerIntuitivTimeoutError, MullerIntuitivConnectionError) as err:
            _LOGGER.error("API communication error: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error during data update: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err
