"""Cover Control Advanced - Home Assistant custom integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_WINDOW_DIRECTION, DOMAIN
from .controller import CoverControlAdvancedController

PLATFORMS = ["sensor"]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Cover Control Advanced instance from a config entry."""
    controller = CoverControlAdvancedController(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = controller
    await controller.async_setup()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        ctrl: CoverControlAdvancedController = hass.data[DOMAIN].pop(entry.entry_id)
        await ctrl.async_unload()
    return ok


def _normalize_window_direction(value: str | None) -> str:
    raw = (value or "").strip().lower()
    mapping = {
        "n": "north",
        "north": "north",
        "nord": "north",
        "norden": "north",
        "o": "east",
        "e": "east",
        "ost": "east",
        "osten": "east",
        "east": "east",
        "s": "south",
        "south": "south",
        "sud": "south",
        "sued": "south",
        "sueden": "south",
        "w": "west",
        "west": "west",
    }
    return mapping.get(raw, "")


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries to the current schema."""
    if entry.version >= 2:
        return True

    data = dict(entry.data)
    legacy_direction = data.get("direction")
    if CONF_WINDOW_DIRECTION not in data:
        data[CONF_WINDOW_DIRECTION] = _normalize_window_direction(legacy_direction)
    data.pop("direction", None)

    hass.config_entries.async_update_entry(entry, data=data, version=2)
    _LOGGER.debug("Migrated config entry %s to version 2", entry.entry_id)
    return True
