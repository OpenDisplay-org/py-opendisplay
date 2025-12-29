"""BLE device discovery for OpenDisplay devices."""

from __future__ import annotations

import logging
from bleak import BleakScanner

from .protocol import MANUFACTURER_ID
from .exceptions import BLETimeoutError

_LOGGER = logging.getLogger(__name__)


async def discover_devices(
        timeout: float = 10.0,
        manufacturer_id: int = MANUFACTURER_ID,
) -> dict[str, str]:
    """Discover OpenDisplay BLE devices.

    Scans for BLE devices with OpenDisplay manufacturer ID and returns
    a mapping of device names to MAC addresses.

    Args:
        timeout: Scan duration in seconds (default: 10.0)
        manufacturer_id: Manufacturer ID to filter (default: 0x2446)

    Returns:
        Dictionary mapping device_name -> mac_address
        - If device has no name, uses "Unknown_{last_4_chars_of_mac}"
        - If duplicate names found, appends "_{last_4}" to subsequent ones

    Raises:
        BLETimeoutError: If scan fails to complete

    Example:
        devices = await discover_devices(timeout=5.0)
        # Returns: {"OpenDisplay-A123": "AA:BB:CC:DD:EE:FF", ...}
    """
    _LOGGER.debug("Starting BLE scan (timeout=%ds, manufacturer_id=0x%04x)", timeout, manufacturer_id)

    try:
        devices = await BleakScanner.discover(timeout=timeout, return_adv=True)
    except Exception as e:
        raise BLETimeoutError(f"BLE scan failed: {e}") from e

    result: dict[str, str] = {}
    name_counts: dict[str, int] = {}  # Track duplicate names

    for device, adv_data in devices.values():
        # Filter by manufacturer ID
        if manufacturer_id not in adv_data.manufacturer_data:
            continue

        # Generate device name
        if device.name:
            name = device.name
        else:
            # Fallback for unnamed devices
            mac_suffix = device.address.replace(":", "")[-4:]
            name = f"Unknown_{mac_suffix}"

        # Handle duplicate names
        if name in result:
            count = name_counts.get(name, 1) + 1
            name_counts[name] = count
            mac_suffix = device.address.replace(":", "")[-4:]
            name = f"{name}_{mac_suffix}"

        result[name] = device.address
        _LOGGER.debug("Found device: %s (%s)", name, device.address)

    _LOGGER.info("Discovery complete: found %d OpenDisplay device(s)", len(result))
    return result