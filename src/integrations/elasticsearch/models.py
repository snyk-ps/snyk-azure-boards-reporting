"""Elasticsearch ingest result models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BulkItemFailure:
    """One failed bulk line."""

    document_id: str
    error_type: str
    reason: str


def format_bulk_item_failure(failure: BulkItemFailure) -> str:
    """Format a bulk item failure for export summary error logs."""
    return f"{failure.document_id}: {failure.error_type}: {failure.reason}"


@dataclass(frozen=True)
class BulkResult:
    """Aggregated bulk upsert outcome."""

    succeeded: int
    failed: int
    errors: tuple[BulkItemFailure, ...] = field(default_factory=tuple)

    @property
    def total(self) -> int:
        """Return the number of documents attempted."""
        return self.succeeded + self.failed
