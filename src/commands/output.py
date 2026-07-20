"""Local JSONL output helper."""

from __future__ import annotations

import argparse
import json
import sys
from typing import TextIO


def register_subcommand(subparsers: argparse._SubParsersAction) -> None:
    """Register the output command."""
    output_parser = subparsers.add_parser(
        "output",
        help="Read normalized JSONL and print it for local inspection",
    )
    output_parser.add_argument(
        "file",
        nargs="?",
        help="Optional JSONL file path; reads stdin when omitted",
    )
    output_parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print each JSON object",
    )
    output_parser.set_defaults(handler=run_output)


def run_output(args: argparse.Namespace) -> int:
    """Print JSONL records from a file or stdin."""
    stream: TextIO
    if args.file:
        stream = open(args.file, encoding="utf-8")
        close_stream = True
    else:
        stream = sys.stdin
        close_stream = False

    try:
        for line_number, line in enumerate(stream, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as error:
                print(
                    f"invalid JSON on line {line_number}: {error}",
                    file=sys.stderr,
                )
                return 1

            if args.pretty:
                sys.stdout.write(json.dumps(record, indent=2, sort_keys=True))
                sys.stdout.write("\n")
            else:
                sys.stdout.write(json.dumps(record, sort_keys=True))
                sys.stdout.write("\n")
    finally:
        if close_stream:
            stream.close()

    return 0
