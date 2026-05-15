"""Unit tests for coordinator device lifecycle management."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.muller_intuitiv.coordinator import MullerIntuitivDataUpdateCoordinator
from custom_components.muller_intuitiv.api import MullerIntuitivApi
from custom_components.muller_intuitiv.device_manager import DeviceChange, DeviceState
from custom_components.muller_intuitiv.exceptions import MullerIntuitivApiError


@pytest.fixture
def mock_hass():
    """Create a mock Home Assistant instance."""
    hass = Mock()
    hass.config_entries = Mock()
    hass.config_entries.async_update_entry = AsyncMock()
    return hass


@pytest.fixture
def mock_api():
    """Create a mock API instance."""
    api = Mock(spec=MullerIntuitivApi)
    api.get_homes_data = AsyncMock()
    api.get_home_status = AsyncMock()
    api.get_home_system_info = AsyncMock(return_value={})
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
        "expires_at": 9999999999,  # Far future
    }
    return entry


@pytest.fixture
def coordinator(mock_hass, mock_api, mock_entry):
    """Create a coordinator instance for testing."""
    return MullerIntuitivDataUpdateCoordinator(mock_hass, mock_api, mock_entry)


class TestCoordinatorLifecycle:
    """Test coordinator device lifecycle management."""

    @pytest.mark.asyncio
    async def test_device_manager_integration(self, coordinator, mock_api):
        """Test that device manager is properly integrated."""
        # Mock API responses
        mock_api.get_homes_data.return_value = {
            "id": "test_home_id",
            "name": "Test Home",
            "rooms": [
                {
                    "id": "room1",
                    "name": "Living Room",
                    "modules": [{"id": "device1", "type": "FPN"}],
                }
            ],
        }

        mock_api.get_home_status.return_value = [
            {
                "id": "device1",
                "name": "Device 1",
                "muller_type": "FPN",
                "therm_measured_temperature": 20.0,
                "therm_setpoint_temperature": 21.0,
                "therm_setpoint_mode": "manual",
            }
        ]

        # Execute update
        result = await coordinator._async_update_data()

        # Verify device manager received the data
        assert "device1" in result
        assert coordinator.device_manager.get_device("device1") is not None

    @pytest.mark.asyncio
    async def test_device_changes_handling(self, coordinator, mock_api):
        """Test handling of device changes."""
        # Setup initial state
        mock_api.get_homes_data.return_value = {
            "id": "test_home_id",
            "rooms": [{"id": "room1", "modules": [{"id": "device1", "type": "FPN"}]}],
        }

        mock_api.get_home_status.return_value = [
            {"id": "device1", "name": "Device 1", "muller_type": "FPN"}
        ]

        # First update
        await coordinator._async_update_data()

        # Mock device manager to return changes
        with patch.object(coordinator.device_manager, "update_devices") as mock_update:
            mock_update.return_value = [
                DeviceChange(
                    device_id="device2",
                    change_type="added",
                    new_data={"id": "device2", "name": "New Device"},
                )
            ]

            # Second update
            await coordinator._async_update_data()

            # Verify update_devices was called
            mock_update.assert_called()

    @pytest.mark.asyncio
    async def test_device_availability_check(self, coordinator):
        """Test device availability checking."""
        device_id = "test_device"

        # Mock device manager
        with patch.object(coordinator.device_manager, "is_device_available") as mock_available:
            mock_available.return_value = True

            assert coordinator.is_device_available(device_id) is True
            mock_available.assert_called_with(device_id)

    def test_device_statistics(self, coordinator):
        """Test device statistics retrieval."""
        expected_stats = {
            "total_devices": 2,
            "device_states": {"available": 2},
            "registered_callbacks": 1,
        }

        with patch.object(coordinator.device_manager, "get_statistics") as mock_stats:
            mock_stats.return_value = expected_stats

            stats = coordinator.get_device_statistics()
            assert stats == expected_stats

    @pytest.mark.asyncio
    async def test_device_change_callback_registration(self, coordinator):
        """Test that device change callback is properly registered."""
        # Verify callback is registered during initialization
        assert len(coordinator.device_manager._change_callbacks) == 1

        # Verify the callback is our handler
        callback = coordinator.device_manager._change_callbacks[0]
        assert callback.__name__ == "_handle_device_changes"

    @pytest.mark.asyncio
    async def test_handle_device_changes_added(self, coordinator):
        """Test handling of added device changes."""
        changes = [
            DeviceChange(
                device_id="new_device",
                change_type="added",
                new_data={"id": "new_device", "name": "New Device"},
            )
        ]

        # Should not raise any exceptions
        coordinator._handle_device_changes(changes)

    @pytest.mark.asyncio
    async def test_handle_device_changes_removed(self, coordinator):
        """Test handling of removed device changes."""
        changes = [
            DeviceChange(
                device_id="removed_device",
                change_type="removed",
                old_data={"id": "removed_device", "name": "Removed Device"},
            )
        ]

        with patch.object(coordinator.device_manager, "mark_device_unavailable") as mock_mark:
            coordinator._handle_device_changes(changes)
            mock_mark.assert_called_with("removed_device")

    @pytest.mark.asyncio
    async def test_handle_device_changes_modified(self, coordinator):
        """Test handling of modified device changes."""
        changes = [
            DeviceChange(
                device_id="modified_device",
                change_type="modified",
                old_data={"id": "modified_device", "temperature": 20.0},
                new_data={"id": "modified_device", "temperature": 22.0},
            )
        ]

        # Should not raise any exceptions
        coordinator._handle_device_changes(changes)

    @pytest.mark.asyncio
    async def test_home_id_refresh_on_invalid_error(self, coordinator, mock_api, mock_hass):
        """Test automatic home_id refresh when invalid home_id error occurs."""
        # Setup mocks
        mock_api.get_homes_data.return_value = {"id": "test_home_id", "rooms": []}

        # First call fails with invalid home_id
        mock_api.get_home_status.side_effect = [
            MullerIntuitivApiError("Invalid home_id"),
            [],  # Second call succeeds
        ]

        # Mock fresh home data with new ID
        fresh_home_data = {"id": "new_home_id"}

        with patch.object(mock_api, "get_homes_data", return_value=fresh_home_data):
            result = await coordinator._async_update_data()

            # Verify home_id was updated
            assert coordinator.home_id == "new_home_id"

            # Verify config entry was updated
            mock_hass.config_entries.async_update_entry.assert_called()

    @pytest.mark.asyncio
    async def test_api_error_propagation(self, coordinator, mock_api):
        """Test that non-recoverable API errors are properly propagated."""
        mock_api.get_homes_data.side_effect = MullerIntuitivApiError("Unrecoverable error")

        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()

    @pytest.mark.asyncio
    async def test_device_mapping_integration(self, coordinator, mock_api):
        """Test integration with device-to-room mapping logic."""
        # Mock complex home structure
        mock_api.get_homes_data.return_value = {
            "id": "test_home_id",
            "rooms": [
                {
                    "id": "room1",
                    "name": "Living Room",
                    "modules": [{"id": "device1", "type": "FPN"}, {"id": "device2", "type": "FPN"}],
                },
                {"id": "room2", "name": "Bedroom", "modules": [{"id": "device3", "type": "FPN"}]},
            ],
        }

        mock_api.get_home_status.return_value = [
            {
                "id": "device1",
                "name": "Living Room Thermostat",
                "muller_type": "FPN",
                "therm_measured_temperature": 20.0,
            },
            {"id": "device2", "name": "Living Room Heater", "muller_type": "FPN"},
            {
                "id": "device3",
                "name": "Bedroom Thermostat",
                "muller_type": "FPN",
                "therm_measured_temperature": 18.0,
            },
        ]

        result = await coordinator._async_update_data()

        # Verify all devices are present with room mappings
        assert len(result) == 3
        assert "device1" in result
        assert "device2" in result
        assert "device3" in result

        # Verify room IDs were mapped correctly
        assert result["device1"]["room_id"] == "room1"
        assert result["device2"]["room_id"] == "room1"
        assert result["device3"]["room_id"] == "room2"

    @pytest.mark.asyncio
    async def test_room_status_id_maps_to_room_id(self, coordinator, mock_api):
        """Test API status entries keyed by room ID are usable for control calls."""
        mock_api.get_homes_data.return_value = {
            "id": "test_home_id",
            "rooms": [
                {
                    "id": "3755235792",
                    "name": "Chambre Quentin",
                    "type": "bedroom",
                    "modules": [],
                }
            ],
        }
        mock_api.get_home_status.return_value = [
            {
                "id": "3755235792",
                "muller_type": "FPN",
                "room_id": None,
                "room_name": "Chambre Quentin",
                "therm_measured_temperature": 18.9,
            }
        ]

        result = await coordinator._async_update_data()

        assert result["3755235792"]["room_id"] == "3755235792"
        assert result["3755235792"]["room_name"] == "Chambre Quentin"
        assert result["3755235792"]["room_type"] == "bedroom"

    @pytest.mark.asyncio
    async def test_room_name_fallback_maps_room_id(self, coordinator, mock_api):
        """Test status entries can be matched by room name when module ids are absent."""
        mock_api.get_homes_data.return_value = {
            "id": "test_home_id",
            "rooms": [
                {
                    "id": "room1",
                    "name": "Chambre Quentin",
                    "type": "bedroom",
                    "modules": [],
                }
            ],
        }
        mock_api.get_home_status.return_value = [
            {
                "id": "device-without-module",
                "muller_type": "FPN",
                "room_id": None,
                "room_name": "Chambre Quentin",
                "therm_measured_temperature": 18.9,
            }
        ]

        result = await coordinator._async_update_data()

        assert result["device-without-module"]["room_id"] == "room1"
