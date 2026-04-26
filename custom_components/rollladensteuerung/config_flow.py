"""Config Flow für Rollladensteuerung."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
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
    DOMAIN,
)

_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_COVER): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="cover")
        ),
        vol.Optional(CONF_WINDOW_ENTITIES, default=[]): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="binary_sensor", multiple=True)
        ),
        vol.Optional(CONF_DIRECTION, default=""): selector.TextSelector(),
        vol.Required(CONF_ROOM_SWITCH): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="input_select")
        ),
        vol.Required(
            CONF_BESCHATTUNG_HYSTERESE,
            default="binary_sensor.beschattung_hysterese",
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="binary_sensor")
        ),
        vol.Required(
            CONF_TAG_NACHT_MODUS,
            default="input_boolean.tag_nacht_modus",
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="input_boolean")
        ),
        vol.Required(
            CONF_HOEHE_NACHT,
            default="input_number.beschattungshohe_nacht",
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="input_number")
        ),
        vol.Required(
            CONF_HOEHE_TAG,
            default="input_number.beschattungshohe_tag",
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="input_number")
        ),
        vol.Optional(CONF_HOEHE_SCHLAFEN): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="input_number")
        ),
        vol.Optional(CONF_PC_SWITCH): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="switch")
        ),
        vol.Optional(CONF_KINO_SWITCH): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="switch")
        ),
        vol.Optional(CONF_MORGENS_AUF_SWITCH): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="switch")
        ),
        vol.Optional(CONF_IS_MORGENS_LABEL, default=False): selector.BooleanSelector(),
        vol.Optional(CONF_IS_FILMEABEND_LABEL, default=False): selector.BooleanSelector(),
    }
)


class RollladensteuerungConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            cover = user_input[CONF_COVER]
            await self.async_set_unique_id(f"{DOMAIN}_{cover}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=cover, data=user_input)

        return self.async_show_form(step_id="user", data_schema=_SCHEMA)
