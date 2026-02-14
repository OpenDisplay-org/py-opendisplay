"""Typed LED flash configuration for firmware LED activate command (0x0073)."""

from __future__ import annotations

from dataclasses import dataclass, field


def _check_u8(name: str, value: int) -> None:
    if not 0 <= value <= 0xFF:
        raise ValueError(f"{name} out of range: {value} (must be 0-255)")


def _check_nibble(name: str, value: int) -> None:
    if not 0 <= value <= 0x0F:
        raise ValueError(f"{name} out of range: {value} (must be 0-15)")


@dataclass(frozen=True, slots=True)
class LedFlashStep:
    """One LED flash step used by firmware LED mode 1."""

    color: int = 0
    flash_count: int = 0
    loop_delay_units: int = 0
    inter_delay_units: int = 0

    def __post_init__(self) -> None:
        _check_u8("color", self.color)
        _check_nibble("flash_count", self.flash_count)
        _check_nibble("loop_delay_units", self.loop_delay_units)
        _check_u8("inter_delay_units", self.inter_delay_units)


@dataclass(frozen=True, slots=True)
class LedFlashConfig:
    """Typed 12-byte payload for firmware LED activate command (0x0073)."""

    mode: int = 1
    brightness: int = 8
    step1: LedFlashStep = field(default_factory=LedFlashStep)
    step2: LedFlashStep = field(default_factory=LedFlashStep)
    step3: LedFlashStep = field(default_factory=LedFlashStep)
    group_repeats: int | None = 1
    reserved: int = 0

    def __post_init__(self) -> None:
        _check_nibble("mode", self.mode)
        if not 1 <= self.brightness <= 16:
            raise ValueError(
                f"brightness out of range: {self.brightness} (must be 1-16)"
            )
        if self.group_repeats is not None and not 1 <= self.group_repeats <= 255:
            raise ValueError(
                "group_repeats out of range: "
                f"{self.group_repeats} (must be 1-255 or None for infinite)"
            )
        _check_u8("reserved", self.reserved)

    @classmethod
    def single(
        cls,
        *,
        color: int,
        flash_count: int = 1,
        loop_delay_units: int = 0,
        inter_delay_units: int = 0,
        brightness: int = 8,
        group_repeats: int | None = 1,
    ) -> LedFlashConfig:
        """Build a simple one-step flash pattern."""
        return cls(
            mode=1,
            brightness=brightness,
            step1=LedFlashStep(
                color=color,
                flash_count=flash_count,
                loop_delay_units=loop_delay_units,
                inter_delay_units=inter_delay_units,
            ),
            group_repeats=group_repeats,
        )

    @staticmethod
    def _encode_step(step: LedFlashStep) -> tuple[int, int, int]:
        packed = ((step.loop_delay_units & 0x0F) << 4) | (step.flash_count & 0x0F)
        return step.color & 0xFF, packed, step.inter_delay_units & 0xFF

    @staticmethod
    def _decode_step(color: int, packed: int, inter_delay: int) -> LedFlashStep:
        return LedFlashStep(
            color=color,
            flash_count=packed & 0x0F,
            loop_delay_units=(packed >> 4) & 0x0F,
            inter_delay_units=inter_delay,
        )

    def to_bytes(self) -> bytes:
        """Serialize to 12-byte firmware payload."""
        mode_and_brightness = (((self.brightness - 1) & 0x0F) << 4) | (self.mode & 0x0F)

        c1, p1, i1 = self._encode_step(self.step1)
        c2, p2, i2 = self._encode_step(self.step2)
        c3, p3, i3 = self._encode_step(self.step3)

        group_repeats_raw = 0xFE if self.group_repeats is None else (self.group_repeats - 1) & 0xFF

        return bytes([
            mode_and_brightness,
            c1, p1, i1,
            c2, p2, i2,
            c3, p3, i3,
            group_repeats_raw,
            self.reserved & 0xFF,
        ])

    @classmethod
    def from_bytes(cls, data: bytes) -> LedFlashConfig:
        """Parse a 12-byte firmware payload."""
        if len(data) != 12:
            raise ValueError(f"LED flash config must be exactly 12 bytes, got {len(data)}")

        mode = data[0] & 0x0F
        brightness = ((data[0] >> 4) & 0x0F) + 1
        group_raw = data[10]
        group_repeats = None if group_raw == 0xFE else (group_raw + 1)

        return cls(
            mode=mode,
            brightness=brightness,
            step1=cls._decode_step(data[1], data[2], data[3]),
            step2=cls._decode_step(data[4], data[5], data[6]),
            step3=cls._decode_step(data[7], data[8], data[9]),
            group_repeats=group_repeats,
            reserved=data[11],
        )
