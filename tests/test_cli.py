# -*- coding: utf-8 -*-
import sys
import pytest

import ghps.cli



def run_cli(monkeypatch, args):
    monkeypatch.setattr(sys, "argv", ["ghps"] + args)
    monkeypatch.setattr(ghps.cli.GHPageServer, "start", lambda self: None)
    ghps.cli.main()



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