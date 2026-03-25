# -*- coding: utf-8 -*-
import pytest
from ghps import GHPageServer


def test_invalid_directory_type():
    with pytest.raises(ValueError, match="`directory` must be str or pathlib.Path."):
        GHPageServer(
            directory=123,
            port=8000,
            base_path="",
            strict=True,
            no_cache=False,
            threaded=True,
        )


def test_directory_not_found():
    with pytest.raises(ValueError, match="`directory` does not exist."):
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

    with pytest.raises(ValueError, match="`directory` must be a valid directory."):
        GHPageServer(
            directory=file_path,
            port=8000,
            base_path="",
            strict=True,
            no_cache=False,
            threaded=True,
        )


def test_invalid_port_type(tmp_path):
    with pytest.raises(ValueError, match="`port` must be int."):
        GHPageServer(
            directory=tmp_path,
            port="8000",
            base_path="",
            strict=True,
            no_cache=False,
            threaded=True,
        )


def test_invalid_port_range(tmp_path):
    with pytest.raises(ValueError, match="`port` must be between 1 and 65535."):
        GHPageServer(
            directory=tmp_path,
            port=70000,
            base_path="",
            strict=True,
            no_cache=False,
            threaded=True,
        )


def test_invalid_base_path_type(tmp_path):
    with pytest.raises(ValueError, match="`base_path` must be str."):
        GHPageServer(
            directory=tmp_path,
            port=8000,
            base_path=123,
            strict=True,
            no_cache=False,
            threaded=True,
        )


def test_invalid_base_path_format(tmp_path):
    with pytest.raises(ValueError, match="`base_path` must start with '/' or be empty."):
        GHPageServer(
            directory=tmp_path,
            port=8000,
            base_path="docs",
            strict=True,
            no_cache=False,
            threaded=True,
        )


def test_invalid_strict_type(tmp_path):
    with pytest.raises(ValueError, match="`strict` must be bool."):
        GHPageServer(
            directory=tmp_path,
            port=8000,
            base_path="",
            strict="yes",
            no_cache=False,
            threaded=True,
        )


def test_invalid_no_cache_type(tmp_path):
    with pytest.raises(ValueError, match="`no_cache` must be bool."):
        GHPageServer(
            directory=tmp_path,
            port=8000,
            base_path="",
            strict=True,
            no_cache="false",
            threaded=True,
        )


def test_invalid_threaded_type(tmp_path):
    with pytest.raises(ValueError, match="`threaded` must be bool."):
        GHPageServer(
            directory=tmp_path,
            port=8000,
            base_path="",
            strict=True,
            no_cache=False,
            threaded="true",
        )


def test_invalid_auto_open_type(tmp_path):
    with pytest.raises(ValueError, match="`auto_open` must be bool."):
        GHPageServer(
            directory=tmp_path,
            port=8000,
            base_path="",
            strict=True,
            no_cache=False,
            threaded=true,
            auto_open="true",
        )
