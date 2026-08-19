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
        self.requests: list[tuple[str, str, dict[str, str], bytes | None]] = []

    def request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str],
        body: bytes | None = None,
    ) -> HttpResponse:
        self.requests.append((method, url, headers, body))
        if not self.responses:
            raise AssertionError("no fake responses configured")
        return self.responses.pop(0)


def _client(responses: list[HttpResponse]) -> tuple[AzureDevOpsReportingClient, FakeTransport]:
    transport = FakeTransport(responses)
    http_client = AzureDevOpsHttpClient("example-pat", transport=transport)
    return AzureDevOpsReportingClient(http_client), transport


def test_list_projects_paginates() -> None:
    client, _transport = _client(
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
    client, _transport = _client(
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
    client, _transport = _client(
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
    client, _transport = _client([])

    with pytest.raises(BatchLimitError):
        client.get_work_items_batch("example-org", "demo", list(range(201)))


def test_get_work_items_batch_accepts_custom_fields() -> None:
    client, _transport = _client(
        [
            HttpResponse(
                status=200,
                headers={},
                body=json.dumps(
                    {
                        "value": [
                                {
                                    "id": 500,
                                    "fields": {
                                        "System.Id": 500,
                                        "System.Title": "Parent story",
                                        "System.State": "Done",
                                    },
                                }
                        ]
                    }
                ).encode("utf-8"),
            )
        ]
    )

    records = client.get_work_items_batch(
        "example-org",
        "demo",
        [500],
        fields=("System.Id", "System.Title"),
    )

    assert records[0]["fields"]["System.Title"] == "Parent story"


def test_get_work_items_batch_normalizes_items() -> None:
    client, _transport = _client(
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


def test_list_projects_encodes_organization_path_segment() -> None:
    client, transport = _client(
        [
            HttpResponse(
                status=200,
                headers={},
                body=json.dumps({"value": [], "continuationToken": None}).encode("utf-8"),
            )
        ]
    )

    client.list_projects("test org")

    _method, url, _headers, _body = transport.requests[0]
    assert "/test%20org/_apis/projects" in url


def test_query_work_item_ids_encodes_org_and_project_path_segments() -> None:
    client, transport = _client(
        [
            HttpResponse(
                status=200,
                headers={},
                body=json.dumps({"workItems": []}).encode("utf-8"),
            )
        ]
    )

    client.query_work_item_ids("test org", "Project Name", "Snyk")

    _method, url, _headers, _body = transport.requests[0]
    assert "/test%20org/Project%20Name/_apis/wit/wiql" in url


def test_get_work_items_batch_encodes_org_and_project_path_segments() -> None:
    client, transport = _client(
        [
            HttpResponse(
                status=200,
                headers={},
                body=json.dumps({"value": []}).encode("utf-8"),
            )
        ]
    )

    client.get_work_items_batch("test org", "Project Name", [1001])

    _method, url, _headers, _body = transport.requests[0]
    assert "/test%20org/Project%20Name/_apis/wit/workitemsbatch" in url
