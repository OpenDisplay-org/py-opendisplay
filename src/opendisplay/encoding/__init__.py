"""Image encoding and processing."""

from .bitplanes import encode_bitplanes
from .compression import compress_image_data, decompress_image_data
from .dithering import dither_image
from .images import encode_1bpp, encode_2bpp, encode_4bpp, encode_image

__all__ = [
    "dither_image",
    "encode_image",
    "encode_1bpp",
    "encode_2bpp",
    "encode_4bpp",
    "encode_bitplanes",
    "compress_image_data",
    "decompress_image_data",
]