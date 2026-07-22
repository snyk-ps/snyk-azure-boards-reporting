"""Tests for export scope resolution."""

import pytest

from config.loader import AzureDevOpsOrganizationConfig, ElasticsearchConfig, ReportingAppConfig
from export.scope import CliScopeArgs, ExportScopeTarget, resolve_export_scope
from integrations.azure_devops_reporting.errors import ConfigurationError
from integrations.azure_devops_reporting.models import ProjectRecord


def _config(*, projects: list[str] | None = None) -> ReportingAppConfig:
    return ReportingAppConfig(
        organizations=[
            AzureDevOpsOrganizationConfig(
                name="test-org",
                filter_tag="Snyk",
                projects=projects if projects is not None else ["snykDemoProject"],
            )
        ],
        closed_states=("Done",),
        elasticsearch=ElasticsearchConfig(
            index_name="snyk-ado-work-items",
            auto_create_index=True,
        ),
    )


def _list_projects(_organization: str) -> list[ProjectRecord]:
    return [
        {"id": "1", "name": "alpha"},
        {"id": "2", "name": "beta"},
    ]


def test_resolve_export_scope_uses_full_config_project_allowlist() -> None:
    scope = resolve_export_scope(
        _config(projects=["snykDemoProject"]),
        CliScopeArgs(org=None, project=None, filter_tag=None),
        list_projects=_list_projects,
    )

    assert scope == [
        ExportScopeTarget(
            organization="test-org",
            project="snykDemoProject",
            filter_tag="Snyk",
        )
    ]


def test_resolve_export_scope_lists_all_projects_when_allowlist_empty() -> None:
    scope = resolve_export_scope(
        _config(projects=[]),
        CliScopeArgs(org=None, project=None, filter_tag=None),
        list_projects=_list_projects,
    )

    assert scope == [
        ExportScopeTarget("test-org", "alpha", "Snyk"),
        ExportScopeTarget("test-org", "beta", "Snyk"),
    ]


def test_resolve_export_scope_applies_cli_filter_tag_override() -> None:
    scope = resolve_export_scope(
        _config(),
        CliScopeArgs(org=None, project=None, filter_tag="CustomTag"),
        list_projects=_list_projects,
    )

    assert scope[0].filter_tag == "CustomTag"


def test_resolve_export_scope_narrows_to_single_project_from_config() -> None:
    scope = resolve_export_scope(
        _config(),
        CliScopeArgs(org=None, project="snykDemoProject", filter_tag=None),
        list_projects=_list_projects,
    )

    assert scope == [
        ExportScopeTarget("test-org", "snykDemoProject", "Snyk"),
    ]


def test_resolve_export_scope_narrows_to_explicit_org() -> None:
    scope = resolve_export_scope(
        _config(projects=[]),
        CliScopeArgs(org="test-org", project=None, filter_tag=None),
        list_projects=_list_projects,
    )

    assert scope == [
        ExportScopeTarget("test-org", "alpha", "Snyk"),
        ExportScopeTarget("test-org", "beta", "Snyk"),
    ]


def test_resolve_export_scope_rejects_unknown_org() -> None:
    with pytest.raises(ConfigurationError, match="not configured"):
        resolve_export_scope(
            _config(),
            CliScopeArgs(org="missing-org", project=None, filter_tag=None),
            list_projects=_list_projects,
        )
