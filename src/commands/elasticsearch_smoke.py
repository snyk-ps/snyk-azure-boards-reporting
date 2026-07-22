"""Elasticsearch smoke-test commands."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from config.loader import DEFAULT_INDEX_NAME, load_config
from integrations.azure_devops_reporting.errors import ConfigurationError
from integrations.elasticsearch.auth import read_elasticsearch_url_from_environ
from integrations.elasticsearch.bulk import document_id
from integrations.elasticsearch.client import build_ingest_client_from_env
from integrations.elasticsearch.errors import (
    AuthenticationError,
    ElasticsearchError,
    ElasticsearchHttpError,
    MissingElasticsearchUrlError,
)
from integrations.elasticsearch.mappings import load_index_mappings

SMOKE_DOCUMENT: dict = {
    "work_item": {
        "id": "12345",
        "organization": "torstencannell",
        "project": "snykDemoProject",
        "title": "[HIGH] example-package: CVE-2024-0001",
        "status": "Done",
        "area_path": "snykDemoProject",
        "created_at": "2026-01-15T10:00:00.000Z",
        "changed_at": "2026-02-01T14:30:00.000Z",
        "closed_at": "2026-02-01T14:30:00.000Z",
        "days_to_close": 17.19,
    },
    "tags": {
        "raw": "Snyk; Snyk-Severity-high; Snyk-Type-open_source",
        "operator": ["Snyk"],
        "severity": "high",
        "finding_type": "open_source",
    },
    "snyk": {
        "issue_id": "uuid-here",
        "status": "resolved",
        "project_origin": "github-enterprise",
    },
    "export": {
        "run_id": "550e8400-e29b-41d4-a716-446655440000",
        "exported_at": "2026-07-20T21:00:00.000Z",
    },
}


def register_subcommand(subparsers: argparse._SubParsersAction) -> None:
    """Register the elasticsearch-smoke command tree."""
    smoke_parser = subparsers.add_parser(
        "elasticsearch-smoke",
        help="Run Elasticsearch smoke checks",
    )
    smoke_subparsers = smoke_parser.add_subparsers(dest="smoke_command", required=True)

    index_one_parser = smoke_subparsers.add_parser(
        "index-one",
        help="Index one hardcoded reporting document into Elasticsearch",
    )
    index_one_parser.add_argument(
        "--config",
        help="Path to reporting YAML configuration",
    )
    index_one_parser.add_argument(
        "--input",
        help="Path to reporting JSONL; indexes one document from this file when set",
    )
    index_one_parser.add_argument(
        "--line",
        type=int,
        default=1,
        help="1-based JSONL line number to index when --input is set (default: 1)",
    )
    index_one_parser.set_defaults(handler=run_index_one_smoke)


def load_document_from_jsonl(path: str | Path, *, line: int = 1) -> dict:
    """Load one reporting document from a JSONL file."""
    if line < 1:
        raise ValueError("--line must be at least 1")

    jsonl_path = Path(path)
    if not jsonl_path.is_file():
        raise ValueError(f"input file not found: {jsonl_path}")

    with jsonl_path.open("r", encoding="utf-8") as handle:
        for index, raw_line in enumerate(handle, start=1):
            if index < line:
                continue
            if index > line:
                break
            stripped = raw_line.strip()
            if not stripped:
                raise ValueError(f"line {line} in {jsonl_path} is empty")
            document = json.loads(stripped)
            if not isinstance(document, dict):
                raise ValueError(f"line {line} in {jsonl_path} must be a JSON object")
            return document

    raise ValueError(f"line {line} not found in {jsonl_path}")


def run_index_one_smoke(args: argparse.Namespace) -> int:
    """Index one reporting document and print a JSON summary."""
    try:
        index_name = DEFAULT_INDEX_NAME
        auto_create_index = True
        if args.config:
            config = load_config(args.config)
            index_name = config.elasticsearch.index_name
            auto_create_index = config.elasticsearch.auto_create_index

        document = (
            load_document_from_jsonl(args.input, line=args.line)
            if args.input
            else SMOKE_DOCUMENT
        )

        read_elasticsearch_url_from_environ()
        client = build_ingest_client_from_env()
        if auto_create_index:
            client.ensure_index(index_name, mappings=load_index_mappings())

        result = client.bulk_upsert_documents(index_name, [document])
        if result.failed:
            raise ElasticsearchError(
                f"bulk upsert failed for {result.failed} document(s)"
            )

        summary = {
            "_id": document_id(document),
            "index_name": index_name,
            "succeeded": result.succeeded,
            "failed": result.failed,
        }
        print(json.dumps(summary, sort_keys=True))
        return 0
    except (
        AuthenticationError,
        ConfigurationError,
        ElasticsearchError,
        ElasticsearchHttpError,
        MissingElasticsearchUrlError,
        ValueError,
    ) as error:
        print(str(error), file=sys.stderr)
        return 1
