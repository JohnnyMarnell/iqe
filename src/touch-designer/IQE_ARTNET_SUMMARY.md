# IQE ArtNet LED Visualizer - Summary

## Current Status
Created `iqe_render.py` that visualizes 420x24 LED grid from ArtNet packets.

### What's Working
- Receiving 72 universes (1-72) on port 7890 from LX Studio
- Displaying 330 pixels per row (7,920 total) instead of expected 420 per row (10,080 total)
- Spaced mode (`--spaced`) shows realistic 25'x21' geometry with proper spacing
- Shift mode (`--shift N`) allows pixel shifting for debugging

### The Issue
- Only seeing 330 lit pixels per row instead of 420
- Missing 90 pixels per row (seems to be rightmost portion)
- Pattern per row: 80 + 170 + 80 = 330 pixels across 3 universes

### Universe Mapping Pattern
```
Each row uses 3 universes:
- Universe N+0: 240 bytes (80 pixels)
- Universe N+1: 510 bytes (170 pixels) 
- Universe N+2: 240 bytes (80 non-zero pixels, but 510 bytes sent)
```

### Usage
```bash
# Basic view
python iqe_render.py

# Realistic spacing (25' x 21' aspect ratio)
python iqe_render.py --spaced

# Shift pixels (for debugging alignment)
python iqe_render.py --shift 90
```

### Key Files
- `iqe_render.py` - Main visualizer
- `iqe2024.lxp` - LX Studio project (fixtures use universes 1,1,2 then 4,4,5 etc)
- `PixLite E16-S Mk3-In Queso Emergency.conf` - Controller config

### Next Steps
1. Analyze tshark capture to understand exact universe structure
2. Figure out why third universe only has 80 non-zero pixels
3. Determine if missing 90 pixels are in different universes or zero-padded

### Theory
DMX universe limit (512 channels = 170 pixels max) is causing complex mapping:
- Strip 1 (140 pixels): Fits in one universe
- Strip 2 (140 pixels): Might span universes 
- Strip 3 (140 pixels): Might be partially sent or zero-padded

The fixture config shows DMX channels 0, 420, 330 which don't align with 512-channel universe boundaries, suggesting LX may be doing complex remapping.