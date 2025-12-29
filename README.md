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

Option 2: Using Device Name (Auto-Discovery)

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

Development

```bash
uv sync --all-extras
uv run pytest
```