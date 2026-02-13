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
    FitMode,
    ICType,
    PowerMode,
    RefreshMode,
    Rotation,
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
    "RefreshMode",
    "ICType",
    "PowerMode",
    "BusType",
    "Rotation",
    # Utilities
    "parse_advertisement",
    # Constants
    "SERVICE_UUID",
    "MANUFACTURER_ID",
]
