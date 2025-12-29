# py-opendisplay

Python library for communicating with OpenDisplay BLE e-paper displays.

## Installation

```bash
pip install py-opendisplay
```

## Quick Start

### Option 1: Using MAC Address

```python
from opendisplay import OpenDisplayDevice
from PIL import Image

async with OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF") as device:
    image = Image.open("photo.jpg")
    await device.upload_image(image)
```

### Option 2: Using Device Name (Auto-Discovery)

```python
from opendisplay import OpenDisplayDevice, discover_devices
from PIL import Image

# List available devices
devices = await discover_devices()
print(devices)  # {"OpenDisplay-A123": "AA:BB:CC:DD:EE:FF", ...}

# Connect using name
async with OpenDisplayDevice(device_name="OpenDisplay-A123") as device:
  image = Image.open("photo.jpg")
  await device.upload_image(image)
```

Image Resizing

Images are automatically resized to match the display dimensions. A warning is logged if resizing occurs:

`WARNING:opendisplay.device:Resizing image from 1920x1080 to 296x128` (device display size)

For best results, resize images to the exact display dimensions before uploading.

## Dithering Algorithms

E-paper displays have limited color palettes, requiring dithering to convert full-color images. py-opendisplay supports 9 dithering algorithms with different quality/speed tradeoffs:

### Available Algorithms

- **`none`** - Direct palette mapping without dithering (fastest, lowest quality)
- **`ordered`** - Bayer/ordered dithering using pattern matrix (fast, visible patterns)
- **`burkes`** - Burkes error diffusion (default, good balance)
- **`floyd-steinberg`** - Floyd-Steinberg error diffusion (most popular, widely used)
- **`sierra-lite`** - Sierra Lite (fast, simple 3-neighbor algorithm)
- **`sierra`** - Sierra-2-4A (balanced quality and performance)
- **`atkinson`** - Atkinson (designed for early Macs, artistic look)
- **`stucki`** - Stucki (high quality, wide error distribution)
- **`jarvis-judice-ninke`** - Jarvis-Judice-Ninke (highest quality, smooth gradients)

### Usage Example

```python
from opendisplay import OpenDisplayDevice, RefreshMode, DitherMode
from PIL import Image

async with OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF") as device:
    image = Image.open("photo.jpg")

    # Use Floyd-Steinberg dithering
    await device.upload_image(
        image,
        dither_mode=DitherMode.FLOYD_STEINBERG,
        refresh_mode=RefreshMode.FULL
    )
```
Comparing Dithering Modes

To preview how different dithering algorithms will look on your e-paper display, use the https://img2lcd.com/ online tool. Upload your image and compare the visual results of different dithering algorithms before choosing one for your application.

Quality vs Speed Tradeoff:
- Fastest: none, ordered, sierra-lite
- Balanced: burkes, floyd-steinberg, sierra
- Highest Quality: atkinson, stucki, jarvis-judice-ninke

## Development

```bash
uv sync --all-extras
uv run pytest
```