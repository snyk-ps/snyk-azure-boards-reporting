"""Tests for elasticsearch-smoke command."""

import json
from unittest.mock import patch

import pytest

from commands import elasticsearch_smoke
from integrations.elasticsearch.errors import MissingElasticsearchUrlError
from integrations.elasticsearch.models import BulkResult
from main import build_parser


class FakeIngestClient:
    """Fake ingest client for smoke command tests."""

    def __init__(self) -> None:
        self.ensure_index_called = False
        self.index_name: str | None = None

    def ensure_index(self, index_name: str, *, mappings: dict) -> None:
        self.ensure_index_called = True
        self.index_name = index_name
        assert mappings

    def bulk_upsert_documents(self, index_name: str, documents: list[dict], **_kwargs):
        assert index_name == "snyk-ado-work-items"
        assert len(documents) == 1
        return BulkResult(succeeded=1, failed=0)


def test_run_index_one_smoke_writes_summary_to_stdout(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELASTICSEARCH_URL", "https://example.es.cloud:9243")
    monkeypatch.setenv("ELASTICSEARCH_API_KEY", "test-key")
    args = build_parser().parse_args(["elasticsearch-smoke", "index-one"])

    fake_client = FakeIngestClient()
    with patch.object(
        elasticsearch_smoke,
        "build_ingest_client_from_env",
        return_value=fake_client,
    ):
        exit_code = elasticsearch_smoke.run_index_one_smoke(args)

    captured = capsys.readouterr()
    summary = json.loads(captured.out)

    assert exit_code == 0
    assert summary["_id"] == "torstencannell:snykDemoProject:12345"
    assert summary["index_name"] == "snyk-ado-work-items"
    assert summary["succeeded"] == 1
    assert fake_client.ensure_index_called is True


def test_run_index_one_smoke_uses_jsonl_input(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELASTICSEARCH_URL", "https://example.es.cloud:9243")
    monkeypatch.setenv("ELASTICSEARCH_API_KEY", "test-key")
    args = build_parser().parse_args(
        [
            "elasticsearch-smoke",
            "index-one",
            "--input",
            "data/reporting-documents.jsonl",
            "--line",
            "1",
        ]
    )

    fake_client = FakeIngestClient()
    with patch.object(
        elasticsearch_smoke,
        "build_ingest_client_from_env",
        return_value=fake_client,
    ):
        exit_code = elasticsearch_smoke.run_index_one_smoke(args)

    captured = capsys.readouterr()
    summary = json.loads(captured.out)

    assert exit_code == 0
    assert summary["_id"] == "torstencannell:snykDemoProject:1"


def test_run_index_one_smoke_returns_non_zero_on_missing_url(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("ELASTICSEARCH_URL", raising=False)
    args = build_parser().parse_args(["elasticsearch-smoke", "index-one"])

    with patch.object(
        elasticsearch_smoke,
        "read_elasticsearch_url_from_environ",
        side_effect=MissingElasticsearchUrlError("ELASTICSEARCH_URL is unset or empty"),
    ):
        exit_code = elasticsearch_smoke.run_index_one_smoke(args)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "ELASTICSEARCH_URL" in captured.err
