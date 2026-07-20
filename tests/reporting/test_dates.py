"""Tests for ADO datetime parsing and days-to-close."""

from datetime import datetime, timezone

import pytest

from reporting.dates import compute_days_to_close, format_ado_datetime, parse_ado_datetime


def test_parse_ado_datetime_with_z_suffix() -> None:
    parsed = parse_ado_datetime("2026-04-21T02:12:50.29Z")

    assert parsed == datetime(2026, 4, 21, 2, 12, 50, 290000, tzinfo=timezone.utc)


def test_parse_ado_datetime_with_millisecond_precision() -> None:
    parsed = parse_ado_datetime("2026-04-21T02:17:19.270Z")

    assert parsed == datetime(2026, 4, 21, 2, 17, 19, 270000, tzinfo=timezone.utc)


def test_format_ado_datetime_normalizes_to_milliseconds() -> None:
    value = datetime(2026, 4, 21, 2, 17, 19, 270000, tzinfo=timezone.utc)

    assert format_ado_datetime(value) == "2026-04-21T02:17:19.270Z"


def test_compute_days_to_close_returns_fractional_days() -> None:
    created = parse_ado_datetime("2026-01-15T10:00:00.000Z")
    closed = parse_ado_datetime("2026-02-01T14:30:00.000Z")

    assert compute_days_to_close(created, closed) == 17.19


def test_compute_days_to_close_short_interval_rounds_to_two_decimals() -> None:
    created = parse_ado_datetime("2026-04-21T02:12:50.29Z")
    closed = parse_ado_datetime("2026-04-21T02:17:19.27Z")

    assert compute_days_to_close(created, closed) == 0.0


def test_compute_days_to_close_returns_none_when_dates_missing() -> None:
    created = parse_ado_datetime("2026-04-21T02:12:50.29Z")

    assert compute_days_to_close(created, None) is None
    assert compute_days_to_close(None, created) is None


def test_parse_ado_datetime_rejects_empty_string() -> None:
    with pytest.raises(ValueError):
        parse_ado_datetime("   ")
