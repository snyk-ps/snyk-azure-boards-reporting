"""Normalized models and helpers for Azure DevOps work items."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, TypedDict

from integrations.azure_devops_reporting.errors import InvalidFilterTagError

WORK_ITEM_BATCH_FIELDS: tuple[str, ...] = (
    "System.Id",
    "System.Title",
    "System.State",
    "System.Tags",
    "System.CreatedDate",
    "System.ChangedDate",
    "Microsoft.VSTS.Common.ClosedDate",
    "Microsoft.VSTS.Common.ResolvedDate",
    "System.TeamProject",
    "System.AreaPath",
)

MAX_BATCH_SIZE = 200
DEFAULT_FILTER_TAG = "Snyk"


class ProjectRecord(TypedDict):
    """Normalized Azure DevOps project."""

    id: str
    name: str


class NormalizedWorkItem(TypedDict):
    """Thin normalized work item record."""

    work_item_id: int
    work_item_status: str
    fields: dict[str, Any]


def sanitize_filter_tag(filter_tag: str) -> str:
    """Validate a WIQL filter tag value."""
    tag = filter_tag.strip()
    if not tag:
        raise InvalidFilterTagError("filter_tag must not be empty")
    if "'" in tag:
        raise InvalidFilterTagError("filter_tag must not contain single quotes")
    return tag


def build_wiql_query(filter_tag: str) -> str:
    """Build the WIQL query for tag-based work item discovery."""
    safe_tag = sanitize_filter_tag(filter_tag)
    return (
        "SELECT [System.Id] FROM WorkItems "
        f"WHERE [System.Tags] CONTAINS '{safe_tag}'"
    )


def normalize_work_item(api_item: dict[str, Any]) -> NormalizedWorkItem:
    """Map an Azure DevOps work item payload to a normalized record."""
    fields = api_item.get("fields") or {}
    work_item_id = api_item.get("id")
    if work_item_id is None:
        work_item_id = fields.get("System.Id")
    if work_item_id is None:
        raise ValueError("work item payload is missing id")

    status = fields.get("System.State")
    if status is None:
        raise ValueError("work item payload is missing System.State")

    return {
        "work_item_id": int(work_item_id),
        "work_item_status": str(status),
        "fields": dict(fields),
    }


def chunk_ids(ids: list[int], chunk_size: int = MAX_BATCH_SIZE) -> Iterator[list[int]]:
    """Yield work item ID lists in fixed-size chunks."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be at least 1")
    for index in range(0, len(ids), chunk_size):
        yield ids[index : index + chunk_size]
