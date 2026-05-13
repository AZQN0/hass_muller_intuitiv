"""Sensor platform for Muller Intuitiv."""
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    EntityCategory,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_HOME_ID

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up the Muller Intuitiv sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    # Create sensors for each device
    for device_id, device_data in coordinator.data.items():

        # Skip system device for room-specific sensors
        if device_data.get("is_system_device"):
            # Create system-wide sensors for the system device
            entities.extend([
                MullerOutdoorTemperatureSensor(coordinator, device_id, entry.data[CONF_HOME_ID]),
                MullerWifiStrengthSensor(coordinator, device_id, entry.data[CONF_HOME_ID]),
            ])
        else:
            # Create per-room sensors
            room_name = device_data.get("room_name", f"Device {device_id}")

            # Only create presence and window sensors for devices with these capabilities
            if "presence" in device_data:
                entities.append(MullerPresenceSensor(coordinator, device_id, entry.data[CONF_HOME_ID]))

            if "open_window" in device_data:
                entities.append(MullerWindowSensor(coordinator, device_id, entry.data[CONF_HOME_ID]))

            if "boost_status" in device_data:
                entities.append(MullerBoostStatusSensor(coordinator, device_id, entry.data[CONF_HOME_ID]))

    async_add_entities(entities)


class MullerSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for Muller Intuitiv sensors."""

    def __init__(self, coordinator, device_id: str, home_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.home_id = home_id

    @property
    def _device_data(self) -> Dict[str, Any]:
        """Get the device data from the coordinator."""
        return self.coordinator.data.get(self.device_id, {})

    @property
    def available(self) -> bool:
        """Return True if device is available."""
        return (
            self.device_id in self.coordinator.data
            and self.coordinator.is_device_available(self.device_id)
        )


class MullerPresenceSensor(MullerSensorBase):
    """Presence sensor for room."""

    def __init__(self, coordinator, device_id: str, home_id: str) -> None:
        """Initialize the presence sensor."""
        super().__init__(coordinator, device_id, home_id)

        device_data = self._device_data
        room_name = device_data.get("room_name", f"Device {device_id}")

        self._attr_device_class = SensorDeviceClass.OCCUPANCY
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_name = f"{room_name} Presence"
        self._attr_unique_id = f"muller_intuitiv_presence_{device_id}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"device_{device_id}")},
            name=room_name,
            manufacturer="Muller",
            model="Intuitiv Presence Sensor",
            via_device=(DOMAIN, f"home_{home_id}"),
        )

    @property
    def native_value(self) -> Optional[str]:
        """Return the state of the sensor."""
        presence = self._device_data.get("presence", False)
        return "detected" if presence else "not_detected"

    @property
    def icon(self) -> str:
        """Return the icon for the sensor."""
        presence = self._device_data.get("presence", False)
        return "mdi:account" if presence else "mdi:account-outline"


class MullerWindowSensor(MullerSensorBase):
    """Window sensor for room."""

    def __init__(self, coordinator, device_id: str, home_id: str) -> None:
        """Initialize the window sensor."""
        super().__init__(coordinator, device_id, home_id)

        device_data = self._device_data
        room_name = device_data.get("room_name", f"Device {device_id}")

        self._attr_device_class = SensorDeviceClass.OPENING
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_name = f"{room_name} Window"
        self._attr_unique_id = f"muller_intuitiv_window_{device_id}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"device_{device_id}")},
            name=room_name,
            manufacturer="Muller",
            model="Intuitiv Window Sensor",
            via_device=(DOMAIN, f"home_{home_id}"),
        )

    @property
    def native_value(self) -> Optional[str]:
        """Return the state of the sensor."""
        open_window = self._device_data.get("open_window", False)
        return "open" if open_window else "closed"

    @property
    def icon(self) -> str:
        """Return the icon for the sensor."""
        open_window = self._device_data.get("open_window", False)
        return "mdi:window-open" if open_window else "mdi:window-closed"


class MullerBoostStatusSensor(MullerSensorBase):
    """Boost status sensor for room."""

    def __init__(self, coordinator, device_id: str, home_id: str) -> None:
        """Initialize the boost status sensor."""
        super().__init__(coordinator, device_id, home_id)

        device_data = self._device_data
        room_name = device_data.get("room_name", f"Device {device_id}")

        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_name = f"{room_name} Boost Status"
        self._attr_unique_id = f"muller_intuitiv_boost_{device_id}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"device_{device_id}")},
            name=room_name,
            manufacturer="Muller",
            model="Intuitiv Boost Control",
            via_device=(DOMAIN, f"home_{home_id}"),
        )

    @property
    def native_value(self) -> Optional[str]:
        """Return the state of the sensor."""
        return self._device_data.get("boost_status", "unknown")

    @property
    def icon(self) -> str:
        """Return the icon for the sensor."""
        boost_status = self._device_data.get("boost_status", "disabled")
        if boost_status == "enabled":
            return "mdi:fire"
        elif boost_status == "disabled":
            return "mdi:fire-off"
        else:
            return "mdi:help-circle"


class MullerOutdoorTemperatureSensor(MullerSensorBase):
    """Outdoor temperature sensor."""

    def __init__(self, coordinator, device_id: str, home_id: str) -> None:
        """Initialize the outdoor temperature sensor."""
        super().__init__(coordinator, device_id, home_id)

        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_name = "Outdoor Temperature"
        self._attr_unique_id = f"muller_intuitiv_outdoor_temp_{home_id}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"home_{home_id}")},
            name="Muller Intuitiv System",
            manufacturer="Muller",
            model="Intuitiv Home System",
        )

    @property
    def native_value(self) -> Optional[float]:
        """Return the outdoor temperature."""
        return self._device_data.get("outdoor_temperature")

    @property
    def available(self) -> bool:
        """Return True if outdoor temperature is available."""
        return (
            self.device_id in self.coordinator.data
            and self._device_data.get("outdoor_temperature") is not None
        )

    @property
    def icon(self) -> str:
        """Return the icon for the sensor."""
        return "mdi:thermometer"


class MullerWifiStrengthSensor(MullerSensorBase):
    """WiFi strength sensor."""

    def __init__(self, coordinator, device_id: str, home_id: str) -> None:
        """Initialize the WiFi strength sensor."""
        super().__init__(coordinator, device_id, home_id)

        self._attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_state_class = SensorStateClass.MEASUREMENT
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_name = "WiFi Strength"
        self._attr_unique_id = f"muller_intuitiv_wifi_{home_id}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"home_{home_id}")},
            name="Muller Intuitiv System",
            manufacturer="Muller",
            model="Intuitiv Home System",
        )

    @property
    def native_value(self) -> Optional[int]:
        """Return the WiFi strength."""
        return self._device_data.get("wifi_strength")

    @property
    def available(self) -> bool:
        """Return True if WiFi strength is available."""
        return (
            self.device_id in self.coordinator.data
            and self._device_data.get("wifi_strength") is not None
        )

    @property
    def icon(self) -> str:
        """Return the icon for the sensor."""
        wifi_strength = self._device_data.get("wifi_strength", 0)
        if wifi_strength >= 75:
            return "mdi:wifi-strength-4"
        elif wifi_strength >= 50:
            return "mdi:wifi-strength-3"
        elif wifi_strength >= 25:
            return "mdi:wifi-strength-2"
        else:
            return "mdi:wifi-strength-1"