"""Main OpenDisplay BLE device class."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from epaper_dithering import ColorScheme, DitherMode, dither_image
from PIL import Image

from .display_palettes import PANELS_4GRAY, get_palette_for_display
from .encoding import (
    compress_image_data,
    encode_bitplanes,
    encode_image,
)
from .exceptions import BLETimeoutError, ProtocolError
from .models.capabilities import DeviceCapabilities
from .models.config import GlobalConfig
from .models.enums import RefreshMode
from .models.firmware import FirmwareVersion
from .protocol import (
    CHUNK_SIZE,
    MAX_COMPRESSED_SIZE,
    CommandCode,
    build_direct_write_data_command,
    build_direct_write_end_command,
    build_direct_write_start_compressed,
    build_direct_write_start_uncompressed,
    build_read_config_command,
    build_read_fw_version_command,
    build_reboot_command,
    build_write_config_command,
    parse_config_response,
    parse_firmware_version,
    serialize_config,
    validate_ack_response,
)
from .protocol.responses import check_response_type, strip_command_echo
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

        # Use theoretical ColorScheme instead of measured palettes
        async with OpenDisplayDevice(mac, use_measured_palettes=False) as device:
            await device.upload_image(image)
    """

    # BLE operation timeouts (seconds)
    TIMEOUT_FIRST_CHUNK = 10.0  # First chunk may take longer
    TIMEOUT_CHUNK = 2.0          # Subsequent chunks
    TIMEOUT_ACK = 5.0            # Command acknowledgments
    TIMEOUT_REFRESH = 90.0       # Display refresh (firmware spec: up to 60s)

    def __init__(
            self,
            mac_address: str | None = None,
            device_name: str | None = None,
            ble_device: BLEDevice | None = None,
            config: GlobalConfig | None = None,
            capabilities: DeviceCapabilities | None = None,
            timeout: float = 10.0,
            discovery_timeout: float = 10.0,
            max_attempts: int = 4,
            use_services_cache: bool = True,
            use_measured_palettes: bool = True,
    ):
        """Initialize OpenDisplay device.

        Args:
            mac_address: Device MAC address (mutually exclusive with device_name)
            device_name: Device name to resolve via BLE scan (mutually exclusive with mac_address)
            ble_device: Optional BLEDevice from HA bluetooth integration
            config: Optional full TLV config (skips interrogation)
            capabilities: Optional minimal device info (skips interrogation)
            timeout: BLE operation timeout in seconds (default: 10)
            discovery_timeout: Timeout for name resolution scan (default: 10)
            max_attempts: Maximum connection attempts for bleak-retry-connector (default: 4)
            use_services_cache: Enable GATT service caching for faster reconnections (default: True)
            use_measured_palettes: Use measured color palettes when available (default: True)

        Raises:
            ValueError: If neither or both mac_address and device_name provided

        Examples:
            # Using MAC address (existing behavior)
            device = OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF")

            # Using device name (new feature)
            device = OpenDisplayDevice(device_name="OpenDisplay-A123")
        """
        # Validation: exactly one of mac_address or device_name must be provided
        if mac_address and device_name:
            raise ValueError("Provide either mac_address or device_name, not both")
        if not mac_address and not device_name:
            raise ValueError("Must provide either mac_address or device_name")

        # Store for resolution in __aenter__
        self._mac_address_param = mac_address
        self._device_name = device_name
        self._discovery_timeout = discovery_timeout
        self._ble_device = ble_device
        self._timeout = timeout
        self._max_attempts = max_attempts
        self._use_services_cache = use_services_cache
        self._use_measured_palettes = use_measured_palettes

        # Will be set after resolution
        self.mac_address = mac_address or ""  # Resolved in __aenter__
        self._connection = None  # Created after MAC resolution

        self._config = config
        self._capabilities = capabilities
        self._fw_version: FirmwareVersion | None = None

    async def __aenter__(self) -> OpenDisplayDevice:
        """Connect and optionally interrogate device."""

        # Resolve device name to MAC address if needed
        if self._device_name:
            _LOGGER.debug("Resolving device name '%s' to MAC address", self._device_name)

            from .discovery import discover_devices
            from .exceptions import BLEConnectionError

            devices = await discover_devices(timeout=self._discovery_timeout)

            if self._device_name not in devices:
                raise BLEConnectionError(
                    f"Device '{self._device_name}' not found during discovery. "
                    f"Available devices: {list(devices.keys())}"
                )

            self.mac_address = devices[self._device_name]
            _LOGGER.info(
                "Resolved device name '%s' to MAC address %s",
                self._device_name,
                self.mac_address,
            )
        else:
            # MAC was provided directly
            self.mac_address = self._mac_address_param

        # Create connection with resolved MAC
        self._connection = BLEConnection(
            self.mac_address,
            self._ble_device,
            self._timeout,
            max_attempts=self._max_attempts,
            use_services_cache=self._use_services_cache,
        )

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

    def _ensure_capabilities(self) -> DeviceCapabilities:
        """Ensure device capabilities are available.

        Returns:
            DeviceCapabilities instance

        Raises:
            RuntimeError: If device not interrogated/configured
        """
        if not self._capabilities:
            raise RuntimeError(
                "Device capabilities unknown - interrogate first or provide config/capabilities"
            )
        return self._capabilities

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
        return self._ensure_capabilities().width

    @property
    def height(self) -> int:
        """Get display height in pixels."""
        return self._ensure_capabilities().height

    @property
    def color_scheme(self) -> ColorScheme:
        """Get display color scheme."""
        return self._ensure_capabilities().color_scheme

    @property
    def rotation(self) -> int:
        """Get display rotation in degrees."""
        return self._ensure_capabilities().rotation

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
        response = await self._connection.read_response(timeout=self.TIMEOUT_FIRST_CHUNK)
        chunk_data = strip_command_echo(response, CommandCode.READ_CONFIG)

        # Parse first chunk header
        total_length = int.from_bytes(chunk_data[2:4], "little")
        tlv_data = bytearray(chunk_data[4:])

        _LOGGER.debug("First chunk: %d bytes, total length: %d", len(chunk_data), total_length)

        # Read remaining chunks
        while len(tlv_data) < total_length:
            next_response = await self._connection.read_response(timeout=self.TIMEOUT_CHUNK)
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

    async def read_firmware_version(self) -> FirmwareVersion:
        """Read firmware version from device.

        Returns:
            FirmwareVersion dictionary with 'major', 'minor', and 'sha' fields
        """
        _LOGGER.debug("Reading firmware version")

        # Send read firmware version command
        cmd = build_read_fw_version_command()
        await self._connection.write_command(cmd)

        # Read response
        response = await self._connection.read_response(timeout=self.TIMEOUT_ACK)

        # Parse version (includes SHA hash)
        self._fw_version = parse_firmware_version(response)

        _LOGGER.info(
            "Firmware version: %d.%d (SHA: %s...)",
            self._fw_version["major"],
            self._fw_version["minor"],
            self._fw_version["sha"][:8],
        )

        return self._fw_version

    async def reboot(self) -> None:
        """Reboot the device.

        Sends a reboot command to the device, which will cause an immediate
        system reset. The device will NOT send an ACK response - it simply
        resets after a 100ms delay.

        Warning:
            The BLE connection will be forcibly terminated when the device
            resets. This is expected behavior. The device will restart and
            begin advertising again after the reset completes (typically
            within a few seconds).

        Raises:
            BLEConnectionError: If command cannot be sent
        """
        _LOGGER.debug("Sending reboot command to device %s", self.mac_address)

        # Build and send reboot command
        cmd = build_reboot_command()
        await self._connection.write_command(cmd)

        # Device will reset immediately - no ACK expected
        _LOGGER.info(
            "Reboot command sent to %s - device will reset (connection will drop)",
            self.mac_address
        )

    async def write_config(self, config: GlobalConfig) -> None:
        """Write configuration to device.

        Serializes the GlobalConfig to TLV binary format and writes it
        to the device using the WRITE_CONFIG (0x0041) command with
        automatic chunking for large configs.

        Args:
            config: GlobalConfig to write to device

        Raises:
            ValueError: If config serialization fails or exceeds size limit
            BLEConnectionError: If write fails
            ProtocolError: If device returns error response

        Example:
            async with OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF") as device:
                # Read current config
                config = device.config

                # Modify config
                config.displays[0].rotation = 180

                # Write back to device
                await device.write_config(config)

                # Reboot to apply changes
                await device.reboot()
        """
        _LOGGER.debug("Writing config to device %s", self.mac_address)

        # Validate critical packets are present
        if not config.system:
            _LOGGER.warning("Config missing system packet - device may not boot correctly")
        if not config.displays:
            raise ValueError("Config must have at least one display")

        # Warn about optional but important packets
        missing_packets = []
        if not config.manufacturer:
            missing_packets.append("manufacturer")
        if not config.power:
            missing_packets.append("power")

        if missing_packets:
            _LOGGER.warning(
                "Config missing optional packets: %s. "
                "Device may lose these settings.",
                ", ".join(missing_packets)
            )

        # Serialize config to binary
        config_data = serialize_config(config)

        _LOGGER.info(
            "Serialized config: %d bytes (chunking %s)",
            len(config_data),
            "required" if len(config_data) > 200 else "not needed"
        )

        # Build command with chunking
        first_cmd, chunk_cmds = build_write_config_command(config_data)

        # Send first command
        _LOGGER.debug("Sending first config chunk (%d bytes)", len(first_cmd))
        await self._connection.write_command(first_cmd)

        # Wait for ACK
        response = await self._connection.read_response(timeout=self.TIMEOUT_ACK)
        validate_ack_response(response, CommandCode.WRITE_CONFIG)

        # Send remaining chunks if needed
        for i, chunk_cmd in enumerate(chunk_cmds, start=1):
            _LOGGER.debug(
                "Sending config chunk %d/%d (%d bytes)",
                i,
                len(chunk_cmds),
                len(chunk_cmd)
            )
            await self._connection.write_command(chunk_cmd)

            # Wait for ACK after each chunk
            response = await self._connection.read_response(timeout=self.TIMEOUT_ACK)
            validate_ack_response(response, CommandCode.WRITE_CONFIG_CHUNK)

        _LOGGER.info("Config written successfully to %s", self.mac_address)

    def export_config_json(self, file_path: str) -> None:
        """Export device config to JSON file.

        Exports the configuration in a format compatible with the
        Open Display Config Builder web tool.

        Args:
            file_path: Path to save JSON file

        Raises:
            ValueError: If no config loaded

        Example:
            async with OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF") as device:
                device.export_config_json("my_config.json")
        """
        if not self._config:
            raise ValueError("No config loaded - interrogate device first")

        import json

        from .models import config_to_json

        data = config_to_json(self._config)

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

        _LOGGER.info("Exported config to %s", file_path)

    @staticmethod
    def import_config_json(file_path: str) -> GlobalConfig:
        """Import config from JSON file.

        Imports configuration from a JSON file created by the
        Open Display Config Builder web tool or exported by
        export_config_json().

        Args:
            file_path: Path to JSON file

        Returns:
            GlobalConfig instance

        Raises:
            FileNotFoundError: If file not found
            ValueError: If JSON invalid

        Example:
            config = OpenDisplayDevice.import_config_json("my_config.json")
            async with OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF") as device:
                await device.write_config(config)
        """
        import json

        from .models import config_from_json

        with open(file_path, 'r') as f:
            data = json.load(f)

        _LOGGER.info("Imported config from %s", file_path)
        return config_from_json(data)

    def _prepare_image(
        self,
        image: Image.Image,
        dither_mode: DitherMode,
        compress: bool,
        tone_compression: float | str = "auto",
    ) -> tuple[bytes, bytes | None]:
        """Prepare image for upload.

        Handles resizing, dithering, encoding, and optional compression.

        Args:
            image: PIL Image to prepare
            dither_mode: Dithering algorithm to use
            compress: Whether to compress the image data
            tone_compression: Dynamic range compression ("auto", or 0.0-1.0)

        Returns:
            Tuple of (uncompressed_data, compressed_data or None)
        """
        # Resize image to display dimensions
        if image.size != (self.width, self.height):
            _LOGGER.warning(
                "Resizing image from %dx%d to %dx%d (device display size)",
                image.width,
                image.height,
                self.width,
                self.height,
            )
            image = image.resize((self.width, self.height), Image.Resampling.LANCZOS)

        panel_ic_type = (
            self._config.displays[0].panel_ic_type
            if self._config and self._config.displays
            else None
        )
        if (
            self.color_scheme == ColorScheme.GRAYSCALE_4
            and panel_ic_type is not None
            and panel_ic_type not in PANELS_4GRAY
        ):
            _LOGGER.warning(
                "Panel IC 0x%04x is not a known 4-gray panel. "
                "GRAYSCALE_4 encoding may not display correctly.",
                panel_ic_type,
            )
        palette = get_palette_for_display(panel_ic_type, self.color_scheme, self._use_measured_palettes)
        dithered = dither_image(image, palette, mode=dither_mode, tone_compression=tone_compression)

        # Encode to device format
        if self.color_scheme in (ColorScheme.BWR, ColorScheme.BWY):
            plane1, plane2 = encode_bitplanes(dithered, self.color_scheme)
            image_data = plane1 + plane2
        else:
            image_data = encode_image(dithered, self.color_scheme)

        # Optionally compress
        compressed_data = None
        if compress:
            compressed_data = compress_image_data(image_data, level=6)

        return image_data, compressed_data

    async def upload_image(
            self,
            image: Image.Image,
            refresh_mode: RefreshMode = RefreshMode.FULL,
            dither_mode: DitherMode = DitherMode.BURKES,
            compress: bool = True,
            tone_compression: float | str = "auto",
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
            tone_compression: Dynamic range compression (default: "auto").
                "auto" = analyze image and fit to display range.
                0.0 = disabled, 0.0-1.0 = fixed linear compression.
                Only applies to measured palettes.

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

        # Prepare image (resize, dither, encode, compress)
        image_data, compressed_data = self._prepare_image(image, dither_mode, compress, tone_compression)

        # Choose protocol based on compression and size
        if compress and compressed_data and len(compressed_data) < MAX_COMPRESSED_SIZE:
            _LOGGER.info("Using compressed upload protocol (size: %d bytes)", len(compressed_data))
            await self._execute_upload(
                image_data,
                refresh_mode,
                use_compression=True,
                compressed_data=compressed_data,
                uncompressed_size=len(image_data),
            )
        else:
            if compress and compressed_data:
                _LOGGER.info("Compressed size exceeds %d bytes, using uncompressed protocol", MAX_COMPRESSED_SIZE)
            else:
                _LOGGER.info("Compression disabled, using uncompressed protocol")
            await self._execute_upload(image_data, refresh_mode, use_compression=False)

        _LOGGER.info("Image upload complete")

    async def _execute_upload(
        self,
        image_data: bytes,
        refresh_mode: RefreshMode,
        use_compression: bool = False,
        compressed_data: bytes | None = None,
        uncompressed_size: int | None = None,
    ) -> None:
        """Execute image upload using compressed or uncompressed protocol.

        Args:
            image_data: Raw uncompressed image data (always needed for uncompressed)
            refresh_mode: Display refresh mode
            use_compression: True to use compressed protocol
            compressed_data: Compressed data (required if use_compression=True)
            uncompressed_size: Original size (required if use_compression=True)

        Raises:
            ProtocolError: If upload fails
        """
        # 1. Send START command (different for each protocol)
        if use_compression:
            start_cmd, remaining_compressed = build_direct_write_start_compressed(
                uncompressed_size, compressed_data
            )
        else:
            start_cmd = build_direct_write_start_uncompressed()
            remaining_compressed = None

        await self._connection.write_command(start_cmd)

        # 2. Wait for START ACK (identical for both protocols)
        response = await self._connection.read_response(timeout=self.TIMEOUT_ACK)
        validate_ack_response(response, CommandCode.DIRECT_WRITE_START)

        # 3. Send data chunks
        auto_completed = False
        if use_compression:
            # Compressed upload: send remaining compressed data as chunks
            if remaining_compressed:
                auto_completed = await self._send_data_chunks(remaining_compressed)
        else:
            # Uncompressed upload: send raw image data as chunks
            auto_completed = await self._send_data_chunks(image_data)

        # 4. Send END command if needed (identical for both protocols)
        if not auto_completed:
            end_cmd = build_direct_write_end_command(refresh_mode.value)
            await self._connection.write_command(end_cmd)

            # Wait for END ACK (90s timeout for display refresh)
            response = await self._connection.read_response(timeout=self.TIMEOUT_REFRESH)
            validate_ack_response(response, CommandCode.DIRECT_WRITE_END)

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
                response = await self._connection.read_response(timeout=self.TIMEOUT_ACK)
            except BLETimeoutError:
                # Timeout on response - firmware might be doing display refresh
                # This happens when the chunk completes directWriteTotalBytes
                _LOGGER.info(
                    "No response after chunk %d (%.1f%%), waiting for device refresh...",
                    chunks_sent,
                    bytes_sent / len(image_data) * 100,
                )

                # Wait up to 90 seconds for the END response
                response = await self._connection.read_response(timeout=self.TIMEOUT_REFRESH)

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
