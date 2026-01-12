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

## Image Resizing

Images are automatically resized to match the display dimensions. A warning is logged if resizing occurs:

- WARNING:opendisplay.device:Resizing image from 1920x1080 to 296x128

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
### Comparing Dithering Modes

To preview how different dithering algorithms will look on your e-paper display, use the **[img2lcd.com](https://img2lcd.com/)** online tool.
Upload your image and compare the visual results before choosing an algorithm.

**Quality vs Speed Tradeoff:**

| Category | Algorithms |
|--------|------------|
| Fastest / Lowest Cost | `none`, `ordered`, `sierra-lite` |
| Best Cost-to-Quality | `floyd-steinberg`, `burkes`, `sierra` |
| Heavy / Rarely Worth It | `stucki`, `jarvis-judice-ninke` |
| Stylized / High Contrast | `atkinson` |

## Refresh Modes

Control how the display updates when uploading images:

```python
from opendisplay import RefreshMode

await device.upload_image(
    image,
    refresh_mode=RefreshMode.FULL  # Options: FULL, FAST, PARTIAL, PARTIAL2
)
```

### Available Modes

| Mode | Description |
|---|---|
| `RefreshMode.FULL` | Full display refresh \(default\). Cleanest image quality; eliminates ghosting; slower \(~5–15 seconds\). |
| `RefreshMode.FAST` | Fast partial refresh. Quicker updates; may show slight ghosting. |
| `RefreshMode.PARTIAL` | Partial refresh mode 2. |
| `RefreshMode.PARTIAL2` | Partial refresh mode 3. |

Note: Partial refresh support varies by display hardware. Check [device capabilities](https://opendisplay.org/firmware/seeed_display_compatibility.html) for supported modes.

## Advanced Features

### Device Interrogation

Query the complete device configuration including hardware specs, sensors, and capabilities:

```python
async with OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF") as device:
    # Automatic interrogation on first connect
    config = device.config
    
    print(f"IC Type: {config.system.ic_type_enum.name}")
    print(f"Displays: {len(config.displays)}")
    print(f"Sensors: {len(config.sensors)}")
```

Skip interrogation if the device info is already cached:
```python

# Provide cached config to skip interrogation
device = OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF", config=cached_config)

# Or provide minimal capabilities
capabilities = DeviceCapabilities(296, 128, ColorScheme.BWR, 0)
device = OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF", capabilities=capabilities)
```

### Firmware Version

Read the device firmware version including git commit SHA:

```python
async with OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF") as device:
    fw = await device.read_firmware_version()
    print(f"Firmware: {fw['major']}.{fw['minor']}")
    print(f"Git SHA: {fw['sha']}")

    # Example output:
    # Firmware: 0.65
    # Git SHA: e63ae32447a83f3b64f3146999060ca1e906bf15
```

### Rebooting the Device

Remotely reboot the device (useful after configuration changes or troubleshooting):

```python
async with OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF") as device:
    await device.reboot()
    # Device will reset after ~100ms
    # BLE connection will drop (this is expected)
```

**Note:** The device performs an immediate system reset and does not send an ACK response. The BLE connection will be terminated when the device resets. Wait a few seconds before attempting to reconnect.

### Configuration Inspection

Access detailed device configuration:

```python
async with OpenDisplayDevice(mac_address="AA:BB:CC:DD:EE:FF") as device:
    # Display configuration
    display = device.config.displays[0]
    print(f"Panel IC: {display.panel_ic_type}")
    print(f"Rotation: {display.rotation}°")
    print(f"Supports ZIP: {display.supports_zip}")
    print(f"Supports Direct Write: {display.supports_direct_write}")

    # System configuration
    system = device.config.system
    print(f"IC Type: {system.ic_type_enum.name}")
    print(f"Has external power pin: {system.has_pwr_pin}")

    # Power configuration
    if device.config.power:
        power = device.config.power
        print(f"Battery: {power.battery_mah}mAh")
        print(f"Power mode: {power.power_mode_enum.name}")
```
### Advertisement Parsing

Parse real-time sensor data from BLE advertisements:

```python
from opendisplay import parse_advertisement

# Parse manufacturer data from BLE advertisement
adv_data = parse_advertisement(manufacturer_data)
print(f"Battery: {adv_data.battery_mv}mV")
print(f"Temperature: {adv_data.temperature_c}°C")
print(f"Loop counter: {adv_data.loop_counter}")
```

### Device Discovery

List all nearby OpenDisplay devices:
```python
from opendisplay import discover_devices

# Scan for 10 seconds
devices = await discover_devices(timeout=10.0)

for name, mac in devices.items():
    print(f"{name}: {mac}")

# Output:
# OpenDisplayA123: AA:BB:CC:DD:EE:FF
# OpenDisplayB456: 11:22:33:44:55:66
```

## Connection Reliability

py-opendisplay uses `bleak-retry-connector` for robust BLE connections with:
- Automatic retry logic with exponential backoff
- Connection slot management for ESP32 Bluetooth proxies
- GATT service caching for faster reconnections
- Better error categorization

### Home Assistant Integration

When using py-opendisplay in Home Assistant custom integrations, pass the `BLEDevice` object for optimal performance:

```python
from homeassistant.components import bluetooth
from opendisplay import OpenDisplayDevice

# Get BLEDevice from Home Assistant
ble_device = bluetooth.async_ble_device_from_address(hass, mac_address)

async with OpenDisplayDevice(mac_address=mac_address, ble_device=ble_device) as device:
    await device.upload_image(image)
```

### Retry Configuration

Configure retry behavior for unreliable environments:

```python
# Increase retry attempts for poor BLE conditions
async with OpenDisplayDevice(
    mac_address="AA:BB:CC:DD:EE:FF",
    max_attempts=6,  # Try up to 6 times (default: 4)
) as device:
    await device.upload_image(image)

# Disable service caching after firmware updates
async with OpenDisplayDevice(
    mac_address="AA:BB:CC:DD:EE:FF",
    use_services_cache=False,  # Force fresh service discovery
) as device:
    await device.upload_image(image)
```



## Development

```bash
uv sync --all-extras
uv run pytest
```