"""Tests for export run orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from config.loader import AzureDevOpsOrganizationConfig, ElasticsearchConfig, ReportingAppConfig
from export.runner import run_export
from export.scope import ExportScopeTarget
from integrations.elasticsearch.models import BulkResult


FIXED_EXPORTED_AT = datetime(2026, 7, 21, 3, 0, 0, tzinfo=timezone.utc)
FIXED_RUN_ID = "550e8400-e29b-41d4-a716-446655440000"


def _valid_item(work_item_id: int = 1) -> dict[str, Any]:
    return {
        "work_item_id": work_item_id,
        "work_item_status": "To Do",
        "fields": {
            "System.Id": work_item_id,
            "System.State": "To Do",
            "System.CreatedDate": "2026-03-31T18:46:23.54Z",
            "System.ChangedDate": "2026-03-31T18:46:23.54Z",
            "System.TeamProject": "snykDemoProject",
            "System.Title": "Example finding",
            "System.Tags": "Snyk",
            "System.AreaPath": "snykDemoProject",
        },
    }


class FakeAdoClient:
    """Fake Azure DevOps client for export tests."""

    def __init__(
        self,
        *,
        work_item_ids: list[int] | None = None,
        items_by_batch: dict[tuple[int, ...], list[dict[str, Any]]] | None = None,
    ) -> None:
        self.work_item_ids = work_item_ids or []
        self.items_by_batch = items_by_batch or {}

    def query_work_item_ids(
        self,
        organization: str,
        project: str,
        filter_tag: str,
    ) -> list[int]:
        assert organization == "test-org"
        assert project == "snykDemoProject"
        assert filter_tag == "Snyk"
        return list(self.work_item_ids)

    def get_work_items_batch(
        self,
        organization: str,
        project: str,
        ids: list[int],
    ) -> list[dict[str, Any]]:
        return self.items_by_batch.get(tuple(ids), [_valid_item(item_id) for item_id in ids])


class FakeEsClient:
    """Fake Elasticsearch client for export tests."""

    def __init__(self, *, bulk_result: BulkResult | None = None) -> None:
        self.ensure_index_called = False
        self.bulk_calls: list[list[dict[str, Any]]] = []
        self.bulk_result = bulk_result or BulkResult(succeeded=0, failed=0)

    def ensure_index(self, index_name: str, *, mappings: dict[str, Any]) -> None:
        self.ensure_index_called = True
        assert index_name == "snyk-ado-work-items"
        assert mappings

    def bulk_upsert_documents(self, index_name: str, documents, **_kwargs) -> BulkResult:
        batch = list(documents)
        self.bulk_calls.append(batch)
        if self.bulk_result.failed == 0:
            return BulkResult(succeeded=len(batch), failed=0)
        return BulkResult(
            succeeded=self.bulk_result.succeeded,
            failed=self.bulk_result.failed,
            errors=self.bulk_result.errors,
        )


def _config(*, auto_create_index: bool = True) -> ReportingAppConfig:
    return ReportingAppConfig(
        organizations=[
            AzureDevOpsOrganizationConfig(
                name="test-org",
                filter_tag="Snyk",
                projects=["snykDemoProject"],
            )
        ],
        closed_states=("Done",),
        elasticsearch=ElasticsearchConfig(
            index_name="snyk-ado-work-items",
            auto_create_index=auto_create_index,
        ),
    )


def _scope() -> list[ExportScopeTarget]:
    return [
        ExportScopeTarget(
            organization="test-org",
            project="snykDemoProject",
            filter_tag="Snyk",
        )
    ]


def test_run_export_happy_path() -> None:
    ado_client = FakeAdoClient(
        work_item_ids=[1, 2],
        items_by_batch={(1, 2): [_valid_item(1), _valid_item(2)]},
    )
    es_client = FakeEsClient(bulk_result=BulkResult(succeeded=2, failed=0))

    result = run_export(
        config=_config(),
        scope=_scope(),
        ado_client=ado_client,
        es_client=es_client,
        export_run_id=FIXED_RUN_ID,
        exported_at=FIXED_EXPORTED_AT,
    )

    assert result.export_outcome == "success"
    assert result.work_items_discovered == 2
    assert result.documents_written == 2
    assert result.documents_failed == 0
    assert es_client.ensure_index_called is True
    assert len(es_client.bulk_calls) == 1
    assert es_client.bulk_calls[0][0]["export"]["run_id"] == FIXED_RUN_ID


def test_run_export_handles_empty_wiql_results() -> None:
    ado_client = FakeAdoClient(work_item_ids=[])
    es_client = FakeEsClient()

    result = run_export(
        config=_config(),
        scope=_scope(),
        ado_client=ado_client,
        es_client=es_client,
        export_run_id=FIXED_RUN_ID,
        exported_at=FIXED_EXPORTED_AT,
    )

    assert result.export_outcome == "success"
    assert result.work_items_discovered == 0
    assert result.documents_written == 0
    assert es_client.bulk_calls == []


def test_run_export_counts_transform_failures_as_partial() -> None:
    invalid_item = _valid_item(3)
    invalid_item["fields"].pop("System.Title")
    ado_client = FakeAdoClient(
        work_item_ids=[1, 3],
        items_by_batch={(1, 3): [_valid_item(1), invalid_item]},
    )
    es_client = FakeEsClient(bulk_result=BulkResult(succeeded=1, failed=0))

    result = run_export(
        config=_config(),
        scope=_scope(),
        ado_client=ado_client,
        es_client=es_client,
        export_run_id=FIXED_RUN_ID,
        exported_at=FIXED_EXPORTED_AT,
    )

    assert result.export_outcome == "partial"
    assert result.documents_written == 1
    assert result.documents_failed == 1
    assert result.errors


def test_run_export_counts_bulk_failures_as_partial() -> None:
    ado_client = FakeAdoClient(
        work_item_ids=[1],
        items_by_batch={(1,): [_valid_item(1)]},
    )
    es_client = FakeEsClient(
        bulk_result=BulkResult(succeeded=0, failed=1, errors=("bulk line failed",)),
    )

    result = run_export(
        config=_config(),
        scope=_scope(),
        ado_client=ado_client,
        es_client=es_client,
        export_run_id=FIXED_RUN_ID,
        exported_at=FIXED_EXPORTED_AT,
    )

    assert result.export_outcome == "failure"
    assert result.documents_written == 0
    assert result.documents_failed == 1


def test_run_export_skips_ensure_index_when_auto_create_disabled() -> None:
    ado_client = FakeAdoClient(work_item_ids=[])
    es_client = FakeEsClient()

    run_export(
        config=_config(auto_create_index=False),
        scope=_scope(),
        ado_client=ado_client,
        es_client=es_client,
        export_run_id=FIXED_RUN_ID,
        exported_at=FIXED_EXPORTED_AT,
    )

    assert es_client.ensure_index_called is False
