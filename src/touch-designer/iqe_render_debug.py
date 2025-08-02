#!/usr/bin/env python3
"""
Debug version to understand the actual ArtNet mapping
"""

import socket
import struct
import time

def debug_artnet(bind_ip="0.0.0.0", port=6454):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((bind_ip, port))
    sock.settimeout(1.0)
    
    print(f"Listening on {bind_ip}:{port}")
    print("Capturing ArtNet packets for analysis...")
    print("-" * 60)
    
    universe_data = {}
    start_time = time.time()
    
    while time.time() - start_time < 5.0:  # Capture for 5 seconds
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
            
            if universe not in universe_data:
                universe_data[universe] = {
                    'length': length,
                    'samples': [],
                    'count': 0
                }
            
            universe_data[universe]['count'] += 1
            
            # Sample first few non-zero pixels
            pixels = []
            for i in range(0, min(length, 30), 3):
                if i+2 < length:
                    r, g, b = dmx_data[i], dmx_data[i+1], dmx_data[i+2]
                    if r > 0 or g > 0 or b > 0:
                        pixels.append((i//3, r, g, b))
            
            if pixels and len(universe_data[universe]['samples']) < 3:
                universe_data[universe]['samples'].append(pixels[:5])
                
        except socket.timeout:
            continue
        except Exception as e:
            print(f"Error: {e}")
    
    sock.close()
    
    # Print analysis
    print("\nANALYSIS RESULTS:")
    print("=" * 60)
    
    for univ in sorted(universe_data.keys()):
        data = universe_data[univ]
        print(f"\nUniverse {univ}:")
        print(f"  Packets received: {data['count']}")
        print(f"  DMX data length: {data['length']} bytes ({data['length']//3} pixels)")
        
        if data['samples']:
            print("  Sample pixels (pixel_idx, R, G, B):")
            for sample in data['samples'][:1]:  # Just show first sample
                for pix in sample:
                    print(f"    Pixel {pix[0]:3d}: RGB({pix[1]:3d}, {pix[2]:3d}, {pix[3]:3d})")
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(f"Total universes detected: {len(universe_data)}")
    print(f"Universe numbers: {sorted(universe_data.keys())}")
    
    # Try to figure out the pattern
    print("\nGUESSING THE PATTERN:")
    if 0 in universe_data and 1 in universe_data:
        print("- Looks like TouchDesigner is using 0-based universe numbering")
        print("- Each universe seems to have 510 bytes (170 pixels)")
        
if __name__ == "__main__":
    debug_artnet()