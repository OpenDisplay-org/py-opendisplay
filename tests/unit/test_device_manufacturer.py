"""Test typed board manufacturer access on OpenDisplayDevice."""

import pytest

from opendisplay import OpenDisplayDevice
from opendisplay.models.config import (
    GlobalConfig,
    ManufacturerData,
    PowerOption,
    SystemConfig,
)
from opendisplay.models.enums import BoardManufacturer


def _system_packet() -> SystemConfig:
    return SystemConfig(
        ic_type=1,
        communication_modes=1,
        device_flags=0,
        pwr_pin=0xFF,
        reserved=b"\x00" * 17,
    )


def _manufacturer_packet(manufacturer_id: int) -> ManufacturerData:
    return ManufacturerData(
        manufacturer_id=manufacturer_id,
        board_type=0,
        board_revision=1,
        reserved=b"\x00" * 18,
    )


def _power_packet() -> PowerOption:
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


def _config_with_manufacturer(manufacturer_id: int) -> GlobalConfig:
    return GlobalConfig(
        system=_system_packet(),
        manufacturer=_manufacturer_packet(manufacturer_id),
        power=_power_packet(),
    )


class TestBoardManufacturerAccess:
    """Test OpenDisplayDevice.get_board_manufacturer()."""

    def test_returns_typed_enum_for_known_manufacturer(self):
        config = _config_with_manufacturer(1)
        device = OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF", config=config)

        assert device.get_board_manufacturer() == BoardManufacturer.SEEED

    def test_returns_raw_int_for_unknown_manufacturer(self):
        config = _config_with_manufacturer(99)
        device = OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF", config=config)

        result = device.get_board_manufacturer()
        assert isinstance(result, int)
        assert result == 99

    def test_raises_when_config_missing(self):
        device = OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF")

        with pytest.raises(RuntimeError, match="config unknown"):
            device.get_board_manufacturer()

    def test_get_board_type_returns_raw_id(self):
        config = _config_with_manufacturer(1)
        config.manufacturer.board_type = 6
        device = OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF", config=config)

        assert device.get_board_type() == 6

    def test_get_board_type_name_returns_known_name(self):
        config = _config_with_manufacturer(1)
        config.manufacturer.board_type = 1
        device = OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF", config=config)

        assert device.get_board_type_name() == "EN04"

    def test_get_board_type_name_returns_none_for_unknown(self):
        config = _config_with_manufacturer(1)
        config.manufacturer.board_type = 99
        device = OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF", config=config)

        assert device.get_board_type_name() is None
