# -*- coding: utf-8 -*-
"""ghps functions."""

import argparse
import http.server
import socketserver
import sys
from pathlib import Path
from urllib.parse import unquote


class _GHRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(
        self,
        *args,
        directory=None,
        base_path="",
        strict=True,
        no_cache=False,
        **kwargs,
    ):
        self.base_path = base_path.rstrip("/")
        self.strict = strict
        self.no_cache = no_cache
        super().__init__(*args, directory=directory, **kwargs)

    def translate_path(self, path):
        path = path.split("?", 1)[0]
        path = unquote(path)

        if self.base_path and path.startswith(self.base_path):
            path = path[len(self.base_path):]

        path = path or "/"

        full_path = Path(self.directory) / path.lstrip("/")

        if full_path.is_dir():
            full_path = full_path / "index.html"

        if not self.strict and not full_path.exists() and full_path.suffix == "":
            candidate = full_path.with_suffix(".html")
            if candidate.exists():
                full_path = candidate

        return str(full_path)


    def send_error(self, code, message=None, explain=None):
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


    def end_headers(self):
        if self.no_cache:
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()


class _ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


class GHPageServer:

    def __init__(
        self,
        directory=".",
        port=4000,
        base_path="",
        strict=True,
        no_cache=False,
        threaded=True,
    ):
        self.directory = str(Path(directory).resolve())
        self.port = port
        self.base_path = base_path
        self.strict = strict
        self.no_cache = no_cache
        self.threaded = threaded
        self._httpd = None

    def start(self):
        handler = lambda *args, **kwargs: _GHRequestHandler(
            *args,
            directory=self.directory,
            base_path=self.base_path,
            strict=self.strict,
            no_cache=self.no_cache,
            **kwargs,
        )

        server_cls = _ThreadedTCPServer if self.threaded else socketserver.TCPServer

        self._httpd = server_cls(("", self.port), handler)

        print(f"Serving at http://localhost:{self.port}{self.base_path}")
        print(f"Directory: {self.directory}")
        print(f"Strict mode: {'ON' if self.strict else 'OFF'}")
        print(f"Cache disabled: {'YES' if self.no_cache else 'NO'}")

        try:
            self._httpd.serve_forever()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        if self._httpd:
            self._httpd.shutdown()
            self._httpd.server_close()
            print("Server stopped.")

