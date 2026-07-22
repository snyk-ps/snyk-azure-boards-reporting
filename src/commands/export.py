"""Export command for Azure DevOps work items to Elasticsearch."""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timezone
from uuid import uuid4

from config.loader import load_config
from config.paths import require_config_path
from export.runner import run_export, to_export_summary
from export.scope import CliScopeArgs, resolve_export_scope
from integrations.azure_devops_reporting.client import AzureDevOpsReportingClient
from integrations.azure_devops_reporting.errors import (
    AuthenticationError,
    AzureDevOpsHttpError,
    BatchLimitError,
    ConfigurationError,
    InvalidFilterTagError,
    MissingPatError,
)
from integrations.azure_devops_reporting.http import UrllibTransport as AdoUrllibTransport
from integrations.elasticsearch.auth import read_elasticsearch_url_from_environ
from integrations.elasticsearch.client import build_ingest_client_from_env
from integrations.elasticsearch.errors import (
    AuthenticationError as ElasticsearchAuthenticationError,
    ElasticsearchError,
    ElasticsearchHttpError,
    MissingElasticsearchUrlError,
)
from integrations.elasticsearch.http import UrllibTransport as EsUrllibTransport
from observability.audit import AuditingTransport, emit_export_summary


def register_subcommand(subparsers: argparse._SubParsersAction) -> None:
    """Register the export command."""
    export_parser = subparsers.add_parser(
        "export",
        help="Export Snyk-tagged work items to Elasticsearch",
    )
    export_parser.add_argument("--config", help="Path to reporting YAML configuration")
    export_parser.add_argument("--org", help="Azure DevOps organization name")
    export_parser.add_argument("--project", help="Azure DevOps project name")
    export_parser.add_argument(
        "--filter-tag",
        help="WIQL tag filter override",
    )
    export_parser.set_defaults(handler=run_export_command)


def run_export_command(args: argparse.Namespace) -> int:
    """Run one export and emit NDJSON audit records on stdout."""
    export_run_id = str(uuid4())
    started = time.monotonic()

    try:
        config_path = require_config_path(config_arg=args.config)
        config = load_config(config_path)
        read_elasticsearch_url_from_environ()

        output = sys.stdout
        ado_client = AzureDevOpsReportingClient.from_environ(
            transport=AuditingTransport(
                AdoUrllibTransport(),
                integration="azure_devops",
                export_run_id=export_run_id,
                output=output,
            ),
        )
        es_client = build_ingest_client_from_env(
            transport=AuditingTransport(
                EsUrllibTransport(),
                integration="elasticsearch",
                export_run_id=export_run_id,
                output=output,
            ),
        )

        scope = resolve_export_scope(
            config,
            CliScopeArgs(
                org=args.org,
                project=args.project,
                filter_tag=args.filter_tag,
            ),
            list_projects=ado_client.list_projects,
        )

        result = run_export(
            config=config,
            scope=scope,
            ado_client=ado_client,
            es_client=es_client,
            export_run_id=export_run_id,
            exported_at=datetime.now(timezone.utc),
        )

        emit_export_summary(
            to_export_summary(
                result,
                export_duration_seconds=time.monotonic() - started,
            ),
            output=output,
        )

        return 0 if result.export_outcome == "success" else 1
    except (
        AuthenticationError,
        AzureDevOpsHttpError,
        BatchLimitError,
        ConfigurationError,
        ElasticsearchAuthenticationError,
        ElasticsearchError,
        ElasticsearchHttpError,
        InvalidFilterTagError,
        MissingElasticsearchUrlError,
        MissingPatError,
        ValueError,
    ) as error:
        print(str(error), file=sys.stderr)
        return 1
