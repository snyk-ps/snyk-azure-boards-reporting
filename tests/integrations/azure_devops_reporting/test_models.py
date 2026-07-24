"""Tests for Azure DevOps reporting models."""

import pytest

from integrations.azure_devops_reporting.errors import InvalidFilterTagError
from integrations.azure_devops_reporting.models import (
    WORK_ITEM_BATCH_FIELDS,
    build_wiql_query,
    chunk_ids,
    normalize_work_item,
)


def test_build_wiql_query_uses_filter_tag() -> None:
    query = build_wiql_query("Snyk")
    assert "CONTAINS 'Snyk'" in query


def test_build_wiql_query_rejects_single_quotes() -> None:
    with pytest.raises(InvalidFilterTagError):
        build_wiql_query("Snyk' OR 1=1 --")


def test_normalize_work_item_maps_required_fields() -> None:
    record = normalize_work_item(
        {
            "id": 1001,
            "fields": {
                "System.Id": 1001,
                "System.State": "Done",
                "System.Title": "Example",
            },
        }
    )
    assert record["work_item_id"] == 1001
    assert record["work_item_status"] == "Done"
    assert record["fields"]["System.Title"] == "Example"


def test_normalize_work_item_allows_missing_closed_date() -> None:
    record = normalize_work_item(
        {
            "id": 1002,
            "fields": {
                "System.Id": 1002,
                "System.State": "New",
            },
        }
    )
    assert "Microsoft.VSTS.Common.ClosedDate" not in record["fields"]


def test_work_item_batch_fields_include_assignee_and_parent() -> None:
    assert "System.AssignedTo" in WORK_ITEM_BATCH_FIELDS
    assert "System.Parent" in WORK_ITEM_BATCH_FIELDS


def test_normalize_work_item_preserves_assignee_and_parent() -> None:
    record = normalize_work_item(
        {
            "id": 1003,
            "fields": {
                "System.Id": 1003,
                "System.State": "To Do",
                "System.AssignedTo": {"displayName": "Jane Doe"},
                "System.Parent": 500,
            },
        }
    )
    assert record["fields"]["System.AssignedTo"]["displayName"] == "Jane Doe"
    assert record["fields"]["System.Parent"] == 500


def test_normalize_work_item_allows_missing_assignee_and_parent() -> None:
    record = normalize_work_item(
        {
            "id": 1004,
            "fields": {
                "System.Id": 1004,
                "System.State": "To Do",
            },
        }
    )
    assert "System.AssignedTo" not in record["fields"]
    assert "System.Parent" not in record["fields"]


def test_chunk_ids_splits_into_two_hundred_item_batches() -> None:
    ids = list(range(1, 451))
    chunks = list(chunk_ids(ids))
    assert len(chunks) == 3
    assert len(chunks[0]) == 200
    assert len(chunks[1]) == 200
    assert len(chunks[2]) == 50
