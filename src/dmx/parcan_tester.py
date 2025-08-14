#!/usr/bin/env python3
"""
ArtNet ParCan Tester - Fixed version with correct DMX mappings
Channel mapping for 7-channel U'King ZQ01047:
1. Dimmer (master brightness)
2. Red
3. Green  
4. Blue
5. Strobe
6. Function (color modes)
7. Color Speed
"""

import socket
import time
import struct
import os

def create_artnet_packet(universe, data):
    """Create an Art-Net DMX packet"""
    header = b'Art-Net\x00'
    opcode = struct.pack('<H', 0x5000)  # OpOutput
    version = struct.pack('>H', 14)
    sequence = b'\x00'
    physical = b'\x00'
    universe_bytes = struct.pack('<H', universe)
    length = struct.pack('>H', len(data))
    dmx_data = data + bytes(512 - len(data))
    return header + opcode + version + sequence + physical + universe_bytes + length + dmx_data

def send_artnet(ip, universe, channels):
    """Send ArtNet packet"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    packet = create_artnet_packet(universe, bytes(channels))
    sock.sendto(packet, (ip, 6454))
    sock.close()

def main():
    CONTROLLER_IP = os.environ.get("CONTROLLER_IP", "10.10.42.68")
    UNIVERSE = int(os.environ.get("UNIVERSE", "1"))  # Changed default to 1
    
    print(f"ArtNet ParCan Tester (Fixed)")
    print(f"Controller: {CONTROLLER_IP}, Universe: {UNIVERSE}")
    print(f"ParCan 1: DMX 1-7, ParCan 2: DMX 8-14")
    print("-" * 40)
    
    channels = [0] * 512
    
    # Set master dimmers to full on startup and initial colors
    channels[0:7] = [255, 255, 0, 0, 0, 0, 0]   # ParCan 1: dimmer full, red
    channels[7:14] = [255, 0, 0, 255, 0, 0, 0]  # ParCan 2: dimmer full, blue
    send_artnet(CONTROLLER_IP, UNIVERSE, channels)
    print("Master dimmers set to FULL")
    print("ParCan 1: RED, ParCan 2: BLUE")
    
    while True:
        print("\nTest Options:")
        print("1. Both Red")
        print("2. Both Green")
        print("3. Both Blue")
        print("4. Both White")
        print("5. Rainbow cycle (both)")
        print("6. Light 1 only (red)")
        print("7. Light 2 only (red)")
        print("8. Alternating flash")
        print("9. Custom RGB")
        print("0. All Off")
        print("q. Quit")
        
        choice = input("\nChoice: ").strip().lower()
        
        if choice == 'q':
            break
        elif choice == '0':
            channels[:14] = [0] * 14
            print("Lights OFF")
        elif choice == '1':
            # Both lights red: dimmer + red channel
            channels[0:7] = [255, 255, 0, 0, 0, 0, 0]
            channels[7:14] = [255, 255, 0, 0, 0, 0, 0]
            print("Both lights RED")
        elif choice == '2':
            # Both lights green
            channels[0:7] = [255, 0, 255, 0, 0, 0, 0]
            channels[7:14] = [255, 0, 255, 0, 0, 0, 0]
            print("Both lights GREEN")
        elif choice == '3':
            # Both lights blue
            channels[0:7] = [255, 0, 0, 255, 0, 0, 0]
            channels[7:14] = [255, 0, 0, 255, 0, 0, 0]
            print("Both lights BLUE")
        elif choice == '4':
            # Both lights white
            channels[0:7] = [255, 255, 255, 255, 0, 0, 0]
            channels[7:14] = [255, 255, 255, 255, 0, 0, 0]
            print("Both lights WHITE")
        elif choice == '5':
            print("Rainbow (Ctrl+C to stop)")
            try:
                while True:
                    for hue in range(0, 360, 5):
                        # Simple HSV to RGB
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
                        
                        # Set both lights
                        channels[0:7] = [255, r, g, b, 0, 0, 0]
                        channels[7:14] = [255, r, g, b, 0, 0, 0]
                        send_artnet(CONTROLLER_IP, UNIVERSE, channels)
                        time.sleep(0.05)
            except KeyboardInterrupt:
                print("\nStopped")
        elif choice == '6':
            # Light 1 only
            channels[0:7] = [255, 255, 0, 0, 0, 0, 0]  # Red
            channels[7:14] = [0, 0, 0, 0, 0, 0, 0]  # Off
            print("Light 1 RED, Light 2 OFF")
        elif choice == '7':
            # Light 2 only
            channels[0:7] = [0, 0, 0, 0, 0, 0, 0]  # Off
            channels[7:14] = [255, 255, 0, 0, 0, 0, 0]  # Red
            print("Light 1 OFF, Light 2 RED")
        elif choice == '8':
            print("Alternating flash (Ctrl+C to stop)")
            try:
                while True:
                    # Light 1 on, 2 off
                    channels[0:7] = [255, 255, 255, 255, 0, 0, 0]
                    channels[7:14] = [0, 0, 0, 0, 0, 0, 0]
                    send_artnet(CONTROLLER_IP, UNIVERSE, channels)
                    time.sleep(0.3)
                    # Light 2 on, 1 off
                    channels[0:7] = [0, 0, 0, 0, 0, 0, 0]
                    channels[7:14] = [255, 255, 255, 255, 0, 0, 0]
                    send_artnet(CONTROLLER_IP, UNIVERSE, channels)
                    time.sleep(0.3)
            except KeyboardInterrupt:
                print("\nStopped")
        elif choice == '9':
            r = int(input("Red (0-255): "))
            g = int(input("Green (0-255): "))
            b = int(input("Blue (0-255): "))
            channels[0:7] = [255, r, g, b, 0, 0, 0]
            channels[7:14] = [255, r, g, b, 0, 0, 0]
            print(f"Both lights RGB({r}, {g}, {b})")
        else:
            continue
            
        send_artnet(CONTROLLER_IP, UNIVERSE, channels)

if __name__ == "__main__":
    main()