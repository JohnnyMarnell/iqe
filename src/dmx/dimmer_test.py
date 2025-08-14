#!/usr/bin/env python3
"""Test if dimmer channel needs to be sent every packet or persists"""

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
    UNIVERSE = 1
    
    print("Dimmer Persistence Test")
    print(f"Controller: {CONTROLLER_IP}, Universe: {UNIVERSE}")
    print("-" * 40)
    
    channels = [0] * 512
    
    print("\nTest 1: Send dimmer once, then only colors")
    print("Step 1: Sending dimmer=255 with RED")
    channels[0:7] = [255, 255, 0, 0, 0, 0, 0]  # Dimmer + Red
    send_artnet(CONTROLLER_IP, UNIVERSE, channels)
    input("Light should be RED. Press Enter...")
    
    print("Step 2: Sending GREEN without dimmer (dimmer=0)")
    channels[0:7] = [0, 0, 255, 0, 0, 0, 0]  # No dimmer, just green
    send_artnet(CONTROLLER_IP, UNIVERSE, channels)
    input("If light turned GREEN, dimmer persists. If OFF, dimmer needed every packet. Press Enter...")
    
    print("\nTest 2: Send dimmer separately from color")
    print("Step 1: Sending only dimmer=255, no colors")
    channels[0:7] = [255, 0, 0, 0, 0, 0, 0]  # Just dimmer
    send_artnet(CONTROLLER_IP, UNIVERSE, channels)
    input("Light should be OFF (dimmer on but no color). Press Enter...")
    
    print("Step 2: Sending only BLUE, no dimmer")
    channels[0:7] = [0, 0, 0, 255, 0, 0, 0]  # Just blue, no dimmer
    send_artnet(CONTROLLER_IP, UNIVERSE, channels)
    input("If light turned BLUE, dimmer persists. If still OFF, dimmer needed. Press Enter...")
    
    print("\nTest 3: Partial channel updates")
    print("Step 1: Full white with dimmer")
    channels[0:7] = [255, 255, 255, 255, 0, 0, 0]
    send_artnet(CONTROLLER_IP, UNIVERSE, channels)
    input("Light should be WHITE. Press Enter...")
    
    print("Step 2: Update ONLY channel 2 (red) to 0, keeping rest same")
    channels[1] = 0  # Turn off red, keep dimmer and green/blue
    send_artnet(CONTROLLER_IP, UNIVERSE, channels)
    input("Light should be CYAN (green+blue). Press Enter...")
    
    print("Step 3: Set dimmer to 0 in packet")
    channels[0] = 0  # Turn off dimmer
    send_artnet(CONTROLLER_IP, UNIVERSE, channels)
    input("Light should be OFF now. Press Enter...")
    
    print("\nConclusion:")
    print("- If lights went off when dimmer=0 was sent: Dimmer MUST be in every packet")
    print("- If lights stayed on with colors changing: Dimmer persists between packets")

if __name__ == "__main__":
    main()