"""Unit tests for climate entity availability."""
import pytest
from unittest.mock import Mock, patch

from custom_components.muller_intuitiv.climate import MullerIntuitivClimate


@pytest.fixture
def mock_coordinator():
    """Create a mock coordinator."""
    coordinator = Mock()
    coordinator.data = {
        "device1": {
            "id": "device1",
            "name": "Test Device",
            "muller_type": "FPN",
            "therm_measured_temperature": 20.0,
            "therm_setpoint_temperature": 21.0,
            "therm_setpoint_mode": "manual",
            "room_id": "room1"
        }
    }
    coordinator.is_device_available = Mock(return_value=True)
    return coordinator


@pytest.fixture
def climate_entity(mock_coordinator):
    """Create a climate entity for testing."""
    return MullerIntuitivClimate(mock_coordinator, "device1", "home1")


class TestClimateAvailability:
    """Test climate entity availability functionality."""

    def test_available_when_device_exists_and_available(self, climate_entity, mock_coordinator):
        """Test that entity is available when device exists and is marked available."""
        mock_coordinator.is_device_available.return_value = True

        assert climate_entity.available is True
        mock_coordinator.is_device_available.assert_called_with("device1")

    def test_unavailable_when_device_not_available(self, climate_entity, mock_coordinator):
        """Test that entity is unavailable when device is marked unavailable."""
        mock_coordinator.is_device_available.return_value = False

        assert climate_entity.available is False

    def test_unavailable_when_device_not_in_data(self, climate_entity, mock_coordinator):
        """Test that entity is unavailable when device is not in coordinator data."""
        # Remove device from coordinator data
        mock_coordinator.data = {}
        mock_coordinator.is_device_available.return_value = True

        assert climate_entity.available is False

    def test_unavailable_when_both_conditions_false(self, climate_entity, mock_coordinator):
        """Test unavailable when both device doesn't exist and isn't available."""
        mock_coordinator.data = {}
        mock_coordinator.is_device_available.return_value = False

        assert climate_entity.available is False

    def test_device_data_property_with_available_device(self, climate_entity, mock_coordinator):
        """Test _device_data property when device is available."""
        device_data = climate_entity._device_data

        assert device_data == mock_coordinator.data["device1"]
        assert device_data["name"] == "Test Device"
        assert device_data["therm_measured_temperature"] == 20.0

    def test_device_data_property_with_missing_device(self, climate_entity, mock_coordinator):
        """Test _device_data property when device is missing."""
        mock_coordinator.data = {}

        device_data = climate_entity._device_data

        assert device_data == {}

    def test_current_temperature_with_available_device(self, climate_entity):
        """Test current_temperature when device is available."""
        assert climate_entity.current_temperature == 20.0

    def test_current_temperature_with_unavailable_device(self, climate_entity, mock_coordinator):
        """Test current_temperature when device is unavailable."""
        mock_coordinator.data = {}

        assert climate_entity.current_temperature is None

    def test_target_temperature_with_available_device(self, climate_entity):
        """Test target_temperature when device is available."""
        assert climate_entity.target_temperature == 21.0

    def test_target_temperature_with_unavailable_device(self, climate_entity, mock_coordinator):
        """Test target_temperature when device is unavailable."""
        mock_coordinator.data = {}

        assert climate_entity.target_temperature is None

    def test_name_with_available_device(self, climate_entity):
        """Test name property when device is available."""
        assert climate_entity.name == "Test Device"

    def test_name_with_unavailable_device(self, climate_entity, mock_coordinator):
        """Test name property when device is unavailable."""
        mock_coordinator.data = {}

        expected_name = f"Heater {climate_entity.device_id}"
        assert climate_entity.name == expected_name

    def test_unique_id(self, climate_entity):
        """Test unique_id property."""
        assert climate_entity.unique_id == "muller_intuitiv_device_device1"

    @patch("custom_components.muller_intuitiv.climate._LOGGER")
    def test_availability_logging_when_unavailable(self, mock_logger, climate_entity, mock_coordinator):
        """Test that unavailability is logged for debugging."""
        mock_coordinator.data = {}
        mock_coordinator.is_device_available.return_value = False

        # Access available property to trigger logging
        available = climate_entity.available

        assert available is False
        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args[0]
        assert "Device device1 availability" in call_args[0]

    @patch("custom_components.muller_intuitiv.climate._LOGGER")
    def test_no_logging_when_available(self, mock_logger, climate_entity, mock_coordinator):
        """Test that no debug logging occurs when device is available."""
        mock_coordinator.is_device_available.return_value = True

        # Access available property
        available = climate_entity.available

        assert available is True
        mock_logger.debug.assert_not_called()

    def test_availability_state_transitions(self, climate_entity, mock_coordinator):
        """Test availability state transitions."""
        # Initially available
        mock_coordinator.is_device_available.return_value = True
        assert climate_entity.available is True

        # Becomes unavailable (device manager marks it so)
        mock_coordinator.is_device_available.return_value = False
        assert climate_entity.available is False

        # Remove from data as well
        mock_coordinator.data = {}
        assert climate_entity.available is False

        # Device comes back
        mock_coordinator.data["device1"] = {
            "id": "device1",
            "name": "Test Device Restored",
            "therm_measured_temperature": 22.0
        }
        mock_coordinator.is_device_available.return_value = True
        assert climate_entity.available is True

    def test_device_info_creation(self, climate_entity):
        """Test device info is properly created."""
        device_info = climate_entity._attr_device_info

        assert device_info is not None
        assert ("muller_intuitiv", "device_device1") in device_info["identifiers"]
        assert device_info["manufacturer"] == "Muller"
        assert "FPN" in device_info["model"]
        assert device_info["via_device"] == ("muller_intuitiv", "home_home1")

    def test_multiple_climate_entities(self, mock_coordinator):
        """Test multiple climate entities with different availability states."""
        # Setup multiple devices in coordinator
        mock_coordinator.data = {
            "device1": {"id": "device1", "name": "Device 1", "muller_type": "FPN"},
            "device2": {"id": "device2", "name": "Device 2", "muller_type": "FPN"}
        }

        # Mock availability - device1 available, device2 unavailable
        def mock_availability(device_id):
            return device_id == "device1"

        mock_coordinator.is_device_available.side_effect = mock_availability

        # Create entities
        entity1 = MullerIntuitivClimate(mock_coordinator, "device1", "home1")
        entity2 = MullerIntuitivClimate(mock_coordinator, "device2", "home1")

        # Test availability
        assert entity1.available is True
        assert entity2.available is False

        # Test data access
        assert entity1.name == "Device 1"
        assert entity2.name == "Device 2"

    def test_edge_case_empty_device_data(self, mock_coordinator):
        """Test handling of edge case with empty device data."""
        mock_coordinator.data = {
            "device1": {}  # Empty device data
        }
        mock_coordinator.is_device_available.return_value = True

        entity = MullerIntuitivClimate(mock_coordinator, "device1", "home1")

        # Should still be available but with fallback values
        assert entity.available is True
        assert entity.current_temperature is None
        assert entity.target_temperature is None
        assert "Heater device1" in entity.name