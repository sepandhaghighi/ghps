# -*- coding: utf-8 -*-
import sys
from unittest.mock import patch
import pytest
from ghps.params import GHPS_VERSION
import ghps.cli


def run_cli(monkeypatch, args):
    monkeypatch.setattr(sys, "argv", ["ghps"] + args)
    monkeypatch.setattr(ghps.cli.GHPageServer, "start", lambda self: None)
    ghps.cli.main()


def test_version_flag(capsys):
    with patch("sys.argv", ["ghps", "--version"]):
        ghps.cli.main()
    out, _ = capsys.readouterr()
    assert out.strip() == GHPS_VERSION


def test_cli_default_arguments(monkeypatch):
    captured = {}

    def fake_init(self, **kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(ghps.cli, "GHPageServer", type(
        "MockServer",
        (),
        {
            "__init__": fake_init,
            "start": lambda self: None,
        },
    ))

    run_cli(monkeypatch, [])

    assert captured["port"] == 8000
    assert captured["strict"] is True
    assert captured["no_cache"] is False
    assert captured["threaded"] is True


def test_cli_custom_port_and_directory(monkeypatch, tmp_path):
    captured = {}

    def fake_init(self, **kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(ghps.cli, "GHPageServer", type(
        "MockServer",
        (),
        {
            "__init__": fake_init,
            "start": lambda self: None,
        },
    ))

    run_cli(monkeypatch, ["-p", "9090", "-d", str(tmp_path)])

    assert captured["port"] == 9090
    assert captured["directory"] == str(tmp_path.resolve())


def test_cli_base_path(monkeypatch):
    captured = {}

    def fake_init(self, **kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(ghps.cli, "GHPageServer", type(
        "MockServer",
        (),
        {
            "__init__": fake_init,
            "start": lambda self: None,
        },
    ))

    run_cli(monkeypatch, ["-b", "/repo"])

    assert captured["base_path"] == "/repo"


def test_cli_flags(monkeypatch):
    captured = {}

    def fake_init(self, **kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(ghps.cli, "GHPageServer", type(
        "MockServer",
        (),
        {
            "__init__": fake_init,
            "start": lambda self: None,
        },
    ))

    run_cli(monkeypatch, ["--no-strict", "--no-cache", "--no-threaded"])

    assert captured["strict"] is False
    assert captured["no_cache"] is True
    assert captured["threaded"] is False


def test_cli_invalid_directory(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["ghps", "-d", "non_existent_dir"])

    with pytest.raises(SystemExit):
        ghps.cli.main()


@patch("ghps.cli.GHPageServer")
@patch("sys.stderr")
def test_cli_unexpected_error(mock_stderr, mock_server_cls):
    mock_server = mock_server_cls.return_value
    mock_server.start.side_effect = Exception("boom")
    test_args = ["ghps"]
    with patch("sys.argv", test_args):
        with pytest.raises(SystemExit) as exc:
            ghps.cli.main()
    assert exc.value.code == 1
    written = "".join(call.args[0] for call in mock_stderr.write.call_args_list)
    assert "[GHPS ERROR] Unexpected error: boom" in written
