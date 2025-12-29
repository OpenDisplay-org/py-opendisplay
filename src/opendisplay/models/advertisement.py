"""BLE advertisement data structures."""
import struct
from dataclasses import dataclass


@dataclass
class AdvertisementData:
    """Parsed BLE advertisement manufacturer data.

    Advertisement format (13 bytes):

    - [0-1]: Manufacturer ID 0x2446 (little-endian)
    - [2-8]: Fixed protocol bytes
    - [9-10]: Battery voltage in millivolts (little-endian uint16)
    - [11]: Chip temperature in Celsius (signed int8)
    - [12]: Loop counter (uint8, increments each advertisement)

    Attributes:
        battery_mv: Battery voltage in millivolts
        temperature_c: Chip temperature in Celsius
        loop_counter: Incrementing counter for each advertisement
    """
    battery_mv: int
    temperature_c: int
    loop_counter: int


def parse_advertisement(data: bytes) -> AdvertisementData:
    """Parse BLE advertisement manufacturer data.

    Args:
        data: Raw manufacturer data (13 bytes minimum)

    Returns:
        AdvertisementData with parsed values

    Raises:
        ValueError: If data is too short or invalid
    """
    if len(data) < 13:
        raise ValueError(f"Advertisement data too short: {len(data)} bytes (need 13)")

    # Verify manufacturer ID (bytes 0-1, little-endian)
    manufacturer_id = struct.unpack("<H", data[0:2])[0]
    if manufacturer_id != 0x2446:
        raise ValueError(
            f"Invalid manufacturer ID: 0x{manufacturer_id:04x} (expected 0x2446)"
        )

    # Parse sensor data (bytes 9-12)
    # Bytes 2-8 are fixed protocol bytes (ignored)
    battery_mv = struct.unpack("<H", data[9:11])[0]  # uint16, little-endian
    temperature_c = struct.unpack("b", data[11:12])[0]  # int8, signed
    loop_counter = data[12]  # uint8

    return AdvertisementData(
        battery_mv=battery_mv,
        temperature_c=temperature_c,
        loop_counter=loop_counter,
    )