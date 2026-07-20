"""Tests for configuration loading."""

from pathlib import Path

import pytest

from config.loader import load_config
from integrations.azure_devops_reporting.errors import ConfigurationError


def test_load_config_reads_sample_file() -> None:
    config_path = Path("data/reporting.sample.yaml")
    config = load_config(config_path)

    assert config.organizations[0].name == "torstencannell"
    assert config.organizations[0].filter_tag == "Snyk"
    assert config.organizations[0].projects == ["snykDemoProject"]


def test_load_config_rejects_empty_organizations(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text("azure_devops:\n  organizations: []\n", encoding="utf-8")

    with pytest.raises(ConfigurationError):
        load_config(config_path)


def test_load_config_rejects_blank_organization_name(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text(
        "azure_devops:\n  organizations:\n    - name: '   '\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError):
        load_config(config_path)
