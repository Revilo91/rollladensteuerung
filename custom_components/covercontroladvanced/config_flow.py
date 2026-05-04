"""Config flow for Cover Control Advanced."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_COVER,
    CONF_DAY_NIGHT_MODE,
    CONF_EVENT_SWITCH,
    CONF_ROOM_SWITCH,
    CONF_SHADING_HEIGHT,
    CONF_SHADING_HYSTERESIS,
    CONF_SUN_AZIMUTH_TOLERANCE,
    CONF_WINDOW_AZIMUTH,
    CONF_WINDOW_ENTITIES,
    DOMAIN,
)

_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_COVER): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="cover")
        ),
        vol.Optional(CONF_WINDOW_ENTITIES, default=[]): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain="binary_sensor", device_class=["window", "door"], multiple=True
            )
        ),
        vol.Required(CONF_WINDOW_AZIMUTH, default=180): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0,
                max=359,
                step=1,
                unit_of_measurement="°",
                mode=selector.NumberSelectorMode.BOX,
            )
        ),
        vol.Optional(CONF_SUN_AZIMUTH_TOLERANCE, default=45): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=5,
                max=90,
                step=1,
                unit_of_measurement="°",
                mode=selector.NumberSelectorMode.BOX,
            )
        ),
        vol.Required(CONF_ROOM_SWITCH): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="input_select")
        ),
        vol.Required(
            CONF_SHADING_HYSTERESIS,
            default="",
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain="binary_sensor", device_class=["light"]
            )
        ),
        vol.Required(
            CONF_DAY_NIGHT_MODE,
            default="",
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="input_boolean")
        ),
        vol.Required(
            CONF_SHADING_HEIGHT,
            default="20", min=0, max=100, step=1, unit_of_measurement="%", mode="box"
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="input_number")
        ),
        vol.Optional(CONF_EVENT_SWITCH): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="switch")
        ),
    }
)


class CoverControlAdvancedConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 3

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            cover = user_input[CONF_COVER]
            await self.async_set_unique_id(f"{DOMAIN}_{cover}")
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=cover, data=user_input)

        return self.async_show_form(step_id="user", data_schema=_SCHEMA)
