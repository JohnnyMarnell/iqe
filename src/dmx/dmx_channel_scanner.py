#!/usr/bin/env python3
"""DMX channel scanner - finds which channels control your lights"""

import socket
import time
import struct
import os

def create_artnet_packet(universe, data):
    """Create an Art-Net DMX packet"""
    header = b'Art-Net\x00'
    opcode = struct.pack('<H', 0x5000)
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
    UNIVERSE = int(os.environ.get("UNIVERSE", "0"))
    
    print(f"DMX Channel Scanner")
    print(f"Controller: {CONTROLLER_IP}, Universe: {UNIVERSE}")
    print("-" * 40)
    
    channels = [0] * 512
    
    print("\n1. Single channel test (0-indexed)")
    print("2. Single channel test (1-indexed)")  
    print("3. Scan first 20 channels")
    print("4. Test 7-channel ParCan pattern")
    print("5. Test second ParCan (channels 8-14)")
    
    choice = input("\nChoice: ").strip()
    
    if choice == '1':
        # 0-indexed test
        for ch in range(0, 14):
            channels = [0] * 512
            channels[ch] = 255
            print(f"Testing channel {ch} (0-indexed) = 255, all others = 0")
            send_artnet(CONTROLLER_IP, UNIVERSE, channels)
            input("Press Enter for next channel...")
            
    elif choice == '2':
        # 1-indexed test (put value at index-1)
        for ch in range(1, 15):
            channels = [0] * 512
            channels[ch-1] = 255  # DMX channel 1 = array index 0
            print(f"Testing DMX channel {ch} (array index {ch-1}) = 255")
            send_artnet(CONTROLLER_IP, UNIVERSE, channels)
            input("Press Enter for next channel...")
            
    elif choice == '3':
        # Scan with visual feedback
        print("Each channel will flash 3 times...")
        for ch in range(20):
            print(f"\nChannel {ch}:", end='', flush=True)
            for _ in range(3):
                channels = [0] * 512
                channels[ch] = 255
                send_artnet(CONTROLLER_IP, UNIVERSE, channels)
                print(" ON", end='', flush=True)
                time.sleep(0.3)
                channels[ch] = 0
                send_artnet(CONTROLLER_IP, UNIVERSE, channels)
                print(" OFF", end='', flush=True)
                time.sleep(0.3)
                
    elif choice == '4':
        # Test standard 7-ch ParCan
        print("Testing 7-channel mode on first fixture")
        test_patterns = [
            ("Master dimmer", [255, 0, 0, 0, 0, 0, 0]),
            ("Red only", [255, 255, 0, 0, 0, 0, 0]),
            ("Green only", [255, 0, 255, 0, 0, 0, 0]),
            ("Blue only", [255, 0, 0, 255, 0, 0, 0]),
            ("White", [255, 255, 255, 255, 0, 0, 0]),
            ("All channels", [255, 255, 255, 255, 255, 255, 255])
        ]
        
        for name, pattern in test_patterns:
            channels = [0] * 512
            channels[0:7] = pattern
            print(f"{name}: {pattern}")
            send_artnet(CONTROLLER_IP, UNIVERSE, channels)
            input("Press Enter for next...")
            
    elif choice == '5':
        # Test second fixture
        print("Testing second ParCan (ch 8-14 assuming 7-ch mode)")
        channels = [0] * 512
        # Keep first light off
        channels[0:7] = [0, 0, 0, 0, 0, 0, 0]
        # Test second light
        channels[7:14] = [255, 255, 0, 0, 0, 0, 0]  # Dimmer + Red
        print(f"Second light RED: channels 8-14 = {channels[7:14]}")
        send_artnet(CONTROLLER_IP, UNIVERSE, channels)
        input("Press Enter...")
        
        channels[7:14] = [255, 0, 255, 0, 0, 0, 0]  # Dimmer + Green
        print(f"Second light GREEN: channels 8-14 = {channels[7:14]}")
        send_artnet(CONTROLLER_IP, UNIVERSE, channels)
        input("Press Enter...")
        
        channels[7:14] = [255, 0, 0, 255, 0, 0, 0]  # Dimmer + Blue
        print(f"Second light BLUE: channels 8-14 = {channels[7:14]}")
        send_artnet(CONTROLLER_IP, UNIVERSE, channels)

if __name__ == "__main__":
    main()