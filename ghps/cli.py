# -*- coding: utf-8 -*-
"""ghps cli."""

import sys
import argparse
from pathlib import Path
from .params import GHPS_VERSION
from .server import GHPageServer


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
    args = _parse_args()

    if args.version:
        print(GHPS_VERSION)
    else:
        directory = Path(args.directory).resolve()

        if not directory.exists():
            print("Error: Directory does not exist.")
            sys.exit(1)

        server = GHPageServer(
            directory=str(directory),
            port=args.port,
            base_path=args.base_path,
            strict=not args.no_strict,
            no_cache=args.no_cache,
            threaded=not args.no_threaded,
            auto_open=args.auto_open,
        )
        server.start()
