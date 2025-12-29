"""Dithering algorithms for e-paper displays."""

from __future__ import annotations

import logging

import numpy as np
from PIL import Image

from ..models.enums import ColorScheme, DitherMode

_LOGGER = logging.getLogger(__name__)


def dither_image(
        image: Image.Image,
        color_scheme: ColorScheme,
        mode: DitherMode = DitherMode.BURKES
) -> Image.Image:
    """Apply dithering to image for e-paper display.

    Args:
        image: Input image (RGB or RGBA)
        color_scheme: Target display color scheme
        mode: mode: Dithering algorithm (default: BURKES)

    Returns:
        Dithered image with palette matching color scheme
    """
    _LOGGER.debug("Applying %s dithering for %s color scheme", mode.name, color_scheme.name)

    match mode:
        case DitherMode.NONE:
            return _direct_palette_map(image, color_scheme)
        case DitherMode.ORDERED:
            return _ordered_dither(image, color_scheme)
        case DitherMode.FLOYD_STEINBERG:
            return _floyd_steinberg_dither(image, color_scheme)
        case DitherMode.ATKINSON:
            return _atkinson_dither(image, color_scheme)
        case DitherMode.STUCKI:
            return _stucki_dither(image, color_scheme)
        case DitherMode.SIERRA:
            return _sierra_dither(image, color_scheme)
        case DitherMode.SIERRA_LITE:
            return _sierra_lite_dither(image, color_scheme)
        case DitherMode.JARVIS_JUDICE_NINKE:
            return _jarvis_judice_ninke_dither(image, color_scheme)
        case _:  # BURKES or fallback
            return _burkes_dither(image, color_scheme)


def _get_palette_colors(color_scheme: ColorScheme) -> list[tuple[int, int, int]]:
    """Get RGB palette for color scheme.

    Args:
        color_scheme: Display color scheme

    Returns:
        List of RGB tuples for palette (order matters for encoding)
    """
    # Extract palette from color scheme enum
    return list(color_scheme.palette.colors.values())


def _find_closest_palette_color(
        rgb: tuple[int, int, int],
        palette: list[tuple[int, int, int]]
) -> int:
    """Find closest palette color index using Euclidean distance.

    Args:
        rgb: Input RGB color
        palette: List of palette RGB colors

    Returns:
        Index of closest palette color
    """
    min_distance = float('inf')
    closest_idx = 0

    for idx, pal_color in enumerate(palette):
        # Euclidean distance in RGB space
        distance = sum((a - b) ** 2 for a, b in zip(rgb, pal_color))
        if distance < min_distance:
            min_distance = distance
            closest_idx = idx

    return closest_idx


def _direct_palette_map(image: Image.Image, color_scheme: ColorScheme) -> Image.Image:
    """Map image colors directly to palette without dithering.

    Args:
        image: Input image
        color_scheme: Target color scheme

    Returns:
        Image with palette colors
    """
    # Convert to RGB
    if image.mode != "RGB":
        image = image.convert("RGB")

    palette = _get_palette_colors(color_scheme)
    pixels = np.array(image)
    height, width = pixels.shape[:2]

    # Create output image
    output = Image.new("P", (width, height))
    output_pixels = np.zeros((height, width), dtype=np.uint8)

    # Map each pixel to closest palette color
    for y in range(height):
        for x in range(width):
            rgb = tuple(pixels[y, x, :3])
            output_pixels[y, x] = _find_closest_palette_color(rgb, palette)

    output.putdata(output_pixels.flatten())

    # Set palette
    flat_palette = [c for rgb in palette for c in rgb]
    output.putpalette(flat_palette)

    return output


def _burkes_dither(image: Image.Image, color_scheme: ColorScheme) -> Image.Image:
    """Apply Burkes error diffusion dithering.

    Burkes kernel (divisor 200):
                 X  32  12
         5  12  26  12   5

    Args:
        image: Input image
        color_scheme: Target color scheme

    Returns:
        Dithered image
    """
    # Convert to RGB
    if image.mode != "RGB":
        image = image.convert("RGB")

    palette = _get_palette_colors(color_scheme)
    pixels = np.array(image, dtype=np.float32)
    height, width = pixels.shape[:2]

    # Create output image
    output = Image.new("P", (width, height))
    output_pixels = np.zeros((height, width), dtype=np.uint8)

    # Burkes error diffusion
    for y in range(height):
        for x in range(width):
            old_pixel = tuple(int(pixels[y, x, i]) for i in range(3))
            new_idx = _find_closest_palette_color(old_pixel, palette)
            new_pixel = palette[new_idx]

            output_pixels[y, x] = new_idx

            # Calculate error
            error = [old_pixel[i] - new_pixel[i] for i in range(3)]

            # Distribute error using Burkes kernel
            if x + 1 < width:
                pixels[y, x + 1] += np.array(error) * 32 / 200
            if x + 2 < width:
                pixels[y, x + 2] += np.array(error) * 12 / 200

            if y + 1 < height:
                if x - 2 >= 0:
                    pixels[y + 1, x - 2] += np.array(error) * 5 / 200
                if x - 1 >= 0:
                    pixels[y + 1, x - 1] += np.array(error) * 12 / 200
                pixels[y + 1, x] += np.array(error) * 26 / 200
                if x + 1 < width:
                    pixels[y + 1, x + 1] += np.array(error) * 12 / 200
                if x + 2 < width:
                    pixels[y + 1, x + 2] += np.array(error) * 5 / 200

    output.putdata(output_pixels.flatten())

    # Set palette
    flat_palette = [c for rgb in palette for c in rgb]
    output.putpalette(flat_palette)

    return output


def _sierra_dither(image: Image.Image, color_scheme: ColorScheme) -> Image.Image:
    """Apply Sierra error diffusion dithering.

    Sierra kernel (divisor 32):
               X   5   3
       2   4   5   4   2
           2   3   2

    Sierra-2-4A variant, balanced quality and performance.

    Args:
        image: Input image
        color_scheme: Target color scheme

    Returns:
        Dithered image
    """
    # Convert to RGB
    if image.mode != "RGB":
        image = image.convert("RGB")

    palette = _get_palette_colors(color_scheme)
    pixels = np.array(image, dtype=np.float32)
    height, width = pixels.shape[:2]

    # Create output image
    output = Image.new("P", (width, height))
    output_pixels = np.zeros((height, width), dtype=np.uint8)

    # Error diffusion loop
    for y in range(height):
        for x in range(width):
            old_pixel = tuple(int(pixels[y, x, i]) for i in range(3))
            new_idx = _find_closest_palette_color(old_pixel, palette)
            new_pixel = palette[new_idx]

            output_pixels[y, x] = new_idx

            # Calculate error
            error = [old_pixel[i] - new_pixel[i] for i in range(3)]

            # Distribute error using Sierra kernel (divisor 32)
            if x + 1 < width:
                pixels[y, x + 1] += np.array(error) * 5 / 32
            if x + 2 < width:
                pixels[y, x + 2] += np.array(error) * 3 / 32

            if y + 1 < height:
                if x - 2 >= 0:
                    pixels[y + 1, x - 2] += np.array(error) * 2 / 32
                if x - 1 >= 0:
                    pixels[y + 1, x - 1] += np.array(error) * 4 / 32
                pixels[y + 1, x] += np.array(error) * 5 / 32
                if x + 1 < width:
                    pixels[y + 1, x + 1] += np.array(error) * 4 / 32
                if x + 2 < width:
                    pixels[y + 1, x + 2] += np.array(error) * 2 / 32

            if y + 2 < height:
                if x - 1 >= 0:
                    pixels[y + 2, x - 1] += np.array(error) * 2 / 32
                pixels[y + 2, x] += np.array(error) * 3 / 32
                if x + 1 < width:
                    pixels[y + 2, x + 1] += np.array(error) * 2 / 32

    output.putdata(output_pixels.flatten())

    # Set palette
    flat_palette = [c for rgb in palette for c in rgb]
    output.putpalette(flat_palette)

    return output


def _sierra_lite_dither(image: Image.Image, color_scheme: ColorScheme) -> Image.Image:
    """Apply Sierra Lite error diffusion dithering.

    Sierra Lite kernel (divisor 4):
         X   2
       1   1

    Fast, simple 3-neighbor algorithm.

    Args:
        image: Input image
        color_scheme: Target color scheme

    Returns:
        Dithered image
    """
    # Convert to RGB
    if image.mode != "RGB":
        image = image.convert("RGB")

    palette = _get_palette_colors(color_scheme)
    pixels = np.array(image, dtype=np.float32)
    height, width = pixels.shape[:2]

    # Create output image
    output = Image.new("P", (width, height))
    output_pixels = np.zeros((height, width), dtype=np.uint8)

    # Error diffusion loop
    for y in range(height):
        for x in range(width):
            old_pixel = tuple(int(pixels[y, x, i]) for i in range(3))
            new_idx = _find_closest_palette_color(old_pixel, palette)
            new_pixel = palette[new_idx]

            output_pixels[y, x] = new_idx

            # Calculate error
            error = [old_pixel[i] - new_pixel[i] for i in range(3)]

            # Distribute error using Sierra Lite kernel (divisor 4)
            if x + 1 < width:
                pixels[y, x + 1] += np.array(error) * 2 / 4

            if y + 1 < height:
                if x - 1 >= 0:
                    pixels[y + 1, x - 1] += np.array(error) * 1 / 4
                pixels[y + 1, x] += np.array(error) * 1 / 4

    output.putdata(output_pixels.flatten())

    # Set palette
    flat_palette = [c for rgb in palette for c in rgb]
    output.putpalette(flat_palette)

    return output


def _floyd_steinberg_dither(image: Image.Image, color_scheme: ColorScheme) -> Image.Image:
    """Apply Floyd-Steinberg error diffusion dithering.

    Floyd-Steinberg kernel (divisor 16):
           X   7
       3   5   1

    Most popular error diffusion algorithm, good balance of quality and speed.

    Args:
        image: Input image
        color_scheme: Target color scheme

    Returns:
        Dithered image
    """
    # Convert to RGB
    if image.mode != "RGB":
        image = image.convert("RGB")

    palette = _get_palette_colors(color_scheme)
    pixels = np.array(image, dtype=np.float32)
    height, width = pixels.shape[:2]

    # Create output image
    output = Image.new("P", (width, height))
    output_pixels = np.zeros((height, width), dtype=np.uint8)

    # Error diffusion loop
    for y in range(height):
        for x in range(width):
            old_pixel = tuple(int(pixels[y, x, i]) for i in range(3))
            new_idx = _find_closest_palette_color(old_pixel, palette)
            new_pixel = palette[new_idx]

            output_pixels[y, x] = new_idx

            # Calculate error
            error = [old_pixel[i] - new_pixel[i] for i in range(3)]

            # Distribute error using Floyd-Steinberg kernel (divisor 16)
            if x + 1 < width:
                pixels[y, x + 1] += np.array(error) * 7 / 16

            if y + 1 < height:
                if x - 1 >= 0:
                    pixels[y + 1, x - 1] += np.array(error) * 3 / 16
                pixels[y + 1, x] += np.array(error) * 5 / 16
                if x + 1 < width:
                    pixels[y + 1, x + 1] += np.array(error) * 1 / 16

    output.putdata(output_pixels.flatten())

    # Set palette
    flat_palette = [c for rgb in palette for c in rgb]
    output.putpalette(flat_palette)

    return output


def _atkinson_dither(image: Image.Image, color_scheme: ColorScheme) -> Image.Image:
    """Apply Atkinson error diffusion dithering.

    Atkinson kernel (divisor 8):
           X   1   1
       1   1   1
           1

    Designed for early Macintosh computers, produces distinct artistic look.

    Args:
        image: Input image
        color_scheme: Target color scheme

    Returns:
        Dithered image
    """
    # Convert to RGB
    if image.mode != "RGB":
        image = image.convert("RGB")

    palette = _get_palette_colors(color_scheme)
    pixels = np.array(image, dtype=np.float32)
    height, width = pixels.shape[:2]

    # Create output image
    output = Image.new("P", (width, height))
    output_pixels = np.zeros((height, width), dtype=np.uint8)

    # Error diffusion loop
    for y in range(height):
        for x in range(width):
            old_pixel = tuple(int(pixels[y, x, i]) for i in range(3))
            new_idx = _find_closest_palette_color(old_pixel, palette)
            new_pixel = palette[new_idx]

            output_pixels[y, x] = new_idx

            # Calculate error
            error = [old_pixel[i] - new_pixel[i] for i in range(3)]

            # Distribute error using Atkinson kernel (divisor 8)
            if x + 1 < width:
                pixels[y, x + 1] += np.array(error) * 1 / 8
            if x + 2 < width:
                pixels[y, x + 2] += np.array(error) * 1 / 8

            if y + 1 < height:
                if x - 1 >= 0:
                    pixels[y + 1, x - 1] += np.array(error) * 1 / 8
                pixels[y + 1, x] += np.array(error) * 1 / 8
                if x + 1 < width:
                    pixels[y + 1, x + 1] += np.array(error) * 1 / 8

            if y + 2 < height:
                pixels[y + 2, x] += np.array(error) * 1 / 8

    output.putdata(output_pixels.flatten())

    # Set palette
    flat_palette = [c for rgb in palette for c in rgb]
    output.putpalette(flat_palette)

    return output


def _stucki_dither(image: Image.Image, color_scheme: ColorScheme) -> Image.Image:
    """Apply Stucki error diffusion dithering.

    Stucki kernel (divisor 42):
               X   8   4
       2   4   8   4   2
       1   2   4   2   1

    High quality algorithm with wide error distribution.

    Args:
        image: Input image
        color_scheme: Target color scheme

    Returns:
        Dithered image
    """
    # Convert to RGB
    if image.mode != "RGB":
        image = image.convert("RGB")

    palette = _get_palette_colors(color_scheme)
    pixels = np.array(image, dtype=np.float32)
    height, width = pixels.shape[:2]

    # Create output image
    output = Image.new("P", (width, height))
    output_pixels = np.zeros((height, width), dtype=np.uint8)

    # Error diffusion loop
    for y in range(height):
        for x in range(width):
            old_pixel = tuple(int(pixels[y, x, i]) for i in range(3))
            new_idx = _find_closest_palette_color(old_pixel, palette)
            new_pixel = palette[new_idx]

            output_pixels[y, x] = new_idx

            # Calculate error
            error = [old_pixel[i] - new_pixel[i] for i in range(3)]

            # Distribute error using Stucki kernel (divisor 42)
            if x + 1 < width:
                pixels[y, x + 1] += np.array(error) * 8 / 42
            if x + 2 < width:
                pixels[y, x + 2] += np.array(error) * 4 / 42

            if y + 1 < height:
                if x - 2 >= 0:
                    pixels[y + 1, x - 2] += np.array(error) * 2 / 42
                if x - 1 >= 0:
                    pixels[y + 1, x - 1] += np.array(error) * 4 / 42
                pixels[y + 1, x] += np.array(error) * 8 / 42
                if x + 1 < width:
                    pixels[y + 1, x + 1] += np.array(error) * 4 / 42
                if x + 2 < width:
                    pixels[y + 1, x + 2] += np.array(error) * 2 / 42

            if y + 2 < height:
                if x - 2 >= 0:
                    pixels[y + 2, x - 2] += np.array(error) * 1 / 42
                if x - 1 >= 0:
                    pixels[y + 2, x - 1] += np.array(error) * 2 / 42
                pixels[y + 2, x] += np.array(error) * 4 / 42
                if x + 1 < width:
                    pixels[y + 2, x + 1] += np.array(error) * 2 / 42
                if x + 2 < width:
                    pixels[y + 2, x + 2] += np.array(error) * 1 / 42

    output.putdata(output_pixels.flatten())

    # Set palette
    flat_palette = [c for rgb in palette for c in rgb]
    output.putpalette(flat_palette)

    return output


def _jarvis_judice_ninke_dither(image: Image.Image, color_scheme: ColorScheme) -> Image.Image:
    """Apply Jarvis-Judice-Ninke error diffusion dithering.

    Jarvis-Judice-Ninke kernel (divisor 48):
               X   7   5
       3   5   7   5   3
       1   3   5   3   1

    Highest quality algorithm with symmetrical error distribution.

    Args:
        image: Input image
        color_scheme: Target color scheme

    Returns:
        Dithered image
    """
    # Convert to RGB
    if image.mode != "RGB":
        image = image.convert("RGB")

    palette = _get_palette_colors(color_scheme)
    pixels = np.array(image, dtype=np.float32)
    height, width = pixels.shape[:2]

    # Create output image
    output = Image.new("P", (width, height))
    output_pixels = np.zeros((height, width), dtype=np.uint8)

    # Error diffusion loop
    for y in range(height):
        for x in range(width):
            old_pixel = tuple(int(pixels[y, x, i]) for i in range(3))
            new_idx = _find_closest_palette_color(old_pixel, palette)
            new_pixel = palette[new_idx]

            output_pixels[y, x] = new_idx

            # Calculate error
            error = [old_pixel[i] - new_pixel[i] for i in range(3)]

            # Distribute error using Jarvis-Judice-Ninke kernel (divisor 48)
            if x + 1 < width:
                pixels[y, x + 1] += np.array(error) * 7 / 48
            if x + 2 < width:
                pixels[y, x + 2] += np.array(error) * 5 / 48

            if y + 1 < height:
                if x - 2 >= 0:
                    pixels[y + 1, x - 2] += np.array(error) * 3 / 48
                if x - 1 >= 0:
                    pixels[y + 1, x - 1] += np.array(error) * 5 / 48
                pixels[y + 1, x] += np.array(error) * 7 / 48
                if x + 1 < width:
                    pixels[y + 1, x + 1] += np.array(error) * 5 / 48
                if x + 2 < width:
                    pixels[y + 1, x + 2] += np.array(error) * 3 / 48

            if y + 2 < height:
                if x - 2 >= 0:
                    pixels[y + 2, x - 2] += np.array(error) * 1 / 48
                if x - 1 >= 0:
                    pixels[y + 2, x - 1] += np.array(error) * 3 / 48
                pixels[y + 2, x] += np.array(error) * 5 / 48
                if x + 1 < width:
                    pixels[y + 2, x + 1] += np.array(error) * 3 / 48
                if x + 2 < width:
                    pixels[y + 2, x + 2] += np.array(error) * 1 / 48

    output.putdata(output_pixels.flatten())

    # Set palette
    flat_palette = [c for rgb in palette for c in rgb]
    output.putpalette(flat_palette)

    return output


def _ordered_dither(image: Image.Image, color_scheme: ColorScheme) -> Image.Image:
    """Apply ordered (Bayer) dithering.

    Uses 4x4 Bayer matrix for threshold comparison.

    Args:
        image: Input image
        color_scheme: Target color scheme

    Returns:
        Dithered image
    """
    # Bayer 4x4 matrix (normalized to 0-255)
    bayer_matrix = np.array([
        [0, 8, 2, 10],
        [12, 4, 14, 6],
        [3, 11, 1, 9],
        [15, 7, 13, 5]
    ]) * 16

    # Convert to RGB
    if image.mode != "RGB":
        image = image.convert("RGB")

    palette = _get_palette_colors(color_scheme)
    pixels = np.array(image, dtype=np.float32)
    height, width = pixels.shape[:2]

    # Create output image
    output = Image.new("P", (width, height))
    output_pixels = np.zeros((height, width), dtype=np.uint8)

    # Apply ordered dithering
    for y in range(height):
        for x in range(width):
            # Get threshold from Bayer matrix
            threshold = bayer_matrix[y % 4, x % 4]

            # Add threshold noise
            noisy_pixel = pixels[y, x, :3] + threshold
            noisy_pixel = np.clip(noisy_pixel, 0, 255)

            rgb = tuple(int(noisy_pixel[i]) for i in range(3))
            output_pixels[y, x] = _find_closest_palette_color(rgb, palette)

    output.putdata(output_pixels.flatten())

    # Set palette
    flat_palette = [c for rgb in palette for c in rgb]
    output.putpalette(flat_palette)

    return output
