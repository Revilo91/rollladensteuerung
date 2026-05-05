"""Diagnostic sensor – shows the last decision reason per cover."""
from collections.abc import Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_COVER,
    CONF_COVERS,
    CONF_EVENT_SWITCH,
    CONF_EVENT_SWITCH_POSITION,
    CONF_ROOM_NAME,
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
    async_add_entities(
        [
            CoverControlAdvancedStatusSensor(entry, ctrl, cover_cfg)
            for cover_cfg in entry.data.get(CONF_COVERS, [])
        ]
    )


class CoverControlAdvancedStatusSensor(SensorEntity):
    _attr_icon = "mdi:window-shutter-open"
    _attr_should_poll = False
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_translation_key = "status"
    _attr_options = [
        "initializing",
        "night_window_shading",
        "door_open",
        "room_closed",
        "room_inactive",
        "event_shading",
        "night_closed",
        "day_shading",
        "default_day",
        "default_night",
    ]

    def __init__(
        self,
        entry: ConfigEntry,
        ctrl: CoverControlAdvancedController,
        cover_cfg: dict,
    ) -> None:
        self._entry = entry
        self._ctrl = ctrl
        self._cover_cfg = cover_cfg
        self._unsubscribe_update: Callable[[], None] | None = None
        cover = cover_cfg[CONF_COVER]
        room_name = entry.data.get(CONF_ROOM_NAME, cover)
        self._attr_unique_id = f"{room_name}_{cover}_status"
        self._attr_name = f"Cover Control Advanced {room_name} {cover}"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._unsubscribe_update = self._ctrl.async_add_listener(self.async_write_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        if self._unsubscribe_update is not None:
            self._unsubscribe_update()
            self._unsubscribe_update = None
        await super().async_will_remove_from_hass()

    @property
    def native_value(self) -> str:
        cover = self._cover_cfg[CONF_COVER]
        return self._ctrl.last_reasons.get(cover, "initializing")

    @property
    def extra_state_attributes(self) -> dict:
        room_cfg = self._entry.data
        cover_cfg = self._cover_cfg
        return {
            "room_name": room_cfg.get(CONF_ROOM_NAME),
            "cover": cover_cfg.get(CONF_COVER),
            "event_switch": room_cfg.get(CONF_EVENT_SWITCH),
            "event_switch_position": room_cfg.get(CONF_EVENT_SWITCH_POSITION),
            "sun_azimuth_start": cover_cfg.get(CONF_SUN_AZIMUTH_START),
            "sun_azimuth_end": cover_cfg.get(CONF_SUN_AZIMUTH_END),
            "window_entities": cover_cfg.get(CONF_WINDOW_ENTITIES),
        }
