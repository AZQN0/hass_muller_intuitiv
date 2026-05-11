"""DataUpdateCoordinator for Muller Intuitiv."""
import logging
from datetime import timedelta
import time
from typing import Dict, List, Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MullerIntuitivApi
from .device_manager import DeviceManager, DeviceChange
from .exceptions import (
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
        self.device_manager = DeviceManager()

        # Register for device change notifications
        self.device_manager.register_change_callback(self._handle_device_changes)

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
                _LOGGER.info("Starting data update for home %s", self.home_id)

                # Get home structure to map devices to room IDs
                _LOGGER.debug("Fetching home structure data...")
                home_data = await self.api.get_homes_data()
                rooms_from_home = home_data.get("rooms", [])

                _LOGGER.info("Home data received: %d rooms found", len(rooms_from_home))

                # Log home structure for debugging
                for i, room in enumerate(rooms_from_home):
                    room_id = room.get("id")
                    room_name = room.get("name", "Unknown")
                    modules = room.get("modules", [])
                    _LOGGER.debug("Room %d: ID=%s, Name=%s, Modules=%d", i, room_id, room_name, len(modules))

                    for j, module in enumerate(modules):
                        module_id = module.get("id")
                        module_type = module.get("type", "Unknown")
                        _LOGGER.debug("  Module %d: ID=%s, Type=%s", j, module_id, module_type)

                # Create device-to-room mapping from home structure
                # Use both string and int versions of IDs to handle API inconsistencies
                device_to_room_map = {}
                for room in rooms_from_home:
                    room_id = room.get("id")
                    room_name = room.get("name", "Unknown")
                    modules = room.get("modules", [])
                    for module in modules:
                        device_id = module.get("id")
                        if device_id:
                            # Store mapping with original ID
                            device_to_room_map[device_id] = room_id
                            # Also store string version
                            device_to_room_map[str(device_id)] = room_id
                            # Also store int version if possible
                            try:
                                int_device_id = int(device_id)
                                device_to_room_map[int_device_id] = room_id
                            except (ValueError, TypeError):
                                pass
                            _LOGGER.info("Mapped device %s to room %s (%s)", device_id, room_id, room_name)

                original_device_count = len([k for k, v in device_to_room_map.items() if not isinstance(k, (str, int)) or (isinstance(k, str) and not k.isdigit())])
                _LOGGER.info("Device-to-room mapping completed: %d total mappings (including type variations)", len(device_to_room_map))
                _LOGGER.debug("All mapping keys: %s", list(device_to_room_map.keys()))

                # Get device status (what API calls "rooms" are actually heating devices)
                _LOGGER.debug("Fetching device status data...")
                try:
                    devices_data = await self.api.get_home_status(self.home_id)
                except MullerIntuitivApiError as err:
                    if "Invalid home_id" in str(err):
                        _LOGGER.warning("Home ID %s is invalid, refreshing home data...", self.home_id)
                        # Refresh home_id from the current home data
                        fresh_home_data = await self.api.get_homes_data()
                        new_home_id = fresh_home_data.get("id")
                        if new_home_id and new_home_id != self.home_id:
                            _LOGGER.info("Updated home_id from %s to %s", self.home_id, new_home_id)
                            self.home_id = new_home_id
                            # Update config entry with new home_id
                            self.hass.config_entries.async_update_entry(
                                self.config_entry,
                                data={**self.config_entry.data, "home_id": new_home_id}
                            )
                            # Retry with new home_id
                            devices_data = await self.api.get_home_status(self.home_id)
                        else:
                            _LOGGER.error("Could not refresh home_id, no valid home found")
                            raise
                    else:
                        raise

                _LOGGER.info("Device status received: %d devices found", len(devices_data))

                # Log all device data for debugging
                for i, device in enumerate(devices_data):
                    device_id = device.get("id")
                    device_name = device.get("name", "Unknown")
                    muller_type = device.get("muller_type", "Unknown")
                    has_temp_sensor = device.get("therm_measured_temperature") is not None
                    current_temp = device.get("therm_measured_temperature")
                    target_temp = device.get("therm_setpoint_temperature")
                    mode = device.get("therm_setpoint_mode")

                    _LOGGER.debug("Device %d: ID=%s, Name=%s, Type=%s, HasTempSensor=%s",
                                 i, device_id, device_name, muller_type, has_temp_sensor)
                    _LOGGER.debug("  Temperatures: Current=%s, Target=%s, Mode=%s",
                                 current_temp, target_temp, mode)

                # Process each heating device and add room mapping
                successfully_mapped = 0
                failed_mappings = 0

                for device in devices_data:
                    device_id = device.get("id")
                    muller_type = device.get("muller_type", "Unknown")

                    # Add the correct room ID for API calls
                    room_id = device_to_room_map.get(device_id)
                    if room_id:
                        device["room_id"] = room_id
                        successfully_mapped += 1
                        _LOGGER.debug("✓ Device %s successfully mapped to room %s", device_id, room_id)
                    else:
                        device["room_id"] = None
                        failed_mappings += 1
                        _LOGGER.warning("✗ Could not find room mapping for device %s", device_id)
                        _LOGGER.warning("Available device IDs in mapping: %s", list(device_to_room_map.keys()))

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
                    _LOGGER.debug("Device %s assigned name: %s", device_id, device_name)

                _LOGGER.info("Mapping summary: %d successful, %d failed out of %d total devices",
                           successfully_mapped, failed_mappings, len(devices_data))

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
                    # Get home structure to map devices to room IDs
                    home_data = await self.api.get_homes_data()
                    rooms_from_home = home_data.get("rooms", [])

                    # Create device-to-room mapping from home structure
                    # Use both string and int versions of IDs to handle API inconsistencies
                    device_to_room_map = {}
                    for room in rooms_from_home:
                        room_id = room.get("id")
                        modules = room.get("modules", [])
                        for module in modules:
                            device_id = module.get("id")
                            if device_id:
                                # Store mapping with original ID
                                device_to_room_map[device_id] = room_id
                                # Also store string version
                                device_to_room_map[str(device_id)] = room_id
                                # Also store int version if possible
                                try:
                                    int_device_id = int(device_id)
                                    device_to_room_map[int_device_id] = room_id
                                except (ValueError, TypeError):
                                    pass
                                _LOGGER.debug("Mapped device %s to room %s", device_id, room_id)

                    devices_data = await self.api.get_home_status(self.home_id)

                    # Process each heating device and add room mapping
                    for device in devices_data:
                        device_id = device.get("id")
                        muller_type = device.get("muller_type", "Unknown")

                        # Add the correct room ID for API calls
                        room_id = device_to_room_map.get(device_id)
                        if room_id:
                            device["room_id"] = room_id
                            _LOGGER.debug("Device %s belongs to room %s", device_id, room_id)
                        else:
                            _LOGGER.warning("Could not find room mapping for device %s", device_id)
                            device["room_id"] = None

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

            # Prepare device data for DeviceManager
            new_devices = {device["id"]: device for device in devices_data}

            # Update device manager and detect changes
            device_changes = self.device_manager.update_devices(new_devices)

            if device_changes:
                _LOGGER.info("Device changes detected: %d changes", len(device_changes))
                for change in device_changes:
                    _LOGGER.info("Device %s: %s", change.change_type, change.device_id)

            return new_devices

        except (MullerIntuitivApiError, MullerIntuitivTimeoutError, MullerIntuitivConnectionError) as err:
            _LOGGER.error("API communication error: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    def _handle_device_changes(self, changes: List[DeviceChange]) -> None:
        """Handle device changes from DeviceManager."""
        _LOGGER.info("Processing %d device changes", len(changes))

        for change in changes:
            if change.change_type == "added":
                _LOGGER.info("New device detected: %s", change.device_id)
                # Device will be added automatically on next platform setup
                # For now, just log the event - full dynamic addition comes later

            elif change.change_type == "removed":
                _LOGGER.info("Device removed: %s", change.device_id)
                # Mark device as unavailable in device manager
                self.device_manager.mark_device_unavailable(change.device_id)

            elif change.change_type == "modified":
                _LOGGER.debug("Device modified: %s", change.device_id)
                # Data updates are handled automatically via coordinator.data
                # This is just for logging and potential future actions

    def is_device_available(self, device_id: str) -> bool:
        """Check if a device is available."""
        return self.device_manager.is_device_available(device_id)

    def get_device_statistics(self) -> Dict[str, Any]:
        """Get device manager statistics."""
        return self.device_manager.get_statistics()
