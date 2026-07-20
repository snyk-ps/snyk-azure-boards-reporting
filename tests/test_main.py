"""Tests for CLI entry point."""

from main import build_parser, main


def test_main_prints_help_when_no_command(capsys) -> None:
    exit_code = main([])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "azure-devops-smoke" in captured.out


def test_build_parser_registers_smoke_command() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "azure-devops-smoke",
            "wiql",
            "--org",
            "example-org",
            "--project",
            "demo",
        ]
    )

    assert args.command == "azure-devops-smoke"
    assert args.smoke_command == "wiql"
    assert args.org == "example-org"
    assert args.project == "demo"
