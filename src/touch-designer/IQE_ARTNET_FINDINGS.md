# IQE ArtNet Visualization - Key Findings

## Coordinate System Discovery
From `buildProject.js` analysis:
- **Row numbering is inverted**: Row 1 (Rafter 1) has highest X coordinate, Row 24 has lowest
- Formula: `x = (numRows - 1) - row * spaceBetweenRows`
- Strips have `yaw: -90` and run along Z axis
- Strip positions per row:
  - Strip 1: z = -1960 (leftmost)
  - Strip 2: z = -1330 (middle) 
  - Strip 3: z = -700 (rightmost)

## Current Issues

### 1. Pixel Mapping: SOLVED! 
- **Expected**: 420 pixels per row (3 strips × 140 pixels)
- **Actual**: 420 pixels per row correctly mapped!
- **Universe pattern** (repeating every 3 universes):
  - Universe N+0: 510 bytes = 170 pixels
  - Universe N+1: 510 bytes = 170 pixels
  - Universe N+2: 240 bytes = 80 pixels
  - Total: 170 + 170 + 80 = 420 pixels ✓

### 2. Visualization Orientation (FIXED)
- Applied horizontal flip + vertical flip to match LX coordinate system
- Row 1 now appears at bottom (Row 24 at top) matching physical layout
- Circle radiating from lower left in LX now correctly shows as lower left in Python
- Strip order after horizontal flip: Strip 3 (left), Strip 2 (middle), Strip 1 (right)
- Animation moving down in LX now moves down in Python visualization

## Universe Mapping
LX Studio is sending universes 1-72:
- 3 universes per row × 24 rows = 72 universes
- Linear mapping: Row 1 uses universes 1-3, Row 2 uses 4-6, etc.
- Using standard ArtNet port 6454 (not 7890)

## DMX/ArtNet Constraints
- DMX universe limit: 512 channels (170 RGB pixels max)
- LX fixture config shows DMX channels: 0, 420, 330
- These don't align with 512-channel boundaries
- Suggests complex remapping is happening

## Debug Tools Created
1. `iqe_render.py` - Main visualizer with:
   - `--spaced` mode for realistic 25'×21' geometry
   - `--shift N` for pixel alignment debugging
   - Row labels matching LX (1-24)

2. `count_pixels.py` - Counts exact non-zero pixels received

3. `debug_universe_data.py` - Analyzes universe patterns and data lengths

## Next Steps
1. Determine why only 330 pixels are lit:
   - Is LX only sending 330 pixels?
   - Are the missing 90 pixels in different universes?
   - Is there zero-padding we're not detecting?

2. Verify pixel ordering within strips (may need reversal due to yaw: -90)

3. Test with full fixture activation in LX to ensure all pixels are being sent