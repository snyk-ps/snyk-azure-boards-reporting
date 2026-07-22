"""Elasticsearch integration errors."""


class ElasticsearchError(Exception):
    """Base error for Elasticsearch integration."""


class ConfigurationError(ElasticsearchError):
    """Raised when required Elasticsearch configuration is missing or invalid."""


class MissingElasticsearchUrlError(ConfigurationError):
    """Raised when ELASTICSEARCH_URL is unset."""


class MissingElasticsearchCredentialsError(ConfigurationError):
    """Raised when no Elasticsearch credentials are configured."""


class AuthenticationError(ElasticsearchError):
    """Raised when Elasticsearch rejects credentials."""


class ElasticsearchHttpError(ElasticsearchError):
    """Raised when an Elasticsearch HTTP request fails."""

    def __init__(
        self,
        message: str,
        *,
        status: int,
        safe_target: str,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.safe_target = safe_target


class BulkDocumentError(ElasticsearchError):
    """Raised when a reporting document is missing fields required for bulk upsert."""

    def __init__(self, message: str, *, document_id: str | None = None) -> None:
        super().__init__(message)
        self.document_id = document_id
