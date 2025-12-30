"""Test protocol response parsing."""

import pytest
from opendisplay.protocol.responses import (
    unpack_command_code,
    strip_command_echo,
    check_response_type,
    validate_ack_response,
    parse_firmware_version,
)
from opendisplay.protocol.commands import CommandCode
from opendisplay.exceptions import InvalidResponseError


class TestUnpackCommandCode:
    """Test command code extraction from responses."""

    def test_unpack_command_code_basic(self):
        """Test extracting 2-byte big-endian command code."""
        data = b'\x00\x40'  # 0x0040
        code = unpack_command_code(data)
        assert code == 0x0040

    def test_unpack_command_code_with_high_bit(self):
        """Test extracting command code with ACK high bit set."""
        data = b'\x80\x43'  # 0x8043 (0x0043 with high bit)
        code = unpack_command_code(data)
        assert code == 0x8043

    def test_unpack_command_code_with_offset(self):
        """Test extracting code from offset position."""
        data = b'\xFF\xFF\x00\x70\x00'
        code = unpack_command_code(data, offset=2)
        assert code == 0x0070

    def test_unpack_command_code_from_real_response(self, real_firmware_response):
        """Test extracting code from real device response."""
        if real_firmware_response and len(real_firmware_response) >= 2:
            code = unpack_command_code(real_firmware_response)
            # Should be 0x0043 or 0x8043 (with ACK bit)
            assert code in [0x0043, 0x8043]


class TestStripCommandEcho:
    """Test command echo removal from responses."""

    def test_strip_echo_exact_match(self):
        """Test stripping exact command echo."""
        response = b'\x00\x40\x01\x02\x03'  # Echo + data
        stripped = strip_command_echo(response, CommandCode.READ_CONFIG)
        assert stripped == b'\x01\x02\x03'

    def test_strip_echo_with_high_bit(self):
        """Test stripping echo with ACK high bit set."""
        response = b'\x80\x43\x01\x05'  # Echo with high bit + data
        stripped = strip_command_echo(response, CommandCode.READ_FW_VERSION)
        assert stripped == b'\x01\x05'

    def test_strip_echo_no_match(self):
        """Test returns original data when echo doesn't match."""
        response = b'\x00\x99\x01\x02'  # Wrong echo
        stripped = strip_command_echo(response, CommandCode.READ_CONFIG)
        assert stripped == response  # Unchanged

    def test_strip_echo_too_short(self):
        """Test returns original data when response too short."""
        response = b'\x40'  # Only 1 byte
        stripped = strip_command_echo(response, CommandCode.READ_CONFIG)
        assert stripped == response


class TestCheckResponseType:
    """Test response type checking and ACK detection."""

    def test_check_response_type_without_ack(self):
        """Test detecting command without ACK bit."""
        response = b'\x00\x40\x01\x02'
        command, is_ack = check_response_type(response)
        assert command == CommandCode.READ_CONFIG
        assert is_ack is False

    def test_check_response_type_with_ack(self):
        """Test detecting command with ACK bit set."""
        response = b'\x80\x43\x01\x05'  # 0x8043 = 0x0043 | 0x8000
        command, is_ack = check_response_type(response)
        assert command == CommandCode.READ_FW_VERSION
        assert is_ack is True

    def test_check_response_type_real_firmware_response(self, real_firmware_response):
        """Test checking real firmware response."""
        if real_firmware_response and len(real_firmware_response) >= 2:
            command, is_ack = check_response_type(real_firmware_response)
            assert command == CommandCode.READ_FW_VERSION
            # Most responses have ACK bit set
            assert isinstance(is_ack, bool)


class TestValidateAckResponse:
    """Test ACK response validation."""

    def test_validate_ack_exact_match(self):
        """Test validating ACK with exact command echo."""
        response = b'\x00\x40'
        # Should not raise
        validate_ack_response(response, CommandCode.READ_CONFIG)

    def test_validate_ack_with_high_bit(self):
        """Test validating ACK with high bit set."""
        response = b'\x80\x43'
        # Should not raise
        validate_ack_response(response, CommandCode.READ_FW_VERSION)

    def test_validate_ack_mismatch(self):
        """Test validation fails on command mismatch."""
        response = b'\x00\x40'  # READ_CONFIG
        with pytest.raises(InvalidResponseError, match="ACK mismatch"):
            validate_ack_response(response, CommandCode.READ_FW_VERSION)

    def test_validate_ack_too_short(self):
        """Test validation fails on short response."""
        response = b'\x40'  # Only 1 byte
        with pytest.raises(InvalidResponseError, match="too short"):
            validate_ack_response(response, CommandCode.READ_CONFIG)

    def test_validate_ack_real_firmware_response(self, real_firmware_response):
        """Test validating real firmware ACK response."""
        if real_firmware_response and len(real_firmware_response) >= 2:
            # Should not raise
            validate_ack_response(real_firmware_response, CommandCode.READ_FW_VERSION)


class TestParseFirmwareVersion:
    """Test firmware version parsing."""

    def test_parse_firmware_version_basic(self):
        """Test parsing firmware version with echo."""
        # Format: [echo:2][major:1][minor:1]
        data = b'\x00\x43\x01\x05'  # Version 1.5
        result = parse_firmware_version(data)
        assert result == {"major": 1, "minor": 5}

    def test_parse_firmware_version_with_ack_bit(self):
        """Test parsing with ACK bit set in echo."""
        data = b'\x80\x43\x02\x03'  # Version 2.3 with ACK
        result = parse_firmware_version(data)
        assert result == {"major": 2, "minor": 3}

    def test_parse_firmware_version_real_data(self, real_firmware_response):
        """Test parsing real firmware response from device."""
        if real_firmware_response and len(real_firmware_response) >= 4:
            result = parse_firmware_version(real_firmware_response)

            # Verify structure
            assert "major" in result
            assert "minor" in result

            # Versions should be reasonable (0-255)
            assert 0 <= result["major"] <= 255
            assert 0 <= result["minor"] <= 255

            print(f"Real device firmware: {result['major']}.{result['minor']}")

    def test_parse_firmware_version_too_short(self):
        """Test parsing fails on truncated response."""
        data = b'\x00\x43\x01'  # Only 3 bytes, need 4
        with pytest.raises(InvalidResponseError, match="too short"):
            parse_firmware_version(data)

    def test_parse_firmware_version_wrong_echo(self):
        """Test parsing fails on wrong command echo."""
        data = b'\x00\x40\x01\x05'  # Wrong command (0x0040 not 0x0043)
        with pytest.raises(InvalidResponseError, match="echo mismatch"):
            parse_firmware_version(data)