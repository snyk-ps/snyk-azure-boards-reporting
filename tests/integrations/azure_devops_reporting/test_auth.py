"""Tests for Azure DevOps PAT auth helpers."""

import base64
import os

import pytest

from integrations.azure_devops_reporting.auth import (
    PAT_ENV_VAR,
    build_authorization_header,
    read_pat_from_environ,
)
from integrations.azure_devops_reporting.errors import MissingPatError


def test_build_authorization_header_uses_empty_username(monkeypatch: pytest.MonkeyPatch) -> None:
    header = build_authorization_header("example-pat")
    encoded = header.removeprefix("Basic ")
    decoded = base64.b64decode(encoded).decode("utf-8")
    assert decoded == ":example-pat"


def test_read_pat_from_environ_returns_trimmed_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(PAT_ENV_VAR, "  secret-pat  ")
    assert read_pat_from_environ() == "secret-pat"


def test_read_pat_from_environ_raises_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(PAT_ENV_VAR, raising=False)
    with pytest.raises(MissingPatError) as exc_info:
        read_pat_from_environ()
    assert PAT_ENV_VAR in str(exc_info.value)
    assert "secret" not in str(exc_info.value).lower()
