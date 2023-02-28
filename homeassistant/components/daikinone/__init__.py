"""The daikinone integration."""

from dataclasses import dataclass

from charles_dev.daikin_cloud import DaikinCloud
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant

from .const import _LOGGER, DOMAIN

PLATFORMS: list[Platform] = [Platform.CLIMATE, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up daikinone from a config entry."""

    hass.data.setdefault(DOMAIN, {})
    email = config_entry.data[CONF_EMAIL]
    password = config_entry.data[CONF_PASSWORD]

    client = DaikinCloud()
    await client.login(email, password)

    _LOGGER.debug("Connected to DaikinCloud")

    data = DaikinData(config_entry.entry_id, client)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = data

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


@dataclass
class DaikinData:
    """Shared Data for Daikin."""

    entry_id: str
    client: DaikinCloud
