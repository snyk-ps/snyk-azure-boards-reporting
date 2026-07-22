"""Tests for configuration path resolution."""

import os
from pathlib import Path

import pytest

from config.paths import (
    DEFAULT_CONTAINER_CONFIG_PATH,
    require_config_path,
    resolve_config_path,
)
from integrations.azure_devops_reporting.errors import ConfigurationError


def test_resolve_config_path_prefers_cli_argument() -> None:
    path = resolve_config_path(config_arg="data/reporting.sample.yaml")

    assert path == Path("data/reporting.sample.yaml")


def test_resolve_config_path_uses_reporting_app_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REPORTING_APP_CONFIG", "data/local.yaml")

    path = resolve_config_path(config_arg=None)

    assert path == Path("data/local.yaml")


def test_resolve_config_path_defaults_to_container_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("REPORTING_APP_CONFIG", raising=False)

    path = resolve_config_path(config_arg=None)

    assert path == Path(DEFAULT_CONTAINER_CONFIG_PATH)


def test_require_config_path_fails_when_file_missing(tmp_path: Path) -> None:
    missing = tmp_path / "missing.yaml"

    with pytest.raises(ConfigurationError, match="configuration file not found"):
        require_config_path(config_arg=str(missing))


def test_require_config_path_returns_existing_file() -> None:
    path = require_config_path(config_arg="data/reporting.sample.yaml")

    assert path.is_file()
