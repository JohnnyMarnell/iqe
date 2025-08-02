#!/usr/bin/env python3
"""Analyze the exact universe structure from ArtNet"""

import socket
import struct
import time
from collections import defaultdict

def analyze_universes(port=7890, duration=5):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))
    sock.settimeout(0.1)
    
    print(f"Analyzing ArtNet on port {port} for {duration} seconds...")
    
    universe_info = defaultdict(lambda: {
        'lengths': set(),
        'count': 0,
        'non_zero_pixels': set()
    })
    
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
            
            universe_info[universe]['count'] += 1
            universe_info[universe]['lengths'].add(length)
            
            # Count non-zero pixels
            non_zero = 0
            for i in range(0, length, 3):
                if i+2 < length:
                    if dmx_data[i] > 0 or dmx_data[i+1] > 0 or dmx_data[i+2] > 0:
                        non_zero += 1
            universe_info[universe]['non_zero_pixels'].add(non_zero)
                
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Error: {e}")
    
    sock.close()
    
    # Analysis
    print("\nUNIVERSE ANALYSIS:")
    print("=" * 80)
    
    # Group by pattern (every 3 universes)
    for base in range(1, 73, 3):
        print(f"\nRow {(base-1)//3 + 1} universes:")
        for offset in range(3):
            u = base + offset
            if u in universe_info:
                info = universe_info[u]
                lengths = sorted(info['lengths'])
                non_zeros = sorted(info['non_zero_pixels'])
                print(f"  U{u:2d}: {lengths[0]:3d} bytes = {lengths[0]//3:3d} pixels total, "
                      f"non-zero pixels: {non_zeros}")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY:")
    
    # Pattern detection
    patterns = defaultdict(list)
    for u in sorted(universe_info.keys()):
        length = sorted(universe_info[u]['lengths'])[0]
        patterns[u % 3].append(length)
    
    for pos in [1, 2, 0]:  # Universe positions in each row
        if pos in patterns:
            unique_lengths = set(patterns[pos])
            print(f"Position {pos} (universe %3 == {pos}): {unique_lengths} bytes")

if __name__ == "__main__":
    analyze_universes()