"""BLE advertisement data structures."""

from __future__ import annotations

import struct
from dataclasses import dataclass, field


@dataclass
class AdvertisementData:
    """Parsed BLE advertisement manufacturer data.

    Supports both legacy and current firmware advertisement layouts.

    Legacy format (11 bytes, manufacturer ID already stripped by Bleak):
    - [0-6]: Fixed protocol bytes
    - [7-8]: Battery voltage in millivolts (little-endian uint16)
    - [9]: Chip temperature in Celsius (signed int8)
    - [10]: Loop counter (uint8, increments each advertisement)

    Current format (14 bytes, firmware 1.0+):
    - [0-10]: dynamic return data bytes
    - [11]: Temperature encoded as (temp_c + 40) * 2 (0.5C resolution)
    - [12]: Battery voltage (10mV units), low byte
    - [13]: Status byte:
      bit0=battery voltage high bit, bit1=reboot flag, bit2=connection requested,
      bits4-7=loop counter (4-bit)

    Note: Bleak provides manufacturer data as {0x2446: bytes([...])},
    so the 2-byte manufacturer ID is not included in this data.
    This parser also accepts payloads where the manufacturer ID is included
    (13-byte legacy or 16-byte current payload) and strips it automatically.

    Attributes:
        battery_mv: Battery voltage in millivolts
        temperature_c: Chip temperature in Celsius
        loop_counter: Incrementing counter for each advertisement
        format_version: Parsed advertisement format ("legacy" or "v1")
        reboot_flag: Reboot flag from status byte (v1 only)
        connection_requested: Connection-request flag from status byte (v1 only)
        dynamic_data: Dynamic return data block (v1 only)
    """
    battery_mv: int
    temperature_c: float
    loop_counter: int
    format_version: str = "legacy"
    reboot_flag: bool | None = None
    connection_requested: bool | None = None
    dynamic_data: bytes = field(default_factory=bytes)
    raw_data: bytes = field(default_factory=bytes)


LEGACY_LENGTH = 11
V1_LENGTH = 14
MANUFACTURER_ID_LE = b"\x46\x24"
LEGACY_PREFIX = b"\x02\x36\x00\x6c\x00\xc3\x01"


def _strip_manufacturer_id(data: bytes) -> bytes:
    """Strip manufacturer ID prefix if present."""
    if len(data) in (13, 16) and data[:2] == MANUFACTURER_ID_LE:
        return data[2:]
    return data


def _parse_legacy(data: bytes) -> AdvertisementData:
    """Parse legacy 11-byte advertisement data."""
    battery_mv = struct.unpack("<H", data[7:9])[0]  # uint16, little-endian
    temperature_c = float(struct.unpack("b", data[9:10])[0])  # int8, signed
    loop_counter = data[10]  # uint8

    return AdvertisementData(
        battery_mv=battery_mv,
        temperature_c=temperature_c,
        loop_counter=loop_counter,
        format_version="legacy",
        raw_data=data[:LEGACY_LENGTH],
    )


def _parse_v1(data: bytes) -> AdvertisementData:
    """Parse v1 14-byte advertisement data (firmware 1.0+)."""
    dynamic_data = data[0:11]
    temperature_c = (data[11] / 2.0) - 40.0
    battery_10mv = data[12] | ((data[13] & 0x01) << 8)
    battery_mv = battery_10mv * 10
    reboot_flag = bool(data[13] & 0x02)
    connection_requested = bool(data[13] & 0x04)
    loop_counter = (data[13] >> 4) & 0x0F

    return AdvertisementData(
        battery_mv=battery_mv,
        temperature_c=temperature_c,
        loop_counter=loop_counter,
        format_version="v1",
        reboot_flag=reboot_flag,
        connection_requested=connection_requested,
        dynamic_data=dynamic_data,
        raw_data=data[:V1_LENGTH],
    )


def parse_advertisement(data: bytes) -> AdvertisementData:
    """Parse BLE advertisement manufacturer data.

    Note: The manufacturer ID (0x2446) is already stripped by Bleak
    and provided as the dictionary key in advertisement_data.manufacturer_data,
    but this parser also accepts payloads where the manufacturer ID is present.

    Args:
        data: Raw manufacturer data in legacy (11 bytes) or v1 (14 bytes) format.

    Returns:
        AdvertisementData with parsed values

    Raises:
        ValueError: If data is too short or has an unsupported format
    """
    payload = _strip_manufacturer_id(data)

    if len(payload) < LEGACY_LENGTH:
        raise ValueError(
            f"Advertisement data too short: {len(payload)} bytes "
            f"(need {LEGACY_LENGTH} for legacy or {V1_LENGTH} for v1)"
        )

    if len(payload) >= V1_LENGTH:
        return _parse_v1(payload)

    if len(payload) >= LEGACY_LENGTH:
        if payload[:7] != LEGACY_PREFIX:
            raise ValueError(
                "Unsupported legacy advertisement signature; expected "
                f"{LEGACY_PREFIX.hex()} at bytes 0-6"
            )
        return _parse_legacy(payload)

    raise ValueError(f"Unsupported advertisement format ({len(payload)} bytes)")
