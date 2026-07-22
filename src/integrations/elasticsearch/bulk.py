"""Elasticsearch bulk request helpers."""

from __future__ import annotations

import json
from typing import Any, Iterable

from integrations.elasticsearch.errors import BulkDocumentError
from integrations.elasticsearch.models import BulkItemFailure, BulkResult


def document_id(document: dict[str, Any]) -> str:
    """Derive the stable Elasticsearch document id for a reporting document."""
    work_item = document.get("work_item")
    if not isinstance(work_item, dict):
        raise BulkDocumentError("reporting document must contain a work_item object")

    organization = work_item.get("organization")
    project = work_item.get("project")
    work_item_id = work_item.get("id")
    if not organization or not project or work_item_id is None:
        raise BulkDocumentError(
            "work_item.organization, work_item.project, and work_item.id are required"
        )

    return f"{organization}:{project}:{work_item_id}"


def build_bulk_payload(
    index_name: str,
    documents: Iterable[dict[str, Any]],
) -> bytes:
    """Build NDJSON bulk payload using update + doc_as_upsert actions."""
    lines: list[str] = []
    for document in documents:
        doc_id = document_id(document)
        action = {"update": {"_index": index_name, "_id": doc_id}}
        payload = {"doc": document, "doc_as_upsert": True}
        lines.append(json.dumps(action, separators=(",", ":")))
        lines.append(json.dumps(payload, separators=(",", ":")))
    return ("\n".join(lines) + "\n").encode("utf-8")


def chunk_documents(
    documents: Iterable[dict[str, Any]],
    chunk_size: int,
) -> list[list[dict[str, Any]]]:
    """Split documents into fixed-size bulk batches."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be at least 1")

    batches: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    for document in documents:
        current.append(document)
        if len(current) >= chunk_size:
            batches.append(current)
            current = []
    if current:
        batches.append(current)
    return batches


def parse_bulk_response(body: bytes) -> BulkResult:
    """Parse an Elasticsearch bulk response into success and failure counts."""
    if not body:
        return BulkResult(succeeded=0, failed=0)

    payload = json.loads(body.decode("utf-8"))
    items = payload.get("items", [])
    succeeded = 0
    failures: list[BulkItemFailure] = []

    for item in items:
        update_item = item.get("update", {})
        status = update_item.get("status", 0)
        doc_id = update_item.get("_id", "")
        if 200 <= status < 300:
            succeeded += 1
            continue

        error = update_item.get("error", {})
        failures.append(
            BulkItemFailure(
                document_id=str(doc_id),
                error_type=str(error.get("type", "bulk_item_error")),
                reason=str(error.get("reason", "bulk item failed")),
            )
        )

    return BulkResult(
        succeeded=succeeded,
        failed=len(failures),
        errors=tuple(failures),
    )
