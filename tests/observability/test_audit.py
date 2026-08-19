"""Tests for export audit logging."""

import io
import json

from export.runner import to_export_summary
from observability.audit import (
    AuditingTransport,
    ExportSummary,
    emit_export_summary,
    emit_integration_http,
)
from integrations.azure_devops_reporting.http import HttpResponse
from integrations.elasticsearch.models import BulkItemFailure


class FakeTransport:
    """Minimal transport for audit wrapper tests."""

    def request(self, method, url, *, headers, body=None):
        return HttpResponse(status=200, headers={}, body=b"{}")


def test_emit_integration_http_writes_ndjson_record() -> None:
    output = io.StringIO()

    emit_integration_http(
        export_run_id="run-1",
        integration="azure_devops",
        method="POST",
        http_status=200,
        duration_ms=12.5,
        safe_target="https://dev.azure.com/example/_apis/wit/wiql",
        output=output,
    )

    record = json.loads(output.getvalue())
    assert record["logger"] == "integration_audit"
    assert record["record"]["event"] == "integration_http"
    assert record["record"]["export_run_id"] == "run-1"


def test_emit_export_summary_writes_required_fields() -> None:
    output = io.StringIO()

    emit_export_summary(
        ExportSummary(
            export_run_id="run-1",
            export_duration_seconds=3.2,
            export_outcome="partial",
            organizations_processed=1,
            projects_processed=1,
            work_items_discovered=10,
            documents_written=9,
            documents_failed=1,
            errors=("bulk line failed",),
        ),
        output=output,
    )

    record = json.loads(output.getvalue())["record"]
    assert record["event"] == "export_summary"
    assert record["export_outcome"] == "partial"
    assert record["work_items_discovered"] == 10
    assert record["documents_written"] == 9
    assert record["documents_failed"] == 1
    assert record["errors"] == ["bulk line failed"]


def test_emit_export_summary_serializes_bulk_failure_strings_from_run_result() -> None:
    bulk_failure = BulkItemFailure(
        document_id="test-org:snykDemoProject:1",
        error_type="mapper_parsing_exception",
        reason="failed to parse field",
    )
    summary = to_export_summary(
        type(
            "ExportRunResult",
            (),
            {
                "export_run_id": "run-1",
                "export_outcome": "failure",
                "organizations_processed": 1,
                "projects_processed": 1,
                "work_items_discovered": 1,
                "documents_written": 0,
                "documents_failed": 1,
                "errors": (
                    f"{bulk_failure.document_id}: {bulk_failure.error_type}: {bulk_failure.reason}",
                ),
            },
        )(),
        export_duration_seconds=1.5,
    )
    output = io.StringIO()

    emit_export_summary(summary, output=output)

    record = json.loads(output.getvalue())["record"]
    assert record["export_outcome"] == "failure"
    assert record["errors"] == [
        "test-org:snykDemoProject:1: mapper_parsing_exception: failed to parse field",
    ]


def test_auditing_transport_emits_integration_http_record() -> None:
    output = io.StringIO()
    transport = AuditingTransport(
        FakeTransport(),
        integration="elasticsearch",
        export_run_id="run-1",
        output=output,
    )

    transport.request(
        "POST",
        "https://example.es.cloud:9243/_bulk",
        headers={},
    )

    record = json.loads(output.getvalue())["record"]
    assert record["integration"] == "elasticsearch"
    assert record["method"] == "POST"
    assert record["http_status"] == 200


def test_resolve_outcome_values_via_export_summary() -> None:
    for outcome, written, failed in (
        ("success", 5, 0),
        ("partial", 4, 1),
        ("failure", 0, 2),
    ):
        output = io.StringIO()
        emit_export_summary(
            ExportSummary(
                export_run_id="run-1",
                export_duration_seconds=1.0,
                export_outcome=outcome,
                organizations_processed=1,
                projects_processed=1,
                work_items_discovered=written + failed,
                documents_written=written,
                documents_failed=failed,
            ),
            output=output,
        )
        record = json.loads(output.getvalue())["record"]
        assert record["export_outcome"] == outcome
