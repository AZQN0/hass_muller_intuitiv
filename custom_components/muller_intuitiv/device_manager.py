"""Device lifecycle management for Muller Intuitiv integration."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import logging
from typing import Any, Callable, Dict, List, Optional

_LOGGER = logging.getLogger(__name__)


class DeviceState(Enum):
    """Device state enumeration."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    REMOVED = "removed"
    NEW = "new"


@dataclass
class DeviceChange:
    """Represents a device change event."""
    device_id: str
    change_type: str  # 'added', 'removed', 'modified'
    old_data: Optional[Dict[str, Any]] = None
    new_data: Optional[Dict[str, Any]] = None


class DeviceManager:
    """Manages device lifecycle and change detection."""

    def __init__(self):
        """Initialize the device manager."""
        self._devices: Dict[str, Dict[str, Any]] = {}
        self._device_states: Dict[str, DeviceState] = {}
        self._change_callbacks: List[Callable[[List[DeviceChange]], None]] = []

    def register_change_callback(self, callback: Callable[[List[DeviceChange]], None]) -> None:
        """Register a callback for device changes."""
        self._change_callbacks.append(callback)
        _LOGGER.debug("Registered device change callback: %s", callback.__name__)

    def unregister_change_callback(self, callback: Callable[[List[DeviceChange]], None]) -> None:
        """Unregister a callback for device changes."""
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)
            _LOGGER.debug("Unregistered device change callback: %s", callback.__name__)

    def update_devices(self, new_devices: Dict[str, Dict[str, Any]]) -> List[DeviceChange]:
        """Update devices and detect changes."""
        changes = self._detect_changes(new_devices)

        if changes:
            _LOGGER.info("Detected %d device changes", len(changes))
            for change in changes:
                _LOGGER.debug("Device change: %s - %s", change.change_type, change.device_id)

        # Update internal state
        self._devices = new_devices.copy()
        self._update_device_states(changes)

        # Notify callbacks
        if changes and self._change_callbacks:
            for callback in self._change_callbacks:
                try:
                    callback(changes)
                except Exception as err:
                    _LOGGER.error("Error in device change callback %s: %s", callback.__name__, err)

        return changes

    def _detect_changes(self, new_devices: Dict[str, Dict[str, Any]]) -> List[DeviceChange]:
        """Detect changes between old and new device sets."""
        changes = []

        old_device_ids = set(self._devices.keys())
        new_device_ids = set(new_devices.keys())

        # Detect added devices
        added_ids = new_device_ids - old_device_ids
        for device_id in added_ids:
            changes.append(DeviceChange(
                device_id=device_id,
                change_type="added",
                new_data=new_devices[device_id]
            ))

        # Detect removed devices
        removed_ids = old_device_ids - new_device_ids
        for device_id in removed_ids:
            changes.append(DeviceChange(
                device_id=device_id,
                change_type="removed",
                old_data=self._devices[device_id]
            ))

        # Detect modified devices
        common_ids = old_device_ids & new_device_ids
        for device_id in common_ids:
            old_data = self._devices[device_id]
            new_data = new_devices[device_id]

            if self._device_data_changed(old_data, new_data):
                changes.append(DeviceChange(
                    device_id=device_id,
                    change_type="modified",
                    old_data=old_data,
                    new_data=new_data
                ))

        return changes

    def _device_data_changed(self, old_data: Dict[str, Any], new_data: Dict[str, Any]) -> bool:
        """Check if device data has meaningfully changed."""
        # Compare key fields that matter for Home Assistant
        key_fields = [
            "name", "muller_type", "room_id",
            "therm_measured_temperature", "therm_setpoint_temperature",
            "therm_setpoint_mode", "heating", "boost_status"
        ]

        for field in key_fields:
            old_val = old_data.get(field)
            new_val = new_data.get(field)

            if old_val != new_val:
                _LOGGER.debug("Device %s field '%s' changed: %s -> %s",
                            old_data.get("id", "unknown"), field, old_val, new_val)
                return True

        return False

    def _update_device_states(self, changes: List[DeviceChange]) -> None:
        """Update device states based on changes."""
        for change in changes:
            if change.change_type == "added":
                self._device_states[change.device_id] = DeviceState.NEW
            elif change.change_type == "removed":
                self._device_states[change.device_id] = DeviceState.REMOVED
            elif change.change_type == "modified":
                # Keep existing state if available, otherwise mark as available
                if change.device_id not in self._device_states:
                    self._device_states[change.device_id] = DeviceState.AVAILABLE

    def get_device_state(self, device_id: str) -> DeviceState:
        """Get the current state of a device."""
        return self._device_states.get(device_id, DeviceState.AVAILABLE)

    def is_device_available(self, device_id: str) -> bool:
        """Check if a device is available."""
        state = self.get_device_state(device_id)
        return state in (DeviceState.AVAILABLE, DeviceState.NEW)

    def get_devices(self) -> Dict[str, Dict[str, Any]]:
        """Get current devices."""
        return self._devices.copy()

    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get specific device data."""
        return self._devices.get(device_id)

    def mark_device_unavailable(self, device_id: str) -> None:
        """Mark a device as unavailable."""
        self._device_states[device_id] = DeviceState.UNAVAILABLE
        _LOGGER.debug("Marked device %s as unavailable", device_id)

    def cleanup_removed_devices(self) -> List[str]:
        """Clean up devices marked as removed and return their IDs."""
        removed_devices = []

        for device_id, state in list(self._device_states.items()):
            if state == DeviceState.REMOVED:
                # Remove from internal tracking
                if device_id in self._devices:
                    del self._devices[device_id]
                del self._device_states[device_id]
                removed_devices.append(device_id)

        if removed_devices:
            _LOGGER.info("Cleaned up %d removed devices: %s", len(removed_devices), removed_devices)

        return removed_devices

    def get_statistics(self) -> Dict[str, Any]:
        """Get device manager statistics."""
        states_count = {}
        for state in DeviceState:
            states_count[state.value] = sum(1 for s in self._device_states.values() if s == state)

        return {
            "total_devices": len(self._devices),
            "device_states": states_count,
            "registered_callbacks": len(self._change_callbacks)
        }
