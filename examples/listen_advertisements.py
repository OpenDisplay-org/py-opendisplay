"""Listen for OpenDisplay BLE advertisements and parse payloads.

Usage:
    uv run python examples/listen_advertisements.py --duration 30
    uv run python examples/listen_advertisements.py --all
"""

from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from dataclasses import dataclass
from datetime import datetime

from bleak import BleakScanner

from opendisplay import (
    MANUFACTURER_ID,
    AdvertisementData,
    AdvertisementTracker,
    parse_advertisement,
)


@dataclass
class SeenDevice:
    """Track per-device payload changes."""

    last_payload: bytes = b""
    packets_seen: int = 0
    packets_printed: int = 0


def _timestamp() -> str:
    return datetime.now().strftime("%H:%M:%S")


def _print_packet(address: str, name: str, rssi: int | None, payload: bytes, parsed: AdvertisementData) -> None:
    """Print one parsed advertisement packet."""
    base = (
        f"[{_timestamp()}] {name} ({address}) rssi={rssi} "
        f"format={parsed.format_version} battery={parsed.battery_mv}mV "
        f"temp={parsed.temperature_c:.1f}C loop={parsed.loop_counter} "
        f"len={len(payload)}"
    )

    if parsed.format_version == "v1":
        print(
            base
            + f" reboot={parsed.reboot_flag} "
            + f"conn_req={parsed.connection_requested} "
            + f"dyn={parsed.dynamic_data.hex()}"
        )
    else:
        print(base)

def _print_event(
    address: str,
    name: str,
    event_type: str,
    byte_index: int,
    button_id: int,
    pressed: bool,
    count: int,
) -> None:
    """Print one tracker event."""
    state = "down" if pressed else "up"
    print(
        f"[{_timestamp()}] EVENT {name} ({address}) type={event_type} "
        f"byte={byte_index} button_id={button_id} state={state} count={count}"
    )


async def listen(duration: float, print_all: bool) -> None:
    """Listen for advertisements and print parsed payloads."""
    seen: dict[str, SeenDevice] = {}
    formats_seen: Counter[str] = Counter()
    event_counts: Counter[str] = Counter()
    tracker = AdvertisementTracker()

    def callback(device, advertisement_data) -> None:
        payload = advertisement_data.manufacturer_data.get(MANUFACTURER_ID)
        if payload is None:
            return

        entry = seen.setdefault(device.address, SeenDevice())
        entry.packets_seen += 1

        payload_bytes = bytes(payload)
        changed = payload_bytes != entry.last_payload
        if not print_all and not changed:
            return

        entry.last_payload = payload_bytes
        entry.packets_printed += 1

        name = device.name or "Unknown"
        try:
            parsed = parse_advertisement(payload_bytes)
        except ValueError as err:
            print(
                f"[{_timestamp()}] {name} ({device.address}) rssi={advertisement_data.rssi} "
                f"len={len(payload_bytes)} parse_error={err} raw={payload_bytes.hex()}"
            )
            return

        formats_seen[parsed.format_version] += 1
        _print_packet(
            address=device.address,
            name=name,
            rssi=advertisement_data.rssi,
            payload=payload_bytes,
            parsed=parsed,
        )

        for event in tracker.update(device.address, parsed):
            event_counts[event.event_type] += 1
            _print_event(
                address=device.address,
                name=name,
                event_type=event.event_type,
                byte_index=event.byte_index,
                button_id=event.button_id,
                pressed=event.pressed,
                count=event.press_count,
            )

    print(
        f"Listening for OpenDisplay advertisements (manufacturer 0x{MANUFACTURER_ID:04x})..."
    )
    if duration > 0:
        print(f"Duration: {duration:.1f}s")
    else:
        print("Duration: unlimited (Ctrl+C to stop)")
    print("Mode: printing all packets" if print_all else "Mode: printing only changed payloads")

    scanner = BleakScanner(detection_callback=callback)
    await scanner.start()
    try:
        if duration > 0:
            await asyncio.sleep(duration)
        else:
            while True:
                await asyncio.sleep(1)
    finally:
        await scanner.stop()

    print("\nSummary:")
    print(f"  devices_seen={len(seen)}")
    print(f"  formats_seen={dict(formats_seen)}")
    print(f"  events_seen={dict(event_counts)}")
    for address, entry in sorted(seen.items()):
        print(
            f"  {address}: packets_seen={entry.packets_seen}, packets_printed={entry.packets_printed}"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Listen for OpenDisplay BLE advertisements and parse legacy/v1 formats."
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=30.0,
        help="Listen duration in seconds (0 = run until Ctrl+C). Default: 30",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Print every packet (default: print only changed payloads).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        asyncio.run(listen(duration=args.duration, print_all=args.all))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
