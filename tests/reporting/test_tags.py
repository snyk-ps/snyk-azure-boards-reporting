"""Tests for System.Tags parsing."""

from reporting.tags import parse_system_tags


def test_parse_system_tags_empty() -> None:
    parsed = parse_system_tags(None)

    assert parsed == {
        "raw": "",
        "operator": [],
        "severity": None,
        "finding_type": None,
    }


def test_parse_system_tags_operator_only() -> None:
    parsed = parse_system_tags("Snyk")

    assert parsed["raw"] == "Snyk"
    assert parsed["operator"] == ["Snyk"]
    assert parsed["severity"] is None
    assert parsed["finding_type"] is None


def test_parse_system_tags_managed_and_operator() -> None:
    parsed = parse_system_tags(
        "Snyk; Snyk-Severity-critical; Snyk-Type-open_source; TestOverride"
    )

    assert parsed["operator"] == ["Snyk", "TestOverride"]
    assert parsed["severity"] == "critical"
    assert parsed["finding_type"] == "open_source"


def test_parse_system_tags_trims_whitespace() -> None:
    parsed = parse_system_tags(" Snyk ; Snyk-Severity-high ; Snyk-Type-code ")

    assert parsed["operator"] == ["Snyk"]
    assert parsed["severity"] == "high"
    assert parsed["finding_type"] == "code"


def test_parse_system_tags_last_managed_tag_wins() -> None:
    parsed = parse_system_tags(
        "Snyk-Severity-low; Snyk-Severity-high; Snyk-Type-code; Snyk-Type-iac"
    )

    assert parsed["severity"] == "high"
    assert parsed["finding_type"] == "iac"
    assert parsed["operator"] == []
