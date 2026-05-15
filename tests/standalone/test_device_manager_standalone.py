#!/usr/bin/env python3
"""Standalone test for DeviceManager without Home Assistant dependencies."""

import os
import sys

sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "custom_components", "muller_intuitiv")
    ),
)

from device_manager import DeviceChange, DeviceManager, DeviceState


def test_device_manager_initialization():
    """Test DeviceManager initialization."""
    manager = DeviceManager()
    assert manager._devices == {}
    assert manager._device_states == {}
    assert manager._change_callbacks == []
    print("✓ DeviceManager initialization test passed")


def test_device_addition():
    """Test adding a device."""
    manager = DeviceManager()

    devices = {"device1": {"id": "device1", "name": "Test Device", "muller_type": "FPN"}}

    changes = manager.update_devices(devices)

    assert len(changes) == 1
    assert changes[0].change_type == "added"
    assert changes[0].device_id == "device1"
    print("✓ Device addition test passed")


def test_device_removal():
    """Test removing a device."""
    manager = DeviceManager()

    # Add device first
    devices = {"device1": {"id": "device1", "name": "Test Device", "muller_type": "FPN"}}
    manager.update_devices(devices)

    # Remove device
    empty_devices = {}
    changes = manager.update_devices(empty_devices)

    assert len(changes) == 1
    assert changes[0].change_type == "removed"
    assert changes[0].device_id == "device1"
    print("✓ Device removal test passed")


def test_device_modification():
    """Test modifying a device."""
    manager = DeviceManager()

    # Initial device
    devices = {
        "device1": {"id": "device1", "name": "Test Device", "therm_measured_temperature": 20.0}
    }
    manager.update_devices(devices)

    # Modify device
    modified_devices = {
        "device1": {
            "id": "device1",
            "name": "Test Device",
            "therm_measured_temperature": 22.0,  # Changed
        }
    }
    changes = manager.update_devices(modified_devices)

    assert len(changes) == 1
    assert changes[0].change_type == "modified"
    assert changes[0].device_id == "device1"
    print("✓ Device modification test passed")


def test_device_availability():
    """Test device availability tracking."""
    manager = DeviceManager()
    device_id = "test_device"

    # Initially available
    assert manager.is_device_available(device_id) is True

    # Mark unavailable
    manager.mark_device_unavailable(device_id)
    assert manager.is_device_available(device_id) is False
    assert manager.get_device_state(device_id) == DeviceState.UNAVAILABLE
    print("✓ Device availability test passed")


def test_callback_system():
    """Test callback system."""
    manager = DeviceManager()
    callback_called = []

    def test_callback(changes):
        callback_called.extend(changes)

    manager.register_change_callback(test_callback)

    # Add device to trigger callback
    devices = {"device1": {"id": "device1", "name": "Callback Test Device"}}
    manager.update_devices(devices)

    assert len(callback_called) == 1
    assert callback_called[0].change_type == "added"
    print("✓ Callback system test passed")


def test_statistics():
    """Test statistics generation."""
    manager = DeviceManager()

    stats = manager.get_statistics()
    assert "total_devices" in stats
    assert "device_states" in stats
    assert "registered_callbacks" in stats
    assert stats["total_devices"] == 0

    # Add device and check stats
    devices = {"device1": {"id": "device1", "name": "Stats Test"}}
    manager.update_devices(devices)

    stats = manager.get_statistics()
    assert stats["total_devices"] == 1
    print("✓ Statistics test passed")


if __name__ == "__main__":
    print("🧪 Running DeviceManager standalone tests...")

    test_device_manager_initialization()
    test_device_addition()
    test_device_removal()
    test_device_modification()
    test_device_availability()
    test_callback_system()
    test_statistics()

    print("\n✅ All DeviceManager tests passed!")
    print("DeviceManager is working correctly and ready for integration.")
