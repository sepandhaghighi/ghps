# -*- coding: utf-8 -*-
"""ghps params."""

GHPS_VERSION = "0.1"

INVALID_DIRECTORY_TYPE_ERROR = "`directory` must be str or pathlib.Path."
DIRECTORY_NOT_FOUND_ERROR = "`directory` does not exist."
DIRECTORY_NOT_DIR_ERROR = "`directory` must be a valid directory."

INVALID_PORT_TYPE_ERROR = "`port` must be int."
INVALID_PORT_RANGE_ERROR = "`port` must be between 1 and 65535."

INVALID_BASE_PATH_TYPE_ERROR = "`base_path` must be str."
INVALID_BASE_PATH_FORMAT_ERROR = "`base_path` must start with '/' or be empty."

INVALID_STRICT_TYPE_ERROR = "`strict` must be bool."
INVALID_NO_CACHE_TYPE_ERROR = "`no_cache` must be bool."
INVALID_THREADED_TYPE_ERROR = "`threaded` must be bool."
