# -*- coding: utf-8 -*-
import threading
import time
import tempfile
from pathlib import Path
import requests
from unittest.mock import patch, MagicMock
from ghps import GHPageServer


def run_server(server):
    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()
    time.sleep(0.5)
    return thread


def test_serves_index_html():
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "index.html").write_text("Hello World")

        server = GHPageServer(directory=tmpdir, port=9001)
        run_server(server)

        response = requests.get("http://localhost:9001/", timeout=5)
        assert response.status_code == 200
        assert "Hello World" in response.text

        server.stop()


def test_404_without_custom_page():
    with tempfile.TemporaryDirectory() as tmpdir:
        server = GHPageServer(directory=tmpdir, port=9002)
        run_server(server)

        response = requests.get("http://localhost:9002/missing", timeout=5)
        assert response.status_code == 404

        server.stop()


def test_custom_404_page():
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "404.html").write_text("Custom Not Found")

        server = GHPageServer(directory=tmpdir, port=9003)
        run_server(server)

        response = requests.get("http://localhost:9003/missing", timeout=5)
        assert response.status_code == 404
        assert "Custom Not Found" in response.text

        server.stop()


def test_non_strict_html_fallback():
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "about.html").write_text("About Page")

        server = GHPageServer(directory=tmpdir, port=9004, strict=False)
        run_server(server)

        response = requests.get("http://localhost:9004/about", timeout=5)
        assert response.status_code == 200
        assert "About Page" in response.text

        server.stop()


def test_strict_mode_blocks_html_fallback():
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "about.html").write_text("About Page")

        server = GHPageServer(directory=tmpdir, port=9005, strict=True)
        run_server(server)

        response = requests.get("http://localhost:9005/about", timeout=5)
        assert response.status_code == 404

        server.stop()


def test_base_path_simulation():
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "index.html").write_text("Base Path OK")

        server = GHPageServer(
            directory=tmpdir,
            port=9006,
            base_path="/repo"
        )
        run_server(server)

        response = requests.get("http://localhost:9006/repo/", timeout=5)
        assert response.status_code == 200
        assert "Base Path OK" in response.text

        server.stop()


def test_no_cache_headers():
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "index.html").write_text("Cache Test")

        server = GHPageServer(
            directory=tmpdir,
            port=9007,
            no_cache=True
        )
        run_server(server)

        response = requests.get("http://localhost:9007/", timeout=5)
        assert response.status_code == 200
        assert response.headers.get("Cache-Control") is not None
        assert "no-store" in response.headers["Cache-Control"]

        server.stop()


def test_keyboard_interrupt(capsys):
    mock_server = MagicMock()
    mock_server.serve_forever.side_effect = KeyboardInterrupt

    with patch("ghps.server._ThreadedTCPServer", return_value=mock_server):
        server = GHPageServer(threaded=True)
        server.start()

    captured = capsys.readouterr()
    assert "Server stopped." in captured.out
