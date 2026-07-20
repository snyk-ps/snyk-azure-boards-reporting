"""Tests for Azure DevOps HTTP client behavior."""

import json

import pytest

from integrations.azure_devops_reporting.errors import AuthenticationError, AzureDevOpsHttpError
from integrations.azure_devops_reporting.http import AzureDevOpsHttpClient, HttpResponse


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


def test_request_json_includes_api_version_and_authorization() -> None:
    transport = FakeTransport(
        [
            HttpResponse(
                status=200,
                headers={},
                body=json.dumps({"value": []}).encode("utf-8"),
            )
        ]
    )
    client = AzureDevOpsHttpClient("example-pat", transport=transport)

    payload = client.request_json("GET", "/org/_apis/projects")

    assert payload == {"value": []}
    method, url, headers, _body = transport.requests[0]
    assert method == "GET"
    assert "api-version=7.1" in url
    assert headers["Authorization"].startswith("Basic ")


def test_request_json_raises_authentication_error_on_401() -> None:
    transport = FakeTransport([HttpResponse(status=401, headers={}, body=b"")])
    client = AzureDevOpsHttpClient("example-pat", transport=transport)

    with pytest.raises(AuthenticationError):
        client.request_json("GET", "/org/_apis/projects")


def test_request_json_retries_transient_500(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("integrations.azure_devops_reporting.http.time.sleep", lambda _seconds: None)
    transport = FakeTransport(
        [
            HttpResponse(status=500, headers={}, body=b""),
            HttpResponse(
                status=200,
                headers={},
                body=json.dumps({"ok": True}).encode("utf-8"),
            ),
        ]
    )
    client = AzureDevOpsHttpClient("example-pat", transport=transport)

    payload = client.request_json("GET", "/org/_apis/projects")

    assert payload == {"ok": True}
    assert len(transport.requests) == 2


def test_request_json_raises_after_retry_exhaustion(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("integrations.azure_devops_reporting.http.time.sleep", lambda _seconds: None)
    transport = FakeTransport(
        [
            HttpResponse(status=503, headers={}, body=b""),
            HttpResponse(status=503, headers={}, body=b""),
            HttpResponse(status=503, headers={}, body=b""),
        ]
    )
    client = AzureDevOpsHttpClient("example-pat", transport=transport)

    with pytest.raises(AzureDevOpsHttpError) as exc_info:
        client.request_json("GET", "/org/_apis/projects")

    assert exc_info.value.status == 503
    assert "dev.azure.com" in exc_info.value.safe_target
