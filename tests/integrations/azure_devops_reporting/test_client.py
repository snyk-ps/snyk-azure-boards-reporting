"""Tests for Azure DevOps reporting client."""

import json

import pytest

from integrations.azure_devops_reporting.client import AzureDevOpsReportingClient
from integrations.azure_devops_reporting.errors import BatchLimitError
from integrations.azure_devops_reporting.http import AzureDevOpsHttpClient, HttpResponse


class FakeTransport:
    """Return configured HTTP responses in order."""

    def __init__(self, responses: list[HttpResponse]) -> None:
        self.responses = list(responses)

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None = None,
    ) -> HttpResponse:
        if not self.responses:
            raise AssertionError("no fake responses configured")
        return self.responses.pop(0)


def _client(responses: list[HttpResponse]) -> AzureDevOpsReportingClient:
    http_client = AzureDevOpsHttpClient("example-pat", transport=FakeTransport(responses))
    return AzureDevOpsReportingClient(http_client)


def test_list_projects_paginates() -> None:
    client = _client(
        [
            HttpResponse(
                status=200,
                headers={},
                body=json.dumps(
                    {
                        "value": [{"id": "1", "name": "proj-a"}],
                        "continuationToken": "next",
                    }
                ).encode("utf-8"),
            ),
            HttpResponse(
                status=200,
                headers={},
                body=json.dumps(
                    {
                        "value": [{"id": "2", "name": "proj-b"}],
                        "continuationToken": None,
                    }
                ).encode("utf-8"),
            ),
        ]
    )

    projects = client.list_projects("example-org")

    assert projects == [
        {"id": "1", "name": "proj-a"},
        {"id": "2", "name": "proj-b"},
    ]


def test_query_work_item_ids_returns_matching_ids() -> None:
    client = _client(
        [
            HttpResponse(
                status=200,
                headers={},
                body=json.dumps(
                    {"workItems": [{"id": 1001}, {"id": 1002}]}
                ).encode("utf-8"),
            )
        ]
    )

    ids = client.query_work_item_ids("example-org", "demo", "Snyk")

    assert ids == [1001, 1002]


def test_query_work_item_ids_returns_empty_list() -> None:
    client = _client(
        [
            HttpResponse(
                status=200,
                headers={},
                body=json.dumps({"workItems": []}).encode("utf-8"),
            )
        ]
    )

    assert client.query_work_item_ids("example-org", "demo", "Snyk") == []


def test_get_work_items_batch_enforces_limit() -> None:
    client = _client([])

    with pytest.raises(BatchLimitError):
        client.get_work_items_batch("example-org", "demo", list(range(201)))


def test_get_work_items_batch_normalizes_items() -> None:
    client = _client(
        [
            HttpResponse(
                status=200,
                headers={},
                body=json.dumps(
                    {
                        "value": [
                            {
                                "id": 1001,
                                "fields": {
                                    "System.Id": 1001,
                                    "System.State": "Done",
                                    "System.Title": "Example",
                                },
                            }
                        ]
                    }
                ).encode("utf-8"),
            )
        ]
    )

    records = client.get_work_items_batch("example-org", "demo", [1001])

    assert records == [
        {
            "work_item_id": 1001,
            "work_item_status": "Done",
            "fields": {
                "System.Id": 1001,
                "System.State": "Done",
                "System.Title": "Example",
            },
        }
    ]
