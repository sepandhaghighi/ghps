# -*- coding: utf-8 -*-
"""ghps server."""

import http.server
import socketserver
from typing import Optional, Any
from pathlib import Path
from urllib.parse import unquote
from .params import (
    INVALID_DIRECTORY_TYPE_ERROR,
    DIRECTORY_NOT_FOUND_ERROR,
    DIRECTORY_NOT_DIR_ERROR,
    INVALID_PORT_TYPE_ERROR,
    INVALID_PORT_RANGE_ERROR,
    INVALID_BASE_PATH_TYPE_ERROR,
    INVALID_BASE_PATH_FORMAT_ERROR,
    INVALID_STRICT_TYPE_ERROR,
    INVALID_NO_CACHE_TYPE_ERROR,
    INVALID_THREADED_TYPE_ERROR,
)

def _validate_inputs(
    directory: Any,
    port: Any,
    base_path: Any,
    strict: Any,
    no_cache: Any,
    threaded: Any,
    ):
    """
    Validate GHPageServer inputs.

    :param directory: Root directory to serve files from.
    :param port: Port number to bind the server to.
    :param base_path: URL base path prefix for serving content.
    :param strict: If False, enables automatic ".html" resolution.
    :param no_cache: If True, disables client-side caching.
    :param threaded: If True, handles requests using threads.
    """
    if not isinstance(directory, (str, Path)):
        raise ValueError(INVALID_DIRECTORY_TYPE_ERROR)

    directory = Path(directory)
    if not directory.exists():
        raise ValueError(DIRECTORY_NOT_FOUND_ERROR)

    if not directory.is_dir():
        raise ValueError(DIRECTORY_NOT_DIR_ERROR)

    if not isinstance(port, int):
        raise ValueError(INVALID_PORT_TYPE_ERROR)

    if not (1 <= port <= 65535):
        raise ValueError(INVALID_PORT_RANGE_ERROR)

    if not isinstance(base_path, str):
        raise ValueError(INVALID_BASE_PATH_TYPE_ERROR)

    if base_path and not base_path.startswith("/"):
        raise ValueError(INVALID_BASE_PATH_FORMAT_ERROR)

    if not isinstance(strict, bool):
        raise ValueError(INVALID_STRICT_TYPE_ERROR)

    if not isinstance(no_cache, bool):
        raise ValueError(INVALID_NO_CACHE_TYPE_ERROR)

    if not isinstance(threaded, bool):
        raise ValueError(INVALID_THREADED_TYPE_ERROR)

class _GHRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler for serving static files with optional base path stripping, strict routing, custom 404 page support, and cache control headers."""

    def __init__(
        self,
        *args: list,
        directory: Optional[str] = None,
        base_path: str = "",
        strict: bool = True,
        no_cache: bool = False,
        **kwargs: dict,
    ):
        """
        Initialize the request handler.

        :param args: Arguments.
        :param directory: Root directory to serve files from.
        :param base_path: URL base path prefix to strip from incoming requests.
        :param strict: If False, allows resolving paths without extension to ".html".
        :param no_cache: If True, disables client-side caching via headers.
        :param kwargs: Keyword arguments.
        """
        self._base_path = base_path.rstrip("/")
        self._strict = strict
        self._no_cache = no_cache
        super().__init__(*args, directory=directory, **kwargs)

    def translate_path(self, path: str) -> str:
        """
        Translate a URL path into a filesystem path within the configured directory.

        Handles base path stripping, optional ".html" resolution in non-strict mode,
        and automatic "index.html" resolution for directories.

        :param path: Incoming HTTP request path.
        """
        path = path.split("?", 1)[0]
        path = unquote(path)

        if self._base_path and path.startswith(self._base_path):
            path = path[len(self._base_path):]

        path = path or "/"

        full_path = Path(self.directory) / path.lstrip("/")

        if full_path.is_dir():
            full_path = full_path / "index.html"

        if not self._strict and not full_path.exists() and full_path.suffix == "":
            candidate = full_path.with_suffix(".html")
            if candidate.exists():
                full_path = candidate

        return str(full_path)

    def send_error(self, code: int, message: Optional[str] = None, explain: Optional[str] = None):
        """
        Send an HTTP error response.

        If a 404 error occurs and a "404.html" file exists in the root directory,
        it will be served instead of the default error response.

        :param code: HTTP status code.
        :param message: Optional short error message.
        :param explain: Optional detailed explanation.
        """
        if code == 404:
            not_found = Path(self.directory) / "404.html"
            if not_found.exists():
                self.send_response(404)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                with open(not_found, "rb") as f:
                    self.wfile.write(f.read())
                return
        super().send_error(code, message, explain)

    def end_headers(self) -> None:
        """
        Finalize HTTP headers before sending the response.

        Adds no-cache headers if caching is disabled.
        """
        if self._no_cache:
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()


class _ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Threaded TCP server that handles each request in a separate thread."""

    allow_reuse_address = True


class GHPageServer:
    """Lightweight static page server with optional threading, strict routing, base path support, and cache control."""

    def __init__(
        self,
        directory: str = ".",
        port: int = 8000,
        base_path: str = "",
        strict: bool = True,
        no_cache: bool = False,
        threaded: bool = True,
    ):
        """
        Initialize the server.

        :param directory: Root directory to serve files from.
        :param port: Port number to bind the server to.
        :param base_path: URL base path prefix for serving content.
        :param strict: If False, enables automatic ".html" resolution.
        :param no_cache: If True, disables client-side caching.
        :param threaded: If True, handles requests using threads.
        """
        _validate_inputs(
            directory = directory,
            port = port,
            base_pat = base_path,
            strict = strict,
            no_cache = no_cache,
            threaded = threaded,
        )
        self._directory = str(Path(directory).resolve())
        self._port = port
        self._base_path = base_path
        self._strict = strict
        self._no_cache = no_cache
        self._threaded = threaded
        self._httpd = None

    def start(self) -> None:
        """
        Start the HTTP server and serve requests indefinitely.

        Prints server configuration details and blocks until interrupted.
        """
        handler = lambda *args, **kwargs: _GHRequestHandler(
            *args,
            directory=self._directory,
            base_path=self._base_path,
            strict=self._strict,
            no_cache=self._no_cache,
            **kwargs,
        )

        server_cls = _ThreadedTCPServer if self._threaded else socketserver.TCPServer

        self._httpd = server_cls(("", self._port), handler)

        print(f"Serving at http://localhost:{self._port}{self._base_path}")
        print(f"Directory: {self._directory}")
        print(f"Strict mode: {'ON' if self._strict else 'OFF'}")
        print(f"Cache disabled: {'YES' if self._no_cache else 'NO'}")

        try:
            self._httpd.serve_forever()
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        """Stop the running HTTP server and release resources."""
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
            print("Server stopped.")
