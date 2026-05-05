"""Room mode select entity for Cover Control Advanced."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import (
    CONF_COVER,
    DOMAIN,
    ROOM_MODE_AUTOMATIC,
    ROOM_MODES,
)

if TYPE_CHECKING:
    from .controller import CoverControlAdvancedController


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the room mode select entity."""
    ctrl: CoverControlAdvancedController = hass.data[DOMAIN][entry.entry_id]
    entity = CoverControlAdvancedRoomModeSelect(entry, ctrl)
    ctrl.room_mode_select = entity
    async_add_entities([entity])


class CoverControlAdvancedRoomModeSelect(SelectEntity, RestoreEntity):
    """Select entity representing the room shading mode."""

    _attr_icon = "mdi:blinds"
    _attr_should_poll = False
    _attr_translation_key = "room_mode"

    def __init__(self, entry: ConfigEntry, ctrl: CoverControlAdvancedController) -> None:
        self._entry = entry
        self._ctrl = ctrl
        cover = entry.data[CONF_COVER]
        self._attr_unique_id = f"{DOMAIN}_{cover}_room_mode"
        self._attr_name = f"Cover Control Advanced {cover} Room Mode"
        self._attr_options = list(ROOM_MODES)
        self._attr_current_option = ROOM_MODE_AUTOMATIC

    async def async_added_to_hass(self) -> None:
        """Restore the previously selected option."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            if last_state.state in self._attr_options:
                self._attr_current_option = last_state.state

    async def async_select_option(self, option: str) -> None:
        """Handle a new option being selected by the user."""
        self._attr_current_option = option
        self.async_write_ha_state()
        self.hass.async_create_task(self._ctrl.async_trigger_evaluation())
