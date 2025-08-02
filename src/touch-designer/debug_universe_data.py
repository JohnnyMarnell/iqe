#!/usr/bin/env python3
"""Debug universe data to understand the 330 vs 420 pixel issue"""

import socket
import struct
import time
from collections import defaultdict

def analyze_universe_data(port=6454, duration=5):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    sock.settimeout(0.1)
    
    print(f"Analyzing universe data on port {port} for {duration} seconds...")
    print("Looking for patterns in universe data lengths and content...")
    print("-" * 80)
    
    universe_data = defaultdict(list)  # universe -> list of (length, non_zero_count)
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
            
            # Count non-zero bytes
            non_zero_count = sum(1 for b in dmx_data if b > 0)
            
            # Store for analysis
            universe_data[universe].append((length, non_zero_count))
                    
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Error: {e}")
    
    sock.close()
    
    # Analyze patterns
    print("\nUNIVERSE ANALYSIS:")
    print("=" * 80)
    print(f"{'Universe':>8} | {'Avg Length':>10} | {'Avg Non-Zero':>12} | {'Samples':>8}")
    print("-" * 80)
    
    # Group by rows (3 universes per row)
    row_total_pixels = defaultdict(int)
    
    for u in sorted(universe_data.keys()):
        samples = universe_data[u]
        if samples:
            avg_length = sum(s[0] for s in samples) / len(samples)
            avg_non_zero = sum(s[1] for s in samples) / len(samples)
            
            # Estimate which row this universe belongs to
            row = (u - 1) // 3
            pixels_in_universe = int(avg_non_zero / 3)  # RGB channels
            row_total_pixels[row] += pixels_in_universe
            
            print(f"{u:>8} | {avg_length:>10.1f} | {avg_non_zero:>12.1f} | {len(samples):>8}")
            
            # Show details for first few universes of each row
            if u <= 6 or u in [70, 71, 72]:
                sample = samples[0]
                print(f"         | Example: {sample[0]} bytes, {sample[1]} non-zero → ~{sample[1]//3} pixels")
    
    print("-" * 80)
    
    # Show row analysis
    print("\nROW ANALYSIS:")
    print("=" * 80)
    for row in sorted(row_total_pixels.keys())[:5]:  # First 5 rows
        print(f"Row {row+1}: ~{row_total_pixels[row]} pixels")
    
    # Check for pattern in universe sizes
    if universe_data:
        print("\nUNIVERSE SIZE PATTERN:")
        for i in range(1, min(10, max(universe_data.keys()) + 1)):
            if i in universe_data and universe_data[i]:
                length = universe_data[i][0][0]
                position = ((i - 1) % 3) + 1
                print(f"Universe {i} (position {position} in row): {length} bytes")

if __name__ == "__main__":
    analyze_universe_data()