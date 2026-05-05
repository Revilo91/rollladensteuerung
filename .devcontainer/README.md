# Development Container for Cover Control Advanced

This repository includes a Home Assistant development container setup similar to the ComfoClime project.

## Quick start

1. Open the repository in VS Code.
2. Run `Dev Containers: Reopen in Container`.
3. Wait for setup to complete.
4. Open Home Assistant at `http://localhost:8123`.

## What is configured automatically

- Python virtual environment in `.venv`
- Home Assistant installation in `.venv`
- Symlink from `.devcontainer/ha-config/custom_components/covercontroladvanced` to `custom_components/covercontroladvanced`
- Local test configuration in `.devcontainer/ha-config`

## Local (non-container) usage

You can run the same flow directly on Linux:

```bash
bash .devcontainer/setup.sh
bash .devcontainer/start-ha.sh
```

Or use the wrapper script:

```bash
bash scripts/start-ha-dev.sh
```

## Useful commands

```bash
bash scripts/lint.sh
bash scripts/lint.sh --fix
bash scripts/stop-ha-dev.sh
```
