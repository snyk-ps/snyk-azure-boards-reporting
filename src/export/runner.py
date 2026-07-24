"""Export run orchestration."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from config.loader import ReportingAppConfig
from export.scope import ExportScopeTarget
from integrations.azure_devops_reporting.client import AzureDevOpsReportingClient
from integrations.azure_devops_reporting.models import (
    PARENT_TITLE_BATCH_FIELDS,
    NormalizedWorkItem,
    chunk_ids,
)
from integrations.elasticsearch.client import ElasticsearchIngestClient
from integrations.elasticsearch.mappings import load_index_mappings
from observability.audit import ExportSummary
from reporting.document import build_reporting_document
from reporting.models import TransformContext, TransformError


@dataclass(frozen=True)
class ExportRunResult:
    """Outcome counters for one export run."""

    export_run_id: str
    export_outcome: str
    organizations_processed: int
    projects_processed: int
    work_items_discovered: int
    documents_written: int
    documents_failed: int
    errors: tuple[str, ...]


def run_export(
    *,
    config: ReportingAppConfig,
    scope: Iterable[ExportScopeTarget],
    ado_client: AzureDevOpsReportingClient,
    es_client: ElasticsearchIngestClient,
    export_run_id: str | None = None,
    exported_at: datetime | None = None,
) -> ExportRunResult:
    """Discover, transform, and bulk upsert work items for the given scope."""
    run_id = export_run_id or str(uuid4())
    export_time = exported_at or datetime.now(timezone.utc)
    scope_targets = list(scope)

    index_name = config.elasticsearch.index_name
    if config.elasticsearch.auto_create_index:
        es_client.ensure_index(index_name, mappings=load_index_mappings())

    work_items_discovered = 0
    documents_written = 0
    documents_failed = 0
    errors: list[str] = []

    for target in scope_targets:
        work_item_ids = ado_client.query_work_item_ids(
            target.organization,
            target.project,
            target.filter_tag,
        )
        work_items_discovered += len(work_item_ids)

        for batch_ids in chunk_ids(work_item_ids):
            normalized_items = ado_client.get_work_items_batch(
                target.organization,
                target.project,
                batch_ids,
            )
            parent_titles = _hydrate_parent_titles(
                ado_client,
                target.organization,
                target.project,
                normalized_items,
            )
            context = TransformContext(
                organization=target.organization,
                run_id=run_id,
                exported_at=export_time,
                closed_states=frozenset(config.closed_states),
                parent_titles=parent_titles,
            )
            documents = []
            for item in normalized_items:
                try:
                    documents.append(build_reporting_document(item, context=context))
                except TransformError as error:
                    documents_failed += 1
                    if len(errors) < 10:
                        errors.append(str(error))

            if not documents:
                continue

            bulk_result = es_client.bulk_upsert_documents(index_name, documents)
            documents_written += bulk_result.succeeded
            documents_failed += bulk_result.failed
            for bulk_error in bulk_result.errors:
                if len(errors) < 10:
                    errors.append(bulk_error)

    organizations_processed = len({target.organization for target in scope_targets})
    export_outcome = _resolve_outcome(
        documents_written=documents_written,
        documents_failed=documents_failed,
    )

    return ExportRunResult(
        export_run_id=run_id,
        export_outcome=export_outcome,
        organizations_processed=organizations_processed,
        projects_processed=len(scope_targets),
        work_items_discovered=work_items_discovered,
        documents_written=documents_written,
        documents_failed=documents_failed,
        errors=tuple(errors),
    )


def to_export_summary(
    result: ExportRunResult,
    *,
    export_duration_seconds: float,
) -> ExportSummary:
    """Convert a run result to an audit summary payload."""
    return ExportSummary(
        export_run_id=result.export_run_id,
        export_duration_seconds=export_duration_seconds,
        export_outcome=result.export_outcome,
        organizations_processed=result.organizations_processed,
        projects_processed=result.projects_processed,
        work_items_discovered=result.work_items_discovered,
        documents_written=result.documents_written,
        documents_failed=result.documents_failed,
        errors=result.errors,
    )


def _resolve_outcome(*, documents_written: int, documents_failed: int) -> str:
    if documents_failed == 0:
        return "success"
    if documents_written == 0:
        return "failure"
    return "partial"


def _hydrate_parent_titles(
    ado_client: AzureDevOpsReportingClient,
    organization: str,
    project: str,
    items: list[NormalizedWorkItem],
) -> dict[int, str]:
    """Batch-fetch parent work item titles referenced by System.Parent."""
    parent_ids = sorted(
        {
            int(item["fields"]["System.Parent"])
            for item in items
            if item["fields"].get("System.Parent") is not None
        }
    )
    if not parent_ids:
        return {}

    parent_titles: dict[int, str] = {}
    for batch_ids in chunk_ids(parent_ids):
        parent_items = ado_client.get_work_items_batch(
            organization,
            project,
            batch_ids,
            fields=PARENT_TITLE_BATCH_FIELDS,
        )
        for parent_item in parent_items:
            title = parent_item["fields"].get("System.Title")
            if title is not None:
                parent_titles[parent_item["work_item_id"]] = str(title)
    return parent_titles
