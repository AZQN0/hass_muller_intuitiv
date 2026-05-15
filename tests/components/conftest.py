"""Fixtures for Home Assistant component tests."""

from __future__ import annotations

import importlib.util

import pytest

if importlib.util.find_spec("pytest_homeassistant_custom_component") is None:
    pytest.skip(
        "Home Assistant component tests require pytest-homeassistant-custom-component "
        "or an equivalent Home Assistant Core test environment.",
        allow_module_level=True,
    )


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Allow Home Assistant to load integrations from custom_components."""
    yield
