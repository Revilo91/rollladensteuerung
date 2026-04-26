import logging
from typing import Callable, Optional

from homeassistant.components.cover import DOMAIN as COVER_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_ON
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_call_later, async_track_state_change_event

from .const import (
    BESCHATTUNG_OFF_DELAY,
    CONF_BESCHATTUNG_HYSTERESE,
    CONF_COVER,
    CONF_DIRECTION,
    CONF_HOEHE_NACHT,
    CONF_HOEHE_SCHLAFEN,
    CONF_HOEHE_TAG,
    CONF_IS_FILMEABEND_LABEL,
    CONF_IS_MORGENS_LABEL,
    CONF_KINO_SWITCH,
    CONF_MORGENS_AUF_SWITCH,
    CONF_PC_SWITCH,
    CONF_ROOM_SWITCH,
    CONF_TAG_NACHT_MODUS,
    CONF_WINDOW_ENTITIES,
)

_LOGGER = logging.getLogger(__name__)


class RollladenController:
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self._cfg = entry.data
        self._unsubs: list[Callable] = []
        self._beschattung_off_unsub: Optional[Callable] = None
        self.last_reason: str = "Initialisierung"

    # ------------------------------------------------------------------ setup

    async def async_setup(self) -> None:
        watch = self._watched_entities()
        beschattung_id = self._cfg[CONF_BESCHATTUNG_HYSTERESE]

        @callback
        def _on_state_change(event: Event) -> None:
            entity_id = event.data.get("entity_id")
            new_state = event.data.get("new_state")
            old_state = event.data.get("old_state")

            if entity_id == beschattung_id:
                old = old_state.state if old_state else None
                new = new_state.state if new_state else None

                if old == STATE_ON and new != STATE_ON:
                    # on→off: verzögertes Auswerten (4 min, wie blueprint "for: 00:04:00")
                    if self._beschattung_off_unsub:
                        self._beschattung_off_unsub()
                    self._beschattung_off_unsub = async_call_later(
                        self.hass,
                        BESCHATTUNG_OFF_DELAY,
                        lambda _: self.hass.async_create_task(self._evaluate()),
                    )
                    return
                elif new == STATE_ON and old != STATE_ON:
                    # off→on: sofortige Auswertung, pending Task abbrechen
                    if self._beschattung_off_unsub:
                        self._beschattung_off_unsub()
                        self._beschattung_off_unsub = None

            self.hass.async_create_task(self._evaluate())

        self._unsubs.append(
            async_track_state_change_event(self.hass, watch, _on_state_change)
        )
        _LOGGER.debug(
            "RollladenController für %s gestartet, überwacht: %s",
            self._cfg[CONF_COVER],
            watch,
        )

    async def async_unload(self) -> None:
        for unsub in self._unsubs:
            unsub()
        if self._beschattung_off_unsub:
            self._beschattung_off_unsub()

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
            cfg[CONF_BESCHATTUNG_HYSTERESE],
            cfg[CONF_TAG_NACHT_MODUS],
            cfg[CONF_ROOM_SWITCH],
            cfg[CONF_HOEHE_NACHT],
            cfg[CONF_HOEHE_TAG],
        ]

        for key in (CONF_PC_SWITCH, CONF_KINO_SWITCH, CONF_MORGENS_AUF_SWITCH, CONF_HOEHE_SCHLAFEN):
            if v := cfg.get(key):
                entities.append(v)

        return [e for e in entities if e]

    def _state(self, entity_id: Optional[str]) -> Optional[str]:
        if not entity_id:
            return None
        s = self.hass.states.get(entity_id)
        return s.state if s else None

    def _is_on(self, entity_id: Optional[str]) -> bool:
        return self._state(entity_id) == STATE_ON

    def _numeric(self, entity_id: Optional[str]) -> int:
        try:
            return int(float(self._state(entity_id) or 0))
        except (ValueError, TypeError):
            return 0

    # -------------------------------------------------- computed properties

    @property
    def _is_day(self) -> bool:
        return self._is_on(self._cfg[CONF_TAG_NACHT_MODUS])

    @property
    def _is_window(self) -> bool:
        """True wenn mindestens ein Sensor device_class=window hat."""
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
        """Aktueller Zustand des Raum-input_select."""
        return self._state(self._cfg[CONF_ROOM_SWITCH]) or ""

    @property
    def _beschattung_aktiv(self) -> bool:
        return "Inaktiv" not in self._rs

    @property
    def _beschattung_erzwungen(self) -> bool:
        return "PC" not in self._rs and "Erzwungen" in self._rs

    @property
    def _beschattung_automatik(self) -> bool:
        return "PC" not in self._rs and "Automatik" in self._rs

    @property
    def _beschattung_manuell(self) -> bool:
        return "Manuell" in self._rs

    @property
    def _pc_erzwungen(self) -> bool:
        return "PC" in self._rs and "Erzwungen" in self._rs

    @property
    def _pc_automatik(self) -> bool:
        return "PC" in self._rs and "Automatik" in self._rs

    @property
    def _is_direction(self) -> bool:
        d = self._cfg.get(CONF_DIRECTION, "")
        return bool(d) and self._is_on(f"binary_sensor.richtung{d}")

    @property
    def _is_pc_direction(self) -> bool:
        d = self._cfg.get(CONF_DIRECTION, "")
        return bool(d) and self._is_on(f"binary_sensor.richtung{d}pc")

    @property
    def _pc_an(self) -> bool:
        return self._is_on(self._cfg.get(CONF_PC_SWITCH))

    @property
    def _hysterese(self) -> bool:
        return self._is_on(self._cfg[CONF_BESCHATTUNG_HYSTERESE])

    # ----------------------------------------------------------- main logic

    async def _evaluate(self) -> None:
        cover = self._cfg[CONF_COVER]

        # 1. Nacht + Fenster offen → Nacht-Höhe
        if not self._is_day and self._is_window and self._is_window_open:
            self.last_reason = "Nacht + Fenster offen → Nacht-Höhe"
            await self._set_pos(cover, self._numeric(self._cfg[CONF_HOEHE_NACHT]))
            return

        # 2. Tür offen (kein Fenster-Sensor) → Öffnen
        if not self._is_window and self._is_window_open:
            self.last_reason = "Tür offen → Öffnen"
            await self._open(cover)
            return

        # 3. Nacht + morgens-Label + morgens_auf + Beschattung im Raum aktiv
        if (
            not self._is_day
            and self._cfg.get(CONF_IS_MORGENS_LABEL)
            and self._is_on(self._cfg.get(CONF_MORGENS_AUF_SWITCH))
            and self._beschattung_aktiv
        ):
            self.last_reason = "Morgens-Modus (Nacht) → Nacht-Höhe"
            await self._set_pos(cover, self._numeric(self._cfg[CONF_HOEHE_NACHT]))
            return

        # 4. Nacht + geschlossen → Schließen
        if not self._is_window_open and not self._is_day:
            self.last_reason = "Nacht + geschlossen → Schließen"
            await self._close(cover)
            return

        # 5. Filmeabend
        if self._is_on(self._cfg.get(CONF_KINO_SWITCH)) and self._cfg.get(CONF_IS_FILMEABEND_LABEL):
            self.last_reason = "Filmeabend → Schließen"
            await self._close(cover)
            return

        # 6. Tag + Schlafen-Modus
        if self._is_day and "Schlafen" in self._rs:
            if schlafen := self._cfg.get(CONF_HOEHE_SCHLAFEN):
                self.last_reason = "Schlafen-Höhe"
                await self._set_pos(cover, self._numeric(schlafen))
                return

        # 7. Raum zwingend geschlossen
        if "Zu" in self._rs:
            self.last_reason = "Raum: Zu → Schließen"
            await self._close(cover)
            return

        # 8. Tag + Beschattung aktiv + Richtungs-/PC-Logik
        window_or_closed_door = self._is_window or (not self._is_window and not self._is_window_open)

        shading = (
            (
                self._hysterese
                and (
                    (self._is_direction and self._beschattung_automatik)
                    or (self._pc_an and self._is_pc_direction and self._pc_automatik)
                )
            )
            or (self._is_direction and self._beschattung_erzwungen)
            or (self._pc_an and self._is_pc_direction and self._pc_erzwungen)
            or self._beschattung_manuell
        )

        if self._beschattung_aktiv and self._is_day and window_or_closed_door and shading:
            self.last_reason = "Tag-Beschattung aktiv → Tag-Höhe"
            await self._set_pos(cover, self._numeric(self._cfg[CONF_HOEHE_TAG]))
            return

        # 9. Standard-Fallback
        if self._is_day:
            self.last_reason = "Standard: Tag → Öffnen"
            await self._open(cover)
        else:
            self.last_reason = "Standard: Nacht → Schließen"
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
