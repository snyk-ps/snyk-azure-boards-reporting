"""Tests for export run orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from config.loader import AzureDevOpsOrganizationConfig, ElasticsearchConfig, ReportingAppConfig
from export.runner import run_export
from export.scope import ExportScopeTarget
from integrations.azure_devops_reporting.models import PARENT_TITLE_BATCH_FIELDS
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
        parent_titles_by_id: dict[int, str] | None = None,
    ) -> None:
        self.work_item_ids = work_item_ids or []
        self.items_by_batch = items_by_batch or {}
        self.parent_titles_by_id = parent_titles_by_id or {}
        self.batch_calls: list[tuple[tuple[int, ...], tuple[str, ...] | None]] = []

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
        *,
        fields: tuple[str, ...] | None = None,
    ) -> list[dict[str, Any]]:
        self.batch_calls.append((tuple(ids), fields))
        batch_key = tuple(ids)
        if batch_key in self.items_by_batch:
            return self.items_by_batch[batch_key]
        if fields == PARENT_TITLE_BATCH_FIELDS:
            return [
                {
                    "work_item_id": parent_id,
                    "work_item_status": "Done",
                    "fields": {
                        "System.Id": parent_id,
                        "System.Title": self.parent_titles_by_id[parent_id],
                    },
                }
                for parent_id in ids
                if parent_id in self.parent_titles_by_id
            ]
        return [_valid_item(item_id) for item_id in ids]


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
    assert es_client.bulk_calls[0][0]["work_item"]["url"] == (
        "https://dev.azure.com/test-org/snykDemoProject/_workitems/edit/1"
    )


def test_run_export_hydrates_shared_parent_story_once() -> None:
    item_one = _valid_item(1)
    item_one["fields"]["System.Parent"] = 500
    item_two = _valid_item(2)
    item_two["fields"]["System.Parent"] = 500
    ado_client = FakeAdoClient(
        work_item_ids=[1, 2],
        items_by_batch={(1, 2): [item_one, item_two]},
        parent_titles_by_id={500: "Shared story"},
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
    parent_batch_calls = [
        call for call in ado_client.batch_calls if call[1] == PARENT_TITLE_BATCH_FIELDS
    ]
    assert parent_batch_calls == [((500,), PARENT_TITLE_BATCH_FIELDS)]
    assert es_client.bulk_calls[0][0]["work_item"]["story_name"] == "Shared story"
    assert es_client.bulk_calls[0][1]["work_item"]["story_name"] == "Shared story"


def test_run_export_leaves_story_null_when_parent_lookup_missing() -> None:
    item = _valid_item(1)
    item["fields"]["System.Parent"] = 500
    ado_client = FakeAdoClient(
        work_item_ids=[1],
        items_by_batch={(1,): [item]},
        parent_titles_by_id={},
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

    assert result.export_outcome == "success"
    document = es_client.bulk_calls[0][0]
    assert document["work_item"]["story_name"] is None
    assert document["work_item"]["story_url"] is None


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
    bulk_failure = BulkItemFailure(
        document_id="test-org:snykDemoProject:1",
        error_type="mapper_parsing_exception",
        reason="failed to parse field",
    )
    es_client = FakeEsClient(
        bulk_result=BulkResult(succeeded=0, failed=1, errors=(bulk_failure,)),
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
    assert result.errors == (
        "test-org:snykDemoProject:1: mapper_parsing_exception: failed to parse field",
    )


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
