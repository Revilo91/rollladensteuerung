"""Diagnostik-Sensor – zeigt den letzten Entscheidungsgrund."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_COVER, DOMAIN
from .controller import RollladenController


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    ctrl: RollladenController = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RollladenStatusSensor(entry, ctrl)])


class RollladenStatusSensor(SensorEntity):
    _attr_icon = "mdi:roller-shade"
    _attr_should_poll = False

    def __init__(self, entry: ConfigEntry, ctrl: RollladenController) -> None:
        self._entry = entry
        self._ctrl = ctrl
        cover = entry.data[CONF_COVER]
        self._attr_unique_id = f"{DOMAIN}_{cover}_status"
        self._attr_name = f"Rollladensteuerung {cover}"

    @property
    def native_value(self) -> str:
        return self._ctrl.last_reason

    @property
    def extra_state_attributes(self) -> dict:
        cfg = self._entry.data
        return {
            "cover": cfg.get("cover_entity"),
            "room_switch": cfg.get("room_switch"),
            "direction": cfg.get("direction"),
            "window_entities": cfg.get("window_entities"),
        }
