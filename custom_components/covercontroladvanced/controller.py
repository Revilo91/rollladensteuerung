import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

from homeassistant.components.cover import DOMAIN as COVER_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event

from .const import (
    CONF_COVER,
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
    ROOM_MODE_SLEEP,
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
        self._shading_off_unsub: Callable | None = None
        self.last_reason: str = "initializing"
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
        _LOGGER.debug(
            "CoverControlAdvancedController for %s started, watching: %s",
            self._cfg[CONF_COVER],
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

    # --------------------------------------------------------------- helpers

    @property
    def _watched_entities(self) -> list[str]:
        cfg = self._cfg
        entities: list[str] = [
            *(cfg.get(CONF_WINDOW_ENTITIES) or []),
            "sun.sun",
            cfg[CONF_SHADING_HYSTERESIS],
            cfg[CONF_DAY_NIGHT_MODE],
        ]
        if v := cfg.get(CONF_EVENT_SWITCH):
            entities.append(v)
        return [e for e in entities if e]

    def _state(self, entity_id: str | None) -> str | None:
        if not entity_id:
            return None
        s = self.hass.states.get(entity_id)
        return s.state if s else None

    def _is_on(self, entity_id: str | None) -> bool:
        return self._state(entity_id) == STATE_ON

    # -------------------------------------------------- computed properties

    @property
    def _sun_azimuth_start(self) -> float:
        try:
            return float(self._cfg.get(CONF_SUN_AZIMUTH_START, 135)) % 360
        except (TypeError, ValueError):
            return 135.0

    @property
    def _sun_azimuth_end(self) -> float:
        try:
            return float(self._cfg.get(CONF_SUN_AZIMUTH_END, 225)) % 360
        except (TypeError, ValueError):
            return 225.0

    @property
    def is_day(self) -> bool:
        return self._is_on(self._cfg[CONF_DAY_NIGHT_MODE])

    @property
    def is_window(self) -> bool:
        """True if at least one sensor has device_class=window."""
        for eid in self._cfg.get(CONF_WINDOW_ENTITIES) or []:
            s = self.hass.states.get(eid)
            if s and s.attributes.get("device_class") == "window":
                return True
        return False

    @property
    def is_window_open(self) -> bool:
        return any(
            self._state(eid) == STATE_ON
            for eid in (self._cfg.get(CONF_WINDOW_ENTITIES) or [])
        )

    @property
    def room_mode(self) -> str:
        """Current room mode from the internal select entity."""
        if self.room_mode_select is not None:
            return self.room_mode_select.current_option or ROOM_MODE_AUTOMATIC
        return ROOM_MODE_AUTOMATIC

    @property
    def is_sun_on_window(self) -> bool:
        sun = self.hass.states.get("sun.sun")
        if not sun:
            return False

        try:
            azimuth = float(sun.attributes.get("azimuth")) % 360
        except (TypeError, ValueError):
            return False

        start = self._sun_azimuth_start
        end = self._sun_azimuth_end

        if start <= end:
            return start <= azimuth <= end
        return azimuth >= start or azimuth <= end

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

    # ----------------------------------------------------------- main logic

    async def _evaluate(self) -> None:
        cover = self._cfg[CONF_COVER]
        room_mode = self.room_mode

        # 1. Night + window open → night position
        if not self.is_day and self.is_window and self.is_window_open:
            self.last_reason = "night_window_shading"
            await self._set_pos(cover, self.shading_height)
            return

        # 2. Door open (no window sensor) → open
        if not self.is_window and self.is_window_open:
            self.last_reason = "door_open"
            await self._open(cover)
            return

        # 3. Night + event switch active → shading height
        if not self.is_day and self.event_on:
            self.last_reason = "night_event_shading"
            await self._set_pos(cover, self.shading_height)
            return

        # 4. Night + closed → close
        if not self.is_day and not self.is_window_open:
            self.last_reason = "night_closed"
            await self._close(cover)
            return

        # 5. Cinema event switch active → close
        if self.event_on:
            self.last_reason = "cinema_event_close"
            await self._close(cover)
            return

        # 6. Day + sleep mode → shading height
        if self.is_day and room_mode == ROOM_MODE_SLEEP:
            self.last_reason = "sleep_shading"
            await self._set_pos(cover, self.shading_height)
            return

        # 7. Room: closed → close completely
        if room_mode == ROOM_MODE_CLOSED:
            self.last_reason = "room_closed"
            await self._close(cover)
            return

        # 8. Day shading logic
        window_or_closed_door = self.is_window or not self.is_window_open

        shading = (
            (room_mode == ROOM_MODE_AUTOMATIC and self.hysteresis and self.is_sun_on_window)
            or (room_mode == ROOM_MODE_ALWAYS_ACTIVE and self.is_sun_on_window)
            or (room_mode == ROOM_MODE_ACTIVE)
        )

        if self.is_day and window_or_closed_door and shading:
            self.last_reason = "day_shading"
            await self._set_pos(cover, self.shading_height)
            return

        # 9. Default fallback
        if self.is_day:
            self.last_reason = "default_day"
            await self._open(cover)
        else:
            self.last_reason = "default_night"
            await self._close(cover)

    # ---------------------------------------------------------- cover calls

    async def _set_pos(self, entity_id: str, position: int) -> None:
        _LOGGER.debug("%s → set_position(%d) [%s]", entity_id, position, self.last_reason)
        await self.hass.services.async_call(
            COVER_DOMAIN,
            "set_cover_position",
            {"entity_id": entity_id, "position": position},
            blocking=False,
        )

    async def _open(self, entity_id: str) -> None:
        _LOGGER.debug("%s → open_cover [%s]", entity_id, self.last_reason)
        await self.hass.services.async_call(
            COVER_DOMAIN,
            "open_cover",
            {"entity_id": entity_id},
            blocking=False,
        )

    async def _close(self, entity_id: str) -> None:
        _LOGGER.debug("%s → close_cover [%s]", entity_id, self.last_reason)
        await self.hass.services.async_call(
            COVER_DOMAIN,
            "close_cover",
            {"entity_id": entity_id},
            blocking=False,
        )
