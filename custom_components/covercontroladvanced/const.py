DOMAIN = "covercontroladvanced"

CONF_COVER = "cover_entity"
CONF_WINDOW_ENTITIES = "window_entities"
CONF_SUN_AZIMUTH_START = "sun_azimuth_start"
CONF_SUN_AZIMUTH_END = "sun_azimuth_end"
CONF_SHADING_HYSTERESIS = "shading_hysteresis"
CONF_DAY_NIGHT_MODE = "day_night_mode"
CONF_EVENT_SWITCH = "event_switch"
CONF_EVENT_SWITCH_POSITION = "event_switch_position"
CONF_SHADING_HEIGHT = "shading_height"
SHADING_OFF_DELAY = 240  # 4 minutes off-delay for shading hysteresis

# Room mode options (internal keys, translated via entity translation)
ROOM_MODE_AUTOMATIC = "automatic"        # Beschattung automatisch
ROOM_MODE_ALWAYS_ACTIVE = "always_active"  # Beschattung immer aktiv
ROOM_MODE_ACTIVE = "active"              # Beschattung aktiv
ROOM_MODE_INACTIVE = "inactive"          # Beschattung inaktiv
ROOM_MODE_SLEEP = "sleep"               # Schlafmodus
ROOM_MODE_CLOSED = "closed"              # Zu

ROOM_MODES: list[str] = [
    ROOM_MODE_AUTOMATIC,
    ROOM_MODE_ALWAYS_ACTIVE,
    ROOM_MODE_ACTIVE,
    ROOM_MODE_INACTIVE,
    ROOM_MODE_SLEEP,
    ROOM_MODE_CLOSED,
]
