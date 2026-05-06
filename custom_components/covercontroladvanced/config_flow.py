"""Config flow for Cover Control Advanced."""

from copy import deepcopy

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import area_registry, device_registry, entity_registry, selector

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

def _get_area_entities(
    hass: HomeAssistant,
    area_id: str,
    domain: str,
    device_classes: list[str] | None = None,
) -> list[str]:
    """Return entity IDs assigned to the given area, optionally filtered by device class."""
    er = entity_registry.async_get(hass)
    dr = device_registry.async_get(hass)
    result = []
    for entry in er.entities.values():
        if entry.domain != domain or entry.disabled:
            continue
        if device_classes is not None:
            dc = entry.device_class or entry.original_device_class
            if dc not in device_classes:
                continue
        # Resolve the effective area: entity-level assignment overrides device-level.
        effective_area = entry.area_id
        if effective_area is None and entry.device_id:
            device = dr.devices.get(entry.device_id)
            if device is not None:
                effective_area = device.area_id
        if effective_area == area_id:
            result.append(entry.entity_id)
    return result


def _cover_schema(hass: HomeAssistant | None = None, area_id: str | None = None) -> vol.Schema:
    covers_in_area: list[str] = (
        _get_area_entities(hass, area_id, "cover")
        if hass is not None and area_id is not None
        else []
    )
    windows_in_area: list[str] = (
        _get_area_entities(hass, area_id, "binary_sensor", ["window", "door"])
        if hass is not None and area_id is not None
        else []
    )

    if covers_in_area:
        cover_selector = selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain="cover",
                include_entities=covers_in_area,
            )
        )
    else:
        cover_selector = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="cover")
        )

    if windows_in_area:
        window_selector = selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain="binary_sensor",
                device_class=["window", "door"],
                multiple=True,
                include_entities=windows_in_area,
            )
        )
    else:
        window_selector = selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain="binary_sensor",
                device_class=["window", "door"],
                multiple=True,
            )
        )

    # Pre-select automatically when the area contains exactly one matching entity.
    cover_key: vol.Required = (
        vol.Required(CONF_COVER, default=covers_in_area[0])
        if len(covers_in_area) == 1
        else vol.Required(CONF_COVER)
    )
    window_default: list[str] = windows_in_area if len(windows_in_area) == 1 else []

    return vol.Schema(
        {
            cover_key: cover_selector,
            vol.Optional(CONF_WINDOW_ENTITIES, default=window_default): window_selector,
            vol.Optional(CONF_SUN_AZIMUTH_SENSOR): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="binary_sensor", device_class=["light"]
                )
            ),
            vol.Optional(CONF_SUN_AZIMUTH_START): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=359,
                    step=1,
                    unit_of_measurement="°",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Optional(CONF_SUN_AZIMUTH_END): selector.NumberSelector(
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


def _cover_schema_with_defaults(
    cover_cfg: dict, hass: HomeAssistant | None = None, area_id: str | None = None
) -> vol.Schema:
    covers_in_area: list[str] = (
        _get_area_entities(hass, area_id, "cover")
        if hass is not None and area_id is not None
        else []
    )
    windows_in_area: list[str] = (
        _get_area_entities(hass, area_id, "binary_sensor", ["window", "door"])
        if hass is not None and area_id is not None
        else []
    )

    # Always keep the currently configured entities visible in the dropdowns.
    current_cover = cover_cfg.get(CONF_COVER, "")
    if covers_in_area and current_cover and current_cover not in covers_in_area:
        filtered_covers = [current_cover, *covers_in_area]
    else:
        filtered_covers = covers_in_area

    current_windows: list[str] = cover_cfg.get(CONF_WINDOW_ENTITIES, [])
    if windows_in_area:
        extra = [e for e in current_windows if e not in windows_in_area]
        filtered_windows = [*extra, *windows_in_area] if extra else windows_in_area
    else:
        filtered_windows = windows_in_area

    if filtered_covers:
        cover_selector = selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain="cover",
                include_entities=filtered_covers,
            )
        )
    else:
        cover_selector = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="cover")
        )

    if filtered_windows:
        window_selector = selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain="binary_sensor",
                device_class=["window", "door"],
                multiple=True,
                include_entities=filtered_windows,
            )
        )
    else:
        window_selector = selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain="binary_sensor",
                device_class=["window", "door"],
                multiple=True,
            )
        )

    existing_sensor = cover_cfg.get(CONF_SUN_AZIMUTH_SENSOR)
    existing_start = cover_cfg.get(CONF_SUN_AZIMUTH_START)
    existing_end = cover_cfg.get(CONF_SUN_AZIMUTH_END)

    sun_sensor_key = (
        vol.Optional(CONF_SUN_AZIMUTH_SENSOR, default=existing_sensor)
        if existing_sensor
        else vol.Optional(CONF_SUN_AZIMUTH_SENSOR)
    )

    return vol.Schema(
        {
            vol.Required(
                CONF_COVER,
                default=cover_cfg.get(CONF_COVER, ""),
            ): cover_selector,
            vol.Optional(
                CONF_WINDOW_ENTITIES,
                default=cover_cfg.get(CONF_WINDOW_ENTITIES, []),
            ): window_selector,
            sun_sensor_key: selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="binary_sensor", device_class=["light"]
                )
            ),
            vol.Optional(
                CONF_SUN_AZIMUTH_START,
                description={"suggested_value": existing_start} if existing_start is not None else None,
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=359,
                    step=1,
                    unit_of_measurement="°",
                    mode=selector.NumberSelectorMode.BOX,
                )
            ),
            vol.Optional(
                CONF_SUN_AZIMUTH_END,
                description={"suggested_value": existing_end} if existing_end is not None else None,
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


def _clean_cover_input(user_input: dict) -> None:
    """Strip optional cover fields that were left empty."""
    for key in (CONF_SUN_AZIMUTH_SENSOR, CONF_SUN_AZIMUTH_START, CONF_SUN_AZIMUTH_END):
        if user_input.get(key) is None:
            user_input.pop(key, None)


def _resolve_room_name(flow: config_entries.ConfigFlow, value: str) -> str:
    area = area_registry.async_get(flow.hass).async_get_area(value)
    return area.name if area is not None else value


class CoverControlAdvancedConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 7

    def __init__(self) -> None:
        self._room_data: dict = {}
        self._covers: list[dict] = []
        self._area_id: str | None = None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        return CoverControlAdvancedOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            raw_room_name = user_input[CONF_ROOM_NAME]
            self._area_id = raw_room_name
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
            _clean_cover_input(user_input)
            if _cover_already_added(self._covers, user_input[CONF_COVER]):
                errors["base"] = "cover_already_added"
            else:
                self._covers.append(user_input)
                return await self.async_step_add_more()

        return self.async_show_form(
            step_id="cover",
            data_schema=_cover_schema(self.hass, self._area_id),
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

    def _get_area_id(self) -> str | None:
        """Return the area ID for the room configured in this entry, if any."""
        room_name = self._working_data.get(CONF_ROOM_NAME, "")
        ar = area_registry.async_get(self.hass)
        area = ar.async_get_area_by_name(room_name)
        return area.id if area is not None else None

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
            _clean_cover_input(user_input)
            if _cover_already_added(covers, user_input[CONF_COVER]):
                errors["base"] = "cover_already_added"
            else:
                self._working_data.setdefault(CONF_COVERS, []).append(user_input)
                self._dirty = True
                return await self.async_step_init()

        return self.async_show_form(
            step_id="cover",
            data_schema=_cover_schema(self.hass, self._get_area_id()),
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
            _clean_cover_input(user_input)
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
            data_schema=_cover_schema_with_defaults(
                selected_cover_cfg, self.hass, self._get_area_id()
            ),
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
