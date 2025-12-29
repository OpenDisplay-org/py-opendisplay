from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum


@dataclass(frozen=True)
class ColorPalette:
    """Color palette for a display type."""
    colors: dict[str, tuple[int, int, int]]  # name -> RGB tuple
    accent: str  # Primary accent color name


class ColorScheme(Enum):
    """Display color scheme with associated palette data.

    Each scheme stores its firmware int value and color palette.

    Usage:
        scheme = ColorScheme.BWR
        scheme.value           # 1 (firmware value)
        scheme.name            # "BWR"
        scheme.palette.colors  # {'black': (0,0,0), 'white': (255,255,255), 'red': (255,0,0)}
        scheme.accent_color    # "red"
    """

    MONO = (0, ColorPalette(
        colors={
            'black': (0, 0, 0),
            'white': (255, 255, 255),
        },
        accent='black'
    ))

    BWR = (1, ColorPalette(
        colors={
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'red': (255, 0, 0),
        },
        accent='red'
    ))

    BWY = (2, ColorPalette(
        colors={
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'yellow': (255, 255, 0),
        },
        accent='yellow'
    ))

    BWRY = (3, ColorPalette(
        colors={
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'red': (255, 0, 0),
            'yellow': (255, 255, 0),
        },
        accent='red'
    ))

    BWGBRY = (4, ColorPalette(
        colors={
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'yellow': (255, 255, 0),
            'red': (255, 0, 0),
            'blue': (0, 0, 255),
            'green': (0, 255, 0),
        },
        accent='red'
    ))

    GRAYSCALE_4 = (5, ColorPalette(
        colors={
            'black': (0, 0, 0),
            'gray1': (85, 85, 85),
            'gray2': (170, 170, 170),
            'white': (255, 255, 255),
        },
        accent='black'
    ))

    def __init__(self, value: int, palette: ColorPalette):
        self._value_ = value
        self.palette = palette

    @property
    def accent_color(self) -> str:
        """Get accent color name for this scheme."""
        return self.palette.accent

    @property
    def color_count(self) -> int:
        """Get number of colors in palette."""
        return len(self.palette.colors)

    @classmethod
    def from_value(cls, value: int) -> ColorScheme:
        """Get ColorScheme from firmware int value.

        Args:
            value: Firmware color scheme value (0-5)

        Returns:
            Matching ColorScheme

        Raises:
            ValueError: If value is invalid
        """
        for scheme in cls:
            if scheme.value == value:
                return scheme
        raise ValueError(f"Invalid color scheme value: {value}")


class RefreshMode(IntEnum):
    """Display refresh modes."""
    FULL = 0
    FAST = 1
    PARTIAL = 2
    PARTIAL2 = 3


class DitherMode(IntEnum):
    """Image dithering algorithms."""
    NONE = 0
    BURKES = 1    # Burkes error diffusion
    ORDERED = 2   # Bayer/ordered dithering


class ICType(IntEnum):
    """Microcontroller IC types."""
    NRF52840 = 1
    ESP32_S3 = 2
    ESP32_C3 = 3
    ESP32_C6 = 4


class PowerMode(IntEnum):
    """Power source types."""
    BATTERY = 1
    USB = 2
    SOLAR = 3


class BusType(IntEnum):
    """Data bus types for sensors."""
    I2C = 0
    SPI = 1


class Rotation(IntEnum):
    """Display rotation angles in degrees."""
    ROTATE_0 = 0
    ROTATE_90 = 90
    ROTATE_180 = 180
    ROTATE_270 = 270