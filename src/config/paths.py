"""Configuration path resolution for CLI commands."""

from __future__ import annotations

import os
from pathlib import Path

from integrations.azure_devops_reporting.errors import ConfigurationError

DEFAULT_CONTAINER_CONFIG_PATH = "/config/reporting.yaml"


def resolve_config_path(*, config_arg: str | None) -> Path:
    """Resolve reporting YAML path from CLI, env, or container default."""
    if config_arg:
        return Path(config_arg)

    env_path = os.environ.get("REPORTING_APP_CONFIG")
    if env_path:
        return Path(env_path)

    return Path(DEFAULT_CONTAINER_CONFIG_PATH)


def require_config_path(*, config_arg: str | None) -> Path:
    """Resolve config path and fail fast when the file is missing."""
    config_path = resolve_config_path(config_arg=config_arg)
    if not config_path.is_file():
        raise ConfigurationError(
            f"configuration file not found: {config_path}. "
            "Pass --config or set REPORTING_APP_CONFIG."
        )
    return config_path
