"""Exceptions for opendisplay package."""

from __future__ import annotations


class OpenDisplayError(Exception):
    """Base exception for all opendisplay errors."""
    pass


class BLEConnectionError(OpenDisplayError):
    """BLE connection failed."""
    pass


class BLETimeoutError(OpenDisplayError):
    """Operation timed out."""
    pass


class ProtocolError(OpenDisplayError):
    """Protocol communication error."""
    pass


class ConfigParseError(ProtocolError):
    """Failed to parse device configuration."""
    pass


class InvalidResponseError(ProtocolError):
    """Device returned invalid response."""
    pass


class ImageEncodingError(OpenDisplayError):
    """Failed to encode image."""
    pass