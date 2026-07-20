"""Azure DevOps smoke-test commands."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import TextIO

from config.loader import first_organization, load_config
from integrations.azure_devops_reporting.client import AzureDevOpsReportingClient
from integrations.azure_devops_reporting.errors import (
    AuthenticationError,
    BatchLimitError,
    ConfigurationError,
    InvalidFilterTagError,
    MissingPatError,
)
from integrations.azure_devops_reporting.http import AzureDevOpsHttpError
from integrations.azure_devops_reporting.models import DEFAULT_FILTER_TAG, chunk_ids


def register_subcommand(subparsers: argparse._SubParsersAction) -> None:
    """Register the azure-devops-smoke command tree."""
    smoke_parser = subparsers.add_parser(
        "azure-devops-smoke",
        help="Run read-only Azure DevOps smoke checks",
    )
    smoke_subparsers = smoke_parser.add_subparsers(dest="smoke_command", required=True)

    wiql_parser = smoke_subparsers.add_parser(
        "wiql",
        help="Run WIQL discovery and batch hydration for one project",
    )
    wiql_parser.add_argument("--org", help="Azure DevOps organization name")
    wiql_parser.add_argument("--project", help="Azure DevOps project name")
    wiql_parser.add_argument(
        "--filter-tag",
        help=f"WIQL tag filter (default: {DEFAULT_FILTER_TAG})",
    )
    wiql_parser.add_argument(
        "--config",
        help="Path to reporting YAML configuration",
    )
    wiql_parser.add_argument(
        "--output",
        "-o",
        help="Write normalized JSONL to this file instead of stdout",
    )
    wiql_parser.set_defaults(handler=run_wiql_smoke)


def run_wiql_smoke(args: argparse.Namespace) -> int:
    """Execute WIQL smoke and emit normalized JSONL to stdout or a file."""
    try:
        organization, project, filter_tag = _resolve_smoke_scope(args)
        client = AzureDevOpsReportingClient.from_environ()
        work_item_ids = client.query_work_item_ids(
            organization,
            project,
            filter_tag,
        )
        output_path = Path(args.output) if args.output else None
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8") as output_file:
                _emit_records(
                    client,
                    organization,
                    project,
                    work_item_ids,
                    output_file,
                )
        else:
            _emit_records(
                client,
                organization,
                project,
                work_item_ids,
                sys.stdout,
            )
        return 0
    except (
        AuthenticationError,
        AzureDevOpsHttpError,
        BatchLimitError,
        ConfigurationError,
        InvalidFilterTagError,
        MissingPatError,
        ValueError,
    ) as error:
        print(str(error), file=sys.stderr)
        return 1


def _emit_records(
    client: AzureDevOpsReportingClient,
    organization: str,
    project: str,
    work_item_ids: list[int],
    output: TextIO,
) -> None:
    """Write normalized work item records as JSONL."""
    for batch_ids in chunk_ids(work_item_ids):
        for record in client.get_work_items_batch(organization, project, batch_ids):
            output.write(json.dumps(record, sort_keys=True))
            output.write("\n")


def _resolve_smoke_scope(args: argparse.Namespace) -> tuple[str, str, str]:
    organization = args.org
    project = args.project
    filter_tag = args.filter_tag

    if args.config:
        config = load_config(args.config)
        org_config = first_organization(config)
        organization = organization or org_config.name
        filter_tag = filter_tag or org_config.filter_tag
        if not project and org_config.projects:
            project = org_config.projects[0]

    if not organization:
        raise ConfigurationError("--org is required when no config supplies an organization")
    if not project:
        raise ConfigurationError("--project is required")
    if not filter_tag:
        filter_tag = DEFAULT_FILTER_TAG

    return organization, project, filter_tag
