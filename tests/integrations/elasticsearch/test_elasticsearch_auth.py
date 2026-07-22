"""Tests for Elasticsearch authentication helpers."""

import base64
import os

import pytest

from integrations.elasticsearch.auth import (
    API_KEY_ENV_VAR,
    PASSWORD_ENV_VAR,
    URL_ENV_VAR,
    USERNAME_ENV_VAR,
    build_authorization_header,
    read_elasticsearch_url_from_environ,
)
from integrations.elasticsearch.client import build_ingest_client_from_env
from integrations.elasticsearch.errors import (
    MissingElasticsearchCredentialsError,
    MissingElasticsearchUrlError,
)


def test_build_authorization_header_uses_api_key() -> None:
    header = build_authorization_header(api_key="abc123")

    assert header == "ApiKey abc123"


def test_build_authorization_header_uses_basic_auth() -> None:
    header = build_authorization_header(username="elastic", password="secret")

    expected = base64.b64encode(b"elastic:secret").decode("ascii")
    assert header == f"Basic {expected}"


def test_build_authorization_header_requires_credentials() -> None:
    with pytest.raises(MissingElasticsearchCredentialsError):
        build_authorization_header()


def test_read_elasticsearch_url_from_environ_strips_trailing_slash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(URL_ENV_VAR, "https://example.es.cloud:9243/")

    assert read_elasticsearch_url_from_environ() == "https://example.es.cloud:9243"


def test_read_elasticsearch_url_from_environ_raises_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(URL_ENV_VAR, raising=False)

    with pytest.raises(MissingElasticsearchUrlError):
        read_elasticsearch_url_from_environ()


def test_build_ingest_client_from_env_uses_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(URL_ENV_VAR, "https://example.es.cloud:9243")
    monkeypatch.setenv(API_KEY_ENV_VAR, "encoded-key")
    monkeypatch.delenv(USERNAME_ENV_VAR, raising=False)
    monkeypatch.delenv(PASSWORD_ENV_VAR, raising=False)

    client = build_ingest_client_from_env()

    assert client.safe_target("/_bulk") == "https://example.es.cloud:9243/_bulk"
