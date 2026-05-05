#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

if [[ ! -f .devcontainer/setup.sh ]]; then
  echo "Missing .devcontainer/setup.sh"
  exit 1
fi

bash .devcontainer/setup.sh
exec .venv/bin/python -m homeassistant --config .devcontainer/ha-config
