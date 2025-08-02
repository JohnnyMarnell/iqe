#!/usr/bin/env python3
"""Count exactly how many non-zero pixels we're receiving"""

import socket
import struct
import time
from collections import defaultdict
import numpy as np

def count_artnet_pixels(port=7890, duration=10):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    sock.settimeout(0.1)
    
    print(f"Counting pixels on port {port} for {duration} seconds...")
    
    # Track pixels by universe
    universe_pixels = defaultdict(lambda: set())  # universe -> set of non-zero pixel indices
    packet_count = 0
    
    start_time = time.time()
    
    while time.time() - start_time < duration:
        try:
            data, addr = sock.recvfrom(1024)
            
            if len(data) < 18 or data[0:8] != b'Art-Net\x00':
                continue
                
            opcode = struct.unpack('<H', data[8:10])[0]
            if opcode != 0x5000:  # OpOutput
                continue
                
            universe = struct.unpack('<H', data[14:16])[0]
            length = struct.unpack('>H', data[16:18])[0]
            dmx_data = data[18:18+length]
            
            packet_count += 1
            
            # Check each pixel in this universe
            for i in range(0, length, 3):
                if i+2 < length:
                    r, g, b = dmx_data[i], dmx_data[i+1], dmx_data[i+2]
                    if r > 0 or g > 0 or b > 0:
                        pixel_idx = i // 3
                        universe_pixels[universe].add(pixel_idx)
                        
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Error: {e}")
    
    sock.close()
    
    # Analysis
    print(f"\nReceived {packet_count} packets")
    print("\nPIXEL COUNT BY UNIVERSE:")
    print("=" * 60)
    
    total_pixels = 0
    for u in sorted(universe_pixels.keys()):
        pixels = len(universe_pixels[u])
        total_pixels += pixels
        print(f"Universe {u:2d}: {pixels:3d} non-zero pixels")
    
    print("=" * 60)
    print(f"TOTAL NON-ZERO PIXELS: {total_pixels}")
    
    # Expected vs actual
    expected_total = 10080  # 24 rows * 420 pixels
    expected_per_row = 420
    actual_per_row = total_pixels / 24 if total_pixels > 0 else 0
    
    print(f"\nEXPECTED: {expected_total} pixels (24 rows × 420 pixels)")
    print(f"ACTUAL:   {total_pixels} pixels")
    print(f"MISSING:  {expected_total - total_pixels} pixels")
    print(f"\nPer row: {actual_per_row:.1f} pixels (expected {expected_per_row})")
    
    # Check pattern
    if len(universe_pixels) >= 6:
        # Check first two rows
        row1_pixels = sum(len(universe_pixels[u]) for u in [1, 2, 3])
        row2_pixels = sum(len(universe_pixels[u]) for u in [4, 5, 6])
        print(f"\nRow 1 (U1-3):  {row1_pixels} pixels")
        print(f"Row 2 (U4-6):  {row2_pixels} pixels")

if __name__ == "__main__":
    count_artnet_pixels()