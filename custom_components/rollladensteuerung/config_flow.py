"""Config flow for Rollladensteuerung."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

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
            CONF_SHADING_HYSTERESIS,
            default="binary_sensor.shading_hysteresis",
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="binary_sensor")
        ),
        vol.Required(
            CONF_DAY_NIGHT_MODE,
            default="input_boolean.day_night_mode",
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="input_boolean")
        ),
        vol.Required(
            CONF_NIGHT_POSITION,
            default="input_number.night_shading_position",
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="input_number")
        ),
        vol.Required(
            CONF_DAY_POSITION,
            default="input_number.day_shading_position",
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="input_number")
        ),
        vol.Optional(CONF_SLEEP_POSITION): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="input_number")
        ),
        vol.Optional(CONF_PC_SWITCH): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="switch")
        ),
        vol.Optional(CONF_CINEMA_SWITCH): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="switch")
        ),
        vol.Optional(CONF_MORNING_OPEN_SWITCH): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="switch")
        ),
        vol.Optional(CONF_ENABLE_MORNING_MODE, default=False): selector.BooleanSelector(),
        vol.Optional(CONF_ENABLE_CINEMA_MODE, default=False): selector.BooleanSelector(),
    }
)


class RollladensteuerungConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            cover = user_input[CONF_COVER]
            await self.async_set_unique_id(f"{DOMAIN}_{cover}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=cover, data=user_input)

        return self.async_show_form(step_id="user", data_schema=_SCHEMA)
