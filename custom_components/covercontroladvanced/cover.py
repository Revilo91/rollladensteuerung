"""Cover proxy entities for Cover Control Advanced."""

from homeassistant.components.cover import (
    ATTR_POSITION,
    DOMAIN as COVER_DOMAIN,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_SUPPORTED_FEATURES,
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING,
)
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from . import build_device_info, entity_friendly_name
from .const import CONF_COVER, CONF_COVERS


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    device_info = build_device_info(hass, entry)
    entities: list[CoverControlAdvancedCoverProxy] = []
    for cover_cfg in entry.data.get(CONF_COVERS, []):
        target_cover_id = cover_cfg.get(CONF_COVER)
        if target_cover_id:
            entities.append(
                CoverControlAdvancedCoverProxy(
                    hass=hass,
                    entry_id=entry.entry_id,
                    target_cover_id=target_cover_id,
                    device_info=device_info,
                )
            )

    async_add_entities(entities)


class CoverControlAdvancedCoverProxy(CoverEntity):
    """Proxy cover to expose configured covers on the integration device."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        target_cover_id: str,
        device_info: DeviceInfo,
    ) -> None:
        self._hass = hass
        self._target_cover_id = target_cover_id
        self._attr_unique_id = f"{entry_id}_{target_cover_id}_proxy"
        self._attr_name = entity_friendly_name(hass, target_cover_id)
        self._attr_device_info = device_info
        self._unsub = None

    def _refresh_name(self) -> None:
        """Refresh the proxy name once the source friendly name is available."""
        resolved_name = entity_friendly_name(self._hass, self._target_cover_id)
        if resolved_name != self._attr_name:
            self._attr_name = resolved_name

    @property
    def available(self) -> bool:
        return self._hass.states.get(self._target_cover_id) is not None

    @property
    def supported_features(self) -> CoverEntityFeature:
        state = self._hass.states.get(self._target_cover_id)
        if state is None:
            return CoverEntityFeature(0)

        try:
            return CoverEntityFeature(int(state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)))
        except (TypeError, ValueError):
            return CoverEntityFeature(0)

    @property
    def current_cover_position(self) -> int | None:
        state = self._hass.states.get(self._target_cover_id)
        if state is None:
            return None

        value = state.attributes.get("current_position")
        try:
            return int(float(value)) if value is not None else None
        except (TypeError, ValueError):
            return None

    @property
    def is_closed(self) -> bool | None:
        state = self._hass.states.get(self._target_cover_id)
        if state is None:
            return None
        if state.state == STATE_CLOSED:
            return True
        if state.state in (STATE_OPEN, STATE_OPENING, STATE_CLOSING):
            return False

        position = self.current_cover_position
        return position == 0 if position is not None else None

    @property
    def is_opening(self) -> bool:
        state = self._hass.states.get(self._target_cover_id)
        return bool(state and state.state == STATE_OPENING)

    @property
    def is_closing(self) -> bool:
        state = self._hass.states.get(self._target_cover_id)
        return bool(state and state.state == STATE_CLOSING)

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        return {"source_entity_id": self._target_cover_id}

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self._refresh_name()

        @callback
        def _on_state_change(event: Event) -> None:  # noqa: ARG001
            self._refresh_name()
            self.async_write_ha_state()

        self._unsub = async_track_state_change_event(
            self._hass,
            [self._target_cover_id],
            _on_state_change,
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub is not None:
            self._unsub()
            self._unsub = None
        await super().async_will_remove_from_hass()

    async def async_open_cover(self, **kwargs) -> None:  # noqa: ARG002
        await self._hass.services.async_call(
            COVER_DOMAIN,
            "open_cover",
            {"entity_id": self._target_cover_id},
            blocking=False,
        )

    async def async_close_cover(self, **kwargs) -> None:  # noqa: ARG002
        await self._hass.services.async_call(
            COVER_DOMAIN,
            "close_cover",
            {"entity_id": self._target_cover_id},
            blocking=False,
        )

    async def async_stop_cover(self, **kwargs) -> None:  # noqa: ARG002
        await self._hass.services.async_call(
            COVER_DOMAIN,
            "stop_cover",
            {"entity_id": self._target_cover_id},
            blocking=False,
        )

    async def async_set_cover_position(self, **kwargs) -> None:
        position = kwargs.get(ATTR_POSITION)
        if position is None:
            return

        await self._hass.services.async_call(
            COVER_DOMAIN,
            "set_cover_position",
            {"entity_id": self._target_cover_id, "position": position},
            blocking=False,
        )
