"""Tests for reporting document transformation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from reporting.document import build_reporting_document, build_reporting_documents
from reporting.models import TransformContext, TransformError

SMOKE_JSONL = Path("data/smoke-wiql.jsonl")
FIXED_EXPORTED_AT = datetime(2026, 7, 20, 21, 0, 0, tzinfo=timezone.utc)
FIXED_RUN_ID = "550e8400-e29b-41d4-a716-446655440000"


def _context(*, closed_states: frozenset[str] | None = None) -> TransformContext:
    return TransformContext(
        organization="test-org",
        run_id=FIXED_RUN_ID,
        exported_at=FIXED_EXPORTED_AT,
        closed_states=closed_states or frozenset({"Done"}),
    )


def _load_smoke_item(work_item_id: int) -> dict:
    for line in SMOKE_JSONL.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record["work_item_id"] == work_item_id:
            return record
    raise KeyError(work_item_id)


def test_build_reporting_document_golden_item_1_operator_only() -> None:
    document = build_reporting_document(
        _load_smoke_item(1),
        context=_context(),
    )

    assert document == {
        "work_item": {
            "id": "1",
            "organization": "test-org",
            "project": "snykDemoProject",
            "title": "NoSQL Injection",
            "status": "To Do",
            "area_path": "snykDemoProject",
            "created_at": "2026-03-31T18:46:23.540Z",
            "changed_at": "2026-03-31T18:46:23.540Z",
            "closed_at": None,
            "days_to_close": None,
        },
        "tags": {
            "raw": "Snyk",
            "operator": ["Snyk"],
            "severity": None,
            "finding_type": None,
        },
        "export": {
            "run_id": FIXED_RUN_ID,
            "exported_at": "2026-07-20T21:00:00.000Z",
        },
    }


def test_build_reporting_document_golden_item_9_closed_with_days() -> None:
    document = build_reporting_document(
        _load_smoke_item(9),
        context=_context(),
    )

    assert document["work_item"]["id"] == "9"
    assert document["work_item"]["status"] == "Done"
    assert document["work_item"]["closed_at"] == "2026-04-21T02:17:19.270Z"
    assert document["work_item"]["days_to_close"] == 0.0
    assert document["tags"]["operator"] == ["Snyk"]


def test_build_reporting_document_golden_item_113_managed_tags_active() -> None:
    document = build_reporting_document(
        _load_smoke_item(113),
        context=_context(),
    )

    assert document["work_item"]["status"] == "To Do"
    assert document["work_item"]["closed_at"] is None
    assert document["work_item"]["days_to_close"] is None
    assert document["tags"] == {
        "raw": "Snyk; Snyk-Severity-critical; Snyk-Type-open_source; TestOverride",
        "operator": ["Snyk", "TestOverride"],
        "severity": "critical",
        "finding_type": "open_source",
    }


def test_build_reporting_document_omits_snyk_object() -> None:
    document = build_reporting_document(
        _load_smoke_item(1),
        context=_context(),
    )

    assert "snyk" not in document


def test_build_reporting_document_is_stable_for_same_input() -> None:
    item = _load_smoke_item(113)
    context = _context()

    first = build_reporting_document(item, context=context)
    second = build_reporting_document(item, context=context)

    assert first == second


def test_build_reporting_document_raises_for_missing_required_field() -> None:
    item = _load_smoke_item(1)
    del item["fields"]["System.Title"]

    with pytest.raises(TransformError, match="missing required field System.Title"):
        build_reporting_document(item, context=_context())


def test_build_reporting_documents_transforms_multiple_items() -> None:
    items = [_load_smoke_item(1), _load_smoke_item(9)]
    context = _context()

    documents = build_reporting_documents(items, context=context)

    assert len(documents) == 2
    assert documents[0]["work_item"]["id"] == "1"
    assert documents[1]["work_item"]["id"] == "9"


@pytest.mark.parametrize("line", SMOKE_JSONL.read_text(encoding="utf-8").splitlines())
def test_smoke_jsonl_records_transform_without_error(line: str) -> None:
    if not line.strip():
        pytest.skip("empty line")
    item = json.loads(line)
    document = build_reporting_document(item, context=_context())

    assert set(document.keys()) == {"work_item", "tags", "export"}
    assert set(document["work_item"].keys()) == {
        "id",
        "organization",
        "project",
        "title",
        "status",
        "area_path",
        "created_at",
        "changed_at",
        "closed_at",
        "days_to_close",
    }
    assert set(document["tags"].keys()) == {
        "raw",
        "operator",
        "severity",
        "finding_type",
    }
    assert set(document["export"].keys()) == {"run_id", "exported_at"}
