"""Bitplane encoding for multi-color e-paper displays."""

from __future__ import annotations

import logging

import numpy as np
from epaper_dithering import ColorScheme
from PIL import Image

_LOGGER = logging.getLogger(__name__)


def encode_bitplanes(
        image: Image.Image,
        color_scheme: ColorScheme,
) -> tuple[bytes, bytes]: # TODO huh, why only two planes? we have displays that have many more colors!?
    """Encode image to bitplane format for BWR/BWY displays.

    BWR/BWY displays use two bitplanes:
    - Plane 1 (BW): Black/White layer
    - Plane 2 (R/Y): Red/Yellow accent color layer

    Args:
        image: Dithered palette image
        color_scheme: Must be BWR or BWY

    Returns:
        Tuple of (plane1_bytes, plane2_bytes)

    Raises:
        ValueError: If color_scheme is not BWR or BWY
    """
    if color_scheme not in (ColorScheme.BWR, ColorScheme.BWY):
        raise ValueError(
            f"Bitplane encoding only supports BWR/BWY, got {color_scheme.name}"
        )

    if image.mode != "P":
        raise ValueError(f"Expected palette image, got {image.mode}")

    pixels = np.array(image)
    height, width = pixels.shape

    # Calculate output size (1bpp, 8 pixels per byte)
    bytes_per_row = (width + 7) // 8
    plane1 = bytearray(bytes_per_row * height)  # BW plane
    plane2 = bytearray(bytes_per_row * height)  # R/Y plane

    # Palette mapping:
    # Index 0 = Black -> BW=0, R/Y=0
    # Index 1 = White -> BW=1, R/Y=0
    # Index 2 = Red/Yellow -> BW=0, R/Y=1

    for y in range(height):
        for x in range(width):
            byte_idx = y * bytes_per_row + x // 8
            bit_idx = 7 - (x % 8)  # MSB first

            palette_idx = pixels[y, x]

            if palette_idx == 1:
                # White - set BW plane
                plane1[byte_idx] |= (1 << bit_idx)
            elif palette_idx == 2:
                # Red/Yellow - set R/Y plane
                plane2[byte_idx] |= (1 << bit_idx)
            # else: palette_idx == 0 (black) - both planes stay 0

    return bytes(plane1), bytes(plane2)
