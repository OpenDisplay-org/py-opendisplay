"""Pytest configuration and fixtures."""

import pytest
from pathlib import Path
from PIL import Image

# Path to captured real protocol data
FIXTURES_DIR = Path(__file__).parent / "fixtures/real_protocol_data"


@pytest.fixture
def small_test_image():
    """Create a small RGB test image for encoding tests."""
    return Image.new("RGB", (10, 10), color=(128, 128, 128))


@pytest.fixture
def real_read_config_command():
    """Real READ_CONFIG command captured from device."""
    file = FIXTURES_DIR / "01_read_config_command.bin"
    if file.exists():
        return file.read_bytes()
    # Fallback if not captured yet
    return b'\x00\x40'


@pytest.fixture
def real_read_config_response():
    """Real config response from actual device."""
    file = FIXTURES_DIR / "01_read_config_response.bin"
    if file.exists():
        return file.read_bytes()
    return b''


@pytest.fixture
def real_firmware_command():
    """Real READ_FW_VERSION command."""
    file = FIXTURES_DIR / "02_read_firmware_command.bin"
    if file.exists():
        return file.read_bytes()
    return b'\x00\x43'


@pytest.fixture
def real_firmware_response():
    """Real firmware version response from device."""
    file = FIXTURES_DIR / "02_read_firmware_response.bin"
    if file.exists():
        return file.read_bytes()
    return b''


@pytest.fixture
def real_upload_start_command():
    """Real DIRECT_WRITE_START command (uncompressed)."""
    file = FIXTURES_DIR / "03_upload_start_uncompressed_command.bin"
    if file.exists():
        return file.read_bytes()
    return b'\x00\x70'


@pytest.fixture
def real_data_chunk_command():
    """Real DIRECT_WRITE_DATA chunk command."""
    file = FIXTURES_DIR / "04_data_chunk_command.bin"
    if file.exists():
        return file.read_bytes()
    return b''


@pytest.fixture
def real_upload_end_command():
    """Real DIRECT_WRITE_END command."""
    file = FIXTURES_DIR / "05_upload_end_command.bin"
    if file.exists():
        return file.read_bytes()
    return b'\x00\x72\x00'


def real_advertisement_data():
    """Real advertisement data from the device (manufacturer ID stripped by Bleak)."""
    # Format: [protocol:7][battery:2 LE][temp:1 signed][loop:1]
    # Real captured data: Battery 3925mV, Temp 22°C, Loop 77
    return bytes([0x02, 0x36, 0x00, 0x6c, 0x00, 0xc3, 0x01, 0x55, 0x0f, 0x16, 0x4d])
