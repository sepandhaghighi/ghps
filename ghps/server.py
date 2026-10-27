# -*- coding: utf-8 -*-
"""ghps server."""
try:
    import tomllib
except ImportError:
    import tomli as tomllib
import http.server
from http import HTTPStatus
import socketserver
import webbrowser
import errno
from functools import partial
from typing import Optional, Any, Union
from pathlib import Path
from urllib.parse import unquote
from .params import (
    GHPS_VERSION,
    GHPS_REPO,
    DEFAULT_ERROR_PAGE,
    INVALID_DIRECTORY_TYPE_ERROR,
    DIRECTORY_NOT_FOUND_ERROR,
    DIRECTORY_NOT_DIR_ERROR,
    INVALID_HOST_TYPE_ERROR,
    INVALID_PORT_TYPE_ERROR,
    INVALID_PORT_RANGE_ERROR,
    INVALID_BASE_PATH_TYPE_ERROR,
    INVALID_BASE_PATH_FORMAT_ERROR,
    INVALID_STRICT_TYPE_ERROR,
    INVALID_NO_CACHE_TYPE_ERROR,
    INVALID_THREADED_TYPE_ERROR,
    INVALID_AUTO_OPEN_TYPE_ERROR,
    INVALID_DIRECTORY_LISTING_TYPE_ERROR,
    INVALID_QUIET_TYPE_ERROR,
    INVALID_CONFIG_TYPE_ERROR,
    INVALID_CONFIG_FILE_ERROR,
    INVALID_CONFIG_FORMAT_ERROR
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
    host: Any,
    port: Any,
    base_path: Any,
    strict: Any,
    no_cache: Any,
    threaded: Any,
    auto_open: Any,
    directory_listing: Any,
    quiet: Any
):
    """
    Validate GHPageServer inputs.

    :param directory: Root directory to serve files from.
    :param host: Host address to bind the server to.
    :param port: Port number to bind the server to.
    :param base_path: URL base path prefix for serving content.
    :param strict: If False, enables automatic ".html" resolution.
    :param no_cache: If True, disables client-side caching.
    :param threaded: If True, handles requests using threads.
    :param auto_open: If True, automatically opens the server URL in the default web browser.
    :param directory_listing: If True, enables directory listing.
    :param quiet: If True, suppresses informational server output.
    """
    if not isinstance(directory, (str, Path)):
        raise GHPSValidationError(INVALID_DIRECTORY_TYPE_ERROR)

    directory = Path(directory)
    if not directory.exists():
        raise GHPSValidationError(DIRECTORY_NOT_FOUND_ERROR)

    if not directory.is_dir():
        raise GHPSValidationError(DIRECTORY_NOT_DIR_ERROR)

    if not isinstance(host, str):
        raise GHPSValidationError(INVALID_HOST_TYPE_ERROR)

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

    if not isinstance(quiet, bool):
        raise GHPSValidationError(INVALID_QUIET_TYPE_ERROR)


def _load_config(directory: Union[str, Path], config_source: Optional[Union[str, Path, dict]] = None, auto_discover: bool = False) -> dict:
    """
    Load config.

    :param directory: Root directory.
    :param config_source: Config source.
    :param auto_discover: Auto discover flag.
    """
    if config_source is None:
        if not auto_discover:
            return {}
        dir_path = Path(directory)
        if dir_path.exists() and dir_path.is_dir():
            candidate = dir_path / ".ghps"
            if candidate.exists() and candidate.is_file():
                config_path = candidate
            else:
                return {}
        else:
            return {}
    elif isinstance(config_source, dict):
        return config_source
    elif isinstance(config_source, (str, Path)):
        config_path = Path(config_source)
    else:
        raise GHPSValidationError(INVALID_CONFIG_TYPE_ERROR)

    if not config_path.exists():
        return {}

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
            if not isinstance(data, dict):
                raise GHPSValidationError(INVALID_CONFIG_FORMAT_ERROR)
            return data
    except Exception as e:
        if isinstance(e, GHPSValidationError):
            raise e
        raise GHPSValidationError(INVALID_CONFIG_FILE_ERROR.format(error=e))


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

    server_version = f"Ghps/{GHPS_VERSION}"
    sys_version = ""

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
        if message is None:
            message = HTTPStatus(code).phrase
        if explain is None:
            explain = HTTPStatus(code).description

        html = DEFAULT_ERROR_PAGE.format(
            code=code,
            message=message,
            explain=explain,
            version=GHPS_VERSION,
            repo=GHPS_REPO,
        )

        encoded = html.encode("utf-8")

        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

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
        host: str = "localhost",
        port: int = 8000,
        base_path: str = "",
        strict: bool = True,
        no_cache: bool = False,
        threaded: bool = True,
        auto_open: bool = False,
        directory_listing: bool = False,
        quiet: bool = False
    ):
        """
        Initialize the server.

        :param directory: Root directory to serve files from.
        :param host: Host address to bind the server to.
        :param port: Port number to bind the server to.
        :param base_path: URL base path prefix for serving content.
        :param strict: If False, enables automatic ".html" resolution.
        :param no_cache: If True, disables client-side caching.
        :param threaded: If True, handles requests using threads.
        :param auto_open: If True, automatically opens the server URL in the default web browser.
        :param directory_listing: If True, enables directory listing.
        :param quiet: If True, suppresses informational server output.
        """
        _validate_inputs(
            directory=directory,
            host=host,
            port=port,
            base_path=base_path,
            strict=strict,
            no_cache=no_cache,
            threaded=threaded,
            auto_open=auto_open,
            directory_listing=directory_listing,
            quiet=quiet
        )
        self._directory = str(Path(directory).resolve())
        self._host = host
        self._port = port
        self._url = None
        self._base_path = base_path
        self._strict = strict
        self._no_cache = no_cache
        self._threaded = threaded
        self._auto_open = auto_open
        self._directory_listing = directory_listing
        self._quiet = quiet
        self._httpd = None

    def _print_server_info(self) -> None:
        """Print the current server configuration and access URL."""
        if self._quiet:
            return

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
            self._httpd = server_cls((self._host, self._port), handler)
        except OSError as e:
            _handle_bind_error(self._port, e)
        self._port = self._httpd.server_address[1]
        self._url = f"http://{self._host}:{self._port}{self._base_path}"
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
    
    @classmethod
    def from_config(
        cls,
        config: Optional[Union[str, Path, dict]] = None,
        directory: Optional[str] = None,
        host: Optional[str] = None,
        port: Optional[int] = None,
        base_path: Optional[str] = None,
        strict: Optional[bool] = None,
        no_cache: Optional[bool] = None,
        threaded: Optional[bool] = None,
        auto_open: Optional[bool] = None,
        directory_listing: Optional[bool] = None,
        quiet: Optional[bool] = None,
        auto_discover: bool = False,
    ):
        """
        Create a GHPageServer instance from a configuration file or dictionary, with explicit parameter overrides.

        :param config: Config input.
        :param directory: Root directory to serve files from.
        :param host: Host address to bind the server to.
        :param port: Port number to bind the server to.
        :param base_path: URL base path prefix for serving content.
        :param strict: If False, enables automatic ".html" resolution.
        :param no_cache: If True, disables client-side caching.
        :param threaded: If True, handles requests using threads.
        :param auto_open: If True, automatically opens the server URL in the default web browser.
        :param directory_listing: If True, enables directory listing.
        :param quiet: If True, suppresses informational server output.
        :param auto_discover: Auto discover flag.
        """
        init_directory = directory if directory is not None else "."
        loaded_config = _load_config(init_directory, config, auto_discover=auto_discover)

        resolved_directory = directory if directory is not None else loaded_config.get("directory", ".")
        resolved_host = host if host is not None else loaded_config.get("host", "localhost")
        resolved_port = port if port is not None else loaded_config.get("port", 8000)
        resolved_base_path = base_path if base_path is not None else loaded_config.get("base_path", "")
        resolved_strict = strict if strict is not None else loaded_config.get("strict", True)
        resolved_no_cache = no_cache if no_cache is not None else loaded_config.get("no_cache", False)
        resolved_threaded = threaded if threaded is not None else loaded_config.get("threaded", True)
        resolved_auto_open = auto_open if auto_open is not None else loaded_config.get("auto_open", False)
        resolved_directory_listing = directory_listing if directory_listing is not None else loaded_config.get("directory_listing", False)
        resolved_quiet = quiet if quiet is not None else loaded_config.get("quiet", False)

        return cls(
            directory=resolved_directory,
            host=resolved_host,
            port=resolved_port,
            base_path=resolved_base_path,
            strict=resolved_strict,
            no_cache=resolved_no_cache,
            threaded=resolved_threaded,
            auto_open=resolved_auto_open,
            directory_listing=resolved_directory_listing,
            quiet=resolved_quiet,
        )
