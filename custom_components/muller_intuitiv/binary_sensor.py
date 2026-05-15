"""Binary sensor platform for Muller Intuitiv."""

from typing import Any, Dict

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_HOME_ID, DOMAIN


def _device_class(name: str) -> BinarySensorDeviceClass | None:
    """Return a binary sensor device class when the HA version supports it."""
    return getattr(BinarySensorDeviceClass, name, None)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up the Muller Intuitiv binary sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    for device_id, device_data in coordinator.data.items():
        if device_data.get("is_system_device"):
            continue

        if "presence" in device_data:
            entities.append(
                MullerPresenceBinarySensor(coordinator, device_id, entry.data[CONF_HOME_ID])
            )

        if "open_window" in device_data:
            entities.append(
                MullerWindowBinarySensor(coordinator, device_id, entry.data[CONF_HOME_ID])
            )

    async_add_entities(entities)


class MullerBinarySensorBase(CoordinatorEntity, BinarySensorEntity):
    """Base class for Muller Intuitiv binary sensors."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator, device_id: str, home_id: str) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.device_id = device_id
        self.home_id = home_id

        room_name = self._device_data.get("room_name", f"Device {device_id}")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"device_{device_id}")},
            name=room_name,
            manufacturer="Muller",
            model="Intuitiv",
            via_device=(DOMAIN, f"home_{home_id}"),
        )

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


class MullerPresenceBinarySensor(MullerBinarySensorBase):
    """Presence binary sensor for a room."""

    _attr_device_class = _device_class("OCCUPANCY")

    def __init__(self, coordinator, device_id: str, home_id: str) -> None:
        """Initialize the presence binary sensor."""
        super().__init__(coordinator, device_id, home_id)

        room_name = self._device_data.get("room_name", f"Device {device_id}")
        self._attr_name = f"{room_name} Presence"
        self._attr_unique_id = f"muller_intuitiv_presence_{device_id}"

    @property
    def is_on(self) -> bool:
        """Return true if presence is detected."""
        return bool(self._device_data.get("presence", False))


class MullerWindowBinarySensor(MullerBinarySensorBase):
    """Open window binary sensor for a room."""

    _attr_device_class = _device_class("OPENING")

    def __init__(self, coordinator, device_id: str, home_id: str) -> None:
        """Initialize the window binary sensor."""
        super().__init__(coordinator, device_id, home_id)

        room_name = self._device_data.get("room_name", f"Device {device_id}")
        self._attr_name = f"{room_name} Window"
        self._attr_unique_id = f"muller_intuitiv_window_{device_id}"

    @property
    def is_on(self) -> bool:
        """Return true if a window is open."""
        return bool(self._device_data.get("open_window", False))
