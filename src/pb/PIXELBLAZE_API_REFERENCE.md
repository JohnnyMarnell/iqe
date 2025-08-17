# PixelBlaze API Reference

## Overview
This document covers what I've learned about the PixelBlaze API through testing and implementation.

## Discovery Protocol
- **UDP Port**: 1889
- **Beacon Format**: Device broadcasts 12+ byte packets
  - Bytes 0-5: Device ID (6 bytes hex)
  - Bytes 6-9: Flash ID (4 bytes, little-endian)
  - Byte 10: Version number
  - Byte 11+: Additional data

## Python Client Library (`pixelblaze-client`)

### Installation
```bash
pip install pixelblaze-client
```

### Basic Connection
```python
from pixelblaze import Pixelblaze
pb = Pixelblaze("192.168.0.96")  # IP address
```

## Working API Methods

### Device Information
```python
# Get device name (e.g., "johnny5")
device_name = pb.getDeviceName()

# Get hardware configuration
hw_config = pb.getHardwareConfig()
# Returns: {'pixelCount': 140, 'colorOrder': 'RGB', ...}

# Get version info
version = pb.getVersion()
# Returns: {'version': '3.30', ...}

# Get statistics
stats = pb.getStatistics()
# Returns: {'fps': 60, 'vmerr': 0, ...}
```

### Pattern Management
```python
# List all patterns
patterns = pb.getPatternList()
# Returns: {'pattern_id': 'pattern_name', ...}

# Get active pattern
active = pb.getActivePattern()
# Returns: {'activeProgramId': 'xxx', 'name': 'pattern_name'}

# Set active pattern by ID
pb.setActivePattern('pattern_id')

# Set active pattern by name
pb.setActivePatternByName('pattern_name')

# Get pattern controls/variables
controls = pb.getVars()
# Returns: {'brightness': 0.5, 'custom_var': 0.7, ...}

# Set control values
pb.setVars({'brightness': 0.8, 'speed': 0.5})
```

### File Operations
```python
# List files on device
files = pb.getFileList()

# Upload a file
pb.putFile('/path/on/device', file_bytes)

# Download a file
content = pb.getFile('/path/on/device')
```

### Pattern Compilation (Requires Native Library)
```python
# Compile pattern source to bytecode
# NOTE: Requires libmini_racer.dylib which may not be available
bytecode = pb.compilePattern(source_code)

# Save pattern (requires compiled bytecode)
pb.savePattern(
    sourceCode=source_code,
    byteCode=bytecode,
    previewImage=b''  # Optional preview image bytes
)
```

## WebSocket API
- **Port**: 81
- **Path**: `/ws`
- Provides real-time updates for:
  - Pattern variables
  - Statistics (FPS, etc.)
  - Preview data

## HTTP API Endpoints

### GET Endpoints
- `/`: Web UI
- `/api/v1/devices`: Device info
- `/api/v1/patterns`: Pattern list
- `/api/v1/patterns/active`: Currently active pattern

### POST Endpoints
- `/api/v1/patterns/active`: Set active pattern
  ```json
  {"patternId": "pattern_id_here"}
  ```

## Pattern Language

### Basic Pattern Structure
```javascript
// Export variables become UI controls
export var speed = 0.5
export var brightness = 1
export var hue = 0

// Called before each frame
export function beforeRender(delta) {
  // delta = milliseconds since last frame
  t1 = time(0.1)  // 0.1 = 10 second cycle
}

// Called for each pixel
export function render(index) {
  // index = pixel number (0 to pixelCount-1)
  hsv(hue, 1, brightness)
}
```

### Time Functions
- `time(interval)`: Returns 0-1 sawtooth wave
  - `time(0.1)` = 10 second cycle
  - `time(0.05)` = 20 second cycle
  - `time(1)` = 1 second cycle

### Color Functions
- `hsv(h, s, v)`: Set pixel color (0-1 for each channel)
- `rgb(r, g, b)`: Alternative color setting

### Math Functions
- Standard: `sin()`, `cos()`, `abs()`, `pow()`, `sqrt()`
- Constants: `PI`

## Pattern Examples

### Simple Pulse
```javascript
export function beforeRender(delta) {
  t1 = time(0.05)  // 20 second cycle
  if (t1 < 0.3) {
    brightness = t1 / 0.3  // Fade up
  } else if (t1 < 0.7) {
    brightness = 1  // Hold at max
  } else {
    brightness = (1 - t1) / 0.3  // Fade down
  }
}

export function render(index) {
  hsv(0, 1, brightness)  // Red pulse
}
```

## Common Patterns Found on Devices
Based on device scanning, these patterns are commonly available:
- **Pulse/Breathing**: "pulse", "fast pulse", "color fade pulse", "blink fade"
- **Color shifts**: "slow color shift", "rainbow melt", "color bands"
- **Effects**: "fireflies", "sparkfire", "firework", "edgeburst"
- **Motion**: "spin cycle", "KITT", "marching rainbow"
- **Audio reactive**: "sound - rays", "sound - spectrum analyser"

## Limitations & Issues

### Pattern Upload
- `compilePattern()` requires `libmini_racer.dylib` native library
- Without compilation, can't upload new patterns via API
- Workaround: Use existing patterns on device

### Method Confusion
- Some methods from docs don't exist (e.g., `getHardwareConfig` vs actual method names)
- API inconsistencies between PixelBlaze versions

### Discovery
- Multiple monitors can't bind to UDP port 1889 simultaneously
- Need to handle port conflicts gracefully

## Best Practices

1. **Always check pattern exists before setting**:
   ```python
   patterns = pb.getPatternList()
   if pattern_id in patterns:
       pb.setActivePattern(pattern_id)
   ```

2. **Use try/except for all API calls**:
   ```python
   try:
       pb.setActivePatternByName("pattern_name")
   except Exception as e:
       # Fall back to pattern ID or handle error
   ```

3. **Parallel execution for multiple devices**:
   ```python
   import concurrent.futures
   with concurrent.futures.ThreadPoolExecutor() as executor:
       futures = [executor.submit(pb.setActivePattern, pid) for pb in devices]
   ```

4. **Pattern synchronization timing**:
   - Network latency causes slight delays between devices
   - Use parallel execution to minimize timing differences
   - Consider using PixelBlaze's built-in sync features for perfect timing

## File Storage on Device
- Patterns stored as `.js` files
- Can be accessed via file API but names don't always match pattern list
- Pattern IDs are unique identifiers, not filenames

## Testing Tools Created
- `test_pb_methods.py`: Enumerate all available methods
- `pb_pulse_and_scatter.py`: Synchronize patterns across devices
- `pbfleet_enhanced.py`: Full monitoring and control web UI
- `patterns/simplePulse.js`: Basic test pattern for synchronization