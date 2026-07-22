"""Load normative Elasticsearch index mappings."""

from __future__ import annotations

import json
from pathlib import Path

DEFAULT_MAPPINGS_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "elasticsearch" / "snyk-ado-work-items-mappings.json"
)


def load_index_mappings(path: str | Path | None = None) -> dict:
    """Load index mapping properties from the checked-in artifact."""
    mappings_path = Path(path) if path is not None else DEFAULT_MAPPINGS_PATH
    with mappings_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise ValueError(f"mappings artifact must be a JSON object: {mappings_path}")

    properties = payload.get("properties")
    if not isinstance(properties, dict):
        raise ValueError(f"mappings artifact must contain properties: {mappings_path}")

    return properties
