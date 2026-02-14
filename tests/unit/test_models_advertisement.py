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
        assert result.format_version == "legacy"
        assert result.reboot_flag is None
        assert result.connection_requested is None
        assert result.dynamic_data == b""

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

    def test_parse_advertisement_v1_format(self):
        """Test parsing v1 (firmware 1.0+) 14-byte advertisement data."""
        # dynamic_data[0:11]
        # temperature: 22.0C -> (22 + 40) * 2 = 124 (0x7c)
        # battery: 3.95V -> 3950mV -> 395 x 10mV units -> low=0x8b, high bit=1
        # status: bit0=batt_msb(1), bit1=reboot(1), bit2=conn_req(0), bits4-7=loop(5)
        data = bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0x7C, 0x8B, 0x53])

        result = parse_advertisement(data)

        assert result.format_version == "v1"
        assert result.temperature_c == 22.0
        assert result.battery_mv == 3950
        assert result.loop_counter == 5
        assert result.reboot_flag is True
        assert result.connection_requested is False
        assert result.dynamic_data == bytes([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11])

    def test_parse_advertisement_strips_manufacturer_id_for_legacy(self):
        """Parser should accept payloads with manufacturer ID included."""
        # Manufacturer ID 0x2446 (little-endian), followed by legacy 11-byte payload
        payload = bytes([0x46, 0x24, 0x02, 0x36, 0x00, 0x6C, 0x00, 0xC3, 0x01, 0x55, 0x0F, 0x16, 0x4D])

        result = parse_advertisement(payload)

        assert result.format_version == "legacy"
        assert result.battery_mv == 3925
        assert result.temperature_c == 22
        assert result.loop_counter == 77

    def test_parse_advertisement_strips_manufacturer_id_for_v1(self):
        """Parser should accept v1 payloads with manufacturer ID included."""
        payload = bytes([0x46, 0x24, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0x7C, 0x8B, 0x53])

        result = parse_advertisement(payload)

        assert result.format_version == "v1"
        assert result.battery_mv == 3950
        assert result.temperature_c == 22.0
        assert result.loop_counter == 5

    def test_parse_advertisement_rejects_unknown_legacy_signature(self):
        """11-byte payload with unknown signature should be rejected."""
        data = bytes([0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF, 0x00, 0x55, 0x0F, 0x16, 0x4D])

        with pytest.raises(ValueError, match="Unsupported legacy advertisement signature"):
            parse_advertisement(data)
