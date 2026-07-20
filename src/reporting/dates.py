"""ADO datetime parsing and days-to-close computation."""

from __future__ import annotations

from datetime import datetime, timezone


def parse_ado_datetime(value: str) -> datetime:
    """Parse an Azure DevOps ISO-8601 timestamp into UTC."""
    text = value.strip()
    if not text:
        raise ValueError("datetime value must not be empty")

    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    if "." in text:
        main, remainder = text.split(".", 1)
        if "+" in remainder:
            fraction, timezone_part = remainder.split("+", 1)
            timezone_suffix = f"+{timezone_part}"
        elif remainder.count("-") > 0 and "T" not in remainder.split("-", 1)[1]:
            fraction, timezone_suffix = remainder.rsplit("-", 1)
            timezone_suffix = f"-{timezone_suffix}"
        else:
            fraction = remainder
            timezone_suffix = ""
        fraction = fraction.ljust(6, "0")[:6]
        text = f"{main}.{fraction}{timezone_suffix}"

    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def format_ado_datetime(value: datetime) -> str:
    """Format a UTC datetime as ADO-style ISO-8601 with millisecond precision."""
    utc = value.astimezone(timezone.utc)
    milliseconds = utc.microsecond // 1000
    return utc.strftime(f"%Y-%m-%dT%H:%M:%S.{milliseconds:03d}Z")


def compute_days_to_close(
    created_at: datetime | None,
    closed_at: datetime | None,
) -> float | None:
    """Return fractional UTC days between creation and closure, rounded to 2 dp."""
    if created_at is None or closed_at is None:
        return None
    delta_seconds = (closed_at - created_at).total_seconds()
    return round(delta_seconds / 86400.0, 2)
