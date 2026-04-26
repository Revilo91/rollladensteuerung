"""Rollladensteuerung – Home Assistant custom integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .controller import RollladenController

PLATFORMS = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Rollladensteuerung instance from a config entry."""
    controller = RollladenController(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = controller
    await controller.async_setup()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        ctrl: RollladenController = hass.data[DOMAIN].pop(entry.entry_id)
        await ctrl.async_unload()
    return ok
