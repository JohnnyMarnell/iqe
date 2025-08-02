#!/usr/bin/env python3
"""Debug pixel mapping to understand the missing pixels issue"""

# Based on the logs, let's trace through exactly what pixels are being mapped

# Pattern for each row (3 universes per row):
# U1: 240 bytes = 80 pixels
# U2: 510 bytes = 170 pixels  
# U3: 510 bytes = 170 pixels

def analyze_mapping():
    print("Analyzing pixel mapping for one row:")
    print("-" * 60)
    
    # Universe mapping from the code
    pixels_per_row = 420
    
    # First universe: 80 pixels starting at 0
    u1_start = 0
    u1_pixels = 80
    u1_end = u1_start + u1_pixels - 1
    print(f"Universe 1: pixels {u1_start}-{u1_end} ({u1_pixels} pixels)")
    
    # Second universe: 170 pixels starting at 80
    u2_start = 80
    u2_pixels = 170
    u2_end = u2_start + u2_pixels - 1
    print(f"Universe 2: pixels {u2_start}-{u2_end} ({u2_pixels} pixels)")
    
    # Third universe: 170 pixels starting at 250
    u3_start = 250
    u3_pixels = 170
    u3_end = u3_start + u3_pixels - 1
    print(f"Universe 3: pixels {u3_start}-{u3_end} ({u3_pixels} pixels)")
    
    print("-" * 60)
    print(f"Total pixels covered: {u1_pixels + u2_pixels + u3_pixels}")
    print(f"Expected pixels: {pixels_per_row}")
    
    # Check for gaps or overlaps
    if u2_start != u1_end + 1:
        print(f"GAP between U1 and U2: pixels {u1_end + 1} to {u2_start - 1}")
    
    if u3_start != u2_end + 1:
        print(f"GAP between U2 and U3: pixels {u2_end + 1} to {u3_start - 1}")
        
    if u3_end >= pixels_per_row:
        print(f"OVERFLOW: U3 ends at pixel {u3_end}, but row only has {pixels_per_row} pixels (0-{pixels_per_row-1})")
    
    # Visual representation
    print("\nVisual pixel coverage (. = uncovered, # = covered):")
    coverage = ['.'] * pixels_per_row
    
    for i in range(u1_start, min(u1_end + 1, pixels_per_row)):
        coverage[i] = '1'
    for i in range(u2_start, min(u2_end + 1, pixels_per_row)):
        coverage[i] = '2'
    for i in range(u3_start, min(u3_end + 1, pixels_per_row)):
        coverage[i] = '3'
    
    # Print in chunks of 20
    for i in range(0, pixels_per_row, 20):
        chunk = ''.join(coverage[i:i+20])
        print(f"{i:3d}: {chunk}")
    
    # Count coverage
    covered = sum(1 for c in coverage if c != '.')
    print(f"\nPixels covered: {covered}/{pixels_per_row}")
    
    # Show what's missing
    missing_ranges = []
    start = None
    for i, c in enumerate(coverage):
        if c == '.':
            if start is None:
                start = i
        else:
            if start is not None:
                missing_ranges.append((start, i-1))
                start = None
    if start is not None:
        missing_ranges.append((start, pixels_per_row-1))
    
    if missing_ranges:
        print(f"\nMissing pixel ranges:")
        for start, end in missing_ranges:
            print(f"  Pixels {start}-{end} ({end-start+1} pixels)")

if __name__ == "__main__":
    analyze_mapping()