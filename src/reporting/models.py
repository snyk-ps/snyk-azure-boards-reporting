"""Types for reporting document transformation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, TypedDict


class TransformError(ValueError):
    """Raised when a work item cannot be transformed into a reporting document."""


@dataclass(frozen=True)
class TransformContext:
    """Export-scoped values required to build a reporting document."""

    organization: str
    run_id: str
    exported_at: datetime
    closed_states: frozenset[str]
    parent_titles: dict[int, str] = field(default_factory=dict)


class TagsParsed(TypedDict):
    """Parsed System.Tags values."""

    raw: str
    operator: list[str]
    severity: str | None
    finding_type: str | None


class WorkItemDocument(TypedDict):
    """work_item object in a reporting document."""

    id: str
    organization: str
    project: str
    title: str
    status: str
    area_path: str
    assignee: str | None
    url: str
    story_name: str | None
    story_url: str | None
    created_at: str
    changed_at: str
    closed_at: str | None
    days_to_close: float | None


class TagsDocument(TypedDict):
    """tags object in a reporting document."""

    raw: str
    operator: list[str]
    severity: str | None
    finding_type: str | None


class ExportDocument(TypedDict):
    """export object in a reporting document."""

    run_id: str
    exported_at: str


class ReportingDocument(TypedDict):
    """Normalized reporting document without optional snyk enrich."""

    work_item: WorkItemDocument
    tags: TagsDocument
    export: ExportDocument


ReportingDocumentDict = dict[str, Any]
