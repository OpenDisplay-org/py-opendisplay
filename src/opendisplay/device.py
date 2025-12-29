"""Main OpenDisplay BLE device class."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PIL import Image

from .encoding import (
    compress_image_data,
    dither_image,
    encode_1bpp,
    encode_bitplanes,
    encode_image,
)
from .exceptions import ProtocolError
from .models.capabilities import DeviceCapabilities
from .models.config import GlobalConfig
from .models.enums import ColorScheme, DitherMode, RefreshMode
from .protocol import (
    ChunkAssembler,
    CommandCode,
    build_direct_write_data_command,
    build_direct_write_end_command,
    build_direct_write_start_command,
    build_read_config_command,
    build_read_fw_version_command,
    parse_config_response,
    parse_firmware_version,
    validate_ack_response,
)
from .protocol.responses import is_chunked_response
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
        """Read device configuration via BLE.

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

        # Strip echo and parse chunk 0 header
        chunk_data = self._strip_echo(response, CommandCode.READ_CONFIG)
        chunk_num = int.from_bytes(chunk_data[0:2], "little")
        total_length = int.from_bytes(chunk_data[2:4], "little")

        _LOGGER.debug(
            "Chunk %d: total_length=%d bytes",
            chunk_num,
            total_length,
        )

        # Extract TLV data from chunk 0
        tlv_data = bytearray(chunk_data[4:])

        # Collect remaining chunks
        while len(tlv_data) < total_length:
            _LOGGER.debug(
                "Waiting for next chunk (have %d/%d bytes)...",
                len(tlv_data),
                total_length,
            )

            next_response = await self._connection.read_response(timeout=2.0)
            next_chunk_data = self._strip_echo(next_response, CommandCode.READ_CONFIG)

            # Skip 2-byte chunk number, append rest
            tlv_data.extend(next_chunk_data[2:])

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

    def _strip_echo(self, data: bytes, expected_cmd: CommandCode) -> bytes:
        """Strip command echo from response.

        Args:
            data: Response data from device
            expected_cmd: Expected command echo

        Returns:
            Data with echo stripped (if present)
        """
        if len(data) >= 2:
            import struct
            echo = struct.unpack(">H", data[0:2])[0]
            if echo == expected_cmd or echo == (expected_cmd | 0x8000):
                return data[2:]
        return data  # Fallback: return as-is


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

        # Compress if enabled
        if compress:
            image_data = compress_image_data(image_data, level=6)
            _LOGGER.debug("Compressed: %d bytes", len(image_data))

        # Upload via direct write protocol
        await self._direct_write_upload(image_data, refresh_mode)

        _LOGGER.info("Image upload complete")

    async def _direct_write_upload(
            self,
            image_data: bytes,
            refresh_mode: RefreshMode,
    ) -> None:
        """Upload image using direct write protocol (0x0070-0x0072).

        Args:
            image_data: Encoded (and optionally compressed) image data
            refresh_mode: Display refresh mode
        """
        from .protocol import CHUNK_SIZE, PIPELINE_CHUNKS

        # 1. Send START command with first chunk
        start_cmd = build_direct_write_start_command(
            image_data,
            self.width,
            self.height,
            is_compressed=True,
        )
        await self._connection.write_command(start_cmd)

        # Wait for START ACK
        response = await self._connection.read_response(timeout=5.0)
        validate_ack_response(response, CommandCode.DIRECT_WRITE_START)

        # Calculate how much data was sent in START command
        # START format: [cmd:2][size:4][initial_data]
        header_size = 6
        initial_data_size = min(len(image_data), CHUNK_SIZE)
        bytes_sent = initial_data_size

        _LOGGER.debug(
            "Sent START with %d bytes (header=%d, data=%d)",
            len(start_cmd),
            header_size,
            initial_data_size,
        )

        # 2. Send remaining data in chunks
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

            # Wait for ACK after every PIPELINE_CHUNKS chunks
            if chunks_sent % PIPELINE_CHUNKS == 0 or bytes_sent >= len(image_data):
                response = await self._connection.read_response(timeout=5.0)
                validate_ack_response(response, CommandCode.DIRECT_WRITE_DATA)

                _LOGGER.debug(
                    "Sent %d/%d bytes (%.1f%%)",
                    bytes_sent,
                    len(image_data),
                    bytes_sent / len(image_data) * 100,
                    )

        # 3. Send END command to trigger refresh
        end_cmd = build_direct_write_end_command(refresh_mode.value)
        await self._connection.write_command(end_cmd)

        # Wait for END ACK (longer timeout for decompression + display refresh)
        # Large displays can take 15-20s to decompress and refresh
        response = await self._connection.read_response(timeout=30.0)
        validate_ack_response(response, CommandCode.DIRECT_WRITE_END)

        _LOGGER.debug("Direct write complete")

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