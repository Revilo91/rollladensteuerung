"""Diagnostic sensor – shows the last decision reason per cover."""
from collections.abc import Callable

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from . import build_device_info, entity_friendly_name
from .const import (
    CONF_COVER,
    CONF_COVERS,
    CONF_EVENT_SWITCH,
    CONF_EVENT_SWITCH_POSITION,
    CONF_ROOM_NAME,
    CONF_SHADING_HEIGHT,
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
    device_info = build_device_info(hass, entry)
    covers = entry.data.get(CONF_COVERS, [])
    multi_cover = len(covers) > 1
    entities: list[SensorEntity] = []
    for cover_cfg in covers:
        cover_id = cover_cfg[CONF_COVER]
        c_name = entity_friendly_name(hass, cover_id) if multi_cover else None
        entities.append(
            CoverControlAdvancedStatusSensor(entry, ctrl, cover_cfg, device_info, c_name)
        )
        entities.append(
            CoverControlAdvancedAzimuthStartSensor(entry, cover_cfg, device_info, c_name)
        )
        entities.append(
            CoverControlAdvancedAzimuthEndSensor(entry, cover_cfg, device_info, c_name)
        )
        entities.append(
            CoverControlAdvancedCoverStateSensor(entry, cover_cfg, device_info, c_name)
        )
        for contact_id in cover_cfg.get(CONF_WINDOW_ENTITIES) or []:
            contact_name = entity_friendly_name(hass, contact_id)
            entities.append(
                CoverControlAdvancedContactSensor(
                    entry, contact_id, device_info, contact_name
                )
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
        cover_name: str | None,
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
        if cover_name:
            self._attr_name = f"{cover_name} Status"

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
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        entry: ConfigEntry,
        cover_cfg: dict,
        device_info: DeviceInfo,
        cover_name: str | None,
    ) -> None:
        cover = cover_cfg[CONF_COVER]
        self._cover_cfg = cover_cfg
        self._attr_unique_id = f"{entry.entry_id}_{cover}_azimuth_start"
        self._attr_device_info = device_info
        if cover_name:
            self._attr_name = f"{cover_name} Azimut Start"

    @property
    def native_value(self) -> int:
        return int(self._cover_cfg.get(CONF_SUN_AZIMUTH_START, 0))


class CoverControlAdvancedAzimuthEndSensor(SensorEntity):
    _attr_icon = "mdi:angle-acute"
    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_translation_key = "azimuth_end"
    _attr_native_unit_of_measurement = "°"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        entry: ConfigEntry,
        cover_cfg: dict,
        device_info: DeviceInfo,
        cover_name: str | None,
    ) -> None:
        cover = cover_cfg[CONF_COVER]
        self._cover_cfg = cover_cfg
        self._attr_unique_id = f"{entry.entry_id}_{cover}_azimuth_end"
        self._attr_device_info = device_info
        if cover_name:
            self._attr_name = f"{cover_name} Azimut Ende"

    @property
    def native_value(self) -> int:
        return int(self._cover_cfg.get(CONF_SUN_AZIMUTH_END, 0))


class CoverControlAdvancedShadingHeightSensor(SensorEntity):
    _attr_icon = "mdi:window-shutter"
    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_translation_key = "shading_height"
    _attr_native_unit_of_measurement = "%"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

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
    _attr_entity_category = EntityCategory.DIAGNOSTIC

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


class CoverControlAdvancedCoverStateSensor(SensorEntity):
    """Diagnostic sensor showing the live position of the assigned cover entity."""

    _attr_icon = "mdi:window-shutter"
    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_translation_key = "cover_position"
    _attr_native_unit_of_measurement = "%"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        entry: ConfigEntry,
        cover_cfg: dict,
        device_info: DeviceInfo,
        cover_name: str | None,
    ) -> None:
        cover = cover_cfg[CONF_COVER]
        self._cover_id = cover
        self._unsubscribe: Callable[[], None] | None = None
        self._attr_unique_id = f"{entry.entry_id}_{cover}_cover_position"
        self._attr_device_info = device_info
        if cover_name:
            self._attr_name = f"{cover_name} Position"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._unsubscribe = async_track_state_change_event(
            self.hass, [self._cover_id], lambda _: self.async_write_ha_state()
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None
        await super().async_will_remove_from_hass()

    @property
    def native_value(self) -> int | None:
        state = self.hass.states.get(self._cover_id)
        if state is None:
            return None
        pos = state.attributes.get("current_position")
        try:
            return int(pos)
        except (TypeError, ValueError):
            return None

    @property
    def extra_state_attributes(self) -> dict:
        state = self.hass.states.get(self._cover_id)
        if state is None:
            return {}
        return {"state": state.state}


class CoverControlAdvancedContactSensor(SensorEntity):
    """Diagnostic sensor showing the live open/closed state of a contact sensor."""

    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_translation_key = "contact_state"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["open", "closed"]
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        entry: ConfigEntry,
        contact_entity_id: str,
        device_info: DeviceInfo,
        contact_name: str,
    ) -> None:
        self._contact_id = contact_entity_id
        self._unsubscribe: Callable[[], None] | None = None
        self._attr_unique_id = f"{entry.entry_id}_{contact_entity_id}_contact_state"
        self._attr_device_info = device_info
        self._attr_name = contact_name

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._unsubscribe = async_track_state_change_event(
            self.hass, [self._contact_id], lambda _: self.async_write_ha_state()
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsubscribe is not None:
            self._unsubscribe()
            self._unsubscribe = None
        await super().async_will_remove_from_hass()

    @property
    def icon(self) -> str:
        state = self.hass.states.get(self._contact_id)
        if state is None:
            return "mdi:help-circle-outline"
        device_class = state.attributes.get("device_class")
        is_open = state.state == STATE_ON
        if device_class == "window":
            return "mdi:window-open" if is_open else "mdi:window-closed"
        if device_class == "door":
            return "mdi:door-open" if is_open else "mdi:door"
        return "mdi:toggle-switch" if is_open else "mdi:toggle-switch-off"

    @property
    def native_value(self) -> str | None:
        state = self.hass.states.get(self._contact_id)
        if state is None:
            return None
        return "open" if state.state == STATE_ON else "closed"
