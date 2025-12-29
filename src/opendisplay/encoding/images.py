"""Image encoding for e-paper displays."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image

if TYPE_CHECKING:
    from ..models.enums import ColorScheme

_LOGGER = logging.getLogger(__name__)


def encode_image(
        image: Image.Image,
        color_scheme: ColorScheme,
) -> bytes:
    """Encode image to display format based on color scheme.

    Args:
        image: Dithered palette image
        color_scheme: Display color scheme

    Returns:
        Encoded image bytes
    """
    from ..models.enums import ColorScheme

    if color_scheme == ColorScheme.MONO:
        return encode_1bpp(image)
    elif color_scheme in (ColorScheme.BWR, ColorScheme.BWY):
        # 3-color displays use bitplane encoding (handled separately)
        raise ValueError(
            f"Color scheme {color_scheme.name} requires bitplane encoding, "
            "use encode_bitplanes() instead"
        )
    elif color_scheme == ColorScheme.BWRY:
        return encode_2bpp(image)
    elif color_scheme == ColorScheme.BWGBRY:
        # 6-color Spectra 6 display uses 4bpp with special firmware values
        # Palette indices 0-5 map to firmware values 0,1,2,3,5,6 (4 is skipped!)
        return encode_4bpp(image, bwgbry_mapping=True)
    elif color_scheme == ColorScheme.GRAYSCALE_4:
        return encode_2bpp(image)
    else:
        raise ValueError(f"Unsupported color scheme: {color_scheme}")


def encode_1bpp(image: Image.Image) -> bytes:
    """Encode image to 1-bit-per-pixel format (monochrome).

    Format: 8 pixels per byte, MSB first
    Palette index 0 = black (0), index 1 = white (1)

    Args:
        image: Palette image (mode 'P')

    Returns:
        Encoded bytes
    """
    if image.mode != "P":
        raise ValueError(f"Expected palette image, got {image.mode}")

    pixels = np.array(image)
    height, width = pixels.shape

    # Calculate output size (round up to byte boundary)
    bytes_per_row = (width + 7) // 8
    output = bytearray(bytes_per_row * height)

    for y in range(height):
        for x in range(width):
            byte_idx = y * bytes_per_row + x // 8
            bit_idx = 7 - (x % 8)  # MSB first

            if pixels[y, x] > 0:  # Non-zero palette index = white
                output[byte_idx] |= (1 << bit_idx)

    return bytes(output)


def encode_2bpp(image: Image.Image) -> bytes:
    """Encode image to 2-bits-per-pixel format (4 colors).

    Format: 4 pixels per byte, MSB first
    Each 2-bit value maps to palette index (0-3)

    Args:
        image: Palette image (mode 'P')

    Returns:
        Encoded bytes
    """
    if image.mode != "P":
        raise ValueError(f"Expected palette image, got {image.mode}")

    pixels = np.array(image)
    height, width = pixels.shape

    # Calculate output size (round up to 4-pixel boundary)
    bytes_per_row = (width + 3) // 4
    output = bytearray(bytes_per_row * height)

    for y in range(height):
        for x in range(width):
            byte_idx = y * bytes_per_row + x // 4
            pixel_in_byte = x % 4
            bit_shift = (3 - pixel_in_byte) * 2  # MSB first

            palette_idx = pixels[y, x] & 0x03  # 2-bit value
            output[byte_idx] |= (palette_idx << bit_shift)

    return bytes(output)


def encode_4bpp(image: Image.Image, bwgbry_mapping: bool = False) -> bytes:
    """Encode image to 4-bits-per-pixel format (16 colors).

    Format: 2 pixels per byte, MSB first
    Each 4-bit value maps to palette index (0-15)

    Args:
        image: Palette image (mode 'P')
        bwgbry_mapping: If True, remap palette indices for BWGBRY firmware
                        (0→0, 1→1, 2→2, 3→3, 4→5, 5→6)

    Returns:
        Encoded bytes
    """
    if image.mode != "P":
        raise ValueError(f"Expected palette image, got {image.mode}")

    pixels = np.array(image)
    height, width = pixels.shape

    # BWGBRY firmware color mapping (Spectra 6 display)
    # Palette indices to firmware values: 0→0, 1→1, 2→2, 3→3, 4→5, 5→6
    BWGBRY_MAP = {0: 0, 1: 1, 2: 2, 3: 3, 4: 5, 5: 6}

    # Calculate output size (round up to 2-pixel boundary)
    bytes_per_row = (width + 1) // 2
    output = bytearray(bytes_per_row * height)

    for y in range(height):
        for x in range(width):
            byte_idx = y * bytes_per_row + x // 2

            palette_idx = pixels[y, x] & 0x0F  # 4-bit value

            # Apply BWGBRY mapping if needed
            if bwgbry_mapping:
                palette_idx = BWGBRY_MAP.get(palette_idx, 0)

            if x % 2 == 0:
                # High nibble
                output[byte_idx] |= (palette_idx << 4)
            else:
                # Low nibble
                output[byte_idx] |= palette_idx

    return bytes(output)