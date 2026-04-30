# -*- coding: utf-8 -*-
"""ghps cli."""

import sys
import argparse
from pathlib import Path
from .params import GHPS_VERSION
from .errors import GHPSValidationError
from .server import GHPageServer

def _print_cli_error(message: str, exit_code: int = 1) -> None:
    """
    Print a formatted CLI error message and exit.

    :param message: Error message to display.
    :param exit_code: Exit status code (default: 1).
    """
    print(f"[GHPS ERROR] {message}", file=sys.stderr)
    sys.exit(exit_code)


def _parse_args() -> argparse.Namespace:
    """Parse arguments."""
    parser = argparse.ArgumentParser(
        description="Minimal GitHub Pages simulator server"
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Version"
    )

    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8000,
        help="Port to serve on (default: 8000)"
    )

    parser.add_argument(
        "-d", "--directory",
        default=".",
        help="Directory to serve (default: current directory)"
    )

    parser.add_argument(
        "-b", "--base-path",
        default="",
        help="Base path for project pages (e.g. /repo-name)"
    )

    parser.add_argument(
        "--no-strict",
        action="store_true",
        help="Enable .html fallback"
    )

    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable HTTP caching headers"
    )

    parser.add_argument(
        "--no-threaded",
        action="store_true",
        help="Disable threaded server"
    )

    parser.add_argument(
        "--auto-open",
        action="store_true",
        help="Automatically open the server URL"
    )

    args = parser.parse_args()
    return args


def main() -> None:
    """CLI main function."""
    try:
        args = _parse_args()
        if args.version:
            print(GHPS_VERSION)
        else:
            server = GHPageServer(
                directory=args.directory,
                port=args.port,
                base_path=args.base_path,
                strict=not args.no_strict,
                no_cache=args.no_cache,
                threaded=not args.no_threaded,
                auto_open=args.auto_open,
            )
            server.start()
    except GHPSValidationError as e:
        _print_cli_error(str(e))
    except Exception as e:
        _print_cli_error(f"Unexpected error: {e}")
