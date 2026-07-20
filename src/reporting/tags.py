"""Parse Azure DevOps System.Tags into reporting dimensions."""

from __future__ import annotations

from reporting.models import TagsParsed

SEVERITY_PREFIX = "Snyk-Severity-"
TYPE_PREFIX = "Snyk-Type-"


def parse_system_tags(raw_tags: str | None) -> TagsParsed:
    """Split and classify ADO work item tags per upstream contract v1."""
    raw = raw_tags or ""
    operator: list[str] = []
    severity: str | None = None
    finding_type: str | None = None

    for token in raw.split(";"):
        tag = token.strip()
        if not tag:
            continue
        if tag.startswith(SEVERITY_PREFIX):
            severity = tag[len(SEVERITY_PREFIX) :]
            continue
        if tag.startswith(TYPE_PREFIX):
            finding_type = tag[len(TYPE_PREFIX) :]
            continue
        operator.append(tag)

    return {
        "raw": raw,
        "operator": operator,
        "severity": severity,
        "finding_type": finding_type,
    }
