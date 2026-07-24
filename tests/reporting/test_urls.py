"""Tests for Azure DevOps work item URL construction."""

from reporting.urls import build_ado_work_item_url


def test_build_ado_work_item_url_encodes_path_segments() -> None:
    url = build_ado_work_item_url("test org", "demo project", 42)

    assert url == "https://dev.azure.com/test%20org/demo%20project/_workitems/edit/42"


def test_build_ado_work_item_url_accepts_string_id() -> None:
    url = build_ado_work_item_url("org", "proj", "1001")

    assert url == "https://dev.azure.com/org/proj/_workitems/edit/1001"
