"""Test BLE advertisement data parsing."""

import pytest

from opendisplay.models.advertisement import AdvertisementData, parse_advertisement


class TestParseAdvertisement:
    """Test BLE advertisement data parsing."""

    def test_parse_advertisement_valid(self):
        """Test parsing valid 11-byte advertisement data."""
        # Real format (manufacturer ID stripped by Bleak):
        # [protocol:7][battery:2 LE][temp:1 signed][loop:1]
        # Battery: 3925mV (0x0f55), Temp: 22°C, Loop: 77
        data = bytes([0x02, 0x36, 0x00, 0x6c, 0x00, 0xc3, 0x01, 0x55, 0x0f, 0x16, 0x4d])

        result = parse_advertisement(data)

        assert isinstance(result, AdvertisementData)
        assert result.battery_mv == 3925
        assert result.temperature_c == 22
        assert result.loop_counter == 77

    def test_parse_advertisement_different_values(self):
        """Test parsing with different sensor values."""
        # Battery: 4200mV (0x1068), Temp: 25°C (0x19), Loop: 100 (0x64)
        data = bytes([0x02, 0x36, 0x00, 0x6c, 0x00, 0xc3, 0x01, 0x68, 0x10, 0x19, 0x64])

        result = parse_advertisement(data)

        assert result.battery_mv == 4200
        assert result.temperature_c == 25
        assert result.loop_counter == 100

    def test_parse_advertisement_low_battery(self):
        """Test parsing with low battery voltage."""
        # Battery: 2800mV (0x0af0), Temp: 20°C, Loop: 50
        data = bytes([0x02, 0x36, 0x00, 0x6c, 0x00, 0xc3, 0x01, 0xf0, 0x0a, 0x14, 0x32])

        result = parse_advertisement(data)

        assert result.battery_mv == 2800
        assert result.temperature_c == 20
        assert result.loop_counter == 50

    def test_parse_advertisement_negative_temperature(self):
        """Test parsing with negative temperature."""
        # Battery: 3000mV, Temp: -5°C (0xfb = -5 in signed int8), Loop: 10
        data = bytes([0x02, 0x36, 0x00, 0x6c, 0x00, 0xc3, 0x01, 0xb8, 0x0b, 0xfb, 0x0a])

        result = parse_advertisement(data)

        assert result.battery_mv == 3000
        assert result.temperature_c == -5
        assert result.loop_counter == 10

    def test_parse_advertisement_too_short(self):
        """Test that too-short data raises ValueError."""
        data = bytes([0x02, 0x36, 0x00, 0x6c, 0x00])  # Only 5 bytes

        with pytest.raises(ValueError, match="too short.*11"):
            parse_advertisement(data)

    def test_parse_advertisement_empty(self):
        """Test that empty data raises ValueError."""
        with pytest.raises(ValueError, match="too short"):
            parse_advertisement(bytes())

    def test_parse_advertisement_loop_counter_overflow(self):
        """Test loop counter wrapping at 255."""
        # Loop counter at max value (255 = 0xff)
        data = bytes([0x02, 0x36, 0x00, 0x6c, 0x00, 0xc3, 0x01, 0x55, 0x0f, 0x16, 0xff])

        result = parse_advertisement(data)

        assert result.loop_counter == 255
