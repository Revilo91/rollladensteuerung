"""Binary sensor mirrors for window/door contacts in Cover Control Advanced."""
from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from . import build_device_info, entity_friendly_name
from .const import CONF_COVER, CONF_COVERS, CONF_WINDOW_ENTITIES


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    device_info = build_device_info(hass, entry)
    covers = entry.data.get(CONF_COVERS, [])
    multi_cover = len(covers) > 1
    entities: list[BinarySensorEntity] = []
    for cover_cfg in covers:
        cover_id = cover_cfg[CONF_COVER]
        c_name = entity_friendly_name(hass, cover_id) if multi_cover else None
        for contact_id in cover_cfg.get(CONF_WINDOW_ENTITIES) or []:
            contact_name = entity_friendly_name(hass, contact_id)
            name = f"{c_name} {contact_name}" if c_name else contact_name
            dc = _detect_device_class(hass, contact_id)
            entities.append(
                CoverContactMirrorSensor(
                    entry_id=entry.entry_id,
                    cover_id=cover_id,
                    contact_id=contact_id,
                    name=name,
                    device_class=dc,
                    device_info=device_info,
                )
            )
    async_add_entities(entities)


def _detect_device_class(
    hass: HomeAssistant, entity_id: str
) -> BinarySensorDeviceClass:
    ent = er.async_get(hass).async_get(entity_id)
    if ent:
        dc = ent.device_class or ent.original_device_class
        if dc == "door":
            return BinarySensorDeviceClass.DOOR
    return BinarySensorDeviceClass.WINDOW


class CoverContactMirrorSensor(BinarySensorEntity):
    """Mirrors the open/closed state of a window or door contact sensor."""

    _attr_should_poll = False
    _attr_has_entity_name = True
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        entry_id: str,
        cover_id: str,
        contact_id: str,
        name: str,
        device_class: BinarySensorDeviceClass,
        device_info: DeviceInfo,
    ) -> None:
        self._contact_id = contact_id
        self._attr_unique_id = f"{entry_id}_{cover_id}_{contact_id}_contact"
        self._attr_name = name
        self._attr_device_class = device_class
        self._attr_device_info = device_info
        self._unsub = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        @callback
        def _on_state_change(event: Event) -> None:  # noqa: ARG001
            self.async_write_ha_state()

        self._unsub = async_track_state_change_event(
            self.hass, [self._contact_id], _on_state_change
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
        await super().async_will_remove_from_hass()

    @property
    def is_on(self) -> bool | None:
        state = self.hass.states.get(self._contact_id)
        if state is None:
            return None
        return state.state == "on"
