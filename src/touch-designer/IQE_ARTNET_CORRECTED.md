# IQE ArtNet Corrected Understanding

## Key Discoveries from buildProject.js

1. **Coordinate System**:
   - Strips run along Z axis (yaw: -90)
   - Row 1 has highest X value, rows decrease going down
   - Formula: `x = (numRows - 1) - row * spaceBetweenRows`
   - This means Row 1 is at top (high X), Row 24 at bottom (low X)

2. **Strip Layout per Row**:
   - Strip 1: z = -1960 (leftmost in real world)
   - Strip 2: z = -1330 (middle)
   - Strip 3: z = -700 (rightmost)
   - All strips in a row share same X coordinate

3. **Universe Mapping**:
   - Uses channels 0, 420, 330 (not aligned with 512 limit)
   - LX must be doing complex remapping to fit in universes
   - We're seeing linearized output as universes 1-72

## The Inversion Issue

The visualization appears inverted because:
- Our code assumes Row 0 = top, but in LX Row 1 (highest number) = top
- We might need to flip the row ordering
- The missing pixels might be due to how LX linearizes the complex DMX mapping

## Next Steps

1. Flip row ordering in visualization
2. Verify pixel ordering within strips (might also be reversed)
3. Debug why only 330 pixels per row are lit instead of 420