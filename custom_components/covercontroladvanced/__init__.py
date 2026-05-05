"""Cover Control Advanced - Home Assistant custom integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry, entity_registry as er
from homeassistant.helpers.entity import DeviceInfo

from .const import (
    CONF_COVER,
    CONF_COVERS,
    CONF_ROOM_NAME,
    CONF_SUN_AZIMUTH_END,
    CONF_SUN_AZIMUTH_START,
    CONF_WINDOW_ENTITIES,
    DOMAIN,
)
from .controller import CoverControlAdvancedController


def entity_friendly_name(hass: HomeAssistant, entity_id: str) -> str:
    """Return the friendly name for an entity, falling back to entity_id."""
    ent_entry = er.async_get(hass).async_get(entity_id)
    if ent_entry:
        return ent_entry.name or ent_entry.original_name or entity_id
    state = hass.states.get(entity_id)
    if state:
        return state.attributes.get("friendly_name") or entity_id
    return entity_id


def build_device_info(hass: HomeAssistant, entry: ConfigEntry) -> DeviceInfo:
    """Return a DeviceInfo for the config entry.

    Named after the cover entity's friendly name when the room contains exactly
    one cover; otherwise named after the room.  The suggested_area is always
    set to the room name so HA places the device in the right area automatically.
    """
    covers = entry.data.get(CONF_COVERS, [])
    room_name = entry.data.get(CONF_ROOM_NAME, entry.title)
    device_name = room_name
    if len(covers) == 1:
        cover_id = covers[0].get(CONF_COVER, "")
        device_name = entity_friendly_name(hass, cover_id) or room_name
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=device_name,
        suggested_area=room_name,
        manufacturer="Cover Control Advanced",
    )

PLATFORMS = ["sensor", "select", "binary_sensor", "switch", "cover"]
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Cover Control Advanced instance from a config entry."""
    controller = CoverControlAdvancedController(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = controller
    await controller.async_setup()
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await controller.async_trigger_evaluation()
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
    if entry.version >= 7:
        return True

    data = dict(entry.data)

    if entry.version < 4:
        if "window_azimuth" not in data:
            if "window_direction" in data:
                data["window_azimuth"] = _direction_to_azimuth(data.get("window_direction"))
            else:
                data["window_azimuth"] = _direction_to_azimuth(data.get("direction"))

        if "sun_azimuth_tolerance" not in data:
            data["sun_azimuth_tolerance"] = 45

        azimuth = float(data.get("window_azimuth", 180)) % 360
        tolerance = float(data.get("sun_azimuth_tolerance", 45))
        tolerance = max(5.0, min(90.0, tolerance))

        if CONF_SUN_AZIMUTH_START not in data:
            data[CONF_SUN_AZIMUTH_START] = int((azimuth - tolerance) % 360)
        if CONF_SUN_AZIMUTH_END not in data:
            data[CONF_SUN_AZIMUTH_END] = int((azimuth + tolerance) % 360)

        data.pop("direction", None)
        data.pop("window_direction", None)
        data.pop("window_azimuth", None)
        data.pop("sun_azimuth_tolerance", None)

    if entry.version < 5:
        # v5: room_switch is now an internal select entity – remove the old config key
        data.pop("room_switch", None)

    if entry.version < 6:
        # v6: restructure flat data into room-level config + covers list
        cover_entry = {
            CONF_COVER: data.pop(CONF_COVER),
            CONF_WINDOW_ENTITIES: data.pop(CONF_WINDOW_ENTITIES, []),
            CONF_SUN_AZIMUTH_START: data.pop(CONF_SUN_AZIMUTH_START, 135),
            CONF_SUN_AZIMUTH_END: data.pop(CONF_SUN_AZIMUTH_END, 225),
        }
        data[CONF_COVERS] = [cover_entry]
        data.setdefault(CONF_ROOM_NAME, cover_entry[CONF_COVER])

    if entry.version < 7:
        room_name = data.get(CONF_ROOM_NAME)
        if isinstance(room_name, str):
            area = area_registry.async_get(hass).async_get_area(room_name)
            if area is not None:
                data[CONF_ROOM_NAME] = area.name

    hass.config_entries.async_update_entry(
        entry,
        data=data,
        title=data.get(CONF_ROOM_NAME, entry.title),
        version=7,
    )
    _LOGGER.debug("Migrated config entry %s to version 7", entry.entry_id)
    return True
