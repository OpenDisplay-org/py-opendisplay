from __future__ import annotations

from enum import IntEnum


class RefreshMode(IntEnum):
    """Display refresh modes."""
    FULL = 0
    FAST = 1
    PARTIAL = 2
    PARTIAL2 = 3


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
