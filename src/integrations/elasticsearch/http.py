"""HTTP transport for Elasticsearch requests."""

from __future__ import annotations

import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol


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
