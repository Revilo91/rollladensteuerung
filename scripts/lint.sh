#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

FIX_MODE=false
if [[ "${1:-}" == "--fix" || "${1:-}" == "-f" ]]; then
  FIX_MODE=true
fi

if [[ ! -x ".venv/bin/ruff" ]]; then
  echo "ruff is not available in .venv"
  echo "Install dependencies with: .devcontainer/setup.sh"
  exit 1
fi

if [[ "$FIX_MODE" == "true" ]]; then
  .venv/bin/ruff format .
  .venv/bin/ruff check --fix custom_components/
else
  .venv/bin/ruff format --check .
  .venv/bin/ruff check custom_components/
fi
