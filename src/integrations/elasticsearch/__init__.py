"""Elasticsearch bulk ingest integration."""

from integrations.elasticsearch.client import (
    ElasticsearchIngestClient,
    build_ingest_client_from_env,
)
from integrations.elasticsearch.models import BulkResult

__all__ = [
    "BulkResult",
    "ElasticsearchIngestClient",
    "build_ingest_client_from_env",
]
