"""BLE response validation and parsing."""

from __future__ import annotations

import struct

from ..exceptions import InvalidResponseError, ProtocolError
from .commands import RESPONSE_HIGH_BIT_FLAG, CommandCode


def unpack_command_code(data: bytes, offset: int = 0) -> int:
    """Extract 2-byte big-endian command code from response data.

    Args:
        data: Response data from device
        offset: Byte offset to read from (default: 0)

    Returns:
        Command code as integer
    """
    return struct.unpack(">H", data[offset:offset+2])[0]


def strip_command_echo(data: bytes, expected_cmd: CommandCode) -> bytes:
    """Strip command echo from response data.

    Firmware echoes commands in responses, sometimes with high bit set.
    This function removes the 2-byte echo if present.

    Args:
        data: Response data from device
        expected_cmd: Expected command echo

    Returns:
        Data with echo stripped (if present), otherwise original data
    """
    if len(data) >= 2:
        echo = unpack_command_code(data)
        if echo == expected_cmd or echo == (expected_cmd | RESPONSE_HIGH_BIT_FLAG):
            return data[2:]
    return data


def check_response_type(response: bytes) -> tuple[CommandCode, bool]:
    """Check response type and whether it's an ACK.

    Args:
        response: Raw response data from device

    Returns:
        Tuple of (command_code, is_ack)
        - command_code: The command code (without high bit)
        - is_ack: True if response has high bit set (RESPONSE_HIGH_BIT_FLAG)
    """
    code = unpack_command_code(response)
    is_ack = bool(code & RESPONSE_HIGH_BIT_FLAG)
    command = CommandCode(code & ~RESPONSE_HIGH_BIT_FLAG)
    return command, is_ack


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

    response_code = unpack_command_code(data)

    # Response can be exact echo or with high bit set (RESPONSE_HIGH_BIT_FLAG | cmd)
    valid_responses = {expected_command, expected_command | RESPONSE_HIGH_BIT_FLAG}

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
    echo = unpack_command_code(data)
    if echo != 0x0043 and echo != (0x0043 | RESPONSE_HIGH_BIT_FLAG):
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
    chunk_id = unpack_command_code(data, offset=2)

    # Chunk IDs should be reasonable (< 100 for config responses)
    return 0 <= chunk_id < 100