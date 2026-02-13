"""OpenDisplay BLE Protocol Package.

  Pure Python package for communicating with OpenDisplay BLE e-paper tags.
  """

from epaper_dithering import ColorScheme, DitherMode

from .device import OpenDisplayDevice
from .discovery import discover_devices
from .exceptions import (
    BLEConnectionError,
    BLETimeoutError,
    ConfigParseError,
    ImageEncodingError,
    InvalidResponseError,
    OpenDisplayError,
    ProtocolError,
)
from .models.advertisement import AdvertisementData, parse_advertisement
from .models.capabilities import DeviceCapabilities
from .models.config import (
    BinaryInputs,
    DataBus,
    DisplayConfig,
    GlobalConfig,
    LedConfig,
    ManufacturerData,
    PowerOption,
    SensorData,
    SystemConfig,
)
from .models.enums import (
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
from .protocol import MANUFACTURER_ID, SERVICE_UUID

__version__ = "0.1.0"

__all__ = [
    # Main API
    "OpenDisplayDevice",
    "discover_devices",
    # Exceptions
    "OpenDisplayError",
    "BLEConnectionError",
    "BLETimeoutError",
    "ProtocolError",
    "ConfigParseError",
    "InvalidResponseError",
    "ImageEncodingError",
    # Models - Config
    "GlobalConfig",
    "SystemConfig",
    "ManufacturerData",
    "PowerOption",
    "DisplayConfig",
    "LedConfig",
    "SensorData",
    "DataBus",
    "BinaryInputs",
    # Models - Other
    "DeviceCapabilities",
    "AdvertisementData",
    # Enums
    "ColorScheme",
    "DitherMode",
    "FitMode",
    "BoardManufacturer",
    "DIYBoardType",
    "RefreshMode",
    "ICType",
    "PowerMode",
    "BusType",
    "Rotation",
    "SeeedBoardType",
    "WaveshareBoardType",
    "get_board_type_name",
    "get_manufacturer_name",
    # Utilities
    "parse_advertisement",
    # Constants
    "SERVICE_UUID",
    "MANUFACTURER_ID",
]
