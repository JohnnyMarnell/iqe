#!/usr/bin/env python3
"""
Debug script to analyze the actual ArtNet data structure
"""

import socket
import struct
import time
from collections import defaultdict

def analyze_artnet(bind_ip="0.0.0.0", port=7890, duration=10):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((bind_ip, port))
    sock.settimeout(0.1)
    
    print(f"Analyzing ArtNet on {bind_ip}:{port} for {duration} seconds...")
    print("-" * 60)
    
    universe_stats = defaultdict(lambda: {'count': 0, 'lengths': set(), 'samples': []})
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
            
            universe_stats[universe]['count'] += 1
            universe_stats[universe]['lengths'].add(length)
            
            # Sample non-zero pixels at different offsets
            if len(universe_stats[universe]['samples']) < 3:
                pixels = []
                # Check at DMX offsets 0, 330, 420 (the key offsets from LX config)
                for offset in [0, 330, 420]:
                    if offset + 6 < length:
                        r, g, b = dmx_data[offset], dmx_data[offset+1], dmx_data[offset+2]
                        pixels.append(f"DMX{offset}: RGB({r},{g},{b})")
                universe_stats[universe]['samples'].append(pixels)
                
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Error: {e}")
    
    sock.close()
    
    # Analysis
    print("\nANALYSIS RESULTS:")
    print("=" * 60)
    
    for univ in sorted(universe_stats.keys()):
        stats = universe_stats[univ]
        print(f"\nUniverse {univ}:")
        print(f"  Packets: {stats['count']}")
        print(f"  Lengths: {sorted(stats['lengths'])} bytes")
        print(f"  Sample data at key offsets:")
        for sample in stats['samples'][:1]:
            for pixel in sample:
                print(f"    {pixel}")
    
    # Try to understand the pattern
    print("\n" + "=" * 60)
    print("PATTERN ANALYSIS:")
    
    # Check if universes follow the expected pattern
    expected_pattern = [(0, 0, 1), (3, 3, 4), (6, 6, 7)]  # First 3 rows
    print(f"Universes received: {sorted(universe_stats.keys())}")
    
    # Check lengths
    print(f"\nUniverse lengths:")
    for u in sorted(universe_stats.keys()):
        lengths = sorted(universe_stats[u]['lengths'])
        print(f"  Universe {u}: {lengths[0] if lengths else 0} bytes = {lengths[0]//3 if lengths else 0} pixels")

if __name__ == "__main__":
    analyze_artnet()