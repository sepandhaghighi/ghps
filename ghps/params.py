# -*- coding: utf-8 -*-
"""ghps params."""

GHPS_VERSION = "0.6"
GHPS_REPO = "https://github.com/sepandhaghighi/ghps"

INVALID_DIRECTORY_TYPE_ERROR = "`directory` must be str or pathlib.Path."
DIRECTORY_NOT_FOUND_ERROR = "`directory` does not exist."
DIRECTORY_NOT_DIR_ERROR = "`directory` must be a valid directory."

INVALID_PORT_TYPE_ERROR = "`port` must be int."
INVALID_PORT_RANGE_ERROR = "`port` must be between 0 and 65535."

INVALID_BASE_PATH_TYPE_ERROR = "`base_path` must be str."
INVALID_BASE_PATH_FORMAT_ERROR = "`base_path` must start with '/' or be empty."

INVALID_STRICT_TYPE_ERROR = "`strict` must be bool."
INVALID_NO_CACHE_TYPE_ERROR = "`no_cache` must be bool."
INVALID_THREADED_TYPE_ERROR = "`threaded` must be bool."
INVALID_AUTO_OPEN_TYPE_ERROR = "`auto_open` must be bool."
INVALID_DIRECTORY_LISTING_TYPE_ERROR = "`directory_listing` must be bool."

PORT_IN_USE_ERROR = "`port` is already in use. Try another port or use `0` for automatic allocation."
PORT_ACCESS_DENIED_ERROR = "`port` access denied. Try a different port or check permissions."
PORT_ADDRESS_NOT_AVAILABLE_ERROR = "`port` address is not available. Check network configuration."
PORT_BIND_GENERIC_ERROR = "Failed to start server on port `{port}`: {error}"

DEFAULT_ERROR_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{code} - {message}</title>
    <style>
        body {{
            margin: 0;
            padding: 40px 20px;
            font-family: system-ui, -apple-system, BlinkMacSystemFont,
                         "Segoe UI", sans-serif;
            background: #f6f8fa;
            color: #24292f;
        }}

        main {{
            max-width: 720px;
            margin: 80px auto;
            padding: 40px;
            background: #ffffff;
            border: 1px solid #d0d7de;
            border-radius: 8px;
        }}

        h1 {{
            margin: 0 0 12px;
            font-size: 32px;
        }}

        p {{
            margin: 8px 0;
            color: #57606a;
        }}

        .status {{
            font-size: 18px;
            font-weight: 600;
            color: #24292f;
        }}

        footer {{
            margin-top: 32px;
            padding-top: 16px;
            border-top: 1px solid #d0d7de;
            font-size: 13px;
            color: #57606a;
        }}
    </style>
</head>
<body>
    <main>
        <h1>{code}</h1>
        <p class="status">{message}</p>
        <p>{explain}</p>
        <p>The requested resource could not be served by Ghps.</p>

        <footer>
            <a href="{repo}">Ghps/{version} &mdash; A Minimal GitHub Pages Simulator for Local Development</a>
        </footer>
    </main>
</body>
</html>
"""
