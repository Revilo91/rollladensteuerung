#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [[ -d "/workspaces/rollladensteuerung" ]]; then
  WORKSPACE_ROOT="/workspaces/rollladensteuerung"
else
  WORKSPACE_ROOT="$PROJECT_ROOT"
fi

VENV_DIR="$WORKSPACE_ROOT/.venv"
CONFIG_DIR="$WORKSPACE_ROOT/.devcontainer/ha-config"

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "Virtual environment not found. Running setup first..."
  bash "$WORKSPACE_ROOT/.devcontainer/setup.sh"
fi

echo "Starting Home Assistant"
echo "Configuration: $CONFIG_DIR"
echo "Web UI: http://localhost:8123"

exec "$VENV_DIR/bin/python" -m homeassistant -c "$CONFIG_DIR"
