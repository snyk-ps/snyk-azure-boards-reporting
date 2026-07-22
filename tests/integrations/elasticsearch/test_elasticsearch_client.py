"""Tests for Elasticsearch ingest client."""

import json

import pytest

from integrations.elasticsearch.client import ElasticsearchIngestClient, build_ingest_client_from_env
from integrations.elasticsearch.errors import AuthenticationError
from integrations.elasticsearch.http import HttpResponse


class FakeTransport:
    """Record requests and return configured responses."""

    def __init__(self, responses: list[HttpResponse]) -> None:
        self.responses = list(responses)
        self.requests: list[tuple[str, str, dict[str, str], bytes | None]] = []

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None = None,
    ) -> HttpResponse:
        self.requests.append((method, url, headers, body))
        if not self.responses:
            raise AssertionError("no fake responses configured")
        return self.responses.pop(0)


def _sample_document() -> dict:
    return {
        "work_item": {
            "id": "12345",
            "organization": "torstencannell",
            "project": "snykDemoProject",
            "title": "Example",
            "status": "Done",
        },
        "tags": {
            "raw": "Snyk",
            "operator": ["Snyk"],
            "severity": None,
            "finding_type": None,
        },
        "export": {
            "run_id": "run",
            "exported_at": "2026-07-20T21:00:00.000Z",
        },
    }


def test_bulk_upsert_documents_posts_to_bulk_endpoint() -> None:
    transport = FakeTransport(
        [
            HttpResponse(
                status=200,
                headers={},
                body=json.dumps(
                    {"items": [{"update": {"_id": "torstencannell:snykDemoProject:12345", "status": 200}}]}
                ).encode("utf-8"),
            )
        ]
    )
    client = ElasticsearchIngestClient(
        url="https://example.es.cloud:9243",
        authorization="ApiKey test",
        transport=transport,
    )

    result = client.bulk_upsert_documents("snyk-ado-work-items", [_sample_document()])

    method, url, headers, body = transport.requests[0]
    assert method == "POST"
    assert url.endswith("/_bulk")
    assert headers["Content-Type"] == "application/x-ndjson"
    assert b'"doc_as_upsert":true' in body
    assert result.succeeded == 1
    assert result.failed == 0


def test_bulk_upsert_documents_raises_on_auth_failure() -> None:
    transport = FakeTransport([HttpResponse(status=401, headers={}, body=b"")])
    client = ElasticsearchIngestClient(
        url="https://example.es.cloud:9243",
        authorization="ApiKey test",
        transport=transport,
    )

    with pytest.raises(AuthenticationError):
        client.bulk_upsert_documents("snyk-ado-work-items", [_sample_document()])


def test_bulk_upsert_documents_reports_partial_item_failure() -> None:
    transport = FakeTransport(
        [
            HttpResponse(
                status=200,
                headers={},
                body=json.dumps(
                    {
                        "items": [
                            {"update": {"_id": "ok", "status": 200}},
                            {
                                "update": {
                                    "_id": "bad",
                                    "status": 400,
                                    "error": {"type": "validation", "reason": "invalid"},
                                }
                            },
                        ]
                    }
                ).encode("utf-8"),
            )
        ]
    )
    client = ElasticsearchIngestClient(
        url="https://example.es.cloud:9243",
        authorization="ApiKey test",
        transport=transport,
    )

    result = client.bulk_upsert_documents(
        "snyk-ado-work-items",
        [_sample_document(), _sample_document()],
    )

    assert result.succeeded == 1
    assert result.failed == 1


def test_ensure_index_creates_index_when_missing() -> None:
    transport = FakeTransport(
        [
            HttpResponse(status=404, headers={}, body=b""),
            HttpResponse(status=200, headers={}, body=b'{"acknowledged":true}'),
        ]
    )
    client = ElasticsearchIngestClient(
        url="https://example.es.cloud:9243",
        authorization="ApiKey test",
        transport=transport,
    )

    client.ensure_index(
        "snyk-ado-work-items",
        mappings={"work_item": {"properties": {"id": {"type": "keyword"}}}},
    )

    head_method, head_url, _, _ = transport.requests[0]
    put_method, put_url, _, put_body = transport.requests[1]
    assert head_method == "HEAD"
    assert head_url.endswith("/snyk-ado-work-items")
    assert put_method == "PUT"
    assert put_url.endswith("/snyk-ado-work-items")
    assert b'"mappings"' in put_body


def test_ensure_index_skips_create_when_index_exists() -> None:
    transport = FakeTransport([HttpResponse(status=200, headers={}, body=b"")])
    client = ElasticsearchIngestClient(
        url="https://example.es.cloud:9243",
        authorization="ApiKey test",
        transport=transport,
    )

    client.ensure_index("snyk-ado-work-items", mappings={"work_item": {"properties": {}}})

    assert len(transport.requests) == 1


def test_build_ingest_client_from_env_requires_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ELASTICSEARCH_URL", raising=False)

    with pytest.raises(Exception):
        build_ingest_client_from_env()
