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
    from homeassistant import core
    from homeassistant.helpers import frame

    hass = Mock()
    hass.data = {}
    hass.loop_thread_id = threading.get_ident()
    if hasattr(frame, "async_setup"):
        frame.async_setup(hass)
    else:
        core._hass.hass = hass
    yield
    if hasattr(frame, "_hass"):
        frame._hass.hass = None
    core._hass.hass = None
