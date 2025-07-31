#!/usr/bin/env python3
"""
Simple ArtNet Receiver Test
Shows raw packet info to debug connection
"""

import socket
import struct
import time

def test_artnet_receiver(bind_ip="127.0.0.1", port=6454):
    """Simple ArtNet packet receiver for testing"""
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((bind_ip, port))
    sock.settimeout(1.0)
    
    print(f"Listening for ArtNet on {bind_ip}:{port}")
    print("Press Ctrl+C to stop\n")
    
    packet_count = 0
    universes_seen = set()
    
    try:
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                
                # Check ArtNet header
                if data[0:8] == b'Art-Net\x00':
                    opcode = struct.unpack('<H', data[8:10])[0]
                    
                    if opcode == 0x5000:  # OpOutput
                        universe = struct.unpack('<H', data[14:16])[0]
                        length = struct.unpack('>H', data[16:18])[0]
                        
                        packet_count += 1
                        universes_seen.add(universe)
                        
                        # Show first few packets in detail
                        if packet_count <= 5:
                            print(f"Packet {packet_count}: Universe {universe}, "
                                  f"Length {length}, From {addr}")
                            # Show first 10 DMX values
                            dmx_vals = list(data[18:28])
                            print(f"  First 10 channels: {dmx_vals}")
                        
                        # Then just show summary
                        elif packet_count % 100 == 0:
                            print(f"Received {packet_count} packets, "
                                  f"Universes: {sorted(universes_seen)[:5]}..."
                                  f" ({len(universes_seen)} total)")
                            
            except socket.timeout:
                if packet_count > 0 and packet_count % 60 == 0:
                    print(f"Status: {packet_count} packets, "
                          f"{len(universes_seen)} universes")
                          
    except KeyboardInterrupt:
        print(f"\n\nSummary:")
        print(f"Total packets: {packet_count}")
        print(f"Universes seen: {sorted(universes_seen)}")
        print(f"Universe count: {len(universes_seen)}")
    finally:
        sock.close()


if __name__ == "__main__":
    test_artnet_receiver()