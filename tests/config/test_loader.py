"""Tests for configuration loading."""

from pathlib import Path

import pytest

from config.loader import DEFAULT_CLOSED_STATES, DEFAULT_INDEX_NAME, load_config
from integrations.azure_devops_reporting.errors import ConfigurationError


def test_load_config_reads_sample_file() -> None:
    config_path = Path("data/reporting.sample.yaml")
    config = load_config(config_path)

    assert config.organizations[0].name == "test-org"
    assert config.organizations[0].filter_tag == "Snyk"
    assert config.organizations[0].projects == ["snykDemoProject"]
    assert config.closed_states == ("Done",)
    assert config.elasticsearch.index_name == "snyk-ado-work-items"
    assert config.elasticsearch.auto_create_index is True


def test_load_config_defaults_closed_states_when_reporting_section_absent(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "minimal.yaml"
    config_path.write_text(
        "azure_devops:\n  organizations:\n    - name: example\n",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.closed_states == DEFAULT_CLOSED_STATES
    assert config.elasticsearch.index_name == DEFAULT_INDEX_NAME
    assert config.elasticsearch.auto_create_index is True


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


def test_load_config_rejects_empty_closed_states(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text(
        "azure_devops:\n  organizations:\n    - name: example\n"
        "reporting:\n  closed_states: []\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError):
        load_config(config_path)


def test_load_config_rejects_invalid_elasticsearch_section(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text(
        "azure_devops:\n  organizations:\n    - name: example\n"
        "elasticsearch: not-a-mapping\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError):
        load_config(config_path)


def test_load_config_rejects_non_boolean_auto_create_index(tmp_path: Path) -> None:
    config_path = tmp_path / "invalid.yaml"
    config_path.write_text(
        "azure_devops:\n  organizations:\n    - name: example\n"
        "elasticsearch:\n  auto_create_index: maybe\n",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError):
        load_config(config_path)
