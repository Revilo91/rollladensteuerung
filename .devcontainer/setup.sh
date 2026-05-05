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
DOMAIN="covercontroladvanced"

mkdir -p "$CONFIG_DIR/custom_components"

if [[ ! -d "$VENV_DIR" ]]; then
  python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install "homeassistant>=2024.1.0" ruff

rm -f "$CONFIG_DIR/custom_components/$DOMAIN"
ln -s "$WORKSPACE_ROOT/custom_components/$DOMAIN" "$CONFIG_DIR/custom_components/$DOMAIN"

cp "$WORKSPACE_ROOT/.devcontainer/configuration.yaml" "$CONFIG_DIR/configuration.yaml"
cp "$WORKSPACE_ROOT/.devcontainer/automations.yaml" "$CONFIG_DIR/automations.yaml"
cp "$WORKSPACE_ROOT/.devcontainer/scripts.yaml" "$CONFIG_DIR/scripts.yaml"
cp "$WORKSPACE_ROOT/.devcontainer/scenes.yaml" "$CONFIG_DIR/scenes.yaml"

echo "Development setup complete"
echo "Config directory: $CONFIG_DIR"
echo "Start command: $WORKSPACE_ROOT/.devcontainer/start-ha.sh"
