"""Tests for Elasticsearch index mappings artifact."""

from integrations.elasticsearch.mappings import load_index_mappings


def test_load_index_mappings_contains_required_field_types() -> None:
    properties = load_index_mappings()

    assert properties["work_item"]["properties"]["created_at"]["type"] == "date"
    assert properties["tags"]["properties"]["severity"]["type"] == "keyword"
    assert properties["work_item"]["properties"]["title"]["type"] == "text"
    assert (
        properties["work_item"]["properties"]["title"]["fields"]["keyword"]["type"]
        == "keyword"
    )
    assert properties["work_item"]["properties"]["assignee"]["type"] == "keyword"
    assert properties["work_item"]["properties"]["url"]["type"] == "keyword"
    assert properties["work_item"]["properties"]["story_name"]["type"] == "keyword"
    assert properties["work_item"]["properties"]["story_url"]["type"] == "keyword"
