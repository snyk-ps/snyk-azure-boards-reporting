"""Tests for closure date resolution."""

from datetime import datetime, timezone

from reporting.closure import resolve_closed_at


def test_resolve_closed_at_prefers_closed_date() -> None:
    fields = {
        "Microsoft.VSTS.Common.ClosedDate": "2026-04-21T02:17:19.27Z",
        "Microsoft.VSTS.Common.ResolvedDate": "2026-04-21T02:16:00.00Z",
        "System.ChangedDate": "2026-04-21T02:17:19.617Z",
        "System.State": "Done",
    }

    resolved = resolve_closed_at(fields, frozenset({"Done"}))

    assert resolved == datetime(2026, 4, 21, 2, 17, 19, 270000, tzinfo=timezone.utc)


def test_resolve_closed_at_uses_resolved_date_when_closed_date_missing() -> None:
    fields = {
        "Microsoft.VSTS.Common.ResolvedDate": "2026-04-21T02:16:00.00Z",
        "System.ChangedDate": "2026-04-21T02:17:19.617Z",
        "System.State": "Done",
    }

    resolved = resolve_closed_at(fields, frozenset({"Done"}))

    assert resolved == datetime(2026, 4, 21, 2, 16, 0, tzinfo=timezone.utc)


def test_resolve_closed_at_falls_back_to_changed_date_for_closed_state() -> None:
    fields = {
        "System.ChangedDate": "2026-04-21T02:17:19.617Z",
        "System.State": "Done",
    }

    resolved = resolve_closed_at(fields, frozenset({"Done"}))

    assert resolved == datetime(2026, 4, 21, 2, 17, 19, 617000, tzinfo=timezone.utc)


def test_resolve_closed_at_returns_none_for_active_item() -> None:
    fields = {
        "System.ChangedDate": "2026-04-21T02:17:19.617Z",
        "System.State": "To Do",
    }

    resolved = resolve_closed_at(fields, frozenset({"Done"}))

    assert resolved is None
