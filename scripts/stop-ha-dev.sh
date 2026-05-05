#!/usr/bin/env bash
set -euo pipefail

pkill -f "homeassistant --config .hass_dev" || true
