"""Main OpenDisplay BLE device class."""

from __future__ import annotations

import logging
import struct
from typing import TYPE_CHECKING

from PIL import Image

from .encoding import (
    compress_image_data,
    dither_image,
    encode_1bpp,
    encode_bitplanes,
    encode_image,
)
from .exceptions import ProtocolError, BLETimeoutError
from .models.capabilities import DeviceCapabilities
from .models.config import GlobalConfig
from .models.enums import ColorScheme, DitherMode, RefreshMode
from .protocol import (
    CHUNK_SIZE,
    MAX_COMPRESSED_SIZE,
    PIPELINE_CHUNKS,
    ChunkAssembler,
    CommandCode,
    build_direct_write_data_command,
    build_direct_write_end_command,
    build_direct_write_start_compressed,
    build_direct_write_start_uncompressed,
    build_read_config_command,
    build_read_fw_version_command,
    parse_config_response,
    parse_firmware_version,
    validate_ack_response,
)
from .protocol.responses import check_response_type, is_chunked_response, strip_command_echo
from .transport import BLEConnection

if TYPE_CHECKING:
    from bleak.backends.device import BLEDevice

_LOGGER = logging.getLogger(__name__)


class OpenDisplayDevice:
    """OpenDisplay BLE e-paper device.

    Main API for communicating with OpenDisplay BLE tags.

    Usage:
        # Auto-interrogate on first connect
        async with OpenDisplayDevice("AA:BB:CC:DD:EE:FF") as device:
            await device.upload_image(image)

        # Skip interrogation with cached config
        async with OpenDisplayDevice(mac, config=cached_config) as device:
            await device.upload_image(image)

        # Skip interrogation with minimal capabilities
        caps = DeviceCapabilities(296, 128, ColorScheme.BWR, 0)
        async with OpenDisplayDevice(mac, capabilities=caps) as device:
            await device.upload_image(image)
    """

    def __init__(
            self,
            mac_address: str,
            ble_device: BLEDevice | None = None,
            config: GlobalConfig | None = None,
            capabilities: DeviceCapabilities | None = None,
            timeout: float = 10.0,
    ):
        """Initialize OpenDisplay device.

        Args:
            mac_address: Device MAC address
            ble_device: Optional BLEDevice from HA bluetooth integration
            config: Optional full TLV config (skips interrogation)
            capabilities: Optional minimal device info (skips interrogation)
            timeout: BLE operation timeout in seconds (default: 10)
        """
        self.mac_address = mac_address
        self._connection = BLEConnection(mac_address, ble_device, timeout)

        self._config = config
        self._capabilities = capabilities
        self._fw_version: dict[str, int] | None = None

    async def __aenter__(self) -> OpenDisplayDevice:
        """Connect and optionally interrogate device."""
        await self._connection.connect()

        # Auto-interrogate if no config or capabilities provided
        if self._config is None and self._capabilities is None:
            _LOGGER.info("No config provided, auto-interrogating device")
            await self.interrogate()

        # Extract capabilities from config if available
        if self._config and not self._capabilities:
            self._capabilities = self._extract_capabilities_from_config()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Disconnect from device."""
        await self._connection.disconnect()

    @property
    def config(self) -> GlobalConfig | None:
        """Get full device configuration (if interrogated)."""
        return self._config

    @property
    def capabilities(self) -> DeviceCapabilities | None:
        """Get device capabilities (width, height, color scheme, rotation)."""
        return self._capabilities

    @property
    def width(self) -> int:
        """Get display width in pixels."""
        if not self._capabilities:
            raise RuntimeError("Device not interrogated - width unknown")
        return self._capabilities.width

    @property
    def height(self) -> int:
        """Get display height in pixels."""
        if not self._capabilities:
            raise RuntimeError("Device not interrogated - height unknown")
        return self._capabilities.height

    @property
    def color_scheme(self) -> ColorScheme:
        """Get display color scheme."""
        if not self._capabilities:
            raise RuntimeError("Device not interrogated - color scheme unknown")
        return self._capabilities.color_scheme

    @property
    def rotation(self) -> int:
        """Get display rotation in degrees."""
        if not self._capabilities:
            raise RuntimeError("Device not interrogated - rotation unknown")
        return self._capabilities.rotation

    async def interrogate(self) -> GlobalConfig:
        """Read device configuration from device.

        Returns:
            GlobalConfig with complete device configuration

        Raises:
            ProtocolError: If interrogation fails
        """
        _LOGGER.debug("Interrogating device %s", self.mac_address)

        # Send read config command
        cmd = build_read_config_command()
        await self._connection.write_command(cmd)

        # Read first chunk
        response = await self._connection.read_response(timeout=10.0)
        chunk_data = strip_command_echo(response, CommandCode.READ_CONFIG)

        # Parse first chunk header
        chunk_num = int.from_bytes(chunk_data[0:2], "little")
        total_length = int.from_bytes(chunk_data[2:4], "little")
        tlv_data = bytearray(chunk_data[4:])

        _LOGGER.debug("First chunk: %d bytes, total length: %d", len(chunk_data), total_length)

        # Read remaining chunks
        while len(tlv_data) < total_length:
            next_response = await self._connection.read_response(timeout=2.0)
            next_chunk_data = strip_command_echo(next_response, CommandCode.READ_CONFIG)

            # Skip chunk number field (2 bytes) and append data
            tlv_data.extend(next_chunk_data[2:])

            _LOGGER.debug(
                "Received chunk, total: %d/%d bytes",
                len(tlv_data),
                total_length,
            )

        _LOGGER.info("Received complete TLV data: %d bytes", len(tlv_data))

        # Parse complete config response (handles wrapper strip)
        self._config = parse_config_response(bytes(tlv_data))
        self._capabilities = self._extract_capabilities_from_config()

        _LOGGER.info(
            "Interrogated device: %dx%d, %s, rotation=%d°",
            self.width,
            self.height,
            self.color_scheme.name,
            self.rotation,
        )

        return self._config

    async def read_firmware_version(self) -> dict[str, int]:
        """Read firmware version from device.

        Returns:
            Dictionary with 'major' and 'minor' version numbers
        """
        _LOGGER.debug("Reading firmware version")

        # Send read firmware version command
        cmd = build_read_fw_version_command()
        await self._connection.write_command(cmd)

        # Read response
        response = await self._connection.read_response(timeout=5.0)

        # Parse version
        self._fw_version = parse_firmware_version(response)

        _LOGGER.info(
            "Firmware version: %d.%d",
            self._fw_version["major"],
            self._fw_version["minor"],
        )

        return self._fw_version

    async def upload_image(
            self,
            image: Image.Image,
            refresh_mode: RefreshMode = RefreshMode.FULL,
            dither_mode: DitherMode = DitherMode.BURKES,
            compress: bool = True,
    ) -> None:
        """Upload image to device display.

        Automatically handles:
        - Image resizing to display dimensions
        - Dithering based on color scheme
        - Encoding to device format
        - Compression
        - Direct write protocol

        Args:
            image: PIL Image to display
            refresh_mode: Display refresh mode (default: FULL)
            dither_mode: Dithering algorithm (default: BURKES)
            compress: Enable zlib compression (default: True)

        Raises:
            RuntimeError: If device not interrogated/configured
            ProtocolError: If upload fails
        """
        if not self._capabilities:
            raise RuntimeError(
                "Device capabilities unknown - interrogate first or provide config/capabilities"
            )

        _LOGGER.info(
            "Uploading image to %s (%dx%d, %s)",
            self.mac_address,
            self.width,
            self.height,
            self.color_scheme.name,
        )

        # Resize image to display dimensions
        if image.size != (self.width, self.height):
            _LOGGER.debug("Resizing image from %s to %s", image.size, (self.width, self.height))
            image = image.resize((self.width, self.height), Image.Resampling.LANCZOS)

        # Apply dithering
        dither_method = dither_mode.name.lower()
        dithered = dither_image(image, self.color_scheme, method=dither_method)

        # Encode to device format
        if self.color_scheme in (ColorScheme.BWR, ColorScheme.BWY):
            # Bitplane encoding for 3-color displays
            plane1, plane2 = encode_bitplanes(dithered, self.color_scheme)
            # Combine planes for direct write
            image_data = plane1 + plane2
        else:
            # Standard encoding (1bpp, 2bpp, 4bpp)
            image_data = encode_image(dithered, self.color_scheme)

        _LOGGER.debug("Encoded image: %d bytes", len(image_data))

        # Choose upload protocol based on compression and size
        if compress:
            compressed_data = compress_image_data(image_data, level=6)
            _LOGGER.debug("Compressed: %d bytes", len(compressed_data))

            if len(compressed_data) < MAX_COMPRESSED_SIZE:
                # Use compressed protocol - all data in START
                _LOGGER.info("Using compressed upload protocol (size: %d bytes)", len(compressed_data))
                await self._upload_compressed(compressed_data, len(image_data), refresh_mode)
            else:
                # Too big for compressed protocol - use uncompressed
                _LOGGER.info("Compressed size exceeds %d bytes, using uncompressed protocol", MAX_COMPRESSED_SIZE)
                await self._upload_uncompressed(image_data, refresh_mode)
        else:
            # User disabled compression - use uncompressed protocol
            _LOGGER.info("Compression disabled, using uncompressed protocol")
            await self._upload_uncompressed(image_data, refresh_mode)

        _LOGGER.info("Image upload complete")

    async def _upload_compressed(
            self,
            compressed_data: bytes,
            uncompressed_size: int,
            refresh_mode: RefreshMode,
    ) -> None:
        """Upload using compressed protocol - all data in START command.

        This protocol sends ALL image data in the START command (0x0070).
        No 0x0071 DATA chunks are sent!

        Args:
            compressed_data: Complete compressed image data
            uncompressed_size: Original uncompressed size
            refresh_mode: Display refresh mode

        Raises:
            ProtocolError: If upload fails
        """
        _LOGGER.debug("Starting compressed upload (%d bytes compressed, %d uncompressed)",
                      len(compressed_data), uncompressed_size)

        # Send START with ALL data
        start_cmd = build_direct_write_start_compressed(uncompressed_size, compressed_data)
        await self._connection.write_command(start_cmd)

        # Wait for START ACK
        response = await self._connection.read_response(timeout=5.0)
        validate_ack_response(response, CommandCode.DIRECT_WRITE_START)

        _LOGGER.debug("START ACK received, sending END command")

        # NO CHUNKS! Go straight to END
        end_cmd = build_direct_write_end_command(refresh_mode.value)
        await self._connection.write_command(end_cmd)

        # Wait for END ACK (90s timeout: firmware can take up to 60s for display refresh)
        response = await self._connection.read_response(timeout=90.0)
        validate_ack_response(response, CommandCode.DIRECT_WRITE_END)

        _LOGGER.debug("Compressed upload complete")

    async def _send_data_chunks(self, image_data: bytes) -> bool:
        """Send image data chunks with ACK handling.

        Sends image data in chunks via 0x0071 DATA commands. Handles:
        - Timeout recovery when firmware starts display refresh
        - Auto-completion detection (firmware sends 0x0072 END early)
        - Progress logging

        Args:
            image_data: Uncompressed encoded image data

        Returns:
            True if device auto-completed (sent 0x0072 END early)
            False if all chunks sent normally (caller should send END)

        Raises:
            ProtocolError: If unexpected response received
            BLETimeoutError: If no response within timeout
        """
        bytes_sent = 0
        chunks_sent = 0

        while bytes_sent < len(image_data):
            # Get next chunk
            chunk_start = bytes_sent
            chunk_end = min(chunk_start + CHUNK_SIZE, len(image_data))
            chunk_data = image_data[chunk_start:chunk_end]

            # Send DATA command
            data_cmd = build_direct_write_data_command(chunk_data)
            await self._connection.write_command(data_cmd)

            bytes_sent += len(chunk_data)
            chunks_sent += 1

            # Wait for response after every chunk (PIPELINE_CHUNKS=1)
            try:
                response = await self._connection.read_response(timeout=5.0)
            except BLETimeoutError:
                # Timeout on response - firmware might be doing display refresh
                # This happens when the chunk completes directWriteTotalBytes
                _LOGGER.info(
                    "No response after chunk %d (%.1f%%), waiting for device refresh...",
                    chunks_sent,
                    bytes_sent / len(image_data) * 100,
                )

                # Wait up to 90 seconds for the END response
                response = await self._connection.read_response(timeout=90.0)

            # Check what response we got (firmware can send 0x0072 on ANY chunk, not just last!)
            command, is_ack = check_response_type(response)

            if command == CommandCode.DIRECT_WRITE_DATA:
                # Normal DATA ACK (0x0071) - continue sending chunks
                pass
            elif command == CommandCode.DIRECT_WRITE_END:
                # Firmware auto-triggered END (0x0072) after receiving all data
                # This happens when last chunk completes directWriteTotalBytes
                _LOGGER.info(
                    "Received END response after chunk %d - device auto-completed",
                    chunks_sent,
                )
                # Note: 0x0072 is sent AFTER display refresh completes (waitforrefresh(60))
                # So we're already done - no need to send our own 0x0072 END command!
                return True  # Auto-completed
            else:
                # Unexpected response
                raise ProtocolError(f"Unexpected response: {command.name} (0x{command:04x})")

            # Log progress every 50 chunks to reduce spam
            if chunks_sent % 50 == 0 or bytes_sent >= len(image_data):
                _LOGGER.debug(
                    "Sent %d/%d bytes (%.1f%%)",
                    bytes_sent,
                    len(image_data),
                    bytes_sent / len(image_data) * 100,
                )

        _LOGGER.debug("All data chunks sent (%d chunks total)", chunks_sent)
        return False  # Normal completion, caller should send END

    async def _upload_uncompressed(
            self,
            image_data: bytes,
            refresh_mode: RefreshMode,
    ) -> None:
        """Upload using uncompressed protocol - START + chunks + END.

        This protocol sends NO data in START - all data follows via 0x0071 chunks.

        Args:
            image_data: Uncompressed encoded image data
            refresh_mode: Display refresh mode

        Raises:
            ProtocolError: If upload fails
        """
        _LOGGER.debug("Starting uncompressed upload (%d bytes)", len(image_data))

        # 1. Send START command (NO DATA!)
        start_cmd = build_direct_write_start_uncompressed()
        await self._connection.write_command(start_cmd)

        # Wait for START ACK
        response = await self._connection.read_response(timeout=5.0)
        validate_ack_response(response, CommandCode.DIRECT_WRITE_START)

        _LOGGER.debug("START ACK received, sending data chunks")

        # 2. Send all data chunks
        auto_completed = await self._send_data_chunks(image_data)

        # 3. Send END command (only if device didn't auto-complete)
        if not auto_completed:
            _LOGGER.debug("Sending END command to trigger refresh")
            end_cmd = build_direct_write_end_command(refresh_mode.value)
            await self._connection.write_command(end_cmd)

            # Wait for END ACK (90s timeout: firmware can take up to 60s for display refresh)
            response = await self._connection.read_response(timeout=90.0)
            validate_ack_response(response, CommandCode.DIRECT_WRITE_END)

        _LOGGER.debug("Uncompressed upload complete")

    def _extract_capabilities_from_config(self) -> DeviceCapabilities:
        """Extract DeviceCapabilities from GlobalConfig.

        Returns:
            DeviceCapabilities with display info

        Raises:
            RuntimeError: If config missing or invalid
        """
        if not self._config:
            raise RuntimeError("No config available")

        if not self._config.displays:
            raise RuntimeError("Config has no display information")

        display = self._config.displays[0]  # Primary display

        return DeviceCapabilities(
            width=display.pixel_width,
            height=display.pixel_height,
            color_scheme=ColorScheme.from_value(display.color_scheme),
            rotation=display.rotation,
        )