"""Tests for Elasticsearch ingest models."""

from integrations.elasticsearch.models import BulkItemFailure, format_bulk_item_failure


def test_format_bulk_item_failure() -> None:
    failure = BulkItemFailure(
        document_id="org:proj:1",
        error_type="mapper_parsing_exception",
        reason="failed to parse",
    )

    assert (
        format_bulk_item_failure(failure)
        == "org:proj:1: mapper_parsing_exception: failed to parse"
    )
