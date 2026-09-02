from pathlib import Path

from watchdog_tui.cli import create_parser, load_env_file


def test_cli_parser_defaults():
    parser = create_parser()
    args = parser.parse_args([])
    assert args.interval == 2.0


def test_cli_parser_custom_args():
    parser = create_parser()
    args = parser.parse_args(["-i", "5.5", "-H", "unix:///var/run/docker.sock"])
    assert args.interval == 5.5
    assert args.docker_host == "unix:///var/run/docker.sock"


def test_load_env_file(tmp_path: Path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("WATCHDOG_INTERVAL=3.5\nDOCKER_HOST=tcp://10.0.0.1:2375\n# Comment\nINVALID_LINE\n")

    monkeypatch.delenv("WATCHDOG_INTERVAL", raising=False)
    monkeypatch.delenv("DOCKER_HOST", raising=False)

    load_env_file(env_file)

    import os
    assert os.getenv("WATCHDOG_INTERVAL") == "3.5"
    assert os.getenv("DOCKER_HOST") == "tcp://10.0.0.1:2375"
