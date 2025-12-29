"""BLE protocol implementation."""

from .chunking import ChunkAssembler
from .commands import (
    CHUNK_SIZE,
    CONFIG_CHUNK_SIZE,
    MANUFACTURER_ID,
    PIPELINE_CHUNKS,
    SERVICE_UUID,
    CommandCode,
    build_direct_write_data_command,
    build_direct_write_end_command,
    build_direct_write_start_command,
    build_read_config_command,
    build_read_fw_version_command,
)
from .config_parser import parse_config_response, parse_tlv_config
from .responses import (
    is_chunked_response,
    parse_firmware_version,
    validate_ack_response,
)

__all__ = [
    "CommandCode",
    "SERVICE_UUID",
    "MANUFACTURER_ID",
    "CHUNK_SIZE",
    "CONFIG_CHUNK_SIZE",
    "PIPELINE_CHUNKS",
    "build_read_config_command",
    "build_read_fw_version_command",
    "build_direct_write_start_command",
    "build_direct_write_data_command",
    "build_direct_write_end_command",
    "ChunkAssembler",
    "parse_config_response",
    "parse_tlv_config",
    "validate_ack_response",
    "parse_firmware_version",
    "is_chunked_response",
]