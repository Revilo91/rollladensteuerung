"""Switch entities for Cover Control Advanced."""

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from . import build_device_info, entity_friendly_name
from .const import CONF_EVENT_SWITCH


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    event_switch = entry.data.get(CONF_EVENT_SWITCH)
    if not event_switch:
        return

    device_info = build_device_info(hass, entry)
    async_add_entities(
        [
            CoverControlAdvancedEventSwitchProxy(
                hass=hass,
                entry_id=entry.entry_id,
                event_switch_entity_id=event_switch,
                device_info=device_info,
            )
        ]
    )


class CoverControlAdvancedEventSwitchProxy(SwitchEntity):
    """Proxy switch to control the configured event switch from this integration device."""

    _attr_icon = "mdi:light-switch"
    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        event_switch_entity_id: str,
        device_info: DeviceInfo,
    ) -> None:
        self._hass = hass
        self._event_switch_entity_id = event_switch_entity_id
        self._attr_unique_id = f"{entry_id}_event_switch_proxy"
        self._attr_name = entity_friendly_name(
            self._hass,
            self._event_switch_entity_id,
        )
        self._attr_device_info = device_info
        self._unsub = None

    def _refresh_name(self) -> None:
        """Refresh the proxy name once the source friendly name is available."""
        resolved_name = entity_friendly_name(self._hass, self._event_switch_entity_id)
        if resolved_name != self._attr_name:
            self._attr_name = resolved_name

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._refresh_name()

        @callback
        def _on_state_change(event: Event) -> None:  # noqa: ARG001
            self._refresh_name()
            self.async_write_ha_state()

        self._unsub = async_track_state_change_event(
            self.hass, [self._event_switch_entity_id], _on_state_change
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub is not None:
            self._unsub()
            self._unsub = None
        await super().async_will_remove_from_hass()

    @property
    def available(self) -> bool:
        return self.hass.states.get(self._event_switch_entity_id) is not None

    @property
    def is_on(self) -> bool | None:
        state = self.hass.states.get(self._event_switch_entity_id)
        if state is None:
            return None
        return state.state == STATE_ON

    async def async_turn_on(self, **kwargs) -> None:  # noqa: ARG002
        await self.hass.services.async_call(
            "switch",
            "turn_on",
            {"entity_id": self._event_switch_entity_id},
            blocking=False,
        )

    async def async_turn_off(self, **kwargs) -> None:  # noqa: ARG002
        await self.hass.services.async_call(
            "switch",
            "turn_off",
            {"entity_id": self._event_switch_entity_id},
            blocking=False,
        )
