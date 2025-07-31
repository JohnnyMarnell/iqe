#!/usr/bin/env python3
"""Debug ArtNet receiver to check what's being received"""

import socket
import struct

def debug_artnet():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 6454))
    sock.settimeout(1.0)
    
    print("Listening for ArtNet on 127.0.0.1:6454...")
    print("Expecting 60 universes with RGB data")
    print("-" * 40)
    
    universes_seen = set()
    packet_count = 0
    
    try:
        while packet_count < 100:  # Capture first 100 packets
            try:
                data, addr = sock.recvfrom(1024)
                
                # Check ArtNet header
                if len(data) >= 18 and data[0:8] == b'Art-Net\x00':
                    opcode = struct.unpack('<H', data[8:10])[0]
                    
                    if opcode == 0x5000:  # OpOutput
                        universe = struct.unpack('<H', data[14:16])[0]
                        length = struct.unpack('>H', data[16:18])[0]
                        
                        # Get first few DMX values
                        dmx_data = data[18:18+min(12, length)]
                        dmx_vals = [d for d in dmx_data]
                        
                        if universe not in universes_seen:
                            print(f"Universe {universe}: Length={length}, First values={dmx_vals}")
                            universes_seen.add(universe)
                        
                        packet_count += 1
                        
            except socket.timeout:
                continue
                
    except KeyboardInterrupt:
        pass
    
    print(f"\nReceived {packet_count} packets")
    print(f"Universes seen: {sorted(universes_seen)}")
    print(f"Total universes: {len(universes_seen)}")
    
    sock.close()

if __name__ == "__main__":
    debug_artnet()