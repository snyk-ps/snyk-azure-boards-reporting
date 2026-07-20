"""Tests for output command."""

import argparse
import io
import json
import sys

import pytest

from commands import output


def test_run_output_pretty_prints_jsonl(capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    args = argparse.Namespace(file=None, pretty=True)
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(json.dumps({"work_item_id": 1001, "work_item_status": "Done", "fields": {}}) + "\n"),
    )

    exit_code = output.run_output(args)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert '"work_item_id": 1001' in captured.out
