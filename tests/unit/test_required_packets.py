"""Test required packet enforcement for parse and write paths."""

from __future__ import annotations

import struct

import pytest

from opendisplay import OpenDisplayDevice
from opendisplay.exceptions import ConfigParseError
from opendisplay.models.config import (
    GlobalConfig,
    ManufacturerData,
    PowerOption,
    SystemConfig,
)
from opendisplay.protocol.config_parser import parse_tlv_config


def _system_payload() -> bytes:
    return struct.pack("<HBBB", 1, 0, 0, 0) + (b"\x00" * 17)


def _manufacturer_payload() -> bytes:
    return struct.pack("<HBB", 1, 0, 1) + (b"\x00" * 18)


def _power_payload() -> bytes:
    return (
        bytes([1])  # power_mode
        + (1000).to_bytes(3, byteorder="little")
        + struct.pack("<HbBBBBBHIH", 1000, 0, 0, 0xFF, 0xFF, 0, 1, 100, 0, 0)
        + (b"\x00" * 10)
    )


def _packet(number: int, packet_type: int, payload: bytes) -> bytes:
    return bytes([number, packet_type]) + payload


def _required_tlv(
    *,
    include_system: bool = True,
    include_manufacturer: bool = True,
    include_power: bool = True,
) -> bytes:
    parts: list[bytes] = []
    packet_number = 0

    if include_system:
        parts.append(_packet(packet_number, 0x01, _system_payload()))
        packet_number += 1
    if include_manufacturer:
        parts.append(_packet(packet_number, 0x02, _manufacturer_payload()))
        packet_number += 1
    if include_power:
        parts.append(_packet(packet_number, 0x04, _power_payload()))

    return b"".join(parts)


def test_parse_tlv_requires_system_manufacturer_power() -> None:
    """Parser should fail when required packets are missing."""
    data = _required_tlv(include_manufacturer=False)

    with pytest.raises(ConfigParseError, match="Missing required packet\\(s\\): manufacturer"):
        parse_tlv_config(data)


def test_parse_tlv_succeeds_when_required_packets_present() -> None:
    """Parser should succeed when all required packets are present."""
    cfg = parse_tlv_config(_required_tlv())

    assert cfg.system is not None
    assert cfg.manufacturer is not None
    assert cfg.power is not None


def _minimal_system() -> SystemConfig:
    return SystemConfig(
        ic_type=1,
        communication_modes=1,
        device_flags=0,
        pwr_pin=0xFF,
        reserved=b"\x00" * 17,
    )


def _minimal_manufacturer() -> ManufacturerData:
    return ManufacturerData(
        manufacturer_id=1,
        board_type=0,
        board_revision=1,
        reserved=b"\x00" * 18,
    )


def _minimal_power() -> PowerOption:
    return PowerOption(
        power_mode=1,
        battery_capacity_mah=1000,
        sleep_timeout_ms=1000,
        tx_power=0,
        sleep_flags=0,
        battery_sense_pin=0xFF,
        battery_sense_enable_pin=0xFF,
        battery_sense_flags=0,
        capacity_estimator=1,
        voltage_scaling_factor=100,
        deep_sleep_current_ua=0,
        deep_sleep_time_seconds=0,
        reserved=b"\x00" * 10,
    )


@pytest.mark.asyncio
async def test_write_config_requires_system_manufacturer_power() -> None:
    """Write path should fail when required packets are missing."""
    device = OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF")

    with pytest.raises(ValueError, match="Config missing required packets: manufacturer, power"):
        await device.write_config(GlobalConfig(system=_minimal_system()))


@pytest.mark.asyncio
async def test_write_config_still_requires_display() -> None:
    """Write path should still require at least one display block."""
    device = OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF")
    cfg = GlobalConfig(
        system=_minimal_system(),
        manufacturer=_minimal_manufacturer(),
        power=_minimal_power(),
        displays=[],
    )

    with pytest.raises(ValueError, match="at least one display"):
        await device.write_config(cfg)
