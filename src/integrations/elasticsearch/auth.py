"""Elasticsearch authentication helpers."""

from __future__ import annotations

import base64
import os

from integrations.elasticsearch.errors import (
    MissingElasticsearchCredentialsError,
    MissingElasticsearchUrlError,
)

URL_ENV_VAR = "ELASTICSEARCH_URL"
API_KEY_ENV_VAR = "ELASTICSEARCH_API_KEY"
USERNAME_ENV_VAR = "ELASTICSEARCH_USERNAME"
PASSWORD_ENV_VAR = "ELASTICSEARCH_PASSWORD"


def read_elasticsearch_url_from_environ() -> str:
    """Return the Elasticsearch cluster URL from the environment or fail fast."""
    url = os.environ.get(URL_ENV_VAR, "").strip().rstrip("/")
    if not url:
        raise MissingElasticsearchUrlError(
            f"{URL_ENV_VAR} is unset or empty; set it in the environment before "
            "calling Elasticsearch."
        )
    return url


def build_authorization_header(
    *,
    api_key: str | None = None,
    username: str | None = None,
    password: str | None = None,
) -> str:
    """Build an Authorization header for Elasticsearch."""
    if api_key:
        return f"ApiKey {api_key.strip()}"
    if username and password:
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        return f"Basic {token}"
    raise MissingElasticsearchCredentialsError(
        f"Set {API_KEY_ENV_VAR} or both {USERNAME_ENV_VAR} and {PASSWORD_ENV_VAR}."
    )


def read_credentials_from_environ() -> tuple[str | None, str | None, str | None]:
    """Return API key or basic auth credentials from the environment."""
    api_key = os.environ.get(API_KEY_ENV_VAR, "").strip() or None
    username = os.environ.get(USERNAME_ENV_VAR, "").strip() or None
    password = os.environ.get(PASSWORD_ENV_VAR, "").strip() or None
    return api_key, username, password
