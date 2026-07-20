"""Entry point for the CLI."""

import argparse

from commands import azure_devops_smoke, output


def build_parser() -> argparse.ArgumentParser:
    """Build the top-level CLI parser."""
    parser = argparse.ArgumentParser(
        description="Export Snyk-tagged Azure DevOps work items for reporting.",
    )
    subparsers = parser.add_subparsers(dest="command")

    azure_devops_smoke.register_subcommand(subparsers)
    output.register_subcommand(subparsers)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments and dispatch to the selected command."""
    parser = build_parser()
    args = parser.parse_args(argv)

    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 0

    return int(handler(args))


if __name__ == "__main__":
    raise SystemExit(main())
