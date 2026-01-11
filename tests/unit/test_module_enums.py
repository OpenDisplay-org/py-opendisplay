"""Test model enums and conversions."""


from opendisplay.models.enums import (
    BusType,
    ICType,
    PowerMode,
    RefreshMode,
    Rotation,
)


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
