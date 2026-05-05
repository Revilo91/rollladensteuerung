"""Config flow for Cover Control Advanced."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import area_registry, selector

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

STEP_FINISH = "finish"

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

def _cover_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_COVER): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="cover")
            ),
            vol.Optional(CONF_WINDOW_ENTITIES, default=[]): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="binary_sensor",
                    device_class=["window", "door"],
                    multiple=True,
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


def _cover_already_added(covers: list[dict], cover_entity: str) -> bool:
    return any(cover_cfg[CONF_COVER] == cover_entity for cover_cfg in covers)


def _resolve_room_name(flow: config_entries.ConfigFlow, value: str) -> str:
    area = area_registry.async_get(flow.hass).async_get_area(value)
    return area.name if area is not None else value


class CoverControlAdvancedConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 7

    def __init__(self) -> None:
        self._room_data: dict = {}
        self._covers: list[dict] = []

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return CoverControlAdvancedOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            raw_room_name = user_input[CONF_ROOM_NAME]
            self._room_data = {
                **user_input,
                CONF_ROOM_NAME: _resolve_room_name(self, raw_room_name),
            }
            await self.async_set_unique_id(f"{DOMAIN}_{raw_room_name}")
            self._abort_if_unique_id_configured()
            return await self.async_step_cover()

        return self.async_show_form(step_id="user", data_schema=_ROOM_SCHEMA)

    async def async_step_cover(self, user_input=None):
        errors: dict[str, str] = {}
        if user_input is not None:
            if _cover_already_added(self._covers, user_input[CONF_COVER]):
                errors["base"] = "cover_already_added"
            else:
                self._covers.append(user_input)
                return await self.async_step_add_more()

        return self.async_show_form(
            step_id="cover",
            data_schema=_cover_schema(),
            errors=errors,
        )

    async def async_step_add_more(self, user_input=None):
        return self.async_show_menu(
            step_id="add_more",
            menu_options=["cover", STEP_FINISH],
        )

    async def async_step_finish(self, user_input=None):
        room_name = self._room_data[CONF_ROOM_NAME]
        data = {**self._room_data, CONF_COVERS: self._covers}
        return self.async_create_entry(title=room_name, data=data)


class CoverControlAdvancedOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry
        self._new_covers: list[dict] = []

    async def async_step_init(self, user_input=None):
        return await self.async_step_cover()

    async def async_step_cover(self, user_input=None):
        errors: dict[str, str] = {}
        if user_input is not None:
            existing_covers = self.config_entry.data.get(CONF_COVERS, [])
            all_covers = [*existing_covers, *self._new_covers]
            if _cover_already_added(all_covers, user_input[CONF_COVER]):
                errors["base"] = "cover_already_added"
            else:
                self._new_covers.append(user_input)
                return await self.async_step_add_more()

        return self.async_show_form(
            step_id="cover",
            data_schema=_cover_schema(),
            errors=errors,
        )

    async def async_step_add_more(self, user_input=None):
        return self.async_show_menu(
            step_id="add_more",
            menu_options=["cover", STEP_FINISH],
        )

    async def async_step_finish(self, user_input=None):
        if self._new_covers:
            updated_data = {
                **self.config_entry.data,
                CONF_COVERS: [
                    *self.config_entry.data.get(CONF_COVERS, []),
                    *self._new_covers,
                ],
            }
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data=updated_data,
            )
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)

        return self.async_create_entry(title="", data={})
