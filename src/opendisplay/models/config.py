"""TLV configuration data structures.

  These dataclasses map directly to the firmware's TLV packet structures.
  Reference: OpenDisplayFirmware/src/structs.h
  """
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import ClassVar, Optional

from epaper_dithering import ColorScheme

from .enums import BoardManufacturer, BusType, ICType, PowerMode, Rotation


@dataclass
class SystemConfig:
    """System configuration (TLV packet type 0x01).

    Size: 22 bytes (packed struct from firmware)
    """
    ic_type: int  # uint16
    communication_modes: int  # uint8 bitfield
    device_flags: int  # uint8 bitfield
    pwr_pin: int  # uint8 (0xFF = none)
    reserved: bytes  # 17 bytes

    @property
    def has_pwr_pin(self) -> bool:
        """Check if device has external power management pin (DEVICE_FLAG_PWR_PIN)."""
        return bool(self.device_flags & 0x01)

    @property
    def needs_xiaoinit(self) -> bool:
        """Check if xiaoinit() should be called after config load - nRF52840 only (DEVICE_FLAG_XIAOINIT)."""
        return bool(self.device_flags & 0x02)

    @property
    def ic_type_enum(self) -> ICType | int:
        """Get IC type as enum, or raw int if unknown."""
        try:
            return ICType(self.ic_type)
        except ValueError:
            return self.ic_type

    SIZE: ClassVar[int] = 22

    @classmethod
    def from_bytes(cls, data: bytes) -> SystemConfig:
        """Parse from TLV packet data."""
        if len(data) < cls.SIZE:
            raise ValueError(f"Invalid SystemConfig size: {len(data)} < {cls.SIZE}")

        return cls(
            ic_type=int.from_bytes(data[0:2], 'little'),
            communication_modes=data[2],
            device_flags=data[3],
            pwr_pin=data[4],
            reserved=data[5:22]
        )


@dataclass
class ManufacturerData:
    """Manufacturer data (TLV packet type 0x02).

    Size: 22 bytes (packed struct from firmware)
    """
    manufacturer_id: int  # uint16
    board_type: int  # uint8
    board_revision: int  # uint8
    reserved: bytes  # 18 bytes

    @property
    def manufacturer_id_enum(self) -> BoardManufacturer | int:
        """Get manufacturer ID as enum, or raw int if unknown."""
        try:
            return BoardManufacturer(self.manufacturer_id)
        except ValueError:
            return self.manufacturer_id

    SIZE: ClassVar[int] = 22

    @classmethod
    def from_bytes(cls, data: bytes) -> ManufacturerData:
        """Parse from TLV packet data."""
        if len(data) < cls.SIZE:
            raise ValueError(f"Invalid ManufacturerData size: {len(data)} < {cls.SIZE}")

        return cls(
            manufacturer_id=int.from_bytes(data[0:2], 'little'),
            board_type=data[2],
            board_revision=data[3],
            reserved=data[4:22]
        )


@dataclass
class PowerOption:
    """Power configuration (TLV packet type 0x04).

    Size: 32 bytes (packed struct from firmware)
    """
    power_mode: int  # uint8
    battery_capacity_mah: int  # 3 bytes (24-bit value)
    sleep_timeout_ms: int  # uint16
    tx_power: int  # uint8
    sleep_flags: int  # uint8 bitfield
    battery_sense_pin: int  # uint8 (0xFF = none)
    battery_sense_enable_pin: int  # uint8 (0xFF = none)
    battery_sense_flags: int  # uint8 bitfield
    capacity_estimator: int  # uint8
    voltage_scaling_factor: int  # uint16
    deep_sleep_current_ua: int  # uint32
    deep_sleep_time_seconds: int  # uint16
    reserved: bytes  # 10 bytes

    @property
    def battery_mah(self) -> int:
        """Get battery capacity in mAh (converts 3-byte array to integer)."""
        return (
                self.battery_capacity_mah[0]
                | (self.battery_capacity_mah[1] << 8)
                | (self.battery_capacity_mah[2] << 16)
        )

    @property
    def power_mode_enum(self) -> PowerMode | int:
        """Get power mode as enum, or raw int if unknown."""
        try:
            return PowerMode(self.power_mode)
        except ValueError:
            return self.power_mode

    SIZE: ClassVar[int] = 32

    @classmethod
    def from_bytes(cls, data: bytes) -> PowerOption:
        """Parse from TLV packet data."""
        if len(data) < cls.SIZE:
            raise ValueError(f"Invalid PowerOption size: {len(data)} < {cls.SIZE}")

        # Parse 3-byte battery capacity
        battery_mah = int.from_bytes(data[1:4], 'little')

        return cls(
            power_mode=data[0],
            battery_capacity_mah=battery_mah,
            sleep_timeout_ms=int.from_bytes(data[4:6], 'little'),
            tx_power=data[6],
            sleep_flags=data[7],
            battery_sense_pin=data[8],
            battery_sense_enable_pin=data[9],
            battery_sense_flags=data[10],
            capacity_estimator=data[11],
            voltage_scaling_factor=int.from_bytes(data[12:14], 'little'),
            deep_sleep_current_ua=int.from_bytes(data[14:18], 'little'),
            deep_sleep_time_seconds=int.from_bytes(data[18:20], 'little'),
            reserved=data[20:32]
        )


@dataclass
class DisplayConfig:
    """Display configuration (TLV packet type 0x20, repeatable max 4).

    Size: 66 bytes (packed struct from firmware)
    """
    instance_number: int  # uint8 (0-3)
    display_technology: int  # uint8
    panel_ic_type: int  # uint16
    pixel_width: int  # uint16
    pixel_height: int  # uint16
    active_width_mm: int  # uint16
    active_height_mm: int  # uint16
    tag_type: int  # uint16 (legacy)
    rotation: int  # uint8 (degrees)
    reset_pin: int  # uint8 (0xFF = none)
    busy_pin: int  # uint8 (0xFF = none)
    dc_pin: int  # uint8 (0xFF = none)
    cs_pin: int  # uint8 (0xFF = none)
    data_pin: int  # uint8
    partial_update_support: int  # uint8
    color_scheme: int  # uint8
    transmission_modes: int  # uint8 bitfield
    clk_pin: int  # uint8
    reserved_pins: bytes  # 7 reserved pins
    reserved: bytes  # 15 bytes

    @property
    def supports_raw(self) -> bool:
        """Check if display supports raw image transmission (TRANSMISSION_MODE_RAW)."""
        return bool(self.transmission_modes & 0x01)

    @property
    def supports_zip(self) -> bool:
        """Check if display supports ZIP compressed transmission (TRANSMISSION_MODE_ZIP)."""
        return bool(self.transmission_modes & 0x02)

    @property
    def supports_g5(self) -> bool:
        """Check if display supports Group 5 compression (TRANSMISSION_MODE_G5)."""
        return bool(self.transmission_modes & 0x04)

    @property
    def supports_direct_write(self) -> bool:
        """Check if display supports direct write mode - bufferless (TRANSMISSION_MODE_DIRECT_WRITE)."""
        return bool(self.transmission_modes & 0x08)

    @property
    def clear_on_boot(self) -> bool:
        """Check if display should clear screen at bootup (TRANSMISSION_MODE_CLEAR_ON_BOOT)."""
        return bool(self.transmission_modes & 0x80)

    @property
    def screen_diagonal_inches(self) -> float | None:
        """Get physical screen diagonal in inches if dimensions are known."""
        if self.active_width_mm <= 0 or self.active_height_mm <= 0:
            return None
        diagonal_mm = math.hypot(self.active_width_mm, self.active_height_mm)
        return diagonal_mm / 25.4

    @property
    def color_scheme_enum(self) -> ColorScheme | int:
        """Get color scheme as enum, or raw int if unknown."""
        try:
            return ColorScheme(self.color_scheme)
        except ValueError:
            return self.color_scheme

    @property
    def rotation_enum(self) -> Rotation | int: # TODO check what rotation does in firmware
        """Get rotation as enum, or raw int if unknown."""
        try:
            return Rotation(self.rotation)
        except ValueError:
            return self.rotation

    SIZE: ClassVar[int] = 66

    @classmethod
    def from_bytes(cls, data: bytes) -> DisplayConfig:
        """Parse from TLV packet data."""
        if len(data) < cls.SIZE:
            raise ValueError(f"Invalid DisplayConfig size: {len(data)} < {cls.SIZE}")

        return cls(
            instance_number=data[0],
            display_technology=data[1],
            panel_ic_type=int.from_bytes(data[2:4], 'little'),
            pixel_width=int.from_bytes(data[4:6], 'little'),
            pixel_height=int.from_bytes(data[6:8], 'little'),
            active_width_mm=int.from_bytes(data[8:10], 'little'),
            active_height_mm=int.from_bytes(data[10:12], 'little'),
            tag_type=int.from_bytes(data[12:14], 'little'),
            rotation=data[14],
            reset_pin=data[15],
            busy_pin=data[16],
            dc_pin=data[17],
            cs_pin=data[18],
            data_pin=data[19],
            partial_update_support=data[20],
            color_scheme=data[21],
            transmission_modes=data[22],
            clk_pin=data[23],
            reserved_pins=data[24:31],  # pins 2-8
            reserved=data[31:66]
        )


@dataclass
class LedConfig:
    """LED configuration (TLV packet type 0x21, repeatable max 4).

    Size: 22 bytes (packed struct from firmware)
    """
    instance_number: int  # uint8
    led_type: int  # uint8
    led_1_r: int  # uint8 (red channel pin)
    led_2_g: int  # uint8 (green channel pin)
    led_3_b: int  # uint8 (blue channel pin)
    led_4: int  # uint8 (4th channel pin)
    led_flags: int  # uint8 bitfield
    reserved: bytes  # 15 bytes

    SIZE: ClassVar[int] = 22

    @classmethod
    def from_bytes(cls, data: bytes) -> LedConfig:
        """Parse from TLV packet data."""
        if len(data) < cls.SIZE:
            raise ValueError(f"Invalid LedConfig size: {len(data)} < {cls.SIZE}")

        return cls(
            instance_number=data[0],
            led_type=data[1],
            led_1_r=data[2],
            led_2_g=data[3],
            led_3_b=data[4],
            led_4=data[5],
            led_flags=data[6],
            reserved=data[7:22]
        )


@dataclass
class SensorData:
    """Sensor configuration (TLV packet type 0x23, repeatable max 4).

    Size: 30 bytes (packed struct from firmware)
    """
    instance_number: int  # uint8
    sensor_type: int  # uint16
    bus_id: int  # uint8
    reserved: bytes  # 26 bytes

    SIZE: ClassVar[int] = 30

    @classmethod
    def from_bytes(cls, data: bytes) -> SensorData:
        """Parse from TLV packet data."""
        if len(data) < cls.SIZE:
            raise ValueError(f"Invalid SensorData size: {len(data)} < {cls.SIZE}")

        return cls(
            instance_number=data[0],
            sensor_type=int.from_bytes(data[1:3], 'little'),
            bus_id=data[3],
            reserved=data[4:30]
        )


@dataclass
class DataBus:
    """Data bus configuration (TLV packet type 0x24, repeatable max 4).

    Size: 28 bytes (packed struct from firmware)
    """
    instance_number: int  # uint8
    bus_type: int  # uint8
    pin_1: int  # uint8 (SCL for I2C)
    pin_2: int  # uint8 (SDA for I2C)
    pin_3: int  # uint8
    pin_4: int  # uint8
    pin_5: int  # uint8
    pin_6: int  # uint8
    pin_7: int  # uint8
    bus_speed_hz: int  # uint32
    bus_flags: int  # uint8 bitfield
    pullups: int  # uint8 bitfield
    pulldowns: int  # uint8 bitfield
    reserved: bytes  # 14 bytes

    SIZE: ClassVar[int] = 28

    @classmethod
    def from_bytes(cls, data: bytes) -> DataBus:
        """Parse from TLV packet data."""
        if len(data) < cls.SIZE:
            raise ValueError(f"Invalid DataBus size: {len(data)} < {cls.SIZE}")

        return cls(
            instance_number=data[0],
            bus_type=data[1],
            pin_1=data[2],
            pin_2=data[3],
            pin_3=data[4],
            pin_4=data[5],
            pin_5=data[6],
            pin_6=data[7],
            pin_7=data[8],
            bus_speed_hz=int.from_bytes(data[9:13], 'little'),
            bus_flags=data[13],
            pullups=data[14],
            pulldowns=data[15],
            reserved=data[16:28]
        )

    @property
    def bus_type_enum(self) -> BusType | int:
        """Get bus type as enum, or raw int if unknown."""
        try:
            return BusType(self.bus_type)
        except ValueError:
            return self.bus_type


@dataclass
class BinaryInputs:
    """Binary inputs configuration (TLV packet type 0x25, repeatable max 4).

    Size: 29 bytes (packed struct from firmware)
    """
    instance_number: int  # uint8
    input_type: int  # uint8
    display_as: int  # uint8
    reserved_pins: bytes  # 8 reserved pins
    input_flags: int  # uint8 bitfield
    invert: int  # uint8 bitfield
    pullups: int  # uint8 bitfield
    pulldowns: int  # uint8 bitfield
    reserved: bytes  # 15 bytes

    SIZE: ClassVar[int] = 29

    @classmethod
    def from_bytes(cls, data: bytes) -> BinaryInputs:
        """Parse from TLV packet data."""
        if len(data) < cls.SIZE:
            raise ValueError(f"Invalid BinaryInputs size: {len(data)} < {cls.SIZE}")

        return cls(
            instance_number=data[0],
            input_type=data[1],
            display_as=data[2],
            reserved_pins=data[3:11],  # 8 pins
            input_flags=data[11],
            invert=data[12],
            pullups=data[13],
            pulldowns=data[14],
            reserved=data[15:29]
        )


@dataclass
class GlobalConfig:
    """Complete device configuration parsed from TLV data.

    Corresponds to GlobalConfig struct in firmware.
    """
    # Required single-instance packets
    system: Optional[SystemConfig] = None
    manufacturer: Optional[ManufacturerData] = None
    power: Optional[PowerOption] = None

    # Optional repeatable packets (max 4 each)
    displays: list[DisplayConfig] = field(default_factory=list)
    leds: list[LedConfig] = field(default_factory=list)
    sensors: list[SensorData] = field(default_factory=list)
    data_buses: list[DataBus] = field(default_factory=list)
    binary_inputs: list[BinaryInputs] = field(default_factory=list)

    # Metadata
    version: int = 0
    minor_version: int = 0
    loaded: bool = False
