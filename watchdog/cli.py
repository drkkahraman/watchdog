"""Command Line Interface for Watchdog TUI."""

import argparse
import sys

from watchdog import __app_name__, __version__
from watchdog.ui.app import WatchdogApp


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        prog="watchdog",
        description="🐕 Watchdog - Real-time Docker & Service Status Monitor (TUI)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  watchdog                      # Launch Watchdog with default settings
  watchdog -i 1.0               # Refresh every 1.0 second
  watchdog -H unix:///var/run/docker.sock  # Specify Docker daemon socket
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
        default=2.0,
        help="Metrics polling interval in seconds (default: 2.0)"
    )
    parser.add_argument(
        "-H", "--docker-host",
        type=str,
        default=None,
        help="Docker daemon socket path or TCP host (e.g., unix:///var/run/docker.sock)"
    )
    return parser


def main() -> None:
    """CLI entrypoint."""
    parser = create_parser()
    args = parser.parse_args()

    app = WatchdogApp(
        docker_host=args.docker_host,
        poll_interval=args.interval
    )
    try:
        app.run()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
