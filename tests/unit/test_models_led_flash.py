"""Test typed LED flash config model."""

import pytest

from opendisplay.models.led_flash import LedFlashConfig, LedFlashStep


def test_led_flash_config_to_bytes_and_from_bytes_roundtrip() -> None:
    cfg = LedFlashConfig(
        mode=1,
        brightness=8,
        step1=LedFlashStep(color=0xE0, flash_count=2, loop_delay_units=2, inter_delay_units=5),
        step2=LedFlashStep(color=0x1C, flash_count=3, loop_delay_units=4, inter_delay_units=7),
        step3=LedFlashStep(color=0x03, flash_count=1, loop_delay_units=6, inter_delay_units=9),
        group_repeats=4,
        reserved=0xAA,
    )

    raw = cfg.to_bytes()

    assert raw == bytes([
        0x71,
        0xE0, 0x22, 0x05,
        0x1C, 0x43, 0x07,
        0x03, 0x61, 0x09,
        0x03,
        0xAA,
    ])
    assert LedFlashConfig.from_bytes(raw) == cfg


def test_led_flash_config_single_helper() -> None:
    cfg = LedFlashConfig.single(
        color=0xE0,
        flash_count=2,
        loop_delay_units=1,
        inter_delay_units=4,
        brightness=10,
        group_repeats=2,
    )

    raw = cfg.to_bytes()
    assert raw[0] == 0x91  # brightness 10 -> raw 9, mode 1
    assert raw[1] == 0xE0
    assert raw[2] == 0x12
    assert raw[3] == 0x04
    assert raw[10] == 0x01  # group repeats 2 -> encoded 1


def test_led_flash_config_supports_infinite_group_repeats() -> None:
    cfg = LedFlashConfig(group_repeats=None)
    raw = cfg.to_bytes()
    assert raw[10] == 0xFE
    parsed = LedFlashConfig.from_bytes(raw)
    assert parsed.group_repeats is None


def test_led_flash_config_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="brightness out of range"):
        LedFlashConfig(brightness=0)

    with pytest.raises(ValueError, match="group_repeats out of range"):
        LedFlashConfig(group_repeats=0)

    with pytest.raises(ValueError, match="color out of range"):
        LedFlashStep(color=256)
