"""Unit tests for DeviceManager."""

from unittest.mock import Mock, call

import pytest

from custom_components.muller_intuitiv.device_manager import (
    DeviceChange,
    DeviceManager,
    DeviceState,
)


class TestDeviceManager:
    """Test the DeviceManager class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.device_manager = DeviceManager()

    def test_initialization(self):
        """Test DeviceManager initialization."""
        assert self.device_manager._devices == {}
        assert self.device_manager._device_states == {}
        assert self.device_manager._change_callbacks == []

    def test_register_change_callback(self):
        """Test registering change callbacks."""
        callback = Mock()
        self.device_manager.register_change_callback(callback)

        assert callback in self.device_manager._change_callbacks

    def test_unregister_change_callback(self):
        """Test unregistering change callbacks."""
        callback = Mock()
        self.device_manager.register_change_callback(callback)
        self.device_manager.unregister_change_callback(callback)

        assert callback not in self.device_manager._change_callbacks

    def test_detect_added_devices(self):
        """Test detection of added devices."""
        # Start with empty devices
        initial_devices = {}

        # Add a device
        new_devices = {"device1": {"id": "device1", "name": "Test Device", "muller_type": "FPN"}}

        changes = self.device_manager.update_devices(new_devices)

        assert len(changes) == 1
        assert changes[0].change_type == "added"
        assert changes[0].device_id == "device1"
        assert changes[0].new_data == new_devices["device1"]
        assert changes[0].old_data is None

    def test_detect_removed_devices(self):
        """Test detection of removed devices."""
        # Start with a device
        initial_devices = {
            "device1": {"id": "device1", "name": "Test Device", "muller_type": "FPN"}
        }
        self.device_manager.update_devices(initial_devices)

        # Remove the device
        new_devices = {}
        changes = self.device_manager.update_devices(new_devices)

        assert len(changes) == 1
        assert changes[0].change_type == "removed"
        assert changes[0].device_id == "device1"
        assert changes[0].old_data == initial_devices["device1"]
        assert changes[0].new_data is None

    def test_detect_modified_devices(self):
        """Test detection of modified devices."""
        # Start with a device
        initial_devices = {
            "device1": {
                "id": "device1",
                "name": "Test Device",
                "muller_type": "FPN",
                "therm_measured_temperature": 20.0,
            }
        }
        self.device_manager.update_devices(initial_devices)

        # Modify the device
        modified_devices = {
            "device1": {
                "id": "device1",
                "name": "Test Device",
                "muller_type": "FPN",
                "therm_measured_temperature": 22.0,  # Changed temperature
            }
        }
        changes = self.device_manager.update_devices(modified_devices)

        assert len(changes) == 1
        assert changes[0].change_type == "modified"
        assert changes[0].device_id == "device1"
        assert changes[0].old_data["therm_measured_temperature"] == 20.0
        assert changes[0].new_data["therm_measured_temperature"] == 22.0

    def test_no_changes_detected(self):
        """Test that no changes are detected when data is identical."""
        devices = {
            "device1": {
                "id": "device1",
                "name": "Test Device",
                "muller_type": "FPN",
                "therm_measured_temperature": 20.0,
            }
        }

        # First update
        self.device_manager.update_devices(devices)

        # Same data again
        changes = self.device_manager.update_devices(devices)

        assert len(changes) == 0

    def test_device_state_management(self):
        """Test device state transitions."""
        device_id = "device1"

        # Initially, device should be available (default)
        assert self.device_manager.get_device_state(device_id) == DeviceState.AVAILABLE
        assert self.device_manager.is_device_available(device_id) is True

        # Mark as unavailable
        self.device_manager.mark_device_unavailable(device_id)
        assert self.device_manager.get_device_state(device_id) == DeviceState.UNAVAILABLE
        assert self.device_manager.is_device_available(device_id) is False

    def test_callback_invocation(self):
        """Test that callbacks are invoked on device changes."""
        callback = Mock()
        self.device_manager.register_change_callback(callback)

        new_devices = {"device1": {"id": "device1", "name": "Test Device", "muller_type": "FPN"}}

        self.device_manager.update_devices(new_devices)

        # Callback should be called once with the changes
        callback.assert_called_once()
        call_args = callback.call_args[0][0]  # First argument (changes list)
        assert len(call_args) == 1
        assert call_args[0].change_type == "added"

    def test_callback_error_handling(self):
        """Test that callback errors don't break the update process."""

        def failing_callback(changes):
            raise Exception("Callback failed")

        self.device_manager.register_change_callback(failing_callback)

        new_devices = {"device1": {"id": "device1", "name": "Test Device", "muller_type": "FPN"}}

        # Should not raise exception despite callback failure
        changes = self.device_manager.update_devices(new_devices)
        assert len(changes) == 1

    def test_cleanup_removed_devices(self):
        """Test cleanup of removed devices."""
        device_id = "device1"
        devices = {device_id: {"id": device_id, "name": "Test Device", "muller_type": "FPN"}}

        # Add device
        self.device_manager.update_devices(devices)

        # Remove device
        self.device_manager.update_devices({})

        # Device should be marked as removed
        assert self.device_manager.get_device_state(device_id) == DeviceState.REMOVED

        # Cleanup removed devices
        removed = self.device_manager.cleanup_removed_devices()

        assert device_id in removed
        assert device_id not in self.device_manager._devices
        assert device_id not in self.device_manager._device_states

    def test_get_statistics(self):
        """Test statistics generation."""
        stats = self.device_manager.get_statistics()

        assert "total_devices" in stats
        assert "device_states" in stats
        assert "registered_callbacks" in stats
        assert stats["total_devices"] == 0
        assert stats["registered_callbacks"] == 0

        # Add a device and check stats
        devices = {"device1": {"id": "device1", "name": "Test Device", "muller_type": "FPN"}}
        self.device_manager.update_devices(devices)

        stats = self.device_manager.get_statistics()
        assert stats["total_devices"] == 1

    def test_device_data_changed_detection(self):
        """Test the _device_data_changed method with various scenarios."""
        manager = self.device_manager

        # Test no changes
        old_data = {"name": "Test", "muller_type": "FPN", "therm_measured_temperature": 20.0}
        new_data = {"name": "Test", "muller_type": "FPN", "therm_measured_temperature": 20.0}
        assert not manager._device_data_changed(old_data, new_data)

        # Test temperature change
        new_data = {"name": "Test", "muller_type": "FPN", "therm_measured_temperature": 22.0}
        assert manager._device_data_changed(old_data, new_data)

        # Test mode change
        old_data = {"therm_setpoint_mode": "manual"}
        new_data = {"therm_setpoint_mode": "home"}
        assert manager._device_data_changed(old_data, new_data)

        # Test irrelevant field change (not in key_fields)
        old_data = {"irrelevant_field": "old_value"}
        new_data = {"irrelevant_field": "new_value"}
        assert not manager._device_data_changed(old_data, new_data)

    def test_multiple_devices_complex_scenario(self):
        """Test a complex scenario with multiple devices and changes."""
        # Initial state: 2 devices
        initial_devices = {
            "device1": {"id": "device1", "name": "Device 1", "therm_measured_temperature": 20.0},
            "device2": {"id": "device2", "name": "Device 2", "therm_measured_temperature": 21.0},
        }
        self.device_manager.update_devices(initial_devices)

        # New state: device1 modified, device2 removed, device3 added
        new_devices = {
            "device1": {
                "id": "device1",
                "name": "Device 1 Updated",
                "therm_measured_temperature": 22.0,
            },
            "device3": {"id": "device3", "name": "Device 3", "therm_measured_temperature": 19.0},
        }
        changes = self.device_manager.update_devices(new_devices)

        assert len(changes) == 3
        change_types = {change.change_type for change in changes}
        assert change_types == {"modified", "removed", "added"}

        # Check specific changes
        device1_change = next(c for c in changes if c.device_id == "device1")
        assert device1_change.change_type == "modified"

        device2_change = next(c for c in changes if c.device_id == "device2")
        assert device2_change.change_type == "removed"

        device3_change = next(c for c in changes if c.device_id == "device3")
        assert device3_change.change_type == "added"
