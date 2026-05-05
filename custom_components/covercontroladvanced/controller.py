import logging
from collections.abc import Callable
from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.components.cover import DOMAIN as COVER_DOMAIN, CoverEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_SUPPORTED_FEATURES, STATE_ON
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_time_interval,
)

from .const import (
    CONF_COVER,
    CONF_COVERS,
    CONF_DAY_NIGHT_MODE,
    CONF_EVENT_SWITCH,
    CONF_EVENT_SWITCH_POSITION,
    CONF_SHADING_HEIGHT,
    CONF_SHADING_HYSTERESIS,
    CONF_SUN_AZIMUTH_END,
    CONF_SUN_AZIMUTH_START,
    CONF_WINDOW_ENTITIES,
    ROOM_MODE_ACTIVE,
    ROOM_MODE_ALWAYS_ACTIVE,
    ROOM_MODE_AUTOMATIC,
    ROOM_MODE_CLOSED,
    ROOM_MODE_INACTIVE,
    SHADING_OFF_DELAY,
)

if TYPE_CHECKING:
    from .select import CoverControlAdvancedRoomModeSelect

_LOGGER = logging.getLogger(__name__)


class CoverControlAdvancedController:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._cfg = entry.data
        self._unsubs: list[Callable] = []
        self._listeners: list[Callable[[], None]] = []
        self._shading_off_unsub: Callable | None = None
        self.last_reasons: dict[str, str] = {
            cover_cfg[CONF_COVER]: "initializing"
            for cover_cfg in entry.data.get(CONF_COVERS, [])
        }
        self.room_mode_select: CoverControlAdvancedRoomModeSelect | None = None

    # ------------------------------------------------------------------ setup

    async def async_setup(self) -> None:
        watch = self._watched_entities
        shading_hysteresis_id = self._cfg[CONF_SHADING_HYSTERESIS]

        @callback
        def _on_state_change(event: Event) -> None:
            entity_id = event.data.get("entity_id")
            new_state = event.data.get("new_state")
            old_state = event.data.get("old_state")

            if entity_id == shading_hysteresis_id:
                old = old_state.state if old_state else None
                new = new_state.state if new_state else None

                if old == STATE_ON and new != STATE_ON:
                    # on→off: delayed evaluation (4 min off-delay)
                    if self._shading_off_unsub:
                        self._shading_off_unsub()
                    self._shading_off_unsub = async_call_later(
                        self.hass,
                        SHADING_OFF_DELAY,
                        lambda _: self.hass.async_create_task(self._evaluate()),
                    )
                    return
                if new == STATE_ON and old != STATE_ON:
                    # off→on: immediate evaluation, cancel pending task
                    if self._shading_off_unsub:
                        self._shading_off_unsub()
                        self._shading_off_unsub = None

            self.hass.async_create_task(self._evaluate())

        self._unsubs.append(
            async_track_state_change_event(self.hass, watch, _on_state_change)
        )
        self._unsubs.append(
            async_track_time_interval(
                self.hass,
                lambda _: self.hass.async_create_task(self._evaluate()),
                timedelta(minutes=1),
            )
        )
        _LOGGER.debug(
            "CoverControlAdvancedController for room '%s' started, watching: %s",
            self._cfg.get("room_name", ""),
            watch,
        )

    async def async_unload(self) -> None:
        for unsub in self._unsubs:
            unsub()
        if self._shading_off_unsub:
            self._shading_off_unsub()

    async def async_trigger_evaluation(self) -> None:
        """Public entry point to trigger a cover re-evaluation (e.g. from the select entity)."""
        await self._evaluate()

    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Register a listener that is notified after each evaluation run."""
        self._listeners.append(listener)

        def _remove_listener() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return _remove_listener

    @callback
    def _notify_listeners(self) -> None:
        for listener in list(self._listeners):
            listener()

    # --------------------------------------------------------------- helpers

    @property
    def _watched_entities(self) -> list[str]:
        cfg = self._cfg
        entities: list[str] = [
            "sun.sun",
            "sensor.sun_solar_azimuth",
            cfg[CONF_SHADING_HYSTERESIS],
            cfg[CONF_DAY_NIGHT_MODE],
        ]
        if v := cfg.get(CONF_EVENT_SWITCH):
            entities.append(v)
        for cover_cfg in cfg.get(CONF_COVERS, []):
            entities.extend(cover_cfg.get(CONF_WINDOW_ENTITIES) or [])
        return [e for e in entities if e]

    def _state(self, entity_id: str | None) -> str | None:
        if not entity_id:
            return None
        s = self.hass.states.get(entity_id)
        return s.state if s else None

    def _is_on(self, entity_id: str | None) -> bool:
        return self._state(entity_id) == STATE_ON

    def _supports_feature(
        self, entity_id: str, feature: CoverEntityFeature
    ) -> bool:
        state = self.hass.states.get(entity_id)
        if state is None:
            return False

        try:
            supported = CoverEntityFeature(
                int(state.attributes.get(ATTR_SUPPORTED_FEATURES, 0))
            )
        except (TypeError, ValueError):
            return False

        return bool(supported & feature)

    # -------------------------------------------------- room-level properties

    @property
    def is_day(self) -> bool:
        return self._is_on(self._cfg[CONF_DAY_NIGHT_MODE])

    @property
    def room_mode(self) -> str:
        """Current room mode from the internal select entity."""
        if self.room_mode_select is not None:
            return self.room_mode_select.current_option or ROOM_MODE_AUTOMATIC
        return ROOM_MODE_AUTOMATIC

    @property
    def event_on(self) -> bool:
        return self._is_on(self._cfg.get(CONF_EVENT_SWITCH))

    @property
    def shading_height(self) -> int:
        try:
            return int(float(self._cfg.get(CONF_SHADING_HEIGHT, 20)))
        except (TypeError, ValueError):
            return 20

    @property
    def event_switch_position(self) -> int:
        try:
            return int(float(self._cfg.get(CONF_EVENT_SWITCH_POSITION, 0)))
        except (TypeError, ValueError):
            return 0

    @property
    def hysteresis(self) -> bool:
        return self._is_on(self._cfg[CONF_SHADING_HYSTERESIS])

    # -------------------------------------------------- cover-level helpers

    def _cover_has_window(self, cover_cfg: dict) -> bool:
        """True if at least one contact sensor has device_class=window."""
        for eid in cover_cfg.get(CONF_WINDOW_ENTITIES) or []:
            s = self.hass.states.get(eid)
            if s and s.attributes.get("device_class") == "window":
                return True
        return False

    def _cover_window_open(self, cover_cfg: dict) -> bool:
        """True if any contact sensor reports open (state=on)."""
        return any(
            self._state(eid) == STATE_ON
            for eid in (cover_cfg.get(CONF_WINDOW_ENTITIES) or [])
        )

    def _cover_sun_on_window(self, cover_cfg: dict) -> bool:
        """True if the sun azimuth is within the range configured for this cover."""
        sun = self.hass.states.get("sun.sun")
        if not sun:
            return False

        try:
            azimuth = float(sun.attributes.get("azimuth")) % 360
        except (TypeError, ValueError):
            return False

        try:
            start = float(cover_cfg.get(CONF_SUN_AZIMUTH_START, 135)) % 360
            end = float(cover_cfg.get(CONF_SUN_AZIMUTH_END, 225)) % 360
        except (TypeError, ValueError):
            return False

        if start <= end:
            return start <= azimuth <= end
        return azimuth >= start or azimuth <= end

    # ----------------------------------------------------------- main logic

    async def _evaluate(self) -> None:
        room_mode = self.room_mode
        for cover_cfg in self._cfg.get(CONF_COVERS, []):
            await self._evaluate_cover(cover_cfg, room_mode)
        self._notify_listeners()

    async def _evaluate_cover(self, cover_cfg: dict, room_mode: str) -> None:
        cover = cover_cfg[CONF_COVER]
        is_window = self._cover_has_window(cover_cfg)
        is_window_open = self._cover_window_open(cover_cfg)
        is_sun_on_window = self._cover_sun_on_window(cover_cfg)

        # 1. Night + window open → night position
        if not self.is_day and is_window and is_window_open:
            self.last_reasons[cover] = "night_window_shading"
            await self._set_pos(cover, self.shading_height)
            return

        # 2. Door open (no window sensor) → open
        if not is_window and is_window_open:
            self.last_reasons[cover] = "door_open"
            await self._open(cover)
            return

        # 3. Room: closed → close completely
        if room_mode == ROOM_MODE_CLOSED:
            self.last_reasons[cover] = "room_closed"
            await self._close(cover)
            return

        # 4. Room: shading inactive → open
        if room_mode == ROOM_MODE_INACTIVE:
            self.last_reasons[cover] = "room_inactive"
            await self._open(cover)
            return

        # 5. Event switch active → configured position (day and night)
        if self.event_on:
            self.last_reasons[cover] = "event_shading"
            await self._set_pos(cover, self.event_switch_position)
            return

        # 6. Night + closed → close
        if not is_window_open and not self.is_day:
            self.last_reasons[cover] = "night_closed"
            await self._close(cover)
            return

        # 7. Day shading logic
        window_or_closed_door = is_window or not is_window_open

        shading = (
            (room_mode == ROOM_MODE_AUTOMATIC and self.hysteresis and is_sun_on_window)
            or (room_mode == ROOM_MODE_ALWAYS_ACTIVE and is_sun_on_window)
            or (room_mode == ROOM_MODE_ACTIVE)
        )

        if self.is_day and window_or_closed_door and shading:
            self.last_reasons[cover] = "day_shading"
            await self._set_pos(cover, self.shading_height)
            return

        # 8. Default fallback
        if self.is_day:
            self.last_reasons[cover] = "default_day"
            await self._open(cover)
        else:
            self.last_reasons[cover] = "default_night"
            await self._close(cover)

    # ---------------------------------------------------------- cover calls

    async def _set_pos(self, entity_id: str, position: int) -> None:
        if not self._supports_feature(entity_id, CoverEntityFeature.SET_POSITION):
            fallback_action = self._close if position < 50 else self._open
            _LOGGER.debug(
                "%s does not support set_position(%d), falling back to %s [%s]",
                entity_id,
                position,
                fallback_action.__name__,
                self.last_reasons.get(entity_id, ""),
            )
            await fallback_action(entity_id)
            return

        _LOGGER.debug(
            "%s → set_position(%d) [%s]",
            entity_id,
            position,
            self.last_reasons.get(entity_id, ""),
        )
        await self.hass.services.async_call(
            COVER_DOMAIN,
            "set_cover_position",
            {"entity_id": entity_id, "position": position},
            blocking=False,
        )

    async def _open(self, entity_id: str) -> None:
        _LOGGER.debug(
            "%s → open_cover [%s]", entity_id, self.last_reasons.get(entity_id, "")
        )
        await self.hass.services.async_call(
            COVER_DOMAIN,
            "open_cover",
            {"entity_id": entity_id},
            blocking=False,
        )

    async def _close(self, entity_id: str) -> None:
        _LOGGER.debug(
            "%s → close_cover [%s]", entity_id, self.last_reasons.get(entity_id, "")
        )
        await self.hass.services.async_call(
            COVER_DOMAIN,
            "close_cover",
            {"entity_id": entity_id},
            blocking=False,
        )
