"""Diagnostic sensor – shows the last decision reason."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_COVER,
    CONF_EVENT_SWITCH,
    CONF_ROOM_SWITCH,
    CONF_SUN_AZIMUTH_END,
    CONF_SUN_AZIMUTH_START,
    CONF_WINDOW_ENTITIES,
    DOMAIN,
)
from .controller import CoverControlAdvancedController


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    ctrl: CoverControlAdvancedController = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([CoverControlAdvancedStatusSensor(entry, ctrl)])


class CoverControlAdvancedStatusSensor(SensorEntity):
    _attr_icon = "mdi:roller-shade"
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry, ctrl: CoverControlAdvancedController) -> None:
        self._entry = entry
        self._ctrl = ctrl
        cover = entry.data[CONF_COVER]
        self._attr_unique_id = f"{DOMAIN}_{cover}_status"
        self._attr_name = f"Cover Control Advanced {cover}"

    @property
    def native_value(self) -> str:
        return self._ctrl.last_reason

    @property
    def extra_state_attributes(self) -> dict:
        cfg = self._entry.data
        return {
            "cover": cfg.get(CONF_COVER),
            "event_switch": cfg.get(CONF_EVENT_SWITCH),
            "room_switch": cfg.get(CONF_ROOM_SWITCH),
            "sun_azimuth_start": cfg.get(CONF_SUN_AZIMUTH_START),
            "sun_azimuth_end": cfg.get(CONF_SUN_AZIMUTH_END),
            "window_entities": cfg.get(CONF_WINDOW_ENTITIES),
        }
