"""BLE response validation and parsing."""

from __future__ import annotations

import struct

from ..exceptions import InvalidResponseError, ProtocolError


def validate_ack_response(data: bytes, expected_command: int) -> None:
    """Validate ACK response from device.

    ACK responses echo the command code (sometimes with high bit set).

    Args:
        data: Raw response data
        expected_command: Command code that was sent

    Raises:
        InvalidResponseError: If response invalid or doesn't match command
    """
    if len(data) < 2:
        raise InvalidResponseError(f"ACK too short: {len(data)} bytes (need at least 2)")

    response_code = struct.unpack(">H", data[0:2])[0]  # Big-endian

    # Response can be exact echo or with high bit set (0x8000 | cmd)
    valid_responses = {expected_command, expected_command | 0x8000}

    if response_code not in valid_responses:
        raise InvalidResponseError(
            f"ACK mismatch: expected 0x{expected_command:04x}, got 0x{response_code:04x}"
        )


def parse_firmware_version(data: bytes) -> dict[str, int]:
    """Parse firmware version response.

    Format: [echo:2][major:1][minor:1]

    Args:
        data: Raw firmware version response

    Returns:
        Dictionary with 'major' and 'minor' version numbers

    Raises:
        InvalidResponseError: If response format invalid
    """
    if len(data) < 4:
        raise InvalidResponseError(
            f"Firmware version response too short: {len(data)} bytes (need 4)"
        )

    # Validate echo
    echo = struct.unpack(">H", data[0:2])[0]
    if echo != 0x0043 and echo != 0x8043:
        raise InvalidResponseError(
            f"Firmware version echo mismatch: expected 0x0043, got 0x{echo:04x}"
        )

    major = data[2]
    minor = data[3]

    return {
        "major": major,
        "minor": minor,
    }


def is_chunked_response(data: bytes) -> bool:
    """Check if response is a multi-chunk response.

    Chunked responses have format: [echo:2][chunk_id:2][data...]

    Args:
        data: Raw response data

    Returns:
        True if this appears to be a chunked response
    """
    if len(data) < 6:
        return False

    # Chunked responses have chunk_id in bytes 2-4
    # Chunk 0 also has total_chunks field
    # Simple heuristic: if bytes 2-4 look like a small chunk ID, it's chunked
    chunk_id = struct.unpack(">H", data[2:4])[0]

    # Chunk IDs should be reasonable (< 100 for config responses)
    return 0 <= chunk_id < 100