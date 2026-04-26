"""Rollladensteuerung – Home Assistant custom integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, LEGACY_KEY_MAPPING
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


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate older config entries with legacy key names."""
    data = dict(entry.data)
    changed = False

    for legacy_key, new_key in LEGACY_KEY_MAPPING.items():
        if legacy_key in data and new_key not in data:
            data[new_key] = data[legacy_key]
            changed = True

    if changed:
        hass.config_entries.async_update_entry(entry, data=data)

    return True
