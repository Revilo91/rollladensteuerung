# CoverControlAdvanced

[![HACS Custom][hacs-badge]][hacs-url]
[![Validate][validate-badge]][validate-url]

A Home Assistant custom integration for automated cover/shutter control – configurable via the UI, no YAML automations required.

## Features

- One config entry per cover
- Full shading logic in Python:
  - Night/day shading with configurable positions
  - Window/door contact detection (multiple sensors per cover)
  - Direction-based shading (`binary_sensor.richtung<suffix>`)
  - PC-based shading (separate direction logic)
  - Cinema/movie-night mode
  - Morning-open function
  - Sleep and closed mode
  - Shading hysteresis with 4-minute off-delay
- Diagnostic sensor per cover showing the last decision reason

## Installation via HACS

1. HACS → Integrations → ⋮ → Custom Repositories
2. URL: `https://github.com/revilo91/CoverControlAdvanced`
3. Category: `Integration`
4. Add repository, then install

## Manual Installation

```bash
cp -r custom_components/CoverControlAdvanced \
      /config/custom_components/CoverControlAdvanced
```

Restart HA.

## Configuration

**Settings → Integrations → + Add → Cover Control**

| Field | Required | Description |
|---|---|---|
| Cover entity | ✅ | The `cover.*` entity to control |
| Window/door contacts | – | Multiple `binary_sensor.*` supported |
| Direction suffix | – | e.g. `south` → `binary_sensor.richtungsouth` |
| Room automation | ✅ | `input_select.*` with values like `Automatic`, `Forced`, `Inactive`, `Manual`, `PC Automatic`, `PC Forced`, `Sleep`, `Closed` |
| Shading hysteresis | ✅ | `binary_sensor.shading_hysteresis` |
| Day/night mode | ✅ | `input_boolean.day_night_mode` |
| Night position | ✅ | `input_number.night_shading_position` |
| Day position | ✅ | `input_number.day_shading_position` |
| Sleep position | – | `input_number.sleep_shading_position` |
| PC switch | – | `switch.buro_steckdose_*` or similar |
| Cinema switch | – | `switch.cinema` |
| Morning-open switch | – | `switch.morning_open` |
| Morning function active | – | Boolean – enables the morning-open feature for this cover |
| Cinema function active | – | Boolean – enables the cinema/movie-night feature for this cover |

## Decision Logic (Priority)

```
1. Night + window open             → Night position
2. Door open (no window sensor)    → Open
3. Night + morning mode active     → Night position
4. Night + closed                  → Close
5. Cinema mode active              → Close
6. Day + sleep mode                → Sleep position
7. Room = closed                   → Close
8. Day + shading + direction       → Day position
9. Default                         → Day: Open / Night: Close
```

## Diagnostic Sensor

Each instance creates a sensor `sensor.CoverControlAdvanced_<cover>` with the last decision reason as its `state`.

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs-url]: https://hacs.xyz
[validate-badge]: https://github.com/revilo91/CoverControlAdvanced/actions/workflows/validate.yml/badge.svg
[validate-url]: https://github.com/revilo91/CoverControlAdvanced/actions/workflows/validate.yml
