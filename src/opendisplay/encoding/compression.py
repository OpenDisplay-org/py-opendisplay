"""Image compression for BLE transfer."""

from __future__ import annotations

import logging
import zlib

_LOGGER = logging.getLogger(__name__)


def compress_image_data(data: bytes, level: int = 6) -> bytes:
    """Compress image data using zlib.

    Args:
        data: Raw image data
        level: Compression level (0-9, default: 6)
            0 = no compression
            1 = fastest
            6 = default balance
            9 = best compression

    Returns:
        Compressed data
    """
    if level == 0:
        return data

    compressed = zlib.compress(data, level=level)

    ratio = len(compressed) / len(data) * 100 if data else 0
    _LOGGER.debug(
        "Compressed %d bytes -> %d bytes (%.1f%%)",
        len(data),
        len(compressed),
        ratio,
    )

    return compressed


def decompress_image_data(data: bytes) -> bytes:
    """Decompress zlib-compressed image data.

    Args:
        data: Compressed data

    Returns:
        Decompressed data

    Raises:
        zlib.error: If decompression fails
    """
    return zlib.decompress(data)
