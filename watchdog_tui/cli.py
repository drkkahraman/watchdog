"""Command Line Interface for Watchdog TUI."""

import argparse
import os
import sys
from pathlib import Path

from watchdog_tui import __app_name__, __version__
from watchdog_tui.ui.app import WatchdogApp


def load_env_file(file_path: Path) -> None:
    """Load key-value pairs from an env file into os.environ."""
    if not file_path.is_file():
        return
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip("'\"")
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception:
        pass


def init_env() -> None:
    """Load configuration from local or global .env file."""
    # 1. Current working directory .env
    cwd_env = Path.cwd() / ".env"
    if cwd_env.is_file():
        load_env_file(cwd_env)
        return

    # 2. User config directory .env (~/.config/watchdog/.env)
    user_config_env = Path.home() / ".config" / "watchdog" / ".env"
    if user_config_env.is_file():
        load_env_file(user_config_env)


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    default_interval = float(os.getenv("WATCHDOG_INTERVAL", "2.0"))
    default_host = os.getenv("DOCKER_HOST", None)

    parser = argparse.ArgumentParser(
        prog="watchdog",
        description="🐕 Watchdog - Real-time Docker & Service Status Monitor (TUI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  DOCKER_HOST           Docker daemon URL or socket (e.g. unix:///var/run/docker.sock)
  WATCHDOG_INTERVAL     Metrics refresh rate in seconds (e.g. 2.0)
  WATCHDOG_LOG_TAIL     Default log tail lines count (e.g. 150)

Examples:
  watchdog                                # Launch Watchdog with defaults / .env
  watchdog -i 1.0                         # Refresh every 1.0 second
  watchdog -H unix:///var/run/docker.sock # Specify Docker daemon socket
  watchdog -H tcp://192.168.1.100:2375    # Connect to remote Docker daemon
        """
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"{__app_name__} v{__version__}"
    )
    parser.add_argument(
        "-i", "--interval",
        type=float,
        default=default_interval,
        help=f"Metrics polling interval in seconds (default: {default_interval})"
    )
    parser.add_argument(
        "-H", "--docker-host",
        type=str,
        default=default_host,
        help="Docker daemon socket path or TCP host (e.g., unix:///var/run/docker.sock)"
    )
    parser.add_argument(
        "--env-file",
        type=str,
        default=None,
        help="Path to custom .env configuration file"
    )
    return parser


def main() -> None:
    """CLI entrypoint."""
    init_env()
    parser = create_parser()
    args = parser.parse_args()

    if args.env_file:
        load_env_file(Path(args.env_file))

    app = WatchdogApp(
        docker_host=args.docker_host or os.getenv("DOCKER_HOST"),
        poll_interval=args.interval
    )
    try:
        app.run()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
