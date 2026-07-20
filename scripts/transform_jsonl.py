#!/usr/bin/env python3
"""Transform normalized ADO JSONL into reporting documents."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO

from config.loader import load_config
from integrations.azure_devops_reporting.models import NormalizedWorkItem
from reporting.document import build_reporting_document
from reporting.models import TransformContext


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transform normalized work item JSONL into reporting documents.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to normalized JSONL (for example data/smoke-wiql.jsonl)",
    )
    parser.add_argument(
        "--org",
        help="Azure DevOps organization name for work_item.organization",
    )
    parser.add_argument(
        "--config",
        help="Optional reporting YAML for closed_states (for example data/reporting.sample.yaml)",
    )
    parser.add_argument(
        "--run-id",
        default="dev-run",
        help="Export run identifier written to export.run_id",
    )
    parser.add_argument(
        "--closed-states",
        nargs="+",
        help="Closed states for closure fallback (overrides config when set)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Write reporting JSONL to this file instead of stdout",
    )
    return parser.parse_args()


def _build_context(args: argparse.Namespace) -> TransformContext:
    closed_states: frozenset[str]
    organization = args.org

    if args.config:
        config = load_config(args.config)
        closed_states = frozenset(config.closed_states)
        if organization is None:
            organization = config.organizations[0].name
    elif args.closed_states:
        closed_states = frozenset(args.closed_states)
    else:
        closed_states = frozenset({"Closed", "Done"})

    if organization is None:
        raise SystemExit("--org is required when --config is not provided")

    return TransformContext(
        organization=organization,
        run_id=args.run_id,
        exported_at=datetime.now(timezone.utc),
        closed_states=closed_states,
    )


def main() -> int:
    """Read normalized JSONL and write reporting JSONL to stdout or a file."""
    args = _parse_args()
    context = _build_context(args)
    input_path = Path(args.input)
    if not input_path.is_file():
        print(f"input file not found: {input_path}", file=sys.stderr)
        return 1

    output_path = Path(args.output) if args.output else None
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as output_file:
            _write_documents(input_path, context, output_file)
    else:
        _write_documents(input_path, context, sys.stdout)

    return 0


def _write_documents(
    input_path: Path,
    context: TransformContext,
    output: TextIO,
) -> None:
    """Transform each normalized JSONL line and write reporting documents."""
    for line in input_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        item: NormalizedWorkItem = json.loads(line)
        document = build_reporting_document(item, context=context)
        output.write(json.dumps(document, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
