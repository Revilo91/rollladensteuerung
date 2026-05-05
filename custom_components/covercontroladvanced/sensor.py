"""Diagnostic sensor – shows the last decision reason per cover."""
from collections.abc import Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import build_device_info
from .const import (
    CONF_COVER,
    CONF_COVERS,
    CONF_EVENT_SWITCH,
    CONF_EVENT_SWITCH_POSITION,
    CONF_ROOM_NAME,
    CONF_SHADING_HEIGHT,
    CONF_SUN_AZIMUTH_END,
    CONF_SUN_AZIMUTH_START,
    DOMAIN,
)
from .controller import CoverControlAdvancedController


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    ctrl: CoverControlAdvancedController = hass.data[DOMAIN][entry.entry_id]
    device_info = build_device_info(hass, entry)
    entities: list[SensorEntity] = []
    for cover_cfg in entry.data.get(CONF_COVERS, []):
        entities.append(
            CoverControlAdvancedStatusSensor(entry, ctrl, cover_cfg, device_info)
        )
        entities.append(
            CoverControlAdvancedAzimuthStartSensor(entry, cover_cfg, device_info)
        )
        entities.append(
            CoverControlAdvancedAzimuthEndSensor(entry, cover_cfg, device_info)
        )
    entities.append(CoverControlAdvancedShadingHeightSensor(entry, device_info))
    if entry.data.get(CONF_EVENT_SWITCH):
        entities.append(
            CoverControlAdvancedEventSwitchPositionSensor(entry, device_info)
        )
    async_add_entities(entities)


class CoverControlAdvancedStatusSensor(SensorEntity):
    _attr_icon = "mdi:window-shutter-open"
    _attr_should_poll = False
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_has_entity_name = True
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
        device_info: DeviceInfo,
    ) -> None:
        self._entry = entry
        self._ctrl = ctrl
        self._cover_cfg = cover_cfg
        self._unsubscribe_update: Callable[[], None] | None = None
        cover = cover_cfg[CONF_COVER]
        room_name = entry.data.get(CONF_ROOM_NAME, cover)
        # Keep legacy unique_id to avoid breaking existing installations
        self._attr_unique_id = f"{room_name}_{cover}_status"
        self._attr_device_info = device_info

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._unsubscribe_update = self._ctrl.async_add_listener(
            self.async_write_ha_state
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsubscribe_update is not None:
            self._unsubscribe_update()
            self._unsubscribe_update = None
        await super().async_will_remove_from_hass()

    @property
    def native_value(self) -> str:
        cover = self._cover_cfg[CONF_COVER]
        return self._ctrl.last_reasons.get(cover, "initializing")


class CoverControlAdvancedAzimuthStartSensor(SensorEntity):
    _attr_icon = "mdi:angle-acute"
    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_translation_key = "azimuth_start"
    _attr_native_unit_of_measurement = "°"

    def __init__(
        self,
        entry: ConfigEntry,
        cover_cfg: dict,
        device_info: DeviceInfo,
    ) -> None:
        cover = cover_cfg[CONF_COVER]
        self._cover_cfg = cover_cfg
        self._attr_unique_id = f"{entry.entry_id}_{cover}_azimuth_start"
        self._attr_device_info = device_info

    @property
    def native_value(self) -> int:
        return int(self._cover_cfg.get(CONF_SUN_AZIMUTH_START, 0))


class CoverControlAdvancedAzimuthEndSensor(SensorEntity):
    _attr_icon = "mdi:angle-acute"
    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_translation_key = "azimuth_end"
    _attr_native_unit_of_measurement = "°"

    def __init__(
        self,
        entry: ConfigEntry,
        cover_cfg: dict,
        device_info: DeviceInfo,
    ) -> None:
        cover = cover_cfg[CONF_COVER]
        self._cover_cfg = cover_cfg
        self._attr_unique_id = f"{entry.entry_id}_{cover}_azimuth_end"
        self._attr_device_info = device_info

    @property
    def native_value(self) -> int:
        return int(self._cover_cfg.get(CONF_SUN_AZIMUTH_END, 0))


class CoverControlAdvancedShadingHeightSensor(SensorEntity):
    _attr_icon = "mdi:window-shutter"
    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_translation_key = "shading_height"
    _attr_native_unit_of_measurement = "%"

    def __init__(self, entry: ConfigEntry, device_info: DeviceInfo) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_shading_height"
        self._attr_device_info = device_info

    @property
    def native_value(self) -> int:
        try:
            return int(float(self._entry.data.get(CONF_SHADING_HEIGHT, 20)))
        except (TypeError, ValueError):
            return 20


class CoverControlAdvancedEventSwitchPositionSensor(SensorEntity):
    _attr_icon = "mdi:calendar-arrow-right"
    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_translation_key = "event_switch_position"
    _attr_native_unit_of_measurement = "%"

    def __init__(self, entry: ConfigEntry, device_info: DeviceInfo) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_event_switch_position"
        self._attr_device_info = device_info

    @property
    def native_value(self) -> int:
        try:
            return int(float(self._entry.data.get(CONF_EVENT_SWITCH_POSITION, 0)))
        except (TypeError, ValueError):
            return 0
