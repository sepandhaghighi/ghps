# -*- coding: utf-8 -*-
"""ghps cli."""

import sys
import argparse
from pathlib import Path
from .params import GHPS_VERSION
from .params import DEFAULT_HOST, DEFAULT_PORT, DEFAULT_DIRECTORY
from .errors import GHPSError
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
        "-c", "--config",
        type=str,
        default=None,
        help="Path to configuration file"
    )

    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help=f"Host address to bind to (default: {DEFAULT_HOST})"
    )

    parser.add_argument(
        "-p", "--port",
        type=int,
        default=None,
        help=f"Port to serve on (default: {DEFAULT_PORT}, use 0 for automatic allocation)"
    )

    parser.add_argument(
        "-d", "--directory",
        default=None,
        help=f"Directory to serve (default: {DEFAULT_DIRECTORY})"
    )

    parser.add_argument(
        "-b", "--base-path",
        default=None,
        help="Base path for project pages (e.g. /repo-name)"
    )

    parser.add_argument(
        "--no-strict",
        action="store_true",
        default=None,
        help="Enable .html fallback"
    )

    parser.add_argument(
        "--no-cache",
        action="store_true",
        default=None,
        help="Disable HTTP caching headers"
    )

    parser.add_argument(
        "--no-threaded",
        action="store_true",
        default=None,
        help="Disable threaded server"
    )

    parser.add_argument(
        "--auto-open",
        action="store_true",
        default=None,
        help="Automatically open the server URL"
    )

    parser.add_argument(
        "--directory-listing",
        action="store_true",
        default=None,
        help="Enable directory listing"
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        default=None,
        help="Suppress informational server output"
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
            server = GHPageServer.from_config(
                directory=args.directory,
                host=args.host,
                port=args.port,
                base_path=args.base_path,
                strict=False if args.no_strict else None,
                no_cache=args.no_cache,
                threaded=False if args.no_threaded else None,
                auto_open=args.auto_open,
                directory_listing=args.directory_listing,
                quiet=args.quiet,
                config=args.config,
                auto_discover=True,
            )
            server.start()
    except GHPSError as e:
        _print_cli_error(str(e))
    except Exception as e:
        _print_cli_error(f"Unexpected error: {e}")
