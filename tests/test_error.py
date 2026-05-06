# -*- coding: utf-8 -*-
import errno
import pytest
from unittest.mock import patch
from ghps import GHPageServer, GHPSValidationError. GHPSRuntimeError


def test_invalid_directory_type():
    with pytest.raises(GHPSValidationError, match="`directory` must be str or pathlib.Path."):
        GHPageServer(
            directory=123,
            port=8000,
            base_path="",
            strict=True,
            no_cache=False,
            threaded=True,
        )


def test_directory_not_found():
    with pytest.raises(GHPSValidationError, match="`directory` does not exist."):
        GHPageServer(
            directory="__not_existing_dir__",
            port=8000,
            base_path="",
            strict=True,
            no_cache=False,
            threaded=True,
        )


def test_directory_not_directory(tmp_path):
    file_path = tmp_path / "file.txt"
    file_path.write_text("data")

    with pytest.raises(GHPSValidationError, match="`directory` must be a valid directory."):
        GHPageServer(
            directory=file_path,
            port=8000,
            base_path="",
            strict=True,
            no_cache=False,
            threaded=True,
        )


def test_invalid_port_type(tmp_path):
    with pytest.raises(GHPSValidationError, match="`port` must be int."):
        GHPageServer(
            directory=tmp_path,
            port="8000",
            base_path="",
            strict=True,
            no_cache=False,
            threaded=True,
        )


def test_invalid_port_range(tmp_path):
    with pytest.raises(GHPSValidationError, match="`port` must be between 1 and 65535."):
        GHPageServer(
            directory=tmp_path,
            port=70000,
            base_path="",
            strict=True,
            no_cache=False,
            threaded=True,
        )


def test_invalid_base_path_type(tmp_path):
    with pytest.raises(GHPSValidationError, match="`base_path` must be str."):
        GHPageServer(
            directory=tmp_path,
            port=8000,
            base_path=123,
            strict=True,
            no_cache=False,
            threaded=True,
        )


def test_invalid_base_path_format(tmp_path):
    with pytest.raises(GHPSValidationError, match="`base_path` must start with '/' or be empty."):
        GHPageServer(
            directory=tmp_path,
            port=8000,
            base_path="docs",
            strict=True,
            no_cache=False,
            threaded=True,
        )


def test_invalid_strict_type(tmp_path):
    with pytest.raises(GHPSValidationError, match="`strict` must be bool."):
        GHPageServer(
            directory=tmp_path,
            port=8000,
            base_path="",
            strict="yes",
            no_cache=False,
            threaded=True,
        )


def test_invalid_no_cache_type(tmp_path):
    with pytest.raises(GHPSValidationError, match="`no_cache` must be bool."):
        GHPageServer(
            directory=tmp_path,
            port=8000,
            base_path="",
            strict=True,
            no_cache="false",
            threaded=True,
        )


def test_invalid_threaded_type(tmp_path):
    with pytest.raises(GHPSValidationError, match="`threaded` must be bool."):
        GHPageServer(
            directory=tmp_path,
            port=8000,
            base_path="",
            strict=True,
            no_cache=False,
            threaded="true",
        )


def test_invalid_auto_open_type(tmp_path):
    with pytest.raises(GHPSValidationError, match="`auto_open` must be bool."):
        GHPageServer(
            directory=tmp_path,
            port=8000,
            base_path="",
            strict=True,
            no_cache=False,
            threaded=True,
            auto_open="true",
        )


@patch("ghps.server.webbrowser.open", side_effect=Exception("boom"))
@patch("ghps.server._ThreadedTCPServer")
@patch("builtins.print")
def test_auto_open_failure_logs_error(mock_print, mock_server_cls, mock_web_open, tmp_path):
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
    assert any(
        "[GHPS ERROR]: Failed to open browser automatically" in str(call)
        for call in mock_print.call_args_list
    )


@patch("ghps.server._ThreadedTCPServer")
def test_port_in_use_error(mock_server_cls, tmp_path):
    mock_server_cls.side_effect = OSError(errno.EADDRINUSE, "in use")

    server = GHPageServer(directory=tmp_path, port=8000)

    with pytest.raises(GHPSRuntimeError) as exc:
        server.start()

    assert "`port` is already in use" in str(exc.value)


@patch("ghps.server._ThreadedTCPServer")
def test_port_access_denied_error(mock_server_cls, tmp_path):
    mock_server_cls.side_effect = OSError(errno.EACCES, "denied")

    server = GHPageServer(directory=tmp_path, port=80)

    with pytest.raises(GHPSRuntimeError) as exc:
        server.start()

    assert "`port` access denied" in str(exc.value)


@patch("ghps.server._ThreadedTCPServer")
def test_port_generic_error(mock_server_cls, tmp_path):
    mock_server_cls.side_effect = OSError(9999, "boom")

    server = GHPageServer(directory=tmp_path, port=8000)

    with pytest.raises(GHPSRuntimeError) as exc:
        server.start()

    assert "Failed to start server on port" in str(exc.value)
