#!/usr/bin/env python3
"""Test getConfigSequencer on live devices"""

from pixelblaze import Pixelblaze
import json

# Test on your device
device_ip = "192.168.0.96"

try:
    pb = Pixelblaze(device_ip)
    
    print(f"Testing device at {device_ip}")
    print("=" * 50)
    
    # Get sequencer config
    sequencer = pb.getConfigSequencer()
    print("\ngetConfigSequencer() result:")
    print(json.dumps(sequencer, indent=2))
    
    if sequencer and 'activeProgram' in sequencer:
        active = sequencer['activeProgram']
        print(f"\nCurrent pattern: {active.get('name', 'UNKNOWN')}")
        print(f"Pattern ID: {active.get('activeProgramId', 'UNKNOWN')}")
    else:
        print("\nNo activeProgram in sequencer data")
        
    # Also try getActivePattern for comparison
    print("\n" + "=" * 50)
    print("For comparison, getActivePattern() result:")
    active2 = pb.getActivePattern()
    print(json.dumps(active2, indent=2))
    
except Exception as e:
    print(f"Error: {e}")