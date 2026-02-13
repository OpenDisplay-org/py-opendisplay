"""Test typed board manufacturer access on OpenDisplayDevice."""

import pytest

from opendisplay import OpenDisplayDevice
from opendisplay.models.config import GlobalConfig, ManufacturerData
from opendisplay.models.enums import BoardManufacturer


def _manufacturer_packet(manufacturer_id: int) -> ManufacturerData:
    return ManufacturerData(
        manufacturer_id=manufacturer_id,
        board_type=0,
        board_revision=1,
        reserved=b"\x00" * 18,
    )


class TestBoardManufacturerAccess:
    """Test OpenDisplayDevice.get_board_manufacturer()."""

    def test_returns_typed_enum_for_known_manufacturer(self):
        config = GlobalConfig(manufacturer=_manufacturer_packet(1))
        device = OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF", config=config)

        assert device.get_board_manufacturer() == BoardManufacturer.SEEED

    def test_returns_raw_int_for_unknown_manufacturer(self):
        config = GlobalConfig(manufacturer=_manufacturer_packet(99))
        device = OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF", config=config)

        result = device.get_board_manufacturer()
        assert isinstance(result, int)
        assert result == 99

    def test_raises_when_config_missing(self):
        device = OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF")

        with pytest.raises(RuntimeError, match="config unknown"):
            device.get_board_manufacturer()

    def test_raises_when_manufacturer_packet_missing(self):
        device = OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF", config=GlobalConfig())

        with pytest.raises(RuntimeError, match="missing manufacturer data"):
            device.get_board_manufacturer()

    def test_get_board_type_returns_raw_id(self):
        config = GlobalConfig(manufacturer=_manufacturer_packet(1))
        config.manufacturer.board_type = 6
        device = OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF", config=config)

        assert device.get_board_type() == 6

    def test_get_board_type_name_returns_known_name(self):
        config = GlobalConfig(manufacturer=_manufacturer_packet(1))
        config.manufacturer.board_type = 1
        device = OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF", config=config)

        assert device.get_board_type_name() == "EN04"

    def test_get_board_type_name_returns_none_for_unknown(self):
        config = GlobalConfig(manufacturer=_manufacturer_packet(1))
        config.manufacturer.board_type = 99
        device = OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF", config=config)

        assert device.get_board_type_name() is None
