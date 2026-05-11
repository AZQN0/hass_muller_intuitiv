"""Integration tests for complete device lifecycle scenarios."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from homeassistant.core import HomeAssistant

from custom_components.muller_intuitiv.coordinator import MullerIntuitivDataUpdateCoordinator
from custom_components.muller_intuitiv.api import MullerIntuitivApi
from custom_components.muller_intuitiv.climate import MullerIntuitivClimate
from custom_components.muller_intuitiv.device_manager import DeviceState


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = Mock(spec=HomeAssistant)
    hass.config_entries = Mock()
    hass.config_entries.async_update_entry = AsyncMock()
    return hass


@pytest.fixture
def mock_api():
    """Create a mock API instance."""
    api = Mock(spec=MullerIntuitivApi)
    api.get_homes_data = AsyncMock()
    api.get_home_status = AsyncMock()
    api.refresh_token = AsyncMock()
    return api


@pytest.fixture
def mock_entry():
    """Create a mock config entry."""
    entry = Mock()
    entry.data = {
        "home_id": "test_home_id",
        "access_token": "test_token",
        "refresh_token": "test_refresh_token",
        "expires_in": 3600,
        "expires_at": 9999999999  # Far future
    }
    return entry


class TestDeviceLifecycleIntegration:
    """Integration tests for complete device lifecycle."""

    @pytest.mark.asyncio
    async def test_complete_device_addition_scenario(self, mock_hass, mock_api, mock_entry):
        """Test complete scenario of adding a new device."""
        # Create coordinator
        coordinator = MullerIntuitivDataUpdateCoordinator(mock_hass, mock_api, mock_entry)

        # Initial state: one device
        mock_api.get_homes_data.return_value = {
            "id": "test_home_id",
            "name": "Test Home",
            "rooms": [
                {
                    "id": "room1",
                    "name": "Living Room",
                    "modules": [{"id": "device1", "type": "FPN"}]
                }
            ]
        }

        mock_api.get_home_status.return_value = [
            {
                "id": "device1",
                "name": "Living Room Thermostat",
                "muller_type": "FPN",
                "therm_measured_temperature": 20.0,
                "therm_setpoint_temperature": 21.0,
                "therm_setpoint_mode": "manual"
            }
        ]

        # First update - initial device
        await coordinator._async_update_data()

        # Verify initial state
        assert len(coordinator.data) == 1
        assert "device1" in coordinator.data
        assert coordinator.is_device_available("device1")

        # Create climate entity for initial device
        climate1 = MullerIntuitivClimate(coordinator, "device1", "test_home_id")
        assert climate1.available is True
        assert climate1.current_temperature == 20.0

        # Simulate adding a new device to the home
        mock_api.get_homes_data.return_value = {
            "id": "test_home_id",
            "name": "Test Home",
            "rooms": [
                {
                    "id": "room1",
                    "name": "Living Room",
                    "modules": [
                        {"id": "device1", "type": "FPN"},
                        {"id": "device2", "type": "FPN"}  # New device added
                    ]
                }
            ]
        }

        mock_api.get_home_status.return_value = [
            {
                "id": "device1",
                "name": "Living Room Thermostat",
                "muller_type": "FPN",
                "therm_measured_temperature": 20.5,  # Slightly changed
                "therm_setpoint_temperature": 21.0,
                "therm_setpoint_mode": "manual"
            },
            {
                "id": "device2",
                "name": "Kitchen Heater",
                "muller_type": "FPN",
                "therm_setpoint_temperature": 19.0,
                "therm_setpoint_mode": "eco"
            }
        ]

        # Second update - device added
        changes_detected = []
        def track_changes(changes):
            changes_detected.extend(changes)

        coordinator.device_manager.register_change_callback(track_changes)
        await coordinator._async_update_data()

        # Verify device was detected as added
        assert len(coordinator.data) == 2
        assert "device1" in coordinator.data
        assert "device2" in coordinator.data

        # Check that changes were detected
        assert len(changes_detected) == 2  # one modified (device1), one added (device2)
        added_change = next(c for c in changes_detected if c.change_type == "added")
        assert added_change.device_id == "device2"

        # Verify both devices are available
        assert coordinator.is_device_available("device1")
        assert coordinator.is_device_available("device2")

        # Create climate entity for new device
        climate2 = MullerIntuitivClimate(coordinator, "device2", "test_home_id")
        assert climate2.available is True
        assert climate2.target_temperature == 19.0

    @pytest.mark.asyncio
    async def test_complete_device_removal_scenario(self, mock_hass, mock_api, mock_entry):
        """Test complete scenario of removing a device."""
        coordinator = MullerIntuitivDataUpdateCoordinator(mock_hass, mock_api, mock_entry)

        # Initial state: two devices
        mock_api.get_homes_data.return_value = {
            "id": "test_home_id",
            "rooms": [
                {
                    "id": "room1",
                    "modules": [
                        {"id": "device1", "type": "FPN"},
                        {"id": "device2", "type": "FPN"}
                    ]
                }
            ]
        }

        mock_api.get_home_status.return_value = [
            {"id": "device1", "name": "Device 1", "muller_type": "FPN"},
            {"id": "device2", "name": "Device 2", "muller_type": "FPN"}
        ]

        # First update
        await coordinator._async_update_data()

        # Create climate entities
        climate1 = MullerIntuitivClimate(coordinator, "device1", "test_home_id")
        climate2 = MullerIntuitivClimate(coordinator, "device2", "test_home_id")

        # Both should be available
        assert climate1.available is True
        assert climate2.available is True

        # Remove device2 from the system
        mock_api.get_homes_data.return_value = {
            "id": "test_home_id",
            "rooms": [
                {
                    "id": "room1",
                    "modules": [{"id": "device1", "type": "FPN"}]  # device2 removed
                }
            ]
        }

        mock_api.get_home_status.return_value = [
            {"id": "device1", "name": "Device 1", "muller_type": "FPN"}
        ]

        # Track changes
        changes_detected = []
        def track_changes(changes):
            changes_detected.extend(changes)

        coordinator.device_manager.register_change_callback(track_changes)

        # Second update - device removed
        await coordinator._async_update_data()

        # Verify device removal was detected
        removed_change = next(c for c in changes_detected if c.change_type == "removed")
        assert removed_change.device_id == "device2"

        # Verify coordinator state
        assert len(coordinator.data) == 1
        assert "device1" in coordinator.data
        assert "device2" not in coordinator.data

        # Verify availability states
        assert coordinator.is_device_available("device1") is True
        assert coordinator.is_device_available("device2") is False  # Marked unavailable

        # Verify climate entity states
        assert climate1.available is True
        assert climate2.available is False  # Should be unavailable now

    @pytest.mark.asyncio
    async def test_device_modification_propagation(self, mock_hass, mock_api, mock_entry):
        """Test that device modifications propagate to climate entities."""
        coordinator = MullerIntuitivDataUpdateCoordinator(mock_hass, mock_api, mock_entry)

        # Initial device state
        mock_api.get_homes_data.return_value = {
            "id": "test_home_id",
            "rooms": [{"id": "room1", "modules": [{"id": "device1", "type": "FPN"}]}]
        }

        mock_api.get_home_status.return_value = [
            {
                "id": "device1",
                "name": "Original Name",
                "muller_type": "FPN",
                "therm_measured_temperature": 20.0,
                "therm_setpoint_temperature": 21.0,
                "therm_setpoint_mode": "manual"
            }
        ]

        await coordinator._async_update_data()
        climate = MullerIntuitivClimate(coordinator, "device1", "test_home_id")

        # Initial state
        assert climate.name == "Original Name"
        assert climate.current_temperature == 20.0
        assert climate.target_temperature == 21.0

        # Modify device properties
        mock_api.get_home_status.return_value = [
            {
                "id": "device1",
                "name": "Updated Name",
                "muller_type": "FPN",
                "therm_measured_temperature": 22.5,
                "therm_setpoint_temperature": 23.0,
                "therm_setpoint_mode": "eco"
            }
        ]

        await coordinator._async_update_data()

        # Verify updates propagated to climate entity
        assert climate.name == "Updated Name"
        assert climate.current_temperature == 22.5
        assert climate.target_temperature == 23.0
        assert climate.available is True

    @pytest.mark.asyncio
    async def test_home_replacement_scenario(self, mock_hass, mock_api, mock_entry):
        """Test scenario where entire home is replaced (e.g., user moves)."""
        coordinator = MullerIntuitivDataUpdateCoordinator(mock_hass, mock_api, mock_entry)

        # Original home with devices
        mock_api.get_homes_data.return_value = {
            "id": "test_home_id",
            "rooms": [
                {"id": "room1", "modules": [
                    {"id": "old_device1", "type": "FPN"},
                    {"id": "old_device2", "type": "FPN"}
                ]}
            ]
        }

        mock_api.get_home_status.return_value = [
            {"id": "old_device1", "name": "Old Device 1", "muller_type": "FPN"},
            {"id": "old_device2", "name": "Old Device 2", "muller_type": "FPN"}
        ]

        await coordinator._async_update_data()

        # Create climate entities for old devices
        old_climate1 = MullerIntuitivClimate(coordinator, "old_device1", "test_home_id")
        old_climate2 = MullerIntuitivClimate(coordinator, "old_device2", "test_home_id")

        assert old_climate1.available is True
        assert old_climate2.available is True

        # Complete home replacement - all new devices
        mock_api.get_homes_data.return_value = {
            "id": "test_home_id",
            "rooms": [
                {"id": "new_room1", "modules": [
                    {"id": "new_device1", "type": "FPN"},
                    {"id": "new_device2", "type": "FPN"},
                    {"id": "new_device3", "type": "FPN"}
                ]}
            ]
        }

        mock_api.get_home_status.return_value = [
            {"id": "new_device1", "name": "New Device 1", "muller_type": "FPN"},
            {"id": "new_device2", "name": "New Device 2", "muller_type": "FPN"},
            {"id": "new_device3", "name": "New Device 3", "muller_type": "FPN"}
        ]

        # Track all changes
        changes_detected = []
        def track_changes(changes):
            changes_detected.extend(changes)

        coordinator.device_manager.register_change_callback(track_changes)

        await coordinator._async_update_data()

        # Verify massive changes detected
        assert len(changes_detected) == 5  # 2 removed + 3 added

        removed_changes = [c for c in changes_detected if c.change_type == "removed"]
        added_changes = [c for c in changes_detected if c.change_type == "added"]

        assert len(removed_changes) == 2
        assert len(added_changes) == 3

        # Old devices should be unavailable
        assert old_climate1.available is False
        assert old_climate2.available is False

        # New devices should be available
        new_climate1 = MullerIntuitivClimate(coordinator, "new_device1", "test_home_id")
        assert new_climate1.available is True

    @pytest.mark.asyncio
    async def test_device_state_persistence_through_updates(self, mock_hass, mock_api, mock_entry):
        """Test that device states persist correctly through multiple updates."""
        coordinator = MullerIntuitivDataUpdateCoordinator(mock_hass, mock_api, mock_entry)

        # Setup device
        mock_api.get_homes_data.return_value = {
            "id": "test_home_id",
            "rooms": [{"id": "room1", "modules": [{"id": "device1", "type": "FPN"}]}]
        }

        mock_api.get_home_status.return_value = [
            {"id": "device1", "name": "Persistent Device", "muller_type": "FPN"}
        ]

        # Multiple updates with same data
        for i in range(5):
            await coordinator._async_update_data()

            # Device should remain available
            assert coordinator.is_device_available("device1") is True

            # No new changes should be detected (after first update)
            stats = coordinator.get_device_statistics()
            assert stats["total_devices"] == 1

        # Verify device manager state is stable
        device_state = coordinator.device_manager.get_device_state("device1")
        assert device_state in (DeviceState.AVAILABLE, DeviceState.NEW)

    @pytest.mark.asyncio
    async def test_error_recovery_maintains_device_state(self, mock_hass, mock_api, mock_entry):
        """Test that device states are maintained during API error recovery."""
        coordinator = MullerIntuitivDataUpdateCoordinator(mock_hass, mock_api, mock_entry)

        # Initial successful update
        mock_api.get_homes_data.return_value = {
            "id": "test_home_id",
            "rooms": [{"id": "room1", "modules": [{"id": "device1", "type": "FPN"}]}]
        }

        mock_api.get_home_status.return_value = [
            {"id": "device1", "name": "Resilient Device", "muller_type": "FPN"}
        ]

        await coordinator._async_update_data()
        climate = MullerIntuitivClimate(coordinator, "device1", "test_home_id")

        # Verify initial state
        assert climate.available is True
        assert coordinator.is_device_available("device1") is True

        # Simulate API error (will be handled by coordinator error handling)
        mock_api.get_home_status.side_effect = Exception("Temporary API error")

        # Try to update - should fail but not crash
        with pytest.raises(Exception):
            await coordinator._async_update_data()

        # Device should still be tracked in device manager
        # (coordinator.data might be stale, but device_manager retains state)
        device_exists_in_manager = coordinator.device_manager.get_device("device1") is not None

        # Recovery - API works again
        mock_api.get_home_status.side_effect = None
        mock_api.get_home_status.return_value = [
            {"id": "device1", "name": "Resilient Device", "muller_type": "FPN"}
        ]

        await coordinator._async_update_data()

        # Device should be available again
        assert climate.available is True
        assert coordinator.is_device_available("device1") is True