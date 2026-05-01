# -*- coding: utf-8 -*-
"""ghps errors."""


class GHPSError(Exception):
    """Base exception for GHPS."""


class GHPSValidationError(GHPSError, ValueError):
    """Raised for invalid input parameters."""


class GHPSRuntimeError(GHPSError):
    """Raised for runtime errors during server execution."""
