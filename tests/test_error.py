# -*- coding: utf-8 -*-
import pytest
from pathlib import Path
from ghps import GHPageServer
from ghps.params import *


def test_invalid_directory_type():
    with pytest.raises(ValueError, match=INVALID_DIRECTORY_TYPE_ERROR):
        GHPageServer(
            directory=123,
            port=8000,
            base_path="",
            strict=True,
            no_cache=False,
            threaded=True,
        )


def test_directory_not_found():
    with pytest.raises(ValueError, match=DIRECTORY_NOT_FOUND_ERROR):
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

    with pytest.raises(ValueError, match=DIRECTORY_NOT_DIR_ERROR):
        GHPageServer(
            directory=file_path,
            port=8000,
            base_path="",
            strict=True,
            no_cache=False,
            threaded=True,
        )


def test_invalid_port_type(tmp_path):
    with pytest.raises(ValueError, match=INVALID_PORT_TYPE_ERROR):
        GHPageServer(
            directory=tmp_path,
            port="8000",
            base_path="",
            strict=True,
            no_cache=False,
            threaded=True,
        )


def test_invalid_port_range(tmp_path):
    with pytest.raises(ValueError, match=INVALID_PORT_RANGE_ERROR):
        GHPageServer(
            directory=tmp_path,
            port=70000,
            base_path="",
            strict=True,
            no_cache=False,
            threaded=True,
        )


def test_invalid_base_path_type(tmp_path):
    with pytest.raises(ValueError, match=INVALID_BASE_PATH_TYPE_ERROR):
        GHPageServer(
            directory=tmp_path,
            port=8000,
            base_path=123,
            strict=True,
            no_cache=False,
            threaded=True,
        )


def test_invalid_base_path_format(tmp_path):
    with pytest.raises(ValueError, match=INVALID_BASE_PATH_FORMAT_ERROR):
        GHPageServer(
            directory=tmp_path,
            port=8000,
            base_path="docs",
            strict=True,
            no_cache=False,
            threaded=True,
        )


def test_invalid_strict_type(tmp_path):
    with pytest.raises(ValueError, match=INVALID_STRICT_TYPE_ERROR):
        GHPageServer(
            directory=tmp_path,
            port=8000,
            base_path="",
            strict="yes",
            no_cache=False,
            threaded=True,
        )


def test_invalid_no_cache_type(tmp_path):
    with pytest.raises(ValueError, match=INVALID_NO_CACHE_TYPE_ERROR):
        GHPageServer(
            directory=tmp_path,
            port=8000,
            base_path="",
            strict=True,
            no_cache="false",
            threaded=True,
        )


def test_invalid_threaded_type(tmp_path):
    with pytest.raises(ValueError, match=INVALID_THREADED_TYPE_ERROR):
        GHPageServer(
            directory=tmp_path,
            port=8000,
            base_path="",
            strict=True,
            no_cache=False,
            threaded="true",
        )
