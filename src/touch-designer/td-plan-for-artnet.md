# Touch Designer Node Structure for 420x24 Video to ArtNet

## Overview
This node network converts a 420x24 pixel video stream into properly mapped ArtNet universes (0-71) using a clean row-based mapping system where each row spans exactly 3 universes.

## Input Stage - Video Processing

### Video Input Chain
```
[Movie File In TOP] or [Video Device In TOP]
├── Resolution: 420x24 (critical - must match exactly)
├── Format: RGB (8-bit per channel)
└── Frame Rate: 30fps (adjust as needed)
```

### Video Conditioning
```
[Resolution TOP]
├── Width: 420
├── Height: 24  
├── Keep Aspect: OFF
├── Filter: Cubic (for clean scaling)
└── Output: Clean 420x24 RGB frames
```

### Pixel Extraction
```
[TOP to CHOP]
├── Method: RGB Separate
├── First Pixel: 0,0 (top-left)
├── Last Pixel: 419,23 (bottom-right)  
├── Output: 30,240 channels (10,080 pixels × 3 RGB)
└── Channel Names: r0c0, g0c0, b0c0, r1c0, g1c0, b1c0...
```

## Mapping Engine - Core Logic

### Lookup Table
```
[Table DAT] - "pixelMapping"
├── Load: The DAT table format from artifact above
├── Columns: PixelIndex, X, Y, Universe, RedChannel, GreenChannel, BlueChannel
├── Rows: 10,080 (one per pixel)
└── Purpose: Maps pixel coordinates to ArtNet universe/channels
```

### Pixel Address Calculator
```
[Script CHOP] - "pixelToArtNet"
```

**Python Script Content:**
```python
# Row-based mapping: 72 universes, 3 per row, 140 pixels per universe
def onCook(scriptOp):
    # Get video pixel data from TOP to CHOP
    videoChop = op('topToChop1')
    
    # Initialize 72 universes, 512 channels each
    universes = {}
    for u in range(72):
        universes[u] = [0] * 512
    
    # Process each pixel with clean row-based mapping
    for y in range(24):  # 24 rows
        for x in range(420):  # 420 pixels per row
            pixelIndex = y * 420 + x
            
            # Get RGB values from video (0.0-1.0 range)
            r_val = videoChop[f'r{pixelIndex}'][0] if f'r{pixelIndex}' in videoChop else 0
            g_val = videoChop[f'g{pixelIndex}'][0] if f'g{pixelIndex}' in videoChop else 0
            b_val = videoChop[f'b{pixelIndex}'][0] if f'b{pixelIndex}' in videoChop else 0
            
            # Calculate universe and channels (row-based mapping)
            universe = y * 3 + (x // 140)  # 3 universes per row, 140 pixels per universe
            pixel_in_universe = x % 140
            base_channel = pixel_in_universe * 3
            
            # Set DMX values (0-255)
            universes[universe][base_channel] = int(r_val * 255)
            universes[universe][base_channel + 1] = int(g_val * 255) 
            universes[universe][base_channel + 2] = int(b_val * 255)
    
    # Output channels for each universe
    scriptOp.numChans = 72 * 512  # 36,864 total channels
    
    for universe in range(72):
        for channel in range(512):
            chanIndex = universe * 512 + channel
            scriptOp.chans[chanIndex].vals = [universes[universe][channel]]
            scriptOp.chans[chanIndex].name = f'u{universe}c{channel}'
```

### Channel Splitter
```
[Select CHOP] - Create 72 instances for each universe
├── Channel Names: u0c*, u1c*, u2c*... u71c*
├── Instances: universe0, universe1, universe2... universe71
└── Purpose: Split single CHOP into per-universe streams
```

## Output Stage - ArtNet Transmission

### DMX Output Nodes (72 instances)
```
[DMX Out CHOP] - "dmxUniverse0" through "dmxUniverse71"
├── Protocol: Art-Net
├── Universe: 0-71 (one per node)
├── IP Address: Broadcast or specific controller IPs
├── Port: 6454 (standard) or alternate port if needed
├── Channels: 512 per universe (420 used, 92 unused)
└── Rate: 30Hz (match video frame rate)
```

### Hardware Split Configuration

**Side 1 Controllers (Universes 0-35)**
```
[DMX Out CHOP] - Universes 0-35
├── Output Ports: #1-12 on first controller
├── IP Range: 192.168.0.79 (or your controller IP)
├── Handles: Rows 0-11 of LED grid (12 rows × 3 universes = 36 universes)
└── Clean mapping: Each row maps to 3 consecutive universes
```

**Side 2 Controllers (Universes 36-71)**  
```
[DMX Out CHOP] - Universes 36-71
├── Output Ports: #17-28 on second controller  
├── IP Range: 192.168.0.229 (or your controller IP)
├── Handles: Rows 12-23 of LED grid (12 rows × 3 universes = 36 universes)
└── Clean split: Universe 36 starts at pixel (0,12)
```

## Advanced Configuration

### Frame Rate Synchronization
```
[Timer CHOP]
├── Rate: 30 Hz
├── Pulse: Trigger frame updates
└── Sync: All DMX outputs to same timing
```

### Brightness Control
```
[Math CHOP] - Insert before DMX outputs
├── Operation: Multiply
├── Value: 0.0-1.0 (master brightness)
└── Apply: To all RGB channels globally
```

## Error Handling & Monitoring

### Channel Validation
```
[Info DAT] - Monitor channel counts
├── Expected: 36,864 total channels (72 × 512)
├── Verify: All universes receiving data
└── Alert: Missing or malformed data
```

### Network Status
```
[Ping DAT] - Monitor controller connectivity  
├── Targets: 192.168.0.79, 192.168.0.229
├── Interval: 1 second
└── Status: Network health indicators
```

## Performance Optimization

### Memory Management
- Use 32-bit float precision for CHOP processing
- Minimize unnecessary TOP processing between frames
- Cache mapping table in memory (avoid file I/O per frame)

### Network Efficiency  
- Use targeted multicast instead of broadcast when possible
- Implement frame differencing to only send changed data
- Configure ArtNet packet sizing for optimal throughput

### Threading
- Process universe chunks in parallel if CPU allows
- Separate rendering thread from network transmission
- Buffer frames to handle network latency spikes

## Testing & Validation

### Test Patterns
```
[Pattern TOP] - Generate test content
├── Solid Colors: Verify all pixels respond
├── Gradients: Check smooth transitions
├── Checkerboard: Validate pixel accuracy
└── Row/Column sweeps: Test mapping precision
```

### Universe Monitoring
```
[DMX Monitor CHOP] - Per universe analysis
├── Channel Activity: Verify all 512 channels active
├── Data Range: Confirm 0-255 output values  
├── Frame Rate: Monitor consistent timing
└── Packet Loss: Network transmission quality
```

This node structure handles the complete pipeline from 420×24 video input through clean row-based mapping to ArtNet output across 72 universes. The row-based approach (3 universes per row, 140 pixels per universe) eliminates complex boundary calculations and provides a clean hardware split at universe 36 between the two controller sections.