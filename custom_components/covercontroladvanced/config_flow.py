"""Config flow for Cover Control Advanced."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import (
    CONF_COVER,
    CONF_COVERS,
    CONF_DAY_NIGHT_MODE,
    CONF_EVENT_SWITCH,
    CONF_EVENT_SWITCH_POSITION,
    CONF_ROOM_NAME,
    CONF_SHADING_HEIGHT,
    CONF_SHADING_HYSTERESIS,
    CONF_SUN_AZIMUTH_END,
    CONF_SUN_AZIMUTH_START,
    CONF_WINDOW_ENTITIES,
    DOMAIN,
)

_ROOM_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ROOM_NAME): selector.AreaSelector(),
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
        vol.Required(CONF_SHADING_HEIGHT, default=20): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0,
                max=100,
                step=1,
                unit_of_measurement="%",
                mode=selector.NumberSelectorMode.SLIDER,
            )
        ),
        vol.Optional(CONF_EVENT_SWITCH): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="switch")
        ),
        vol.Optional(CONF_EVENT_SWITCH_POSITION, default=0): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0,
                max=100,
                step=1,
                unit_of_measurement="%",
                mode=selector.NumberSelectorMode.SLIDER,
            )
        ),
    }
)

_COVER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_COVER): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="cover")
        ),
        vol.Optional(CONF_WINDOW_ENTITIES, default=[]): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain="binary_sensor", device_class=["window", "door"], multiple=True
            )
        ),
        vol.Required(CONF_SUN_AZIMUTH_START, default=135): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0,
                max=359,
                step=1,
                unit_of_measurement="°",
                mode=selector.NumberSelectorMode.BOX,
            )
        ),
        vol.Required(CONF_SUN_AZIMUTH_END, default=225): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0,
                max=359,
                step=1,
                unit_of_measurement="°",
                mode=selector.NumberSelectorMode.BOX,
            )
        ),
    }
)


class CoverControlAdvancedConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 6

    def __init__(self) -> None:
        self._room_data: dict = {}

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            self._room_data = user_input
            return await self.async_step_cover()

        return self.async_show_form(step_id="user", data_schema=_ROOM_SCHEMA)

    async def async_step_cover(self, user_input=None):
        if user_input is not None:
            room_name = self._room_data[CONF_ROOM_NAME]
            await self.async_set_unique_id(f"{DOMAIN}_{room_name}")
            self._abort_if_unique_id_configured()
            data = {**self._room_data, CONF_COVERS: [user_input]}
            return self.async_create_entry(title=room_name, data=data)

        return self.async_show_form(step_id="cover", data_schema=_COVER_SCHEMA)
