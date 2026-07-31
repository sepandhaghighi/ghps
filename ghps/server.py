# -*- coding: utf-8 -*-
"""ghps server."""

import http.server
import socketserver
import webbrowser
import errno
from functools import partial
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
    INVALID_AUTO_OPEN_TYPE_ERROR,
    INVALID_DIRECTORY_LISTING_TYPE_ERROR
)
from .params import (
    PORT_IN_USE_ERROR,
    PORT_ACCESS_DENIED_ERROR,
    PORT_ADDRESS_NOT_AVAILABLE_ERROR,
    PORT_BIND_GENERIC_ERROR,
)
from .errors import GHPSValidationError, GHPSRuntimeError


def _validate_inputs(
    directory: Any,
    port: Any,
    base_path: Any,
    strict: Any,
    no_cache: Any,
    threaded: Any,
    auto_open: Any,
    directory_listing: Any
):
    """
    Validate GHPageServer inputs.

    :param directory: Root directory to serve files from.
    :param port: Port number to bind the server to.
    :param base_path: URL base path prefix for serving content.
    :param strict: If False, enables automatic ".html" resolution.
    :param no_cache: If True, disables client-side caching.
    :param threaded: If True, handles requests using threads.
    :param auto_open: If True, automatically opens the server URL in the default web browser.
    :param directory_listing: If True, enables directory listing.
    """
    if not isinstance(directory, (str, Path)):
        raise GHPSValidationError(INVALID_DIRECTORY_TYPE_ERROR)

    directory = Path(directory)
    if not directory.exists():
        raise GHPSValidationError(DIRECTORY_NOT_FOUND_ERROR)

    if not directory.is_dir():
        raise GHPSValidationError(DIRECTORY_NOT_DIR_ERROR)

    if not isinstance(port, int) or isinstance(port, bool):
        raise GHPSValidationError(INVALID_PORT_TYPE_ERROR)

    if not (0 <= port <= 65535):
        raise GHPSValidationError(INVALID_PORT_RANGE_ERROR)

    if not isinstance(base_path, str):
        raise GHPSValidationError(INVALID_BASE_PATH_TYPE_ERROR)

    if base_path and not base_path.startswith("/"):
        raise GHPSValidationError(INVALID_BASE_PATH_FORMAT_ERROR)

    if not isinstance(strict, bool):
        raise GHPSValidationError(INVALID_STRICT_TYPE_ERROR)

    if not isinstance(no_cache, bool):
        raise GHPSValidationError(INVALID_NO_CACHE_TYPE_ERROR)

    if not isinstance(threaded, bool):
        raise GHPSValidationError(INVALID_THREADED_TYPE_ERROR)

    if not isinstance(auto_open, bool):
        raise GHPSValidationError(INVALID_AUTO_OPEN_TYPE_ERROR)

    if not isinstance(directory_listing, bool):
        raise GHPSValidationError(INVALID_DIRECTORY_LISTING_TYPE_ERROR)


def _handle_bind_error(port: int, e: OSError) -> None:
    """
    Handle socket binding errors and raise a user-friendly runtime exception.

    :param port: Port number that the server attempted to bind to.
    :param e: Original OSError raised during binding.
    """
    err = getattr(e, "errno", None)

    if err == errno.EADDRINUSE:
        raise GHPSRuntimeError(PORT_IN_USE_ERROR) from e

    elif err in (errno.EACCES, errno.EPERM):
        raise GHPSRuntimeError(PORT_ACCESS_DENIED_ERROR) from e

    elif err == errno.EADDRNOTAVAIL:
        raise GHPSRuntimeError(PORT_ADDRESS_NOT_AVAILABLE_ERROR) from e

    else:
        raise GHPSRuntimeError(
            PORT_BIND_GENERIC_ERROR.format(port=port, error=e)
        ) from e


class _GHRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler for serving static files with optional base path stripping, strict routing, custom 404 page support, and cache control headers."""

    def __init__(
        self,
        *args: list,
        directory: Optional[str] = None,
        base_path: str = "",
        strict: bool = True,
        no_cache: bool = False,
        directory_listing=False,
        **kwargs: dict,
    ):
        """
        Initialize the request handler.

        :param args: Arguments.
        :param directory: Root directory to serve files from.
        :param base_path: URL base path prefix to strip from incoming requests.
        :param strict: If False, allows resolving paths without extension to ".html".
        :param no_cache: If True, disables client-side caching via headers.
        :param directory_listing: If True, enables directory listing.
        :param kwargs: Keyword arguments.
        """
        self._base_path = base_path.rstrip("/")
        self._strict = strict
        self._no_cache = no_cache
        self._directory_listing = directory_listing
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

        if full_path.is_dir() and not self._directory_listing:
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
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(not_found.stat().st_size))
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
        auto_open: bool = False,
        directory_listing: bool = False
    ):
        """
        Initialize the server.

        :param directory: Root directory to serve files from.
        :param port: Port number to bind the server to.
        :param base_path: URL base path prefix for serving content.
        :param strict: If False, enables automatic ".html" resolution.
        :param no_cache: If True, disables client-side caching.
        :param threaded: If True, handles requests using threads.
        :param auto_open: If True, automatically opens the server URL in the default web browser.
        :param directory_listing: If True, enables directory listing.
        """
        _validate_inputs(
            directory=directory,
            port=port,
            base_path=base_path,
            strict=strict,
            no_cache=no_cache,
            threaded=threaded,
            auto_open=auto_open,
            directory_listing=directory_listing
        )
        self._directory = str(Path(directory).resolve())
        self._port = port
        self._url = None
        self._base_path = base_path
        self._strict = strict
        self._no_cache = no_cache
        self._threaded = threaded
        self._auto_open = auto_open
        self._directory_listing = directory_listing
        self._httpd = None

    def _print_server_info(self) -> None:
        """Print the current server configuration and access URL."""
        print(f"Serving at {self._url}")
        print(f"Directory: {self._directory}")
        print(f"Strict mode: {'ON' if self._strict else 'OFF'}")
        print(f"Cache disabled: {'YES' if self._no_cache else 'NO'}")

    def start(self) -> None:
        """
        Start the HTTP server and serve requests indefinitely.

        Prints server configuration details and blocks until interrupted.
        """
        handler = partial(
            _GHRequestHandler,
            directory=self._directory,
            base_path=self._base_path,
            strict=self._strict,
            no_cache=self._no_cache,
            directory_listing=self._directory_listing
        )

        server_cls = _ThreadedTCPServer if self._threaded else socketserver.TCPServer

        try:
            self._httpd = server_cls(("", self._port), handler)
        except OSError as e:
            _handle_bind_error(self._port, e)
        self._port = self._httpd.server_address[1]
        self._url = f"http://localhost:{self._port}{self._base_path}"
        self._print_server_info()

        if self._auto_open:
            try:
                webbrowser.open(self._url)
            except Exception:
                print("[GHPS ERROR]: Failed to open browser automatically")
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
