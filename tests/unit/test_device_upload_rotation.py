"""Test upload image source-rotation behavior."""

from __future__ import annotations

import pytest
from epaper_dithering import ColorScheme, DitherMode
from PIL import Image

from opendisplay import OpenDisplayDevice
from opendisplay.models.capabilities import DeviceCapabilities
from opendisplay.models.enums import FitMode, Rotation


def _device(width: int = 2, height: int = 2) -> OpenDisplayDevice:
    caps = DeviceCapabilities(
        width=width,
        height=height,
        color_scheme=ColorScheme.MONO,
        rotation=0,
    )
    return OpenDisplayDevice(
        mac_address="AA:BB:CC:DD:EE:FF",
        capabilities=caps,
    )


def _stub_prepare_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "opendisplay.device.get_palette_for_display",
        lambda panel_ic_type, color_scheme, use_measured_palettes: None,
    )
    monkeypatch.setattr(
        "opendisplay.device.dither_image",
        lambda image, palette, mode, tone_compression: image.convert("P"),
    )
    monkeypatch.setattr(
        "opendisplay.device.encode_image",
        lambda image, color_scheme: b"\x01\x02",
    )


def test_rotate_source_image_requires_rotation_enum() -> None:
    """rotate must be Rotation enum, not raw int."""
    device = _device()
    image = Image.new("RGB", (2, 1), (255, 255, 255))

    with pytest.raises(TypeError, match="rotate must be Rotation"):
        device._rotate_source_image(image, 90)  # type: ignore[arg-type]


def test_prepare_image_rotates_before_fit(monkeypatch: pytest.MonkeyPatch) -> None:
    """Rotation should be applied before fit strategy sees source dimensions."""
    device = _device(width=2, height=2)
    _stub_prepare_pipeline(monkeypatch)

    seen: dict[str, tuple[int, int]] = {}

    def fake_fit_image(image: Image.Image, target_size: tuple[int, int], fit: FitMode) -> Image.Image:
        seen["size_before_fit"] = image.size
        return image.resize(target_size)

    monkeypatch.setattr("opendisplay.device.fit_image", fake_fit_image)

    image = Image.new("RGB", (4, 2), (255, 255, 255))
    encoded, compressed, processed = device._prepare_image(
        image,
        dither_mode=DitherMode.BURKES,
        compress=False,
        fit=FitMode.CONTAIN,
        rotate=Rotation.ROTATE_90,
    )

    assert seen["size_before_fit"] == (2, 4)
    assert encoded == b"\x01\x02"
    assert compressed is None
    assert processed.size == (2, 2)


def test_prepare_image_without_rotation_preserves_orientation_before_fit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """ROTATE_0 should keep source orientation before fit."""
    device = _device(width=2, height=2)
    _stub_prepare_pipeline(monkeypatch)

    seen: dict[str, tuple[int, int]] = {}

    def fake_fit_image(image: Image.Image, target_size: tuple[int, int], fit: FitMode) -> Image.Image:
        seen["size_before_fit"] = image.size
        return image.resize(target_size)

    monkeypatch.setattr("opendisplay.device.fit_image", fake_fit_image)

    image = Image.new("RGB", (4, 2), (255, 255, 255))
    device._prepare_image(
        image,
        dither_mode=DitherMode.BURKES,
        compress=False,
        fit=FitMode.CONTAIN,
        rotate=Rotation.ROTATE_0,
    )

    assert seen["size_before_fit"] == (4, 2)
