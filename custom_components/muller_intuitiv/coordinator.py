"""DataUpdateCoordinator for Muller Intuitiv."""

import logging
import time
from datetime import timedelta
from typing import Any, Dict, List

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MullerIntuitivApi
from .const import (
    CONF_ACCESS_TOKEN,
    CONF_EXPIRES_AT,
    CONF_EXPIRES_IN,
    CONF_HOME_ID,
    CONF_REFRESH_TOKEN,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)
from .device_manager import DeviceChange, DeviceManager
from .exceptions import (
    MullerIntuitivApiError,
    MullerIntuitivAuthError,
    MullerIntuitivConnectionError,
    MullerIntuitivTimeoutError,
)

_LOGGER = logging.getLogger(__name__)


def _normalise_name(name: Any) -> str:
    """Return a stable key for user-facing room/device names."""
    return str(name or "").strip().casefold()


def _build_room_context(rooms: List[dict]) -> tuple[dict, dict, dict]:
    """Build lookup tables for room ids and room metadata."""
    device_to_room_map: dict[Any, Any] = {}
    rooms_by_id: dict[str, dict] = {}
    rooms_by_name: dict[str, dict] = {}

    for room in rooms:
        room_id = room.get("id")
        if room_id is not None:
            device_to_room_map[room_id] = room_id
            device_to_room_map[str(room_id)] = room_id
            rooms_by_id[str(room_id)] = room
            try:
                device_to_room_map[int(room_id)] = room_id
            except (ValueError, TypeError):
                pass

        room_name = _normalise_name(room.get("name"))
        if room_name:
            rooms_by_name[room_name] = room

        modules = room.get("modules", [])
        for module in modules:
            if isinstance(module, str):
                device_id = module
            else:
                device_id = module.get("id")
            if device_id:
                device_to_room_map[device_id] = room_id
                device_to_room_map[str(device_id)] = room_id
                try:
                    device_to_room_map[int(device_id)] = room_id
                except (ValueError, TypeError):
                    pass
                _LOGGER.debug(
                    "Mapped module %s to room %s (%s)",
                    device_id,
                    room_id,
                    room.get("name", "Unknown"),
                )

    return device_to_room_map, rooms_by_id, rooms_by_name


def _find_room_for_device(device: dict, rooms_by_id: dict, rooms_by_name: dict) -> dict | None:
    """Find the room represented by a device status payload."""
    device_id = device.get("id")
    if device_id is not None:
        room = rooms_by_id.get(str(device_id))
        if room:
            return room

    room_name = _normalise_name(device.get("room_name") or device.get("name"))
    if room_name:
        return rooms_by_name.get(room_name)

    return None


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
                try:
                    await self._async_refresh_access_token()
                except MullerIntuitivAuthError as err:
                    if "expired" in str(err).lower() or "invalid" in str(err).lower():
                        _LOGGER.error(
                            "Refresh token expired or invalid - reconfiguration required: %s", err
                        )
                        raise UpdateFailed(
                            "Authentication tokens expired - please reconfigure the integration"
                        )
                    else:
                        raise UpdateFailed(f"Token refresh failed: {err}") from err

            try:
                devices_data = await self._async_fetch_devices_data()
            except MullerIntuitivAuthError:
                # If we still get auth error after checking expiration, try refresh once more
                _LOGGER.info("Authentication failed, attempting emergency token refresh...")
                try:
                    await self._async_refresh_access_token()
                    devices_data = await self._async_fetch_devices_data()
                except MullerIntuitivAuthError as err:
                    if "expired" in str(err).lower() or "invalid" in str(err).lower():
                        _LOGGER.error("Emergency token refresh failed - tokens expired: %s", err)
                        raise UpdateFailed(
                            "Authentication tokens expired - please reconfigure the integration"
                        )
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

        except (
            MullerIntuitivApiError,
            MullerIntuitivTimeoutError,
            MullerIntuitivConnectionError,
        ) as err:
            _LOGGER.error("API communication error: %s", err)
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    async def _async_refresh_access_token(self) -> None:
        """Refresh tokens and persist the updated config entry data."""
        refresh_token = self.entry.data.get(CONF_REFRESH_TOKEN)
        if not refresh_token:
            raise UpdateFailed("No refresh token available - please reconfigure integration")

        new_tokens = await self.api.refresh_token(refresh_token)
        access_token = new_tokens.get("access_token")
        if not access_token:
            raise UpdateFailed("Token refresh response did not include an access token")

        new_data = {**self.entry.data}
        new_data[CONF_ACCESS_TOKEN] = access_token
        new_data[CONF_REFRESH_TOKEN] = new_tokens.get(CONF_REFRESH_TOKEN, refresh_token)
        if CONF_EXPIRES_IN in new_tokens:
            new_data[CONF_EXPIRES_IN] = new_tokens[CONF_EXPIRES_IN]
        if CONF_EXPIRES_AT in new_tokens:
            new_data[CONF_EXPIRES_AT] = new_tokens[CONF_EXPIRES_AT]
        self.hass.config_entries.async_update_entry(self.entry, data=new_data)
        self.api.set_token(access_token)

    async def _async_fetch_devices_data(self) -> List[dict]:
        """Fetch and enrich the device data used by Home Assistant entities."""
        _LOGGER.info("Starting data update for home %s", self.home_id)

        home_data = await self.api.get_homes_data()
        rooms_from_home = home_data.get("rooms", [])
        self._log_home_structure(rooms_from_home)

        devices_data = await self._async_get_home_status()
        _LOGGER.info("Device status received: %d devices found", len(devices_data))

        system_info = await self._async_get_system_info()
        self._enrich_devices(devices_data, rooms_from_home, system_info)
        return devices_data

    async def _async_get_home_status(self) -> List[dict]:
        """Fetch home status, refreshing a stale stored home id once when needed."""
        try:
            return await self.api.get_home_status(self.home_id)
        except MullerIntuitivApiError as err:
            if "Invalid home_id" not in str(err):
                raise

            _LOGGER.warning("Home ID %s is invalid, refreshing home data...", self.home_id)
            fresh_home_data = await self.api.get_homes_data()
            new_home_id = fresh_home_data.get("id")
            if not new_home_id or new_home_id == self.home_id:
                _LOGGER.error("Could not refresh home_id, no valid home found")
                raise

            _LOGGER.info("Updated home_id from %s to %s", self.home_id, new_home_id)
            self.home_id = new_home_id
            self.hass.config_entries.async_update_entry(
                self.entry, data={**self.entry.data, CONF_HOME_ID: new_home_id}
            )
            return await self.api.get_home_status(self.home_id)

    async def _async_get_system_info(self) -> dict:
        """Fetch optional system sensor data without failing the main update."""
        try:
            system_info = await self.api.get_home_system_info(self.home_id)
            _LOGGER.info(
                "System info retrieved: outdoor_temp=%s°C, wifi=%s%%, modules=%d",
                system_info.get("outdoor_temperature"),
                system_info.get("wifi_strength"),
                len(system_info.get("modules", [])),
            )
            return system_info
        except (
            MullerIntuitivApiError,
            MullerIntuitivTimeoutError,
            MullerIntuitivConnectionError,
        ) as err:
            _LOGGER.warning("Could not retrieve system info: %s", err)
            return {
                "outdoor_temperature": None,
                "wifi_strength": None,
                "firmware_info": {},
                "modules": [],
            }

    def _log_home_structure(self, rooms_from_home: List[dict]) -> None:
        """Log home structure details at debug level."""
        _LOGGER.info("Home data received: %d rooms found", len(rooms_from_home))
        for i, room in enumerate(rooms_from_home):
            room_id = room.get("id")
            room_name = room.get("name", "Unknown")
            modules = room.get("modules", [])
            _LOGGER.debug(
                "Room %d: ID=%s, Name=%s, Modules=%d", i, room_id, room_name, len(modules)
            )

            for j, module in enumerate(modules):
                if isinstance(module, str):
                    module_id = module
                    module_type = "Unknown"
                else:
                    module_id = module.get("id")
                    module_type = module.get("type", "Unknown")
                _LOGGER.debug("  Module %d: ID=%s, Type=%s", j, module_id, module_type)

    def _enrich_devices(
        self,
        devices_data: List[dict],
        rooms_from_home: List[dict],
        system_info: dict,
    ) -> None:
        """Add room mapping, display names, and system data to device payloads."""
        device_to_room_map, rooms_by_id, rooms_by_name = _build_room_context(rooms_from_home)
        _LOGGER.info(
            "Device-to-room mapping completed: %d total mappings (including type variations)",
            len(device_to_room_map),
        )
        _LOGGER.debug("All mapping keys: %s", list(device_to_room_map.keys()))

        successfully_mapped = 0
        failed_mappings = 0

        for i, device in enumerate(devices_data):
            device_id = device.get("id")
            self._log_device_status(i, device)

            room = _find_room_for_device(device, rooms_by_id, rooms_by_name)
            room_id = (
                device_to_room_map.get(device_id)
                or device.get("room_id")
                or (room.get("id") if room else None)
            )
            if room_id:
                device["room_id"] = room_id
                successfully_mapped += 1
                _LOGGER.debug("Device %s successfully mapped to room %s", device_id, room_id)
            else:
                device["room_id"] = None
                failed_mappings += 1
                _LOGGER.debug("Could not find room mapping for device %s", device_id)

            room_name = device.get("room_name")
            room_type = device.get("room_type")
            if room:
                room_name = room.get("name", room_name or "Unknown")
                room_type = room.get("type", room_type or "unknown")

            device["room_name"] = room_name
            device["room_type"] = room_type
            device["name"] = self._device_name(device, room_name)

        if system_info:
            devices_data.append(self._system_device(system_info))
            _LOGGER.info(
                "Added system device with outdoor_temp=%s°C, wifi=%s%%",
                system_info.get("outdoor_temperature"),
                system_info.get("wifi_strength"),
            )

        _LOGGER.info(
            "Mapping summary: %d successful, %d failed out of %d total devices",
            successfully_mapped,
            failed_mappings,
            len(devices_data) - (1 if system_info else 0),
        )

    def _log_device_status(self, index: int, device: dict) -> None:
        """Log device status details at debug level."""
        _LOGGER.debug(
            "Device %d: ID=%s, Name=%s, Type=%s, HasTempSensor=%s",
            index,
            device.get("id"),
            device.get("name", "Unknown"),
            device.get("muller_type", "Unknown"),
            device.get("therm_measured_temperature") is not None,
        )
        _LOGGER.debug(
            "  Temperatures: Current=%s, Target=%s, Mode=%s",
            device.get("therm_measured_temperature"),
            device.get("therm_setpoint_temperature"),
            device.get("therm_setpoint_mode"),
        )

    @staticmethod
    def _device_name(device: dict, room_name: str | None) -> str:
        """Return the Home Assistant-facing device name."""
        if room_name:
            if device.get("therm_measured_temperature") is not None:
                return room_name
            return f"{room_name} (Heater)"

        device_id = device.get("id")
        short_id = device_id[-4:] if device_id else "XXXX"
        muller_type = device.get("muller_type", "Unknown")
        if device.get("therm_measured_temperature") is not None:
            return f"{muller_type} Thermostat {short_id}"
        return f"{muller_type} Heater {short_id}"

    @staticmethod
    def _system_device(system_info: dict) -> dict:
        """Return the synthetic system device used by global sensors."""
        return {
            "id": "_system",
            "name": "Muller System",
            "muller_type": "System",
            "room_id": None,
            "room_name": "System",
            "room_type": "system",
            "outdoor_temperature": system_info.get("outdoor_temperature"),
            "wifi_strength": system_info.get("wifi_strength"),
            "firmware_info": system_info.get("firmware_info", {}),
            "modules": system_info.get("modules", []),
            "is_system_device": True,
        }

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
