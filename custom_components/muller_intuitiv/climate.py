"""Climate platform for Muller Intuitiv."""
import logging
from typing import Any, Dict, Optional, Union

_LOGGER = logging.getLogger(__name__)

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.climate.const import (
    PRESET_ECO,
    PRESET_HOME,
    PRESET_NONE,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_HOME_ID

_LOGGER = logging.getLogger(__name__)

# Map Muller Intuitiv modes to HA preset modes
MULLER_TO_HA_PRESET = {
    "manual": PRESET_NONE,
    "home": PRESET_HOME,
    "hg": PRESET_ECO,
}

HA_TO_MULLER_PRESET = {
    PRESET_NONE: "manual",
    PRESET_HOME: "home",
    PRESET_ECO: "hg",
}

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up the Muller Intuitiv climate platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for device_id, device_data in coordinator.data.items():
        entities.append(MullerIntuitivClimate(coordinator, device_id, entry.data[CONF_HOME_ID]))

    async_add_entities(entities)

class MullerIntuitivClimate(CoordinatorEntity, ClimateEntity):
    """Representation of a Muller Intuitiv Room."""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
    )
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_preset_modes = [PRESET_NONE, PRESET_HOME, PRESET_ECO]

    def __init__(self, coordinator, device_id: str, home_id: str) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.home_id = home_id

        # Get device info
        device_data = coordinator.data.get(device_id, {})
        muller_type = device_data.get("muller_type", "Unknown")
        room_id = device_data.get("room_id")

        _LOGGER.info("Initializing climate entity for device %s (type: %s, room_id: %s)",
                    device_id, muller_type, room_id)

        # Get enhanced device information
        room_name = device_data.get("room_name")
        room_type = device_data.get("room_type")
        has_temp_sensor = device_data.get("therm_measured_temperature") is not None

        # Create enhanced device name
        if room_name:
            if has_temp_sensor:
                device_name = f"{room_name} Thermostat"
            else:
                device_name = f"{room_name} Heater"
        else:
            device_name = f"Muller {muller_type} {device_id[-4:]}"

        # Enhanced device info with room type and capabilities
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"device_{device_id}")},
            name=device_name,
            manufacturer="Muller",
            model=f"Intuitiv {muller_type}",
            via_device=(DOMAIN, f"home_{home_id}"),
            suggested_area=room_name if room_name else None,
        )

        # Add firmware info if available
        firmware_info = device_data.get("firmware_info")
        if firmware_info:
            self._attr_device_info["sw_version"] = f"Rev {firmware_info.get('firmware_revision', 'Unknown')}"

    @property
    def _device_data(self) -> Dict[str, Any]:
        """Get the device data from the coordinator."""
        return self.coordinator.data.get(self.device_id, {})

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"muller_intuitiv_device_{self.device_id}"

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        # Use room name if available, otherwise fall back to device name
        room_name = self._device_data.get("room_name")
        if room_name:
            return room_name
        return self._device_data.get("name", f"Heater {self.device_id}")

    @property
    def available(self) -> bool:
        """Return True if device is available."""
        # Check if device exists in coordinator data and is marked as available
        device_exists = self.device_id in self.coordinator.data
        device_available = self.coordinator.is_device_available(self.device_id)

        available = device_exists and device_available

        if not available:
            _LOGGER.debug("Device %s availability: exists=%s, available=%s",
                         self.device_id, device_exists, device_available)

        return available

    @property
    def current_temperature(self) -> Optional[float]:
        """Return the current temperature."""
        return self._device_data.get("therm_measured_temperature")

    @property
    def target_temperature(self) -> Optional[float]:
        """Return the temperature we try to reach."""
        return self._device_data.get("therm_setpoint_temperature")

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current operation ie. heat, cool, idle."""
        mode = self._device_data.get("therm_setpoint_mode")
        if mode == "off":
            return HVACMode.OFF
        return HVACMode.HEAT

    @property
    def preset_mode(self) -> Optional[str]:
        """Return current preset mode."""
        mode = self._device_data.get("therm_setpoint_mode")
        return MULLER_TO_HA_PRESET.get(mode, PRESET_NONE)

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return extra state attributes."""
        data = self._device_data

        # Base attributes
        attrs = {
            "device_id": data.get("id"),
            "room_id": data.get("room_id"),
            "room_name": data.get("room_name"),
            "room_type": data.get("room_type"),
            "muller_type": data.get("muller_type"),
            "open_window": data.get("open_window", False),
            "muller_mode": data.get("therm_setpoint_mode"),
            "presence": data.get("presence", False),
            "boost_status": data.get("boost_status"),
        }

        # Enhanced temporal and status attributes
        if "therm_setpoint_end_time" in data and data["therm_setpoint_end_time"]:
            end_time = data["therm_setpoint_end_time"]
            if end_time and end_time != 2147483647:  # Not permanent
                import datetime
                try:
                    end_dt = datetime.datetime.fromtimestamp(end_time)
                    attrs["setpoint_expires_at"] = end_dt.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, OSError):
                    attrs["setpoint_expires_at"] = "Invalid time"
            else:
                attrs["setpoint_expires_at"] = "Permanent"

        # Advanced status attributes
        attrs.update({
            "anticipating": data.get("anticipating", False),
            "lowering": data.get("lowering", False),
            "pairing_status": data.get("pairing"),
        })

        # System connectivity (if available)
        if "reachable" in data:
            attrs["reachable"] = data["reachable"]
        if "last_seen" in data:
            import datetime
            try:
                last_seen_dt = datetime.datetime.fromtimestamp(data["last_seen"])
                attrs["last_seen"] = last_seen_dt.strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, OSError):
                attrs["last_seen"] = "Unknown"

        return attrs

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get("temperature")
        if temperature is None:
            _LOGGER.warning("Temperature not provided in kwargs: %s", kwargs)
            return

        # Get the room_id from the device data (mapped in coordinator)
        room_id = self._device_data.get("room_id")
        if not room_id:
            _LOGGER.error("No room_id found for device %s. Device data: %s", self.device_id, self._device_data)
            return

        _LOGGER.info("Climate entity %s requesting temperature change to %.1f°C (device_id=%s, room_id=%s)",
                    self.name, temperature, self.device_id, room_id)

        try:
            await self.coordinator.api.set_room_temperature(
                self.home_id, room_id, temperature
            )
            _LOGGER.info("Temperature change request completed for %s", self.name)
        except Exception as err:
            _LOGGER.error("Failed to set temperature for %s: %s", self.name, err)
            raise

        await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new target preset mode."""
        muller_mode = HA_TO_MULLER_PRESET.get(preset_mode)

        if not muller_mode:
            _LOGGER.error("Unknown preset mode '%s' for entity %s", preset_mode, self.name)
            return

        # Get the room_id from the device data (mapped in coordinator)
        room_id = self._device_data.get("room_id")
        if not room_id:
            _LOGGER.error("No room_id found for device %s. Device data: %s", self.device_id, self._device_data)
            return

        _LOGGER.info("Climate entity %s requesting preset mode change to '%s' -> '%s' (device_id=%s, room_id=%s)",
                    self.name, preset_mode, muller_mode, self.device_id, room_id)

        try:
            if muller_mode == "home":
                await self.coordinator.api.set_room_mode(self.home_id, room_id, "home")
            elif muller_mode == "hg":
                await self.coordinator.api.set_room_mode(self.home_id, room_id, "hg")
            elif muller_mode == "manual":
                # Just set the current temperature to stay in manual mode
                current_target = self.target_temperature
                if current_target is not None:
                    _LOGGER.debug("Setting manual mode by maintaining current temperature %.1f°C", current_target)
                    await self.coordinator.api.set_room_temperature(
                        self.home_id, room_id, current_target
                    )
                else:
                    _LOGGER.warning("Cannot set manual mode for %s: no current target temperature", self.name)
                    return

            _LOGGER.info("Preset mode change completed for %s", self.name)
        except Exception as err:
            _LOGGER.error("Failed to set preset mode for %s: %s", self.name, err)
            raise

        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        # Get the room_id from the device data (mapped in coordinator)
        room_id = self._device_data.get("room_id")
        if not room_id:
            _LOGGER.error("No room_id found for device %s", self.device_id)
            return

        # The API doesn't cleanly support turning a specific room ON/OFF directly
        # from the set state payload based on our Jeedom reference,
        # but we could attempt to send "off" or "home"
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.api.set_room_mode(self.home_id, room_id, "off")
        elif hvac_mode == HVACMode.HEAT:
            await self.coordinator.api.set_room_mode(self.home_id, room_id, "home")

        await self.coordinator.async_request_refresh()
