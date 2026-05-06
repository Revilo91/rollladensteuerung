"""Config flow for Cover Control Advanced."""

from copy import deepcopy

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
    CONF_SUN_AZIMUTH_SENSOR,
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
            vol.Optional(CONF_SUN_AZIMUTH_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="binary_sensor", device_class=["light"]
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


def _cover_schema_with_defaults(cover_cfg: dict) -> vol.Schema:
    existing_sensor = cover_cfg.get(CONF_SUN_AZIMUTH_SENSOR)
    return vol.Schema(
        {
            vol.Required(
                CONF_COVER,
                default=cover_cfg.get(CONF_COVER, ""),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="cover")
            ),
            vol.Optional(
                CONF_WINDOW_ENTITIES,
                default=cover_cfg.get(CONF_WINDOW_ENTITIES, []),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="binary_sensor",
                    device_class=["window", "door"],
                    multiple=True,
                )
            ),
            vol.Optional(
                CONF_SUN_AZIMUTH_SENSOR,
                description={"suggested_value": existing_sensor} if existing_sensor else None,
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="binary_sensor", device_class=["light"]
                )
            ),
            vol.Required(
                CONF_SUN_AZIMUTH_START,
                default=cover_cfg.get(CONF_SUN_AZIMUTH_START, 135),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=359,
                    step=1,
                    unit_of_measurement="°",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Required(
                CONF_SUN_AZIMUTH_END,
                default=cover_cfg.get(CONF_SUN_AZIMUTH_END, 225),
            ): selector.NumberSelector(
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


def _room_options_schema(data: dict) -> vol.Schema:
    event_switch = data.get(CONF_EVENT_SWITCH)
    event_switch_description = (
        {"suggested_value": event_switch} if event_switch else None
    )

    return vol.Schema(
        {
            vol.Required(
                CONF_ROOM_NAME,
                default=data.get(CONF_ROOM_NAME, ""),
            ): selector.TextSelector(),
            vol.Required(
                CONF_SHADING_HYSTERESIS,
                default=data.get(CONF_SHADING_HYSTERESIS, ""),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="binary_sensor", device_class=["light"]
                )
            ),
            vol.Required(
                CONF_DAY_NIGHT_MODE,
                default=data.get(CONF_DAY_NIGHT_MODE, ""),
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="input_boolean")
            ),
            vol.Required(
                CONF_SHADING_HEIGHT,
                default=data.get(CONF_SHADING_HEIGHT, 20),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=100,
                    step=1,
                    unit_of_measurement="%",
                    mode=selector.NumberSelectorMode.SLIDER,
                )
            ),
            vol.Optional(
                CONF_EVENT_SWITCH,
                description=event_switch_description,
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="switch")
            ),
            vol.Optional(
                CONF_EVENT_SWITCH_POSITION,
                default=data.get(CONF_EVENT_SWITCH_POSITION, 0),
            ): selector.NumberSelector(
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


def _cover_select_schema(hass, covers: list[dict]) -> vol.Schema:
    options = [
        selector.SelectOptionDict(
            value=cover_cfg[CONF_COVER],
            label=(
                state.name
                if (state := hass.states.get(cover_cfg[CONF_COVER])) is not None
                else cover_cfg[CONF_COVER]
            ),
        )
        for cover_cfg in covers
    ]
    return vol.Schema(
        {
            vol.Required("selected_cover"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        }
    )


def _options_init_menu(has_covers: bool) -> list[str]:
    options = ["room", "cover"]
    if has_covers:
        options.append("cover_select")
    options.append("finish")
    return options


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
            if not user_input.get(CONF_SUN_AZIMUTH_SENSOR):
                user_input.pop(CONF_SUN_AZIMUTH_SENSOR, None)
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


class CoverControlAdvancedOptionsFlow(config_entries.OptionsFlowWithConfigEntry):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        super().__init__(config_entry)
        self._working_data: dict = deepcopy(dict(config_entry.data))
        self._selected_cover: str | None = None
        self._dirty = False

    async def async_step_init(self, user_input=None):
        return self.async_show_menu(
            step_id="init",
            menu_options=_options_init_menu(
                bool(self._working_data.get(CONF_COVERS))
            ),
        )

    async def async_step_room(self, user_input=None):
        if user_input is not None:
            # Optional fields are absent when cleared in the form.
            # Some frontends can also submit an empty string for a cleared selector.
            if not user_input.get(CONF_EVENT_SWITCH):
                self._working_data.pop(CONF_EVENT_SWITCH, None)
                user_input.pop(CONF_EVENT_SWITCH, None)
            self._working_data.update(user_input)
            self._dirty = True
            return await self.async_step_init()

        return self.async_show_form(
            step_id="room",
            data_schema=_room_options_schema(self._working_data),
        )

    async def async_step_cover(self, user_input=None):
        errors: dict[str, str] = {}
        covers = self._working_data.get(CONF_COVERS, [])
        if user_input is not None:
            if not user_input.get(CONF_SUN_AZIMUTH_SENSOR):
                user_input.pop(CONF_SUN_AZIMUTH_SENSOR, None)
            if _cover_already_added(covers, user_input[CONF_COVER]):
                errors["base"] = "cover_already_added"
            else:
                self._working_data.setdefault(CONF_COVERS, []).append(user_input)
                self._dirty = True
                return await self.async_step_init()

        return self.async_show_form(
            step_id="cover",
            data_schema=_cover_schema(),
            errors=errors,
        )

    async def async_step_cover_select(self, user_input=None):
        errors: dict[str, str] = {}
        covers = self._working_data.get(CONF_COVERS, [])
        if user_input is not None:
            selected_cover = user_input["selected_cover"]
            if not _cover_already_added(covers, selected_cover):
                errors["base"] = "cover_not_found"
            else:
                self._selected_cover = selected_cover
                return await self.async_step_cover_edit()

        return self.async_show_form(
            step_id="cover_select",
            data_schema=_cover_select_schema(self.hass, covers),
            errors=errors,
        )

    async def async_step_cover_edit(self, user_input=None):
        covers = self._working_data.get(CONF_COVERS, [])
        if self._selected_cover is None:
            return await self.async_step_cover_select()

        selected_idx = next(
            (
                i
                for i, cover_cfg in enumerate(covers)
                if cover_cfg[CONF_COVER] == self._selected_cover
            ),
            None,
        )
        if selected_idx is None:
            self._selected_cover = None
            return await self.async_step_cover_select()

        selected_cover_cfg = covers[selected_idx]

        errors: dict[str, str] = {}
        if user_input is not None:
            new_cover_entity = user_input[CONF_COVER]
            if not user_input.get(CONF_SUN_AZIMUTH_SENSOR):
                user_input.pop(CONF_SUN_AZIMUTH_SENSOR, None)
            duplicate_cover = any(
                i != selected_idx and c[CONF_COVER] == new_cover_entity
                for i, c in enumerate(covers)
            )
            if duplicate_cover:
                errors["base"] = "cover_already_added"
            else:
                covers[selected_idx] = user_input
                self._selected_cover = user_input[CONF_COVER]
                self._dirty = True
                return await self.async_step_init()

        return self.async_show_form(
            step_id="cover_edit",
            data_schema=_cover_schema_with_defaults(selected_cover_cfg),
            errors=errors,
        )

    async def async_step_finish(self, user_input=None):
        if self._dirty:
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                title=self._working_data.get(CONF_ROOM_NAME, self.config_entry.title),
                data=self._working_data,
            )
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)

        return self.async_create_entry(title="", data={})
