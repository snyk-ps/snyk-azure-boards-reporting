"""Azure DevOps reporting client for read-only WIT operations."""

from __future__ import annotations

from typing import Any

from integrations.azure_devops_reporting.auth import read_pat_from_environ
from integrations.azure_devops_reporting.errors import BatchLimitError
from integrations.azure_devops_reporting.http import AzureDevOpsHttpClient, DEFAULT_ORIGIN
from integrations.azure_devops_reporting.models import (
    MAX_BATCH_SIZE,
    WORK_ITEM_BATCH_FIELDS,
    NormalizedWorkItem,
    ProjectRecord,
    build_wiql_query,
    normalize_work_item,
)


class AzureDevOpsReportingClient:
    """Read-only Azure DevOps WIT client for reporting."""

    def __init__(
        self,
        http_client: AzureDevOpsHttpClient,
    ) -> None:
        self._http = http_client

    @classmethod
    def from_environ(
        cls,
        *,
        origin: str = DEFAULT_ORIGIN,
        transport: Any | None = None,
    ) -> AzureDevOpsReportingClient:
        """Create a client using AZURE_DEVOPS_PAT from the environment."""
        pat = read_pat_from_environ()
        http_client = AzureDevOpsHttpClient(pat, origin=origin, transport=transport)
        return cls(http_client)

    def list_projects(self, organization: str) -> list[ProjectRecord]:
        """List all team projects for an organization."""
        org = _require_non_blank(organization, "organization")
        projects: list[ProjectRecord] = []
        continuation_token: str | None = None

        while True:
            query: dict[str, str] = {"$top": "100"}
            if continuation_token:
                query["continuationToken"] = continuation_token

            payload = self._http.request_json(
                "GET",
                f"/{org}/_apis/projects",
                query=query,
            )
            for project in payload.get("value", []):
                projects.append(
                    {
                        "id": str(project["id"]),
                        "name": str(project["name"]),
                    }
                )

            continuation_token = payload.get("continuationToken")
            if not continuation_token:
                break

        return projects

    def query_work_item_ids(
        self,
        organization: str,
        project: str,
        filter_tag: str,
    ) -> list[int]:
        """Run WIQL and return matching work item IDs."""
        org = _require_non_blank(organization, "organization")
        proj = _require_non_blank(project, "project")
        wiql = build_wiql_query(filter_tag)

        payload = self._http.request_json(
            "POST",
            f"/{org}/{proj}/_apis/wit/wiql",
            body={"query": wiql},
        )
        work_items = payload.get("workItems") or []
        return [int(item["id"]) for item in work_items if "id" in item]

    def get_work_items_batch(
        self,
        organization: str,
        project: str,
        ids: list[int],
        *,
        fields: tuple[str, ...] | None = None,
    ) -> list[NormalizedWorkItem]:
        """Hydrate up to 200 work items and return normalized records."""
        org = _require_non_blank(organization, "organization")
        proj = _require_non_blank(project, "project")
        if len(ids) > MAX_BATCH_SIZE:
            raise BatchLimitError(
                f"batch request accepts at most {MAX_BATCH_SIZE} IDs; got {len(ids)}"
            )

        if not ids:
            return []

        batch_fields = fields or WORK_ITEM_BATCH_FIELDS
        payload = self._http.request_json(
            "POST",
            f"/{org}/{proj}/_apis/wit/workitemsbatch",
            body={
                "ids": ids,
                "fields": list(batch_fields),
            },
        )
        normalized: list[NormalizedWorkItem] = []
        for item in payload.get("value", []):
            normalized.append(normalize_work_item(item))
        return normalized


def _require_non_blank(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be blank")
    return normalized
