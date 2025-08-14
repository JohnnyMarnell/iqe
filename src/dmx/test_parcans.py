#!/usr/bin/env python3
"""Simple ArtNet ParCan tester - sends RGB values to test DMX lights"""

import socket
import time
import struct

def create_artnet_packet(universe, data):
    """Create an Art-Net DMX packet"""
    # Art-Net header
    header = b'Art-Net\x00'  # Art-Net ID
    opcode = struct.pack('<H', 0x5000)  # OpOutput
    version = struct.pack('>H', 14)  # Protocol version
    sequence = b'\x00'  # Sequence (0 for no sequencing)
    physical = b'\x00'  # Physical port
    universe_bytes = struct.pack('<H', universe)  # Universe number
    length = struct.pack('>H', len(data))  # DMX data length
    
    # Pad data to 512 channels if needed
    dmx_data = data + bytes(512 - len(data))
    
    return header + opcode + version + sequence + physical + universe_bytes + length + dmx_data

def send_artnet(ip, universe, channels):
    """Send ArtNet packet to controller"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    packet = create_artnet_packet(universe, bytes(channels))
    sock.sendto(packet, (ip, 6454))  # ArtNet port is 6454
    sock.close()

def main():
    import os
    # Controller IP address - can be set via environment variable
    CONTROLLER_IP = os.environ.get("CONTROLLER_IP", "10.10.42.68")
    UNIVERSE = int(os.environ.get("UNIVERSE", "0"))  # Also allow universe override
    
    print(f"ArtNet ParCan Tester")
    print(f"Sending to: {CONTROLLER_IP}")
    print(f"Universe: {UNIVERSE}")
    print("-" * 40)
    
    # Initialize DMX channels (512 channels, all at 0)
    channels = [0] * 512
    
    while True:
        print("\nTest Options:")
        print("1. All Red")
        print("2. All Green") 
        print("3. All Blue")
        print("4. All White")
        print("5. Rainbow cycle")
        print("6. Custom RGB")
        print("7. Channel test (1-7 for 7ch mode)")
        print("0. All Off")
        print("q. Quit")
        
        choice = input("\nEnter choice: ").strip().lower()
        
        if choice == 'q':
            break
        elif choice == '0':
            channels[:7] = [0, 0, 0, 0, 0, 0, 0]
            print("Lights OFF")
        elif choice == '1':
            channels[:3] = [255, 0, 0]  # RGB mode
            print("Sending RED")
        elif choice == '2':
            channels[:3] = [0, 255, 0]
            print("Sending GREEN")
        elif choice == '3':
            channels[:3] = [0, 0, 255]
            print("Sending BLUE")
        elif choice == '4':
            channels[:3] = [255, 255, 255]
            print("Sending WHITE")
        elif choice == '5':
            print("Rainbow cycle (press Ctrl+C to stop)")
            try:
                while True:
                    for hue in range(0, 360, 5):
                        # Simple HSV to RGB conversion
                        h = hue / 60
                        c = 255
                        x = int(c * (1 - abs(h % 2 - 1)))
                        
                        if h < 1:
                            r, g, b = c, x, 0
                        elif h < 2:
                            r, g, b = x, c, 0
                        elif h < 3:
                            r, g, b = 0, c, x
                        elif h < 4:
                            r, g, b = 0, x, c
                        elif h < 5:
                            r, g, b = x, 0, c
                        else:
                            r, g, b = c, 0, x
                            
                        channels[:3] = [r, g, b]
                        send_artnet(CONTROLLER_IP, UNIVERSE, channels)
                        time.sleep(0.05)
            except KeyboardInterrupt:
                print("\nStopped rainbow")
        elif choice == '6':
            r = int(input("Red (0-255): "))
            g = int(input("Green (0-255): "))
            b = int(input("Blue (0-255): "))
            channels[:3] = [r, g, b]
            print(f"Sending RGB({r}, {g}, {b})")
        elif choice == '7':
            print("7-channel DMX mode test")
            for i in range(7):
                channels[i] = int(input(f"Channel {i+1} value (0-255): "))
            print(f"Sending channels: {channels[:7]}")
        else:
            continue
            
        send_artnet(CONTROLLER_IP, UNIVERSE, channels)

if __name__ == "__main__":
    main()