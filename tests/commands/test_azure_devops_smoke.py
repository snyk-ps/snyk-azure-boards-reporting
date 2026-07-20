"""Tests for azure-devops-smoke command."""

import argparse
import json
from unittest.mock import patch

import pytest

from commands import azure_devops_smoke
from integrations.azure_devops_reporting.errors import MissingPatError
from main import build_parser


class FakeReportingClient:
    """Fake client for smoke command tests."""

    def __init__(self, *_args, **_kwargs) -> None:
        pass

    @classmethod
    def from_environ(cls) -> "FakeReportingClient":
        return cls()

    def query_work_item_ids(self, organization: str, project: str, filter_tag: str) -> list[int]:
        assert organization == "example-org"
        assert project == "demo"
        assert filter_tag == "Snyk"
        return [1001, 1002]

    def get_work_items_batch(self, organization: str, project: str, ids: list[int]):
        assert organization == "example-org"
        assert project == "demo"
        assert ids == [1001, 1002]
        return [
            {
                "work_item_id": 1001,
                "work_item_status": "Done",
                "fields": {"System.Id": 1001, "System.State": "Done"},
            },
            {
                "work_item_id": 1002,
                "work_item_status": "New",
                "fields": {"System.Id": 1002, "System.State": "New"},
            },
        ]


def test_run_wiql_smoke_writes_jsonl_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    args = build_parser().parse_args(
        [
            "azure-devops-smoke",
            "wiql",
            "--org",
            "example-org",
            "--project",
            "demo",
            "--filter-tag",
            "Snyk",
        ]
    )

    with patch.object(
        azure_devops_smoke.AzureDevOpsReportingClient,
        "from_environ",
        return_value=FakeReportingClient(),
    ):
        exit_code = azure_devops_smoke.run_wiql_smoke(args)

    captured = capsys.readouterr()
    lines = [json.loads(line) for line in captured.out.strip().splitlines()]

    assert exit_code == 0
    assert lines[0]["work_item_id"] == 1001
    assert lines[1]["work_item_status"] == "New"


def test_run_wiql_smoke_writes_jsonl_to_output_file(tmp_path) -> None:
    output_path = tmp_path / "smoke.jsonl"
    args = argparse.Namespace(
        org="example-org",
        project="demo",
        filter_tag="Snyk",
        config=None,
        output=str(output_path),
    )

    with patch.object(
        azure_devops_smoke.AzureDevOpsReportingClient,
        "from_environ",
        return_value=FakeReportingClient(),
    ):
        exit_code = azure_devops_smoke.run_wiql_smoke(args)

    lines = [json.loads(line) for line in output_path.read_text(encoding="utf-8").splitlines()]

    assert exit_code == 0
    assert lines[0]["work_item_id"] == 1001
    assert lines[1]["work_item_status"] == "New"


def test_run_wiql_smoke_returns_non_zero_on_missing_pat(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(
        org="example-org",
        project="demo",
        filter_tag="Snyk",
        config=None,
        output=None,
    )

    with patch.object(
        azure_devops_smoke.AzureDevOpsReportingClient,
        "from_environ",
        side_effect=MissingPatError("AZURE_DEVOPS_PAT is unset or empty"),
    ):
        exit_code = azure_devops_smoke.run_wiql_smoke(args)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "AZURE_DEVOPS_PAT" in captured.err
