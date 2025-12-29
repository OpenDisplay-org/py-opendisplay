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

    # Image upload commands (direct write mode)
    DIRECT_WRITE_START = 0x0070   # Start direct write transfer
    DIRECT_WRITE_DATA = 0x0071    # Send image data chunk
    DIRECT_WRITE_END = 0x0072     # End transfer and refresh display


# Protocol constants
SERVICE_UUID = "00002446-0000-1000-8000-00805F9B34FB"
MANUFACTURER_ID = 0x2446  # 9286 decimal

# Chunking constants
CHUNK_SIZE = 230  # Maximum data bytes per chunk
CONFIG_CHUNK_SIZE = 96  # TLV config chunk data size
PIPELINE_CHUNKS = 3  # Number of chunks to send before waiting for ACK


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


def build_direct_write_start_command(
        image_data: bytes,
        width: int,
        height: int,
        is_compressed: bool = True
) -> bytes:
    """Build command to start direct write image transfer.

    Args:
        image_data: Complete image data (compressed or raw)
        width: Display width in pixels
        height: Display height in pixels
        is_compressed: Whether image_data is compressed (default: True)

    Returns:
        Command bytes: 0x0070 + size (4 bytes) + initial_data

    Format:
        [cmd:2][size:4][initial_data:variable]
        - cmd: 0x0070 (big-endian)
        - size: Total image size in bytes (little-endian uint32)
        - initial_data: First chunk of image data (fits in MTU)
    """
    cmd = CommandCode.DIRECT_WRITE_START.to_bytes(2, byteorder='big')
    size = len(image_data).to_bytes(4, byteorder='little')

    # First packet: cmd (2) + size (4) = 6 bytes header
    # MTU is typically 244, so we can send ~238 bytes of data in first packet
    # But be conservative and match CHUNK_SIZE
    initial_chunk_size = min(len(image_data), CHUNK_SIZE)
    initial_data = image_data[:initial_chunk_size]

    return cmd + size + initial_data


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