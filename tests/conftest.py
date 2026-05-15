"""Shared pytest configuration for the Muller Intuitiv tests."""

from __future__ import annotations

import importlib.util
import threading
from unittest.mock import Mock

import pytest

pytest_plugins = []

if importlib.util.find_spec("pytest_homeassistant_custom_component") is not None:
    pytest_plugins.append("pytest_homeassistant_custom_component")


@pytest.fixture(autouse=True)
def setup_homeassistant_frame_helper():
    """Initialize Home Assistant's frame helper for mock-based tests."""
    from homeassistant.helpers import frame

    hass = Mock()
    hass.data = {}
    hass.loop_thread_id = threading.get_ident()
    frame.async_setup(hass)
    yield
    frame._hass.hass = None
