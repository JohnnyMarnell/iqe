#!/usr/bin/env python3
"""Debug what DMX data is actually being sent over time"""

import socket
import struct
import time
from collections import defaultdict

def debug_dmx_timing():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 6454))
    sock.settimeout(0.1)
    
    print("Monitoring ArtNet for 5 seconds...")
    print("Checking what data each universe sends")
    print("-" * 40)
    
    universe_data = defaultdict(list)
    start_time = time.time()
    
    while time.time() - start_time < 5:
        try:
            data, addr = sock.recvfrom(1024)
            
            if len(data) >= 18 and data[0:8] == b'Art-Net\x00':
                opcode = struct.unpack('<H', data[8:10])[0]
                
                if opcode == 0x5000:  # OpOutput
                    universe = struct.unpack('<H', data[14:16])[0]
                    length = struct.unpack('>H', data[16:18])[0]
                    dmx_data = data[18:18+length]
                    
                    # Record non-zero positions
                    non_zero_positions = []
                    for i, val in enumerate(dmx_data):
                        if val > 0:
                            non_zero_positions.append((i, val))
                    
                    if non_zero_positions:
                        universe_data[universe].append({
                            'time': time.time() - start_time,
                            'positions': non_zero_positions[:5]  # First 5 non-zero
                        })
                        
        except socket.timeout:
            continue
    
    # Analyze results
    print("\nResults:")
    for univ in sorted(universe_data.keys())[:5]:  # First 5 universes
        print(f"\nUniverse {univ}:")
        entries = universe_data[univ]
        if len(entries) > 3:
            # Show first few and last
            for e in entries[:2]:
                print(f"  t={e['time']:.2f}s: {e['positions']}")
            print(f"  ... ({len(entries)-4} more entries)")
            for e in entries[-2:]:
                print(f"  t={e['time']:.2f}s: {e['positions']}")
    
    sock.close()

if __name__ == "__main__":
    debug_dmx_timing()