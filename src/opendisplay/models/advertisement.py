"""BLE advertisement data structures."""
import struct
from dataclasses import dataclass


@dataclass
class AdvertisementData:
    """Parsed BLE advertisement manufacturer data.

    Advertisement format (11 bytes, manufacturer ID already stripped by Bleak):

    - [0-6]: Fixed protocol bytes
    - [7-8]: Battery voltage in millivolts (little-endian uint16)
    - [9]: Chip temperature in Celsius (signed int8)
    - [10]: Loop counter (uint8, increments each advertisement)

    Note: Bleak provides manufacturer data as {0x2446: bytes([...])},
    so the 2-byte manufacturer ID is not included in this data.

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

    Note: The manufacturer ID (0x2446) is already stripped by Bleak
    and provided as the dictionary key in advertisement_data.manufacturer_data.

    Args:
        data: Raw manufacturer data (11 bytes, without the manufacturer ID prefix)

    Returns:
        AdvertisementData with parsed values

    Raises:
        ValueError: If data is too short
    """
    if len(data) < 11:
        raise ValueError(f"Advertisement data too short: {len(data)} bytes (need 11)")

    # Parse sensor data
    # Bytes 0-6 are fixed protocol bytes (ignored)
    battery_mv = struct.unpack("<H", data[7:9])[0]  # uint16, little-endian
    temperature_c = struct.unpack("b", data[9:10])[0]  # int8, signed
    loop_counter = data[10]  # uint8

    return AdvertisementData(
        battery_mv=battery_mv,
        temperature_c=temperature_c,
        loop_counter=loop_counter,
    )
