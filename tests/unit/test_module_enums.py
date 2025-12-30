"""Test model enums and conversions."""

import pytest

from opendisplay.models.enums import (
    BusType,
    ColorScheme,
    DitherMode,
    ICType,
    PowerMode,
    RefreshMode,
    Rotation,
)


class TestColorScheme:
    """Test ColorScheme enum."""

    def test_color_scheme_values(self):
        """Test all color schemes have correct firmware values."""
        assert ColorScheme.MONO.value == 0
        assert ColorScheme.BWR.value == 1
        assert ColorScheme.BWY.value == 2
        assert ColorScheme.BWRY.value == 3
        assert ColorScheme.BWGBRY.value == 4
        assert ColorScheme.GRAYSCALE_4.value == 5

    def test_color_scheme_from_value(self):
        """Test converting firmware value to ColorScheme."""
        assert ColorScheme.from_value(0) == ColorScheme.MONO
        assert ColorScheme.from_value(1) == ColorScheme.BWR
        assert ColorScheme.from_value(2) == ColorScheme.BWY
        assert ColorScheme.from_value(3) == ColorScheme.BWRY
        assert ColorScheme.from_value(4) == ColorScheme.BWGBRY
        assert ColorScheme.from_value(5) == ColorScheme.GRAYSCALE_4

    def test_color_scheme_from_value_invalid(self):
        """Test invalid firmware value raises ValueError."""
        with pytest.raises(ValueError):
            ColorScheme.from_value(99)

    def test_color_scheme_names(self):
        """Test enum names are correct."""
        assert ColorScheme.MONO.name == "MONO"
        assert ColorScheme.BWR.name == "BWR"
        assert ColorScheme.BWY.name == "BWY"
        assert ColorScheme.BWRY.name == "BWRY"
        assert ColorScheme.BWGBRY.name == "BWGBRY"
        assert ColorScheme.GRAYSCALE_4.name == "GRAYSCALE_4"

    def test_color_scheme_palette(self):
        """Test color schemes have palettes."""
        # All schemes should have palette attribute
        assert hasattr(ColorScheme.MONO.palette, 'colors')
        assert hasattr(ColorScheme.BWR.palette, 'colors')
        assert hasattr(ColorScheme.BWY.palette, 'colors')
        assert hasattr(ColorScheme.BWRY.palette, 'colors')
        assert hasattr(ColorScheme.BWGBRY.palette, 'colors')
        assert hasattr(ColorScheme.GRAYSCALE_4.palette, 'colors')

        # MONO should have 2 colors
        assert len(ColorScheme.MONO.palette.colors) == 2

        # BWR should have 3 colors
        assert len(ColorScheme.BWR.palette.colors) == 3

        # BWY should have 3 colors
        assert len(ColorScheme.BWY.palette.colors) == 3

        # BWGBRY should have 6 colors
        assert len(ColorScheme.BWGBRY.palette.colors) == 6

        # Grayscale should have 4 colors
        assert len(ColorScheme.GRAYSCALE_4.palette.colors) == 4

    def test_color_scheme_accent_color(self):
        """Test accent color detection."""
        assert ColorScheme.MONO.accent_color == "black"
        assert ColorScheme.BWR.accent_color == "red"
        assert ColorScheme.BWY.accent_color == "yellow"
        # BWRY has both red and yellow, red is primary
        assert ColorScheme.BWRY.accent_color == "red"
        # BWGBRY has red, yellow, gree, and blue, red is primary
        assert ColorScheme.BWGBRY.accent_color == "red"
        # Grayscale has black as primary color
        assert ColorScheme.GRAYSCALE_4.accent_color == "black"


class TestRefreshMode:
    """Test RefreshMode enum."""

    def test_refresh_mode_values(self):
        """Test all refresh modes have correct values."""
        assert RefreshMode.FULL == 0
        assert RefreshMode.FAST == 1
        assert RefreshMode.PARTIAL == 2
        assert RefreshMode.PARTIAL2 == 3

    def test_refresh_mode_names(self):
        """Test refresh mode names."""
        assert RefreshMode.FULL.name == "FULL"
        assert RefreshMode.FAST.name == "FAST"
        assert RefreshMode.PARTIAL.name == "PARTIAL"
        assert RefreshMode.PARTIAL2.name == "PARTIAL2"


class TestDitherMode:
    """Test DitherMode enum."""

    def test_dither_mode_values(self):
        """Test all dithering modes have correct values."""
        assert DitherMode.NONE == 0
        assert DitherMode.BURKES == 1
        assert DitherMode.ORDERED == 2
        assert DitherMode.FLOYD_STEINBERG == 3
        assert DitherMode.ATKINSON == 4
        assert DitherMode.STUCKI == 5
        assert DitherMode.SIERRA == 6
        assert DitherMode.SIERRA_LITE == 7
        assert DitherMode.JARVIS_JUDICE_NINKE == 8

    def test_dither_mode_names(self):
        """Test dithering mode names."""
        assert DitherMode.NONE.name == "NONE"
        assert DitherMode.BURKES.name == "BURKES"
        assert DitherMode.ORDERED.name == "ORDERED"
        assert DitherMode.FLOYD_STEINBERG.name == "FLOYD_STEINBERG"
        assert DitherMode.ATKINSON.name == "ATKINSON"
        assert DitherMode.STUCKI.name == "STUCKI"
        assert DitherMode.SIERRA.name == "SIERRA"
        assert DitherMode.SIERRA_LITE.name == "SIERRA_LITE"
        assert DitherMode.JARVIS_JUDICE_NINKE.name == "JARVIS_JUDICE_NINKE"

    def test_all_dither_modes_exist(self):
        """Test all 9 dithering modes are defined."""
        modes = list(DitherMode)
        assert len(modes) == 9


class TestICType:
    """Test IC (microcontroller) type enum."""

    def test_ic_type_values(self):
        """Test IC type values."""
        assert ICType.NRF52840 == 1
        assert ICType.ESP32_S3 == 2
        assert ICType.ESP32_C3 == 3
        assert ICType.ESP32_C6 == 4

    def test_ic_type_names(self):
        """Test IC type names."""
        assert ICType.NRF52840.name == "NRF52840"
        assert ICType.ESP32_S3.name == "ESP32_S3"


class TestPowerMode:
    """Test PowerMode enum."""

    def test_power_mode_values(self):
        """Test power mode values."""
        assert PowerMode.BATTERY == 1
        assert PowerMode.USB == 2
        assert PowerMode.SOLAR == 3

    def test_power_mode_names(self):
        """Test power mode names."""
        assert PowerMode.BATTERY.name == "BATTERY"
        assert PowerMode.USB.name == "USB"
        assert PowerMode.SOLAR.name == "SOLAR"


class TestBusType:
    """Test BusType enum."""

    def test_bus_type_values(self):
        """Test bus type values."""
        assert BusType.I2C == 0
        assert BusType.SPI == 1

    def test_bus_type_names(self):
        """Test bus type names."""
        assert BusType.I2C.name == "I2C"
        assert BusType.SPI.name == "SPI"


class TestRotation:
    """Test Rotation enum."""

    def test_rotation_values(self):
        """Test rotation degree values."""
        assert Rotation.ROTATE_0 == 0
        assert Rotation.ROTATE_90 == 90
        assert Rotation.ROTATE_180 == 180
        assert Rotation.ROTATE_270 == 270

    def test_rotation_names(self):
        """Test rotation names."""
        assert Rotation.ROTATE_0.name == "ROTATE_0"
        assert Rotation.ROTATE_90.name == "ROTATE_90"
        assert Rotation.ROTATE_180.name == "ROTATE_180"
        assert Rotation.ROTATE_270.name == "ROTATE_270"

    def test_all_rotations_exist(self):
        """Test all 4 rotations are defined."""
        rotations = list(Rotation)
        assert len(rotations) == 4
