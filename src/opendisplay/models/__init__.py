"""Data models for OpenDisplay devices."""

from .advertisement import AdvertisementData, parse_advertisement
from .capabilities import DeviceCapabilities
from .config import (
    BinaryInputs,
    DataBus,
    DisplayConfig,
    GlobalConfig,
    LedConfig,
    ManufacturerData,
    PowerOption,
    SensorData,
    SystemConfig,
    WifiConfig,
)
from .config_json import config_from_json, config_to_json
from .enums import (
    BoardManufacturer,
    BusType,
    DIYBoardType,
    FitMode,
    ICType,
    PowerMode,
    RefreshMode,
    Rotation,
    SeeedBoardType,
    WaveshareBoardType,
    get_board_type_name,
    get_manufacturer_name,
)
from .firmware import FirmwareVersion

__all__ = [
    "AdvertisementData",
    "parse_advertisement",
    "BinaryInputs",
    "BoardManufacturer",
    "BusType",
    "DIYBoardType",
    "config_from_json",
    "config_to_json",
    "DataBus",
    "DeviceCapabilities",
    "DisplayConfig",
    "FirmwareVersion",
    "FitMode",
    "GlobalConfig",
    "ICType",
    "LedConfig",
    "ManufacturerData",
    "PowerMode",
    "PowerOption",
    "RefreshMode",
    "Rotation",
    "SeeedBoardType",
    "SensorData",
    "SystemConfig",
    "WifiConfig",
    "WaveshareBoardType",
    "get_board_type_name",
    "get_manufacturer_name",
]
