"""Tests for Elasticsearch HTTP transport."""

import json

from integrations.elasticsearch.http import HttpResponse, UrllibTransport


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


def test_fake_transport_records_request() -> None:
    transport = FakeTransport(
        [HttpResponse(status=200, headers={}, body=b'{"ok":true}')]
    )

    response = transport.request(
        "POST",
        "https://example.es.cloud:9243/_bulk",
        headers={"Authorization": "ApiKey test"},
        body=b"{}\n",
    )

    assert response.status == 200
    method, url, headers, body = transport.requests[0]
    assert method == "POST"
    assert url.endswith("/_bulk")
    assert headers["Authorization"] == "ApiKey test"
    assert body == b"{}\n"


def test_urllib_transport_exists() -> None:
    assert UrllibTransport().request is not None
