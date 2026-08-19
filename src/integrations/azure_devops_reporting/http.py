"""HTTP transport and Azure DevOps REST helpers."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

from integrations.azure_devops_reporting.auth import build_authorization_header
from integrations.azure_devops_reporting.errors import (
    AuthenticationError,
    AzureDevOpsHttpError,
)

API_VERSION = "7.1"
DEFAULT_ORIGIN = "https://dev.azure.com"
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 1.0
RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})


def encode_ado_path_segment(value: str) -> str:
    """Percent-encode an Azure DevOps URL path segment."""
    return urllib.parse.quote(value, safe="")


@dataclass(frozen=True)
class HttpResponse:
    """HTTP response returned by a transport."""

    status: int
    headers: dict[str, str]
    body: bytes


class HttpTransport(Protocol):
    """Protocol for injectable HTTP transports."""

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None = None,
    ) -> HttpResponse:
        """Execute an HTTP request."""


class UrllibTransport:
    """Default stdlib HTTP transport."""

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None = None,
    ) -> HttpResponse:
        """Execute an HTTP request using urllib."""
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request) as response:
                response_headers = {
                    key.lower(): value for key, value in response.headers.items()
                }
                return HttpResponse(
                    status=response.status,
                    headers=response_headers,
                    body=response.read(),
                )
        except urllib.error.HTTPError as error:
            response_headers = {
                key.lower(): value for key, value in error.headers.items()
            }
            return HttpResponse(
                status=error.code,
                headers=response_headers,
                body=error.read(),
            )


class AzureDevOpsHttpClient:
    """Low-level Azure DevOps HTTP client with bounded retries."""

    def __init__(
        self,
        pat: str,
        *,
        origin: str = DEFAULT_ORIGIN,
        transport: HttpTransport | None = None,
    ) -> None:
        self._authorization = build_authorization_header(pat)
        self._origin = origin.rstrip("/")
        self._transport = transport or UrllibTransport()

    def request_json(
        self,
        method: str,
        path: str,
        *,
        query: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Issue a JSON request and return a parsed JSON object."""
        url = self._build_url(path, query)
        payload = None if body is None else json.dumps(body).encode("utf-8")
        headers = {
            "Authorization": self._authorization,
            "Accept": "application/json",
        }
        if payload is not None:
            headers["Content-Type"] = "application/json"

        response = self._request_with_retries(method, url, headers=headers, body=payload)
        if not response.body:
            return {}
        return json.loads(response.body.decode("utf-8"))

    def safe_target(self, path: str) -> str:
        """Return a host + path pattern safe for logs."""
        return f"{self._origin}{path}"

    def _build_url(self, path: str, query: dict[str, str] | None) -> str:
        normalized_path = path if path.startswith("/") else f"/{path}"
        params = {"api-version": API_VERSION}
        if query:
            params.update(query)
        query_string = urllib.parse.urlencode(params)
        return f"{self._origin}{normalized_path}?{query_string}"

    def _request_with_retries(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None,
    ) -> HttpResponse:
        safe_target = self.safe_target(urllib.parse.urlparse(url).path)
        last_response: HttpResponse | None = None

        for attempt in range(MAX_RETRIES):
            response = self._transport.request(
                method,
                url,
                headers=headers,
                body=body,
            )
            if response.status in (401, 403):
                raise AuthenticationError(
                    f"Azure DevOps authentication failed with HTTP {response.status} "
                    f"for {safe_target}"
                )
            if response.status < 400:
                return response
            if response.status not in RETRYABLE_STATUS_CODES:
                raise AzureDevOpsHttpError(
                    f"Azure DevOps request failed with HTTP {response.status} "
                    f"for {safe_target}",
                    status=response.status,
                    safe_target=safe_target,
                )
            last_response = response
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF_SECONDS * (2**attempt))

        status = last_response.status if last_response else 0
        raise AzureDevOpsHttpError(
            f"Azure DevOps request failed after retries with HTTP {status} "
            f"for {safe_target}",
            status=status,
            safe_target=safe_target,
        )
