# Cover Control Advanced

[![HACS Custom][hacs-badge]][hacs-url]
[![Validate][validate-badge]][validate-url]

A Home Assistant custom integration for automated cover/shutter control – configurable via the UI, no YAML automations required.

## Features

- One config entry per room
- Multiple covers per room
- Full shading logic in Python:
  - Night/day shading with configurable positions
  - Window/door contact detection (multiple sensors per cover)
  - Sun-position based shading via configured sun azimuth range (start/end degrees)
  - Event-switch controlled shading events
  - Cinema/event handling via a shared event switch
  - Sleep and closed mode
    - Shading release via binary sensor (`on` = shade allowed, `off` = shade blocked) with 4-minute off-delay
- Diagnostic sensor per cover showing the last decision reason

## Installation via HACS

1. HACS → Integrations → ⋮ → Custom Repositories
2. URL: `https://github.com/revilo91/CoverControlAdvanced`
3. Category: `Integration`
4. Add repository, then install

## Manual Installation

```bash
cp -r custom_components/covercontroladvanced \
  /config/custom_components/covercontroladvanced
```

Restart HA.

## Configuration

**Settings → Integrations → + Add → Cover Control**

First configure the room-level settings, then add one or more covers to the room. Existing rooms can be extended later via the integration's configure dialog.

| Field | Required | Description |
|---|---|---|
| Room name | ✅ | Area-based room selection shown with the friendly area name |
| Shading hysteresis | ✅ | Binary sensor for shading (`on` = shading , `off` = no shading). `off` is delayed by 4 minutes before reevaluation. |
| Day/night mode | ✅ | `input_boolean.day_night_mode` |
| Shading height | ✅ | Shared target position for shading |
| Event switch | – | `switch.*` used as the shared trigger for shading events |
| Event switch position | – | Target position used while the event switch is active |
| Cover entity | ✅ | The `cover.*` entity to control |
| Window/door contacts | – | Multiple `binary_sensor.*` supported |
| Sun azimuth start | ✅ | `0..359` degrees |
| Sun azimuth end | ✅ | `0..359` degrees (`start > end` wraps over `0°`) |

## Decision Logic (Priority)

```
1. Night + window open             → Shading height
2. Door open (no window sensor)    → Open
3. Night + event switch active     → Shading height
4. Night + closed                  → Close
5. Cinema event switch active      → Close
6. Day + sleep mode                → Shading height
7. Room = closed                   → Close
8. Day + shading + sun on side     → Shading height
9. Default                         → Day: Open / Night: Close
```
# System Architecture:

This document describes the hierarchical structure and logical dependencies of the entities for automated roller shutter and blind control (cover control) at the room level.

## Visual Architecture
```mermaid
flowchart TD
    %% Room Level
    Room["🏠 Room"]

    subgraph RoomParams [Room Configuration]
        State["Status Dropdown<br/>(Shading / Forced / Inactive / Closed)"]
        BaseHeight["Global Shading Height"]
        Hysteresis["Binary Sensor (Shading ON/OFF)"]
    end

    subgraph EventSwitch [Event Control]
        Toggle["Event Switch (ON/OFF)"]
        EvHeight{{"Event-specific Height"}}
    end

    %% Links to Room
    Room --- State
    Room --- BaseHeight
    Room --- Hysteresis
    Room --- Toggle
    Toggle ---> EvHeight

    %% Stacked Covers using 'docs' shape
    CoverStack@{ shape: docs, label: "Covers 1..N" }

    Room ==> CoverStack

    subgraph CoverDetails [Cover Instance Specification]
        direction TB

        %% Separate Azimuth Nodes
        StartAz["Start Azimuth"]
        EndAz["End Azimuth"]

        %% Stacked Contacts with Device Class
        ContactStack@{ shape: docs, label: "Contacts 1..N" }
        DClass{{"device_class:<br/>door / window"}}

        ContactStack --- DClass
    end

    %% Connect the stack to its shared definition
    CoverStack --- StartAz
    CoverStack --- EndAz
    CoverStack --- ContactStack
 ```
## Technical Specification
- **Entity: Room**
    - **State (Dropdown Helper):** Defines the global operating mode. Valid values: `Shading`, `Forced Shading`, `Inactive`, `Closed`.
    - **Hysteresis (Binary Sensor):** Shading release input (`on` = shading , `off` = no shading). When it changes from `on` to `off`, reevaluation is delayed by 4 minutes to avoid rapid toggling.
    - **Shading Height (Value):** The default target position for all covers in the room.
    - **Event Switch:** A specialized toggle that activates a secondary set of height settings, overriding the default room height.
    - **1:N Relationship:** A single Room manages a collection of $N$ associated Covers.
- **Entity: Cover**
    - **Start Azimuth:** The sun's angle at which shading for this specific cover begins.
    - **End Azimuth:** The sun's angle at which shading for this specific cover ends.
    - **1:N Relationship (Contacts):** Every cover is linked to $N$ binary sensors.
    - **Contact Attribution** (`device_class`):
        - *Logic Rule:* Contacts primarily serve as safety or lockout conditions (e.g., "lock-out protection") specific to that individual cover.
        - `window`: Triggers ventilation or prevents closing if open.
        - `door`: Provides lock-out protection to prevent accidental closure while people are outside.

## Diagnostic Sensor

Each instance creates a diagnostic sensor for the configured cover and exposes the last decision reason as its `state`.

## Developer Setup

This repository ships with a Home Assistant dev platform similar to the ComfoClime project.

### Dev Container (recommended)

1. Open this repository in VS Code.
2. Run `Dev Containers: Reopen in Container`.
3. Wait for setup scripts to finish.
4. Open Home Assistant at `http://localhost:8123`.

Detailed docs: `.devcontainer/README.md`

### Local Linux setup

```bash
bash .devcontainer/setup.sh
bash .devcontainer/start-ha.sh
```

Or with the wrapper:

```bash
bash scripts/start-ha-dev.sh
```

### Linting

```bash
bash scripts/lint.sh
bash scripts/lint.sh --fix
```

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs-url]: https://hacs.xyz
[validate-badge]: https://github.com/revilo91/CoverControlAdvanced/actions/workflows/validate.yml/badge.svg
[validate-url]: https://github.com/revilo91/CoverControlAdvanced/actions/workflows/validate.yml
