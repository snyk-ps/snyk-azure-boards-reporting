"""Tests for export command."""

import json
from unittest.mock import patch

import pytest

from commands import export as export_command
from export.runner import ExportRunResult
from integrations.azure_devops_reporting.errors import MissingPatError
from integrations.elasticsearch.errors import MissingElasticsearchUrlError
from main import build_parser


class FakeAdoClient:
    """Fake ADO client for export command tests."""

    @classmethod
    def from_environ(cls, *, transport=None):
        return cls()

    def list_projects(self, organization: str):
        assert organization == "test-org"
        return [{"id": "1", "name": "snykDemoProject"}]

    def query_work_item_ids(self, organization: str, project: str, filter_tag: str):
        return []

    def get_work_items_batch(self, organization: str, project: str, ids: list[int]):
        return []


class FakeEsClient:
    """Fake ES client for export command tests."""

    def ensure_index(self, index_name: str, *, mappings: dict) -> None:
        pass

    def bulk_upsert_documents(self, index_name: str, documents, **_kwargs):
        from integrations.elasticsearch.models import BulkResult

        return BulkResult(succeeded=0, failed=0)


def test_run_export_command_emits_export_summary(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELASTICSEARCH_URL", "https://example.es.cloud:9243")
    monkeypatch.setenv("ELASTICSEARCH_API_KEY", "test-key")
    args = build_parser().parse_args(
        ["export", "--config", "data/reporting.sample.yaml", "--project", "snykDemoProject"]
    )

    fake_result = ExportRunResult(
        export_run_id="run-123",
        export_outcome="success",
        organizations_processed=1,
        projects_processed=1,
        work_items_discovered=0,
        documents_written=0,
        documents_failed=0,
        errors=(),
    )

    with patch.object(
        export_command.AzureDevOpsReportingClient,
        "from_environ",
        return_value=FakeAdoClient(),
    ), patch.object(
        export_command,
        "build_ingest_client_from_env",
        return_value=FakeEsClient(),
    ), patch.object(
        export_command,
        "run_export",
        return_value=fake_result,
    ):
        exit_code = export_command.run_export_command(args)

    captured = capsys.readouterr()
    summary_lines = [
        json.loads(line)
        for line in captured.out.splitlines()
        if json.loads(line)["record"]["event"] == "export_summary"
    ]

    assert exit_code == 0
    assert summary_lines[-1]["record"]["export_outcome"] == "success"
    assert summary_lines[-1]["record"]["work_items_discovered"] == 0


def test_run_export_command_returns_non_zero_on_missing_pat(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELASTICSEARCH_URL", "https://example.es.cloud:9243")
    args = build_parser().parse_args(
        ["export", "--config", "data/reporting.sample.yaml", "--project", "snykDemoProject"]
    )

    with patch.object(
        export_command.AzureDevOpsReportingClient,
        "from_environ",
        side_effect=MissingPatError("AZURE_DEVOPS_PAT is unset or empty"),
    ):
        exit_code = export_command.run_export_command(args)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "AZURE_DEVOPS_PAT" in captured.err


def test_run_export_command_returns_non_zero_on_missing_es_url(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ELASTICSEARCH_URL", raising=False)
    args = build_parser().parse_args(
        ["export", "--config", "data/reporting.sample.yaml", "--project", "snykDemoProject"]
    )

    with patch.object(
        export_command,
        "read_elasticsearch_url_from_environ",
        side_effect=MissingElasticsearchUrlError("ELASTICSEARCH_URL is unset or empty"),
    ):
        exit_code = export_command.run_export_command(args)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "ELASTICSEARCH_URL" in captured.err
