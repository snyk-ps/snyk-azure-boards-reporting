"""Elasticsearch ingest result models."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BulkItemFailure:
    """One failed bulk line."""

    document_id: str
    error_type: str
    reason: str


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
