DOMAIN = "rollladensteuerung"

CONF_COVER = "cover_entity"
CONF_WINDOW_ENTITIES = "window_entities"
CONF_DIRECTION = "direction"
CONF_ROOM_SWITCH = "room_switch"
CONF_SHADING_HYSTERESIS = "shading_hysteresis"
CONF_DAY_NIGHT_MODE = "day_night_mode"
CONF_PC_SWITCH = "pc_switch"
CONF_CINEMA_SWITCH = "cinema_switch"
CONF_MORNING_OPEN_SWITCH = "morning_open_switch"
CONF_ENABLE_MORNING_MODE = "enable_morning_mode"
CONF_ENABLE_CINEMA_MODE = "enable_cinema_mode"
CONF_NIGHT_POSITION = "night_position"
CONF_DAY_POSITION = "day_position"
CONF_SLEEP_POSITION = "sleep_position"

LEGACY_KEY_MAPPING = {
    "beschattung_hysterese": CONF_SHADING_HYSTERESIS,
    "tag_nacht_modus": CONF_DAY_NIGHT_MODE,
    "kino_switch": CONF_CINEMA_SWITCH,
    "morgens_auf_switch": CONF_MORNING_OPEN_SWITCH,
    "is_morgens_label": CONF_ENABLE_MORNING_MODE,
    "is_filmeabend_label": CONF_ENABLE_CINEMA_MODE,
    "hoehe_nacht": CONF_NIGHT_POSITION,
    "hoehe_tag": CONF_DAY_POSITION,
    "hoehe_schlafen": CONF_SLEEP_POSITION,
}

SHADING_OFF_DELAY = 240  # 4 minutes off-delay for shading hysteresis
