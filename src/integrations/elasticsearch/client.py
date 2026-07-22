"""Elasticsearch bulk ingest client."""

from __future__ import annotations

import json
from typing import Any, Iterable
from urllib.parse import quote

from integrations.elasticsearch.auth import (
    build_authorization_header,
    read_credentials_from_environ,
    read_elasticsearch_url_from_environ,
)
from integrations.elasticsearch.bulk import (
    build_bulk_payload,
    chunk_documents,
    parse_bulk_response,
)
from integrations.elasticsearch.errors import AuthenticationError, ElasticsearchHttpError
from integrations.elasticsearch.http import HttpTransport, UrllibTransport
from integrations.elasticsearch.models import BulkResult

DEFAULT_BULK_CHUNK_SIZE = 500


class ElasticsearchIngestClient:
    """Low-level Elasticsearch ingest client for reporting documents."""

    def __init__(
        self,
        *,
        url: str,
        authorization: str,
        transport: HttpTransport | None = None,
    ) -> None:
        self._url = url.rstrip("/")
        self._authorization = authorization
        self._transport = transport or UrllibTransport()

    def ensure_index(self, index_name: str, *, mappings: dict[str, Any]) -> None:
        """Create the index with mappings when it does not exist."""
        encoded_index = quote(index_name, safe="")
        index_url = f"{self._url}/{encoded_index}"
        head_response = self._transport.request(
            "HEAD",
            index_url,
            headers=self._request_headers(content_type=False),
        )
        if head_response.status == 200:
            return
        if head_response.status not in {404, 405}:
            self._raise_for_status(head_response, safe_target=f"{self._url}/{index_name}")

        body = json.dumps({"mappings": {"properties": mappings}}).encode("utf-8")
        put_response = self._transport.request(
            "PUT",
            index_url,
            headers=self._request_headers(),
            body=body,
        )
        if put_response.status in {401, 403}:
            raise AuthenticationError(
                f"Elasticsearch authentication failed with HTTP {put_response.status} "
                f"for {self._url}/{index_name}"
            )
        if put_response.status >= 400 and put_response.status != 400:
            self._raise_for_status(put_response, safe_target=f"{self._url}/{index_name}")

    def bulk_upsert_documents(
        self,
        index_name: str,
        documents: Iterable[dict[str, Any]],
        *,
        chunk_size: int = DEFAULT_BULK_CHUNK_SIZE,
    ) -> BulkResult:
        """Bulk upsert reporting documents using update + doc_as_upsert."""
        total_succeeded = 0
        total_failed = 0
        all_errors = []

        for batch in chunk_documents(documents, chunk_size):
            payload = build_bulk_payload(index_name, batch)
            response = self._transport.request(
                "POST",
                f"{self._url}/_bulk",
                headers=self._request_headers(content_type="application/x-ndjson"),
                body=payload,
            )
            if response.status in {401, 403, 404}:
                if response.status in {401, 403}:
                    raise AuthenticationError(
                        f"Elasticsearch authentication failed with HTTP {response.status} "
                        f"for {self._url}/_bulk"
                    )
                self._raise_for_status(response, safe_target=f"{self._url}/_bulk")
            if response.status >= 400:
                self._raise_for_status(response, safe_target=f"{self._url}/_bulk")

            result = parse_bulk_response(response.body)
            total_succeeded += result.succeeded
            total_failed += result.failed
            all_errors.extend(result.errors)

        return BulkResult(
            succeeded=total_succeeded,
            failed=total_failed,
            errors=tuple(all_errors),
        )

    def safe_target(self, path: str) -> str:
        """Return a host + path pattern safe for logs."""
        normalized = path if path.startswith("/") else f"/{path}"
        return f"{self._url}{normalized}"

    def _request_headers(
        self,
        *,
        content_type: str | bool = "application/json",
    ) -> dict[str, str]:
        headers = {
            "Authorization": self._authorization,
            "Accept": "application/json",
        }
        if content_type:
            headers["Content-Type"] = str(content_type)
        return headers

    def _raise_for_status(self, response, *, safe_target: str) -> None:
        raise ElasticsearchHttpError(
            f"Elasticsearch request failed with HTTP {response.status} for {safe_target}",
            status=response.status,
            safe_target=safe_target,
        )


def build_ingest_client_from_env(
    *,
    transport: HttpTransport | None = None,
) -> ElasticsearchIngestClient:
    """Build an ingest client from environment variables."""
    url = read_elasticsearch_url_from_environ()
    api_key, username, password = read_credentials_from_environ()
    authorization = build_authorization_header(
        api_key=api_key,
        username=username,
        password=password,
    )
    return ElasticsearchIngestClient(
        url=url,
        authorization=authorization,
        transport=transport,
    )
