"""NDJSON audit logging for export runs."""

from __future__ import annotations

import json
import sys
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol, TextIO

from integrations.azure_devops_reporting.http import HttpResponse as AdoHttpResponse
from integrations.elasticsearch.http import HttpResponse as EsHttpResponse


class HttpTransport(Protocol):
    """Minimal HTTP transport protocol for audit wrapping."""

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None = None,
    ) -> AdoHttpResponse | EsHttpResponse:
        """Execute an HTTP request."""


def format_timestamp(value: datetime) -> str:
    """Format a UTC timestamp as RFC 3339 with Z suffix."""
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def emit_ndjson_record(record: dict[str, Any], *, output: TextIO | None = None) -> None:
    """Write one NDJSON record to output."""
    stream = output or sys.stdout
    stream.write(json.dumps(record, sort_keys=True))
    stream.write("\n")


def emit_integration_http(
    *,
    export_run_id: str,
    integration: str,
    method: str,
    http_status: int,
    duration_ms: float,
    safe_target: str,
    output: TextIO | None = None,
) -> None:
    """Emit one integration HTTP audit record."""
    emit_ndjson_record(
        {
            "timestamp": format_timestamp(datetime.now(timezone.utc)),
            "level": "INFO",
            "logger": "integration_audit",
            "record": {
                "event": "integration_http",
                "export_run_id": export_run_id,
                "integration": integration,
                "method": method,
                "http_status": http_status,
                "duration_ms": round(duration_ms, 3),
                "safe_target": safe_target,
            },
        },
        output=output,
    )


@dataclass(frozen=True)
class ExportSummary:
    """Counts emitted once per export run."""

    export_run_id: str
    export_duration_seconds: float
    export_outcome: str
    organizations_processed: int
    projects_processed: int
    work_items_discovered: int
    documents_written: int
    documents_failed: int
    errors: tuple[str, ...] = ()


def emit_export_summary(summary: ExportSummary, *, output: TextIO | None = None) -> None:
    """Emit the export run summary audit record."""
    record: dict[str, Any] = {
        "timestamp": format_timestamp(datetime.now(timezone.utc)),
        "level": "INFO",
        "logger": "integration_audit",
        "record": {
            "event": "export_summary",
            "export_run_id": summary.export_run_id,
            "export_duration_seconds": round(summary.export_duration_seconds, 3),
            "export_outcome": summary.export_outcome,
            "organizations_processed": summary.organizations_processed,
            "projects_processed": summary.projects_processed,
            "work_items_discovered": summary.work_items_discovered,
            "documents_written": summary.documents_written,
            "documents_failed": summary.documents_failed,
        },
    }
    if summary.errors:
        record["record"]["errors"] = list(summary.errors)
    emit_ndjson_record(record, output=output)


def safe_target_from_url(url: str) -> str:
    """Return a host + path safe for audit logs."""
    parsed = urllib.parse.urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


class AuditingTransport:
    """HTTP transport wrapper that emits integration audit records."""

    def __init__(
        self,
        inner: HttpTransport,
        *,
        integration: str,
        export_run_id: str,
        output: TextIO | None = None,
    ) -> None:
        self._inner = inner
        self._integration = integration
        self._export_run_id = export_run_id
        self._output = output

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None = None,
    ) -> AdoHttpResponse | EsHttpResponse:
        """Execute a request and emit an audit record."""
        started = time.monotonic()
        response = self._inner.request(
            method,
            url,
            headers=headers,
            body=body,
        )
        emit_integration_http(
            export_run_id=self._export_run_id,
            integration=self._integration,
            method=method,
            http_status=response.status,
            duration_ms=(time.monotonic() - started) * 1000,
            safe_target=safe_target_from_url(url),
            output=self._output,
        )
        return response
