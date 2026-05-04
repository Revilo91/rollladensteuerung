"""Cover Control Advanced - Home Assistant custom integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_SUN_AZIMUTH_TOLERANCE, CONF_WINDOW_AZIMUTH, DOMAIN
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


def _direction_to_azimuth(value: str | None) -> int:
    raw = (value or "").strip().lower()
    mapping = {
        "n": 0,
        "north": 0,
        "nord": 0,
        "norden": 0,
        "o": 90,
        "e": 90,
        "ost": 90,
        "osten": 90,
        "east": 90,
        "s": 180,
        "south": 180,
        "sud": 180,
        "sued": 180,
        "sueden": 180,
        "w": 270,
        "west": 270,
    }
    return mapping.get(raw, 180)


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate old config entries to the current schema."""
    if entry.version >= 3:
        return True

    data = dict(entry.data)
    if CONF_WINDOW_AZIMUTH not in data:
        if "window_direction" in data:
            data[CONF_WINDOW_AZIMUTH] = _direction_to_azimuth(data.get("window_direction"))
        else:
            data[CONF_WINDOW_AZIMUTH] = _direction_to_azimuth(data.get("direction"))

    if CONF_SUN_AZIMUTH_TOLERANCE not in data:
        data[CONF_SUN_AZIMUTH_TOLERANCE] = 45

    data.pop("direction", None)
    data.pop("window_direction", None)

    hass.config_entries.async_update_entry(entry, data=data, version=3)
    _LOGGER.debug("Migrated config entry %s to version 3", entry.entry_id)
    return True
