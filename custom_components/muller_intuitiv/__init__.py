"""The Muller Intuitiv integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MullerIntuitivApi
from .const import DOMAIN, CONF_ACCESS_TOKEN
from .coordinator import MullerIntuitivDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CLIMATE]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Muller Intuitiv from a config entry."""
    session = async_get_clientsession(hass)
    
    token = entry.data.get(CONF_ACCESS_TOKEN)
    api = MullerIntuitivApi(session, token)
    
    coordinator = MullerIntuitivDataUpdateCoordinator(hass, api, entry)
    
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
