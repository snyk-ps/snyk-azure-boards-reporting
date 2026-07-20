"""Closure date resolution for reporting documents."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from reporting.dates import parse_ado_datetime

CLOSED_DATE_FIELD = "Microsoft.VSTS.Common.ClosedDate"
RESOLVED_DATE_FIELD = "Microsoft.VSTS.Common.ResolvedDate"
CHANGED_DATE_FIELD = "System.ChangedDate"
STATE_FIELD = "System.State"


def resolve_closed_at(
    fields: dict[str, Any],
    closed_states: frozenset[str],
) -> datetime | None:
    """Derive closure datetime using R1-FR-EXP-5 precedence."""
    closed_date = fields.get(CLOSED_DATE_FIELD)
    if closed_date is not None:
        return parse_ado_datetime(str(closed_date))

    resolved_date = fields.get(RESOLVED_DATE_FIELD)
    if resolved_date is not None:
        return parse_ado_datetime(str(resolved_date))

    state = fields.get(STATE_FIELD)
    if state is not None and str(state) in closed_states:
        changed_date = fields.get(CHANGED_DATE_FIELD)
        if changed_date is not None:
            return parse_ado_datetime(str(changed_date))

    return None
