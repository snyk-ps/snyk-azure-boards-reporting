"""Tests for Elasticsearch bulk helpers."""

import json

import pytest

from integrations.elasticsearch.bulk import (
    build_bulk_payload,
    chunk_documents,
    document_id,
    parse_bulk_response,
)
from integrations.elasticsearch.errors import BulkDocumentError


def test_document_id_builds_stable_key() -> None:
    document = {
        "work_item": {
            "id": "12345",
            "organization": "torstencannell",
            "project": "snykDemoProject",
        }
    }

    assert document_id(document) == "torstencannell:snykDemoProject:12345"


def test_document_id_requires_work_item_fields() -> None:
    with pytest.raises(BulkDocumentError):
        document_id({"work_item": {"id": "1"}})


def test_build_bulk_payload_uses_update_with_doc_as_upsert() -> None:
    document = {
        "work_item": {
            "id": "1",
            "organization": "org",
            "project": "proj",
        },
        "tags": {"raw": "Snyk", "operator": ["Snyk"], "severity": None, "finding_type": None},
        "export": {"run_id": "run", "exported_at": "2026-07-20T21:00:00.000Z"},
    }

    payload = build_bulk_payload("snyk-ado-work-items", [document]).decode("utf-8")
    lines = payload.strip().splitlines()

    assert json.loads(lines[0]) == {
        "update": {"_index": "snyk-ado-work-items", "_id": "org:proj:1"}
    }
    assert json.loads(lines[1]) == {"doc": document, "doc_as_upsert": True}


def test_chunk_documents_splits_batches() -> None:
    documents = [{"n": index} for index in range(5)]

    batches = chunk_documents(documents, chunk_size=2)

    assert batches == [
        [{"n": 0}, {"n": 1}],
        [{"n": 2}, {"n": 3}],
        [{"n": 4}],
    ]


def test_parse_bulk_response_counts_success_and_failure() -> None:
    body = json.dumps(
        {
            "items": [
                {"update": {"_id": "a", "status": 200}},
                {
                    "update": {
                        "_id": "b",
                        "status": 400,
                        "error": {"type": "mapper_parsing_exception", "reason": "bad"},
                    }
                },
            ]
        }
    ).encode("utf-8")

    result = parse_bulk_response(body)

    assert result.succeeded == 1
    assert result.failed == 1
    assert result.errors[0].document_id == "b"
