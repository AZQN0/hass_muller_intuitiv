"""Sensor platform for Muller Intuitiv."""

import logging
from typing import Any, Dict, Optional

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_HOME_ID, DOMAIN

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
            entities.extend(
                [
                    MullerOutdoorTemperatureSensor(
                        coordinator, device_id, entry.data[CONF_HOME_ID]
                    ),
                    MullerWifiStrengthSensor(coordinator, device_id, entry.data[CONF_HOME_ID]),
                ]
            )
        else:
            # Create per-room status sensors. Boolean sensors live in binary_sensor.py.
            if "boost_status" in device_data:
                entities.append(
                    MullerBoostStatusSensor(coordinator, device_id, entry.data[CONF_HOME_ID])
                )

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
        return self.device_id in self.coordinator.data and self.coordinator.is_device_available(
            self.device_id
        )


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
        wifi_strength = self._device_data.get("wifi_strength")
        if wifi_strength is None:
            return "mdi:wifi-strength-off"

        if wifi_strength >= 75:
            return "mdi:wifi-strength-4"
        elif wifi_strength >= 50:
            return "mdi:wifi-strength-3"
        elif wifi_strength >= 25:
            return "mdi:wifi-strength-2"
        else:
            return "mdi:wifi-strength-1"
