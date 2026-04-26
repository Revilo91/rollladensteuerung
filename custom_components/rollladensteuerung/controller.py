import logging
from collections.abc import Callable

from homeassistant.components.cover import DOMAIN as COVER_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event

from .const import (
    CONF_CINEMA_SWITCH,
    CONF_COVER,
    CONF_DAY_NIGHT_MODE,
    CONF_DAY_POSITION,
    CONF_DIRECTION,
    CONF_ENABLE_CINEMA_MODE,
    CONF_ENABLE_MORNING_MODE,
    CONF_MORNING_OPEN_SWITCH,
    CONF_NIGHT_POSITION,
    CONF_PC_SWITCH,
    CONF_ROOM_SWITCH,
    CONF_SHADING_HYSTERESIS,
    CONF_SLEEP_POSITION,
    CONF_WINDOW_ENTITIES,
    SHADING_OFF_DELAY,
)

_LOGGER = logging.getLogger(__name__)


class RollladenController:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._cfg = entry.data
        self._unsubs: list[Callable] = []
        self._shading_off_unsub: Callable | None = None
        self.last_reason: str = "Initializing"

    # ------------------------------------------------------------------ setup

    async def async_setup(self) -> None:
        watch = self._watched_entities()
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
            "RollladenController for %s started, watching: %s",
            self._cfg[CONF_COVER],
            watch,
        )

    async def async_unload(self) -> None:
        for unsub in self._unsubs:
            unsub()
        if self._shading_off_unsub:
            self._shading_off_unsub()

    # --------------------------------------------------------------- helpers

    def _watched_entities(self) -> list[str]:
        cfg = self._cfg
        entities: list[str] = []

        entities.extend(cfg.get(CONF_WINDOW_ENTITIES) or [])

        if d := cfg.get(CONF_DIRECTION, ""):
            entities += [
                f"binary_sensor.richtung{d}",
                f"binary_sensor.richtung{d}pc",
            ]

        entities += [
            cfg[CONF_SHADING_HYSTERESIS],
            cfg[CONF_DAY_NIGHT_MODE],
            cfg[CONF_ROOM_SWITCH],
            cfg[CONF_NIGHT_POSITION],
            cfg[CONF_DAY_POSITION],
        ]

        for key in (CONF_PC_SWITCH, CONF_CINEMA_SWITCH, CONF_MORNING_OPEN_SWITCH, CONF_SLEEP_POSITION):
            if v := cfg.get(key):
                entities.append(v)

        return [e for e in entities if e]

    def _state(self, entity_id: str | None) -> str | None:
        if not entity_id:
            return None
        s = self.hass.states.get(entity_id)
        return s.state if s else None

    def _is_on(self, entity_id: str | None) -> bool:
        return self._state(entity_id) == STATE_ON

    def _numeric(self, entity_id: str | None) -> int:
        try:
            return int(float(self._state(entity_id) or 0))
        except (ValueError, TypeError):
            return 0

    # -------------------------------------------------- computed properties

    @property
    def _is_day(self) -> bool:
        return self._is_on(self._cfg[CONF_DAY_NIGHT_MODE])

    @property
    def _is_window(self) -> bool:
        """True if at least one sensor has device_class=window."""
        for eid in self._cfg.get(CONF_WINDOW_ENTITIES) or []:
            s = self.hass.states.get(eid)
            if s and s.attributes.get("device_class") == "window":
                return True
        return False

    @property
    def _is_window_open(self) -> bool:
        return any(
            self._state(eid) == STATE_ON
            for eid in (self._cfg.get(CONF_WINDOW_ENTITIES) or [])
        )

    @property
    def _rs(self) -> str:
        """Current state of the room input_select."""
        return self._state(self._cfg[CONF_ROOM_SWITCH]) or ""

    @property
    def _shading_active(self) -> bool:
        rs = self._rs.lower()
        return "inaktiv" not in rs and "inactive" not in rs

    @property
    def _shading_forced(self) -> bool:
        rs = self._rs.lower()
        return "pc" not in rs and ("erzwungen" in rs or "forced" in rs)

    @property
    def _shading_automatic(self) -> bool:
        rs = self._rs.lower()
        return "pc" not in rs and ("automatik" in rs or "automatic" in rs)

    @property
    def _shading_manual(self) -> bool:
        rs = self._rs.lower()
        return "manuell" in rs or "manual" in rs

    @property
    def _pc_forced(self) -> bool:
        rs = self._rs.lower()
        return "pc" in rs and ("erzwungen" in rs or "forced" in rs)

    @property
    def _pc_automatic(self) -> bool:
        rs = self._rs.lower()
        return "pc" in rs and ("automatik" in rs or "automatic" in rs)

    @property
    def _is_direction(self) -> bool:
        d = self._cfg.get(CONF_DIRECTION, "")
        return bool(d) and self._is_on(f"binary_sensor.richtung{d}")

    @property
    def _is_pc_direction(self) -> bool:
        d = self._cfg.get(CONF_DIRECTION, "")
        return bool(d) and self._is_on(f"binary_sensor.richtung{d}pc")

    @property
    def _pc_on(self) -> bool:
        return self._is_on(self._cfg.get(CONF_PC_SWITCH))

    @property
    def _hysteresis(self) -> bool:
        return self._is_on(self._cfg[CONF_SHADING_HYSTERESIS])

    # ----------------------------------------------------------- main logic

    async def _evaluate(self) -> None:
        cover = self._cfg[CONF_COVER]

        # 1. Night + window open → night position
        if not self._is_day and self._is_window and self._is_window_open:
            self.last_reason = "Night + window open → night position"
            await self._set_pos(cover, self._numeric(self._cfg[CONF_NIGHT_POSITION]))
            return

        # 2. Door open (no window sensor) → open
        if not self._is_window and self._is_window_open:
            self.last_reason = "Door open → open"
            await self._open(cover)
            return

        # 3. Night + morning label + morning switch + shading active
        if (
            not self._is_day
            and self._cfg.get(CONF_ENABLE_MORNING_MODE)
            and self._is_on(self._cfg.get(CONF_MORNING_OPEN_SWITCH))
            and self._shading_active
        ):
            self.last_reason = "Morning mode (night) → night position"
            await self._set_pos(cover, self._numeric(self._cfg[CONF_NIGHT_POSITION]))
            return

        # 4. Night + closed → close
        if not self._is_window_open and not self._is_day:
            self.last_reason = "Night + closed → close"
            await self._close(cover)
            return

        # 5. Cinema mode
        if self._is_on(self._cfg.get(CONF_CINEMA_SWITCH)) and self._cfg.get(CONF_ENABLE_CINEMA_MODE):
            self.last_reason = "Cinema mode → close"
            await self._close(cover)
            return

        # 6. Day + sleep mode
        if self._is_day and ("schlafen" in self._rs.lower() or "sleep" in self._rs.lower()):
            if sleep_position := self._cfg.get(CONF_SLEEP_POSITION):
                self.last_reason = "Sleep position"
                await self._set_pos(cover, self._numeric(sleep_position))
                return

        # 7. Room forced closed
        if "zu" in self._rs.lower() or "closed" in self._rs.lower():
            self.last_reason = "Room: closed → close"
            await self._close(cover)
            return

        # 8. Day + shading active + direction/PC logic
        window_or_closed_door = self._is_window or (not self._is_window and not self._is_window_open)

        shading = (
            (
                self._hysteresis
                and (
                    (self._is_direction and self._shading_automatic)
                    or (self._pc_on and self._is_pc_direction and self._pc_automatic)
                )
            )
            or (self._is_direction and self._shading_forced)
            or (self._pc_on and self._is_pc_direction and self._pc_forced)
            or self._shading_manual
        )

        if self._shading_active and self._is_day and window_or_closed_door and shading:
            self.last_reason = "Day shading active → day position"
            await self._set_pos(cover, self._numeric(self._cfg[CONF_DAY_POSITION]))
            return

        # 9. Default fallback
        if self._is_day:
            self.last_reason = "Default: day → open"
            await self._open(cover)
        else:
            self.last_reason = "Default: night → close"
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
