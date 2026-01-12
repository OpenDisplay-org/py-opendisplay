"""BLE protocol commands for OpenDisplay devices."""

from __future__ import annotations

from enum import IntEnum


class CommandCode(IntEnum):
    """BLE command codes for OpenDisplay protocol."""

    # Configuration commands
    READ_CONFIG = 0x0040          # Read TLV configuration
    WRITE_CONFIG = 0x0041         # Write TLV configuration (chunked)

    # Firmware commands
    READ_FW_VERSION = 0x0043      # Read firmware version
    REBOOT = 0x000F               # Reboot device

    # Image upload commands (direct write mode)
    DIRECT_WRITE_START = 0x0070   # Start direct write transfer
    DIRECT_WRITE_DATA = 0x0071    # Send image data chunk
    DIRECT_WRITE_END = 0x0072     # End transfer and refresh display


# Protocol constants
SERVICE_UUID = "00002446-0000-1000-8000-00805F9B34FB"
MANUFACTURER_ID = 0x2446  # 9286 decimal
RESPONSE_HIGH_BIT_FLAG = 0x8000  # High bit set in response codes indicates ACK

# Chunking constants
CHUNK_SIZE = 230  # Maximum data bytes per chunk
CONFIG_CHUNK_SIZE = 96  # TLV config chunk data size
PIPELINE_CHUNKS = 1  # Wait for ACK after each chunk

# Upload protocol constants
MAX_COMPRESSED_SIZE = 50 * 1024  # 50KB - firmware buffer limit for compressed uploads
MAX_START_PAYLOAD = 200  # Maximum bytes in START command (prevents MTU issues)


def build_read_config_command() -> bytes:
    """Build command to read device TLV configuration.

    Returns:
        Command bytes: 0x0040 (2 bytes, big-endian)
    """
    return CommandCode.READ_CONFIG.to_bytes(2, byteorder='big')


def build_read_fw_version_command() -> bytes:
    """Build command to read firmware version.

    Returns:
        Command bytes: 0x0043 (2 bytes, big-endian)
    """
    return CommandCode.READ_FW_VERSION.to_bytes(2, byteorder='big')


def build_reboot_command() -> bytes:
    """Build command to reboot device.

    The device will perform an immediate system reset and will NOT send
    an ACK response. The BLE connection will drop when the device resets.

    Returns:
        Command bytes: 0x000F (2 bytes, big-endian)
    """
    return CommandCode.REBOOT.to_bytes(2, byteorder='big')


def build_direct_write_start_compressed(
        uncompressed_size: int,
        compressed_data: bytes
) -> tuple[bytes, bytes]:
    """Build START command for compressed upload with chunking.

    To prevent BLE MTU issues, the START command is limited to MAX_START_PAYLOAD
    bytes. For large compressed payloads, this returns:
    - START command with header + first chunk of compressed data
    - Remaining compressed data (to be sent via DATA chunks)

    Args:
        uncompressed_size: Original uncompressed image size in bytes
        compressed_data: Complete compressed image data

    Returns:
        Tuple of (start_command, remaining_data):
        - start_command: 0x0070 + uncompressed_size (4 bytes) + first chunk
        - remaining_data: Compressed data not included in START (empty if all fits)

    Format of START command:
        [cmd:2][uncompressed_size:4][compressed_data:up to 194 bytes]
        - cmd: 0x0070 (big-endian)
        - uncompressed_size: Original size before compression (little-endian uint32)
        - compressed_data: First chunk of compressed data
    """
    cmd = CommandCode.DIRECT_WRITE_START.to_bytes(2, byteorder='big')
    size = uncompressed_size.to_bytes(4, byteorder='little')

    # Calculate max compressed data that fits in START
    # MAX_START_PAYLOAD = 200 total bytes
    # Header uses: 2 (cmd) + 4 (size) = 6 bytes
    # Remaining for compressed data: 200 - 6 = 194 bytes
    max_data_in_start = MAX_START_PAYLOAD - 6  # 194 bytes

    if len(compressed_data) <= max_data_in_start:
        # All compressed data fits in START command
        return cmd + size + compressed_data, b''
    else:
        # Split: first chunk in START, rest returned separately
        first_chunk = compressed_data[:max_data_in_start]
        remaining = compressed_data[max_data_in_start:]
        return cmd + size + first_chunk, remaining


def build_direct_write_start_uncompressed() -> bytes:
    """Build START command for uncompressed upload protocol.

    This protocol sends NO data in START - all data follows via 0x0071 chunks.

    Returns:
        Command bytes: 0x0070 (just the command, no data!)

    Format:
        [cmd:2]
        - cmd: 0x0070 (big-endian)
        - NO size, NO data - everything sent via 0x0071 DATA chunks
    """
    return CommandCode.DIRECT_WRITE_START.to_bytes(2, byteorder='big')


def build_direct_write_data_command(chunk_data: bytes) -> bytes:
    """Build command to send image data chunk.

    Args:
        chunk_data: Image data chunk (max CHUNK_SIZE bytes)

    Returns:
        Command bytes: 0x0071 + chunk_data

    Format:
        [cmd:2][data:230]
        - cmd: 0x0071 (big-endian)
        - data: Image data chunk
    """
    if len(chunk_data) > CHUNK_SIZE:
        raise ValueError(f"Chunk size {len(chunk_data)} exceeds maximum {CHUNK_SIZE}")

    cmd = CommandCode.DIRECT_WRITE_DATA.to_bytes(2, byteorder='big')
    return cmd + chunk_data


def build_direct_write_end_command(refresh_mode: int = 0) -> bytes:
    """Build command to end image transfer and refresh display.

    Args:
        refresh_mode: Display refresh mode
            0 = FULL (default)
            1 = FAST/PARTIAL (if supported)

    Returns:
        Command bytes: 0x0072 + refresh_mode

    Format:
        [cmd:2][refresh:1]
        - cmd: 0x0072 (big-endian)
        - refresh: Refresh mode (0=full, 1=fast)
    """
    cmd = CommandCode.DIRECT_WRITE_END.to_bytes(2, byteorder='big')
    refresh = refresh_mode.to_bytes(1, byteorder='big')
    return cmd + refresh
