# -*- coding: utf-8 -*-
import threading
import time
import tempfile
from pathlib import Path
import requests
from unittest.mock import patch, MagicMock
from ghps import GHPageServer
from ghps.server import _GHRequestHandler
from http import HTTPStatus


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
        assert "404" in response.text
        assert "The requested resource could not be served by Ghps." in response.text
        assert "Ghps/" in response.text

        server.stop()


def test_default_error_page_content():
    with tempfile.TemporaryDirectory() as tmpdir:
        server = GHPageServer(directory=tmpdir, port=9010)
        run_server(server)

        response = requests.get("http://localhost:9010/missing", timeout=5)

        assert response.status_code == 404
        assert response.headers["Content-Type"].startswith("text/html")
        assert "404" in response.text
        assert "The requested resource could not be served by Ghps." in response.text
        assert "A Minimal GitHub Pages Simulator for Local Development" in response.text

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


def test_send_error_uses_default_message(tmp_path):
    handler = _GHRequestHandler.__new__(_GHRequestHandler)

    handler.directory = str(tmp_path)
    handler.wfile = MagicMock()
    handler._no_cache = False

    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()

    _GHRequestHandler.send_error(
        handler,
        404,
        message=None,
        explain="custom explanation",
    )

    html = handler.wfile.write.call_args[0][0].decode("utf-8")

    assert HTTPStatus(404).phrase in html
    assert "custom explanation" in html


def test_send_error_uses_default_explain(tmp_path):
    handler = _GHRequestHandler.__new__(_GHRequestHandler)

    handler.directory = str(tmp_path)
    handler.wfile = MagicMock()
    handler._no_cache = False

    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()

    _GHRequestHandler.send_error(
        handler,
        404,
        message="Custom message",
        explain=None,
    )

    html = handler.wfile.write.call_args[0][0].decode("utf-8")

    assert "Custom message" in html
    assert HTTPStatus(404).description in html


def test_send_error_uses_default_message_and_explain(tmp_path):
    handler = _GHRequestHandler.__new__(_GHRequestHandler)

    handler.directory = str(tmp_path)
    handler.wfile = MagicMock()
    handler._no_cache = False

    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()

    _GHRequestHandler.send_error(
        handler,
        404,
        message=None,
        explain=None,
    )

    html = handler.wfile.write.call_args[0][0].decode("utf-8")

    assert HTTPStatus(404).phrase in html
    assert HTTPStatus(404).description in html


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


@patch("ghps.server.webbrowser.open")
@patch("ghps.server._ThreadedTCPServer")
def test_auto_open_enabled(mock_server_cls, mock_web_open, tmp_path):
    mock_server = mock_server_cls.return_value
    mock_server.server_address = ("127.0.0.1", 8000)
    mock_server.serve_forever.side_effect = KeyboardInterrupt

    server = GHPageServer(
        directory=tmp_path,
        port=8000,
        auto_open=True,
    )

    server.start()

    mock_web_open.assert_called_once_with("http://localhost:8000")


@patch("ghps.server.webbrowser.open")
@patch("ghps.server._ThreadedTCPServer")
def test_auto_open_disabled(mock_server_cls, mock_web_open, tmp_path):
    mock_server = mock_server_cls.return_value
    mock_server.server_address = ("127.0.0.1", 8000)
    mock_server.serve_forever.side_effect = KeyboardInterrupt

    server = GHPageServer(
        directory=tmp_path,
        port=8000,
        auto_open=False,
    )

    server.start()

    mock_web_open.assert_not_called()


@patch("ghps.server._ThreadedTCPServer")
def test_random_port_resolution(mock_server_cls, tmp_path):
    mock_server = mock_server_cls.return_value
    mock_server.server_address = ("127.0.0.1", 54321)
    mock_server.serve_forever.side_effect = KeyboardInterrupt
    server = GHPageServer(
        directory=tmp_path,
        port=0,
    )
    server.start()
    assert server._port == 54321


@patch("ghps.server._ThreadedTCPServer")
def test_custom_host_binding(mock_server_cls, tmp_path):
    mock_server = mock_server_cls.return_value
    mock_server.server_address = ("127.0.0.1", 8000)
    mock_server.serve_forever.side_effect = KeyboardInterrupt

    server = GHPageServer(
        directory=tmp_path,
        port=8000,
        host="127.0.0.1",
    )

    server.start()

    mock_server_cls.assert_called_once()
    address = mock_server_cls.call_args[0][0]

    assert address == ("127.0.0.1", 8000)


def test_directory_listing_enabled():
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "file.txt").write_text("Hello")

        server = GHPageServer(
            directory=tmpdir,
            port=9008,
            directory_listing=True,
        )
        run_server(server)

        response = requests.get("http://localhost:9008/", timeout=5)

        assert response.status_code == 200
        assert "file.txt" in response.text

        server.stop()


def test_directory_listing_disabled():
    with tempfile.TemporaryDirectory() as tmpdir:
        Path(tmpdir, "file.txt").write_text("Hello")

        server = GHPageServer(
            directory=tmpdir,
            port=9009,
            directory_listing=False,
        )
        run_server(server)

        response = requests.get("http://localhost:9009/", timeout=5)

        assert response.status_code == 404

        server.stop()
