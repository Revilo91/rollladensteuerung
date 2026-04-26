# Rollladensteuerung

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
2. URL: `https://github.com/revilo91/rollladensteuerung`
3. Category: `Integration`
4. Add repository, then install

## Manual Installation

```bash
cp -r custom_components/rollladensteuerung \
      /config/custom_components/rollladensteuerung
```

Restart HA.

## Configuration

**Settings → Integrations → + Add → Rollladensteuerung**

| Field | Required | Description |
|---|---|---|
| Cover entity | ✅ | The `cover.*` entity to control |
| Window/door contacts | – | Multiple `binary_sensor.*` supported |
| Direction suffix | – | e.g. `suden` → `binary_sensor.richtungsuden` |
| Room automation | ✅ | `input_select.*` with values like `Automatik`, `Erzwungen`, `Inaktiv`, `Manuell`, `PC Automatik`, `PC Erzwungen`, `Schlafen`, `Zu` |
| Shading hysteresis | ✅ | `binary_sensor.beschattung_hysterese` |
| Day/night mode | ✅ | `input_boolean.tag_nacht_modus` |
| Night position | ✅ | `input_number.beschattungshohe_nacht` |
| Day position | ✅ | `input_number.beschattungshohe_tag` |
| Sleep position | – | `input_number.beschattungshohe_schlafen` |
| PC switch | – | `switch.buro_steckdose_*` or similar |
| Cinema switch | – | `switch.kino` |
| Morning-open switch | – | `switch.rolllade_ankleide_morgens_auf` |
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

Each instance creates a sensor `sensor.rollladensteuerung_<cover>` with the last decision reason as its `state`.

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs-url]: https://hacs.xyz
[validate-badge]: https://github.com/revilo91/rollladensteuerung/actions/workflows/validate.yml/badge.svg
[validate-url]: https://github.com/revilo91/rollladensteuerung/actions/workflows/validate.yml
