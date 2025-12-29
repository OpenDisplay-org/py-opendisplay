"""Multi-chunk response assembly for BLE protocol."""

from __future__ import annotations

import struct

from ..exceptions import ProtocolError
from .commands import RESPONSE_HIGH_BIT_FLAG


class ChunkAssembler:
    """Assembles multi-chunk responses from BLE device.

    The device sends large responses (like TLV config) in multiple chunks:
    - Chunk 0: [echo:2][chunk_id:2][total_chunks:2][data:~94 bytes]
    - Chunk N: [echo:2][chunk_id:2][data:~96 bytes]
    """

    def __init__(self, expected_command: int):
        """Initialize chunk assembler.

        Args:
            expected_command: Command code this response is for (e.g., 0x0040)
        """
        self.expected_command = expected_command
        self.chunks: dict[int, bytes] = {}
        self.total_chunks: int | None = None
        self.complete = False

    def add_chunk(self, data: bytes) -> bool:
        """Add a chunk to the assembly.

        Args:
            data: Raw chunk data from BLE notification

        Returns:
            True if all chunks received and assembly complete

        Raises:
            ProtocolError: If chunk format invalid or command mismatch
        """
        if len(data) < 6:
            raise ProtocolError(f"Chunk too short: {len(data)} bytes (need at least 6)")

        # Parse header: [echo:2][chunk_id:2][total_chunks:2 (chunk 0 only)]
        echo_cmd = struct.unpack(">H", data[0:2])[0]  # Big-endian (command codes)
        chunk_id = struct.unpack("<H", data[2:4])[0]  # Little-endian (chunk metadata)

        # Verify echo matches expected command (with or without high-bit flag)
        valid_echoes = {self.expected_command, self.expected_command | RESPONSE_HIGH_BIT_FLAG}
        if echo_cmd not in valid_echoes:
            raise ProtocolError(
                f"Command echo mismatch: expected 0x{self.expected_command:04x}, "
                f"got 0x{echo_cmd:04x}"
            )

        # First chunk includes total_chunks field
        if chunk_id == 0:
            if len(data) < 8:
                raise ProtocolError(f"Chunk 0 too short: {len(data)} bytes (need at least 8)")

            self.total_chunks = struct.unpack("<H", data[4:6])[0]  # Little-endian
            chunk_data = data[6:]  # Data starts after total_chunks
        else:
            chunk_data = data[4:]  # Data starts after chunk_id

        # Store chunk
        self.chunks[chunk_id] = chunk_data

        # Check if complete
        if self.total_chunks is not None and len(self.chunks) == self.total_chunks:
            self.complete = True
            return True

        return False

    def get_assembled_data(self) -> bytes:
        """Get assembled data from all chunks.

        Returns:
            Complete assembled data

        Raises:
            ProtocolError: If assembly not complete
        """
        if not self.complete:
            raise ProtocolError(
                f"Assembly incomplete: have {len(self.chunks)}/{self.total_chunks or '?'} chunks"
            )

        # Assemble chunks in order
        result = b""
        for chunk_id in sorted(self.chunks.keys()):
            result += self.chunks[chunk_id]

        return result

    @property
    def is_complete(self) -> bool:
        """Check if all chunks received."""
        return self.complete

    @property
    def chunks_received(self) -> int:
        """Get number of chunks received."""
        return len(self.chunks)