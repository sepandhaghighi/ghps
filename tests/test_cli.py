# -*- coding: utf-8 -*-
import sys
from unittest.mock import MagicMock

import pytest

import ghps.cli



def run_cli(monkeypatch, args):
    monkeypatch.setattr(sys, "argv", ["ghps"] + args)
    ghps.cli.main()



def test_cli_default_arguments(monkeypatch):
    mock_server = MagicMock()
    monkeypatch.setattr(ghps, "GHPageServer", MagicMock(return_value=mock_server))

    run_cli(monkeypatch, [])

    ghps.GHPageServer.assert_called_once_with(
        directory=str(ghps.Path(".").resolve()),
        port=8000,
        base_path="",
        strict=True,
        no_cache=False,
        threaded=True,
    )

    mock_server.start.assert_called_once()


def test_cli_custom_port_and_directory(monkeypatch, tmp_path):
    mock_server = MagicMock()
    monkeypatch.setattr(ghps, "GHPageServer", MagicMock(return_value=mock_server))

    run_cli(monkeypatch, ["-p", "9090", "-d", str(tmp_path)])

    ghps.GHPageServer.assert_called_once()
    kwargs = ghps.GHPageServer.call_args.kwargs

    assert kwargs["port"] == 9090
    assert kwargs["directory"] == str(tmp_path.resolve())

    mock_server.start.assert_called_once()



def test_cli_base_path(monkeypatch):
    mock_server = MagicMock()
    monkeypatch.setattr(ghps, "GHPageServer", MagicMock(return_value=mock_server))

    run_cli(monkeypatch, ["-b", "/repo"])

    kwargs = ghps.GHPageServer.call_args.kwargs
    assert kwargs["base_path"] == "/repo"



def test_cli_no_strict(monkeypatch):
    mock_server = MagicMock()
    monkeypatch.setattr(ghps, "GHPageServer", MagicMock(return_value=mock_server))

    run_cli(monkeypatch, ["--no-strict"])

    kwargs = ghps.GHPageServer.call_args.kwargs
    assert kwargs["strict"] is False



def test_cli_no_cache(monkeypatch):
    mock_server = MagicMock()
    monkeypatch.setattr(ghps, "GHPageServer", MagicMock(return_value=mock_server))

    run_cli(monkeypatch, ["--no-cache"])

    kwargs = ghps.GHPageServer.call_args.kwargs
    assert kwargs["no_cache"] is True


def test_cli_no_threaded(monkeypatch):
    mock_server = MagicMock()
    monkeypatch.setattr(ghps, "GHPageServer", MagicMock(return_value=mock_server))

    run_cli(monkeypatch, ["--no-threaded"])

    kwargs = ghps.GHPageServer.call_args.kwargs
    assert kwargs["threaded"] is False


def test_cli_invalid_directory(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["ghps", "-d", "non_existent_dir"])

    with pytest.raises(SystemExit):
        ghps.cli.main()