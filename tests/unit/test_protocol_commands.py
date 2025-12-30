import pytest

from opendisplay.protocol.commands import (
    CHUNK_SIZE,
    CommandCode,
    build_direct_write_data_command,
    build_direct_write_end_command,
    build_direct_write_start_compressed,
    build_direct_write_start_uncompressed,
    build_read_config_command,
    build_read_fw_version_command,
)


class TestCommandBuilders:
    """Test command builder functions against real protocol data."""

    def test_build_read_config_command(self, real_read_config_command):
        """Test READ_CONFIG command matches real captured data."""
        cmd = build_read_config_command()
        assert len(cmd) == 2
        assert cmd == b'\x00\x40'  # 0x0040 big-endian
        # Verify matches real device command
        if real_read_config_command:
            assert cmd == real_read_config_command

    def test_build_read_fw_version_command(self, real_firmware_command):
        """Test READ_FW_VERSION command matches real captured data."""
        cmd = build_read_fw_version_command()
        assert len(cmd) == 2
        assert cmd == b'\x00\x43'  # 0x0043 big-endian
        # Verify matches real device command
        if real_firmware_command:
            assert cmd == real_firmware_command

    def test_build_direct_write_start_uncompressed(self, real_upload_start_command):
        """Test uncompressed START command matches real data."""
        cmd = build_direct_write_start_uncompressed()
        assert len(cmd) == 2
        assert cmd == b'\x00\x70'  # 0x0070 big-endian
        # Verify matches real device command
        if real_upload_start_command:
            assert cmd == real_upload_start_command

    def test_build_direct_write_start_compressed(self):
        """Test compressed START includes size and data."""
        compressed_data = b'\x78\x9c\x01\x02\x03'  # 5 bytes zlib data
        uncompressed_size = 100

        cmd = build_direct_write_start_compressed(uncompressed_size, compressed_data)

        # Format: [cmd:2][size:4 LE][data:all]
        assert cmd[:2] == b'\x00\x70'  # Command code
        assert cmd[2:6] == uncompressed_size.to_bytes(4, 'little')  # Size
        assert cmd[6:] == compressed_data  # Compressed data

    def test_build_direct_write_data_command(self, real_data_chunk_command):
        """Test DATA command prepends command code to chunk."""
        chunk = b'A' * 100
        cmd = build_direct_write_data_command(chunk)

        assert cmd[:2] == b'\x00\x71'  # 0x0071 big-endian
        assert cmd[2:] == chunk

        # Verify structure matches real captured chunk
        if real_data_chunk_command:
            assert cmd[:2] == real_data_chunk_command[:2]  # Same command code

    def test_build_direct_write_data_command_max_size(self):
        """Test DATA command accepts max CHUNK_SIZE."""
        chunk = b'A' * CHUNK_SIZE
        cmd = build_direct_write_data_command(chunk)
        assert len(cmd) == CHUNK_SIZE + 2

    def test_build_direct_write_data_command_too_large(self):
        """Test DATA command rejects oversized chunks."""
        chunk = b'A' * (CHUNK_SIZE + 1)
        with pytest.raises(ValueError, match="exceeds maximum"):
            build_direct_write_data_command(chunk)

    def test_build_direct_write_end_command(self, real_upload_end_command):
        """Test END command includes refresh mode."""
        # Default refresh mode (0 = FULL)
        cmd = build_direct_write_end_command()
        assert len(cmd) == 3
        assert cmd == b'\x00\x72\x00'  # cmd + refresh 0

        # Verify matches real device command
        if real_upload_end_command:
            assert cmd == real_upload_end_command

        # Fast refresh mode (1)
        cmd = build_direct_write_end_command(refresh_mode=1)
        assert cmd == b'\x00\x72\x01'  # cmd + refresh 1


class TestCommandCode:
    """Test CommandCode enum values."""

    def test_command_code_values(self):
        """Test all command codes have correct values."""
        assert CommandCode.READ_CONFIG == 0x0040
        assert CommandCode.WRITE_CONFIG == 0x0041
        assert CommandCode.READ_FW_VERSION == 0x0043
        assert CommandCode.DIRECT_WRITE_START == 0x0070
        assert CommandCode.DIRECT_WRITE_DATA == 0x0071
        assert CommandCode.DIRECT_WRITE_END == 0x0072

    def test_command_code_to_bytes(self):
        """Test command codes convert to correct big-endian bytes."""
        assert CommandCode.READ_CONFIG.to_bytes(2, 'big') == b'\x00\x40'
        assert CommandCode.READ_FW_VERSION.to_bytes(2, 'big') == b'\x00\x43'
        assert CommandCode.DIRECT_WRITE_START.to_bytes(2, 'big') == b'\x00\x70'
