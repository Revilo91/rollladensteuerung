# Project Guidelines

## Scope

- This repository is a Home Assistant custom integration with UI-based setup via config entries; do not introduce YAML-only configuration paths unless explicitly requested.
- Keep changes focused on the integration under `custom_components/covercontroladvanced` and preserve Home Assistant conventions for config flows, entity setup, and async lifecycle methods.

## Python And Home Assistant Conventions

- Prefer fully typed Python code and keep the existing simple module structure instead of introducing unnecessary abstractions.
- Use Home Assistant async APIs end-to-end. Avoid blocking I/O, synchronous sleeps, or long-running work in entity and controller code.
- Preserve the current setup pattern: controller state is created in `__init__.py`, stored in `hass.data[DOMAIN][entry.entry_id]`, and reused by the sensor platform.
- Keep service calls and state tracking aligned with Home Assistant helpers such as `async_track_state_change_event`, `async_call_later`, and `hass.services.async_call`.

## Integration-Specific Rules

- Treat `config_flow.py`, `const.py`, `controller.py`, and `sensor.py` as the core contract of the integration. Changes to config keys in `const.py` must be reflected in config flow fields, runtime logic, and translations.
- The diagnostic sensor exposes the controller decision reason. When changing decision logic, keep `last_reason` meaningful and user-readable.
- This integration relies on Home Assistant entity IDs stored in the config entry. Do not replace them with hardcoded assumptions or derived values unless the user asks for a migration.
- The current logic distinguishes between day/night, shading hysteresis, room modes, direction sensors, optional sleep position, and optional event switch. Preserve that behavior unless the task explicitly changes business rules.

## Naming Consistency

- The repository currently contains mixed naming: folder `covercontroladvanced`, manifest and README text `CoverControlAdvanced`, and constant `DOMAIN = "cover_control_advanced"`.
- Do not partially rename one of these identifiers. If a task requires renaming, update all affected touchpoints together, including manifest metadata, README, translations, sensor naming, and any generated entity identifiers.

## Translations And Documentation

- Any user-facing config flow field, title, or abort message change must be mirrored in both translation files under `custom_components/covercontroladvanced/translations/`.
- Keep README examples and terminology aligned with the actual integration behavior and installation path.

## Validation

- Before finishing substantial Python changes, run `ruff check custom_components/`.
- When changes affect manifest, structure, translations, or Home Assistant integration metadata, also consider the repository CI expectations from `.github/workflows/validate.yml`: HACS validation and Hassfest.