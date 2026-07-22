"""Export scope resolution from configuration and CLI overrides."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from config.loader import AzureDevOpsOrganizationConfig, ReportingAppConfig
from integrations.azure_devops_reporting.errors import ConfigurationError
from integrations.azure_devops_reporting.models import DEFAULT_FILTER_TAG, ProjectRecord


@dataclass(frozen=True)
class ExportScopeTarget:
    """One organization/project/filter tag tuple to export."""

    organization: str
    project: str
    filter_tag: str


@dataclass(frozen=True)
class CliScopeArgs:
    """CLI scope overrides for export."""

    org: str | None
    project: str | None
    filter_tag: str | None


def resolve_export_scope(
    config: ReportingAppConfig,
    cli: CliScopeArgs,
    *,
    list_projects: Callable[[str], list[ProjectRecord]],
) -> list[ExportScopeTarget]:
    """Resolve export targets from config and optional CLI narrowing."""
    if cli.org or cli.project:
        return _resolve_narrowed_scope(config, cli, list_projects=list_projects)

    return _resolve_full_config_scope(config, cli, list_projects=list_projects)


def _resolve_full_config_scope(
    config: ReportingAppConfig,
    cli: CliScopeArgs,
    *,
    list_projects: Callable[[str], list[ProjectRecord]],
) -> list[ExportScopeTarget]:
    targets: list[ExportScopeTarget] = []
    for organization in config.organizations:
        filter_tag = cli.filter_tag or organization.filter_tag or DEFAULT_FILTER_TAG
        project_names = _project_names_for_org(
            organization,
            list_projects=list_projects,
        )
        for project in project_names:
            targets.append(
                ExportScopeTarget(
                    organization=organization.name,
                    project=project,
                    filter_tag=filter_tag,
                )
            )
    return targets


def _resolve_narrowed_scope(
    config: ReportingAppConfig,
    cli: CliScopeArgs,
    *,
    list_projects: Callable[[str], list[ProjectRecord]],
) -> list[ExportScopeTarget]:
    organization_name = cli.org
    organization_config = None
    if organization_name:
        organization_config = _find_organization(config, organization_name)
        if organization_config is None:
            raise ConfigurationError(
                f"organization {organization_name!r} is not configured in reporting YAML"
            )
    else:
        organization_config = config.organizations[0]
        organization_name = organization_config.name

    filter_tag = (
        cli.filter_tag
        or (organization_config.filter_tag if organization_config else None)
        or DEFAULT_FILTER_TAG
    )

    if cli.project:
        return [
            ExportScopeTarget(
                organization=organization_name,
                project=cli.project,
                filter_tag=filter_tag,
            )
        ]

    project_names = _project_names_for_org(
        organization_config,
        list_projects=list_projects,
        organization_name=organization_name,
    )
    return [
        ExportScopeTarget(
            organization=organization_name,
            project=project,
            filter_tag=filter_tag,
        )
        for project in project_names
    ]


def _project_names_for_org(
    organization: AzureDevOpsOrganizationConfig | None,
    *,
    list_projects: Callable[[str], list[ProjectRecord]],
    organization_name: str | None = None,
) -> list[str]:
    org_name = organization_name or (organization.name if organization else "")
    if organization and organization.projects:
        return list(organization.projects)

    return [project["name"] for project in list_projects(org_name)]


def _find_organization(
    config: ReportingAppConfig,
    organization_name: str,
) -> AzureDevOpsOrganizationConfig | None:
    for organization in config.organizations:
        if organization.name == organization_name:
            return organization
    return None
