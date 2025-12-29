# py-opendisplay

Python library for communicating with OpenDisplay BLE e-paper displays.

## Installation

```bash
pip install py-opendisplay
```

  Quick Start
```python
from opendisplay import OpenDisplayDevice
from PIL import Image

async with OpenDisplayDevice("AA:BB:CC:DD:EE:FF") as device:
  image = Image.open("photo.jpg")
  await device.upload_image(image)
```

Development

```bash
uv sync --all-extras
uv run pytest
```