"""Tests for CLI argument parsing."""

from watchdog_tui.cli import create_parser


def test_cli_parser_defaults():
    parser = create_parser()
    args = parser.parse_args([])
    assert args.interval == 2.0
    assert args.docker_host is None


def test_cli_parser_custom_args():
    parser = create_parser()
    args = parser.parse_args(["-i", "5.5", "-H", "unix:///var/run/docker.sock"])
    assert args.interval == 5.5
    assert args.docker_host == "unix:///var/run/docker.sock"
