"""Build reporting documents from normalized Azure DevOps work items."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from integrations.azure_devops_reporting.models import NormalizedWorkItem

from reporting.closure import resolve_closed_at
from reporting.dates import compute_days_to_close, format_ado_datetime, parse_ado_datetime
from reporting.models import ReportingDocumentDict, TransformContext, TransformError
from reporting.tags import parse_system_tags
from reporting.urls import build_ado_work_item_url

_REQUIRED_FIELDS = (
    "System.State",
    "System.CreatedDate",
    "System.ChangedDate",
    "System.TeamProject",
    "System.Title",
)


def _parse_assignee_display_name(fields: dict[str, Any]) -> str | None:
    assigned_to = fields.get("System.AssignedTo")
    if not isinstance(assigned_to, dict):
        return None
    display_name = assigned_to.get("displayName")
    if display_name is None or str(display_name).strip() == "":
        return None
    return str(display_name)


def _resolve_story_fields(
    fields: dict[str, Any],
    *,
    context: TransformContext,
    project: str,
) -> tuple[str | None, str | None]:
    parent_id = fields.get("System.Parent")
    if parent_id is None:
        return None, None

    parent_key = int(parent_id)
    story_name = context.parent_titles.get(parent_key)
    if story_name is None:
        return None, None

    return story_name, build_ado_work_item_url(context.organization, project, parent_key)


def build_reporting_document(
    item: NormalizedWorkItem,
    *,
    context: TransformContext,
) -> ReportingDocumentDict:
    """Map a normalized work item to a reporting document."""
    fields = item["fields"]
    work_item_id = item["work_item_id"]

    for field_name in _REQUIRED_FIELDS:
        if fields.get(field_name) is None:
            raise TransformError(
                f"work item {work_item_id} is missing required field {field_name}"
            )

    created_at = parse_ado_datetime(str(fields["System.CreatedDate"]))
    changed_at = parse_ado_datetime(str(fields["System.ChangedDate"]))
    closed_at_dt = resolve_closed_at(fields, context.closed_states)

    tags = parse_system_tags(
        str(fields["System.Tags"]) if fields.get("System.Tags") is not None else None
    )
    project = str(fields["System.TeamProject"])
    story_name, story_url = _resolve_story_fields(
        fields,
        context=context,
        project=project,
    )

    return {
        "work_item": {
            "id": str(work_item_id),
            "organization": context.organization,
            "project": project,
            "title": str(fields["System.Title"]),
            "status": str(fields["System.State"]),
            "area_path": str(fields.get("System.AreaPath") or ""),
            "assignee": _parse_assignee_display_name(fields),
            "url": build_ado_work_item_url(context.organization, project, work_item_id),
            "story_name": story_name,
            "story_url": story_url,
            "created_at": format_ado_datetime(created_at),
            "changed_at": format_ado_datetime(changed_at),
            "closed_at": format_ado_datetime(closed_at_dt) if closed_at_dt else None,
            "days_to_close": compute_days_to_close(created_at, closed_at_dt),
        },
        "tags": tags,
        "export": {
            "run_id": context.run_id,
            "exported_at": format_ado_datetime(context.exported_at),
        },
    }


def build_reporting_documents(
    items: Iterable[NormalizedWorkItem],
    *,
    context: TransformContext,
) -> list[ReportingDocumentDict]:
    """Transform multiple normalized work items."""
    return [build_reporting_document(item, context=context) for item in items]
