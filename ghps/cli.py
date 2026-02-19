# -*- coding: utf-8 -*-
"""ghps cli."""

import sys
import argparse
from pathlib import Path

def _parse_args() -> argparse.Namespace:
    """Parse arguments."""
    parser = argparse.ArgumentParser(
        description="Minimal GitHub Pages simulator server"
    )

    parser.add_argument(
        "-p", "--port",
        type=int,
        default=4000,
        help="Port to serve on (default: 4000)"
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
        help="Enable .html fallback (non-GitHub behavior)"
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

    args = parser.parse_args()
    return args


def main():
    args = _parse_args()
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
    )
    server.start()