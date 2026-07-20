"""Application configuration loading."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from integrations.azure_devops_reporting.errors import ConfigurationError
from integrations.azure_devops_reporting.models import DEFAULT_FILTER_TAG

DEFAULT_CLOSED_STATES: tuple[str, ...] = ("Closed", "Done")


@dataclass(frozen=True)
class AzureDevOpsOrganizationConfig:
    """Azure DevOps organization scope from YAML."""

    name: str
    filter_tag: str
    projects: list[str]


@dataclass(frozen=True)
class ReportingAppConfig:
    """Non-secret reporting application configuration."""

    organizations: list[AzureDevOpsOrganizationConfig]
    closed_states: tuple[str, ...]


def load_config(path: str | Path) -> ReportingAppConfig:
    """Load and validate reporting configuration from YAML."""
    config_path = Path(path)
    if not config_path.is_file():
        raise ConfigurationError(f"configuration file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)

    if not isinstance(raw, dict):
        raise ConfigurationError("configuration root must be a mapping")

    azure_devops = raw.get("azure_devops")
    if not isinstance(azure_devops, dict):
        raise ConfigurationError("azure_devops section is required")

    organizations_raw = azure_devops.get("organizations")
    if not isinstance(organizations_raw, list) or not organizations_raw:
        raise ConfigurationError("azure_devops.organizations must be a non-empty list")

    organizations: list[AzureDevOpsOrganizationConfig] = []
    for index, organization in enumerate(organizations_raw):
        if not isinstance(organization, dict):
            raise ConfigurationError(
                f"azure_devops.organizations[{index}] must be a mapping"
            )
        name = str(organization.get("name", "")).strip()
        if not name:
            raise ConfigurationError(
                f"azure_devops.organizations[{index}].name must not be blank"
            )
        filter_tag = organization.get("filter_tag", DEFAULT_FILTER_TAG)
        projects_raw = organization.get("projects", [])
        if projects_raw is None:
            projects_raw = []
        if not isinstance(projects_raw, list):
            raise ConfigurationError(
                f"azure_devops.organizations[{index}].projects must be a list"
            )
        projects = [str(project).strip() for project in projects_raw if str(project).strip()]
        organizations.append(
            AzureDevOpsOrganizationConfig(
                name=name,
                filter_tag=str(filter_tag),
                projects=projects,
            )
        )

    closed_states = _load_closed_states(raw.get("reporting"))

    return ReportingAppConfig(
        organizations=organizations,
        closed_states=closed_states,
    )


def _load_closed_states(reporting: object) -> tuple[str, ...]:
    """Parse reporting.closed_states with defaults per R1-FR-CFG-3."""
    if reporting is None:
        return DEFAULT_CLOSED_STATES
    if not isinstance(reporting, dict):
        raise ConfigurationError("reporting section must be a mapping")

    closed_states_raw = reporting.get("closed_states")
    if closed_states_raw is None:
        return DEFAULT_CLOSED_STATES
    if not isinstance(closed_states_raw, list) or not closed_states_raw:
        raise ConfigurationError("reporting.closed_states must be a non-empty list")

    closed_states = tuple(
        str(state).strip()
        for state in closed_states_raw
        if str(state).strip()
    )
    if not closed_states:
        raise ConfigurationError("reporting.closed_states must not be blank")
    return closed_states


def first_organization(config: ReportingAppConfig) -> AzureDevOpsOrganizationConfig:
    """Return the first configured organization."""
    return config.organizations[0]
