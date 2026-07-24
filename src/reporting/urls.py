"""Construct Azure DevOps work item URLs for reporting documents."""

from __future__ import annotations

from urllib.parse import quote


def build_ado_work_item_url(
    organization: str,
    project: str,
    work_item_id: int | str,
) -> str:
    """Build a dev.azure.com edit URL for a work item."""
    org_segment = quote(organization, safe="")
    project_segment = quote(project, safe="")
    return (
        f"https://dev.azure.com/{org_segment}/{project_segment}"
        f"/_workitems/edit/{work_item_id}"
    )
