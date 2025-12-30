"""Firmware version data structure."""

from __future__ import annotations

from typing import TypedDict


class FirmwareVersion(TypedDict):
    """Firmware version information.

    Attributes:
        major: Major version number (0-255)
        minor: Minor version number (0-255)
        sha: Git commit SHA hash
    """

    major: int
    minor: int
    sha: str
