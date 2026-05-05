#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

mkdir -p .hass_dev

if [[ ! -f .hass_dev/configuration.yaml ]]; then
cat > .hass_dev/configuration.yaml <<'YAML'
default_config:

homeassistant:
  name: Cover Control Advanced Dev
  unit_system: metric
  time_zone: Europe/Berlin

logger:
  default: info
YAML
fi

if [[ ! -e .hass_dev/custom_components ]]; then
  ln -s ../custom_components .hass_dev/custom_components
fi

exec .venv/bin/python -m homeassistant --config .hass_dev
