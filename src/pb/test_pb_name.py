#!/usr/bin/env python3
"""
Test script to get PixelBlaze device name
"""

import sys
from pixelblaze import Pixelblaze
import json

if len(sys.argv) < 2:
    print("Usage: python test_pb_name.py <IP_ADDRESS>")
    print("Example: python test_pb_name.py 192.168.0.241")
    sys.exit(1)

ip = sys.argv[1]
print(f"Connecting to PixelBlaze at {ip}...")

try:
    pb = Pixelblaze(ip)
    
    # Method 1: getHardwareConfig
    print("\n1. Trying getHardwareConfig():")
    try:
        config = pb.getHardwareConfig()
        print(f"   Full config: {json.dumps(config, indent=2)}")
        print(f"   Name from config: {config.get('name', 'NOT FOUND')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Method 2: Direct WebSocket attributes
    print("\n2. Checking WebSocket attributes:")
    if hasattr(pb, 'ws'):
        ws_attrs = dir(pb.ws)
        name_attrs = [attr for attr in ws_attrs if 'name' in attr.lower()]
        print(f"   WebSocket attributes with 'name': {name_attrs}")
        
        for attr in ['name', 'deviceName', 'device_name']:
            if hasattr(pb.ws, attr):
                print(f"   ws.{attr} = {getattr(pb.ws, attr)}")
    
    # Method 3: Get all system values
    print("\n3. Trying getVars() for system info:")
    try:
        vars = pb.getVars()
        print(f"   Variables: {vars}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Method 4: Send custom command
    print("\n4. Trying custom WebSocket command:")
    try:
        if hasattr(pb, '_send_string'):
            pb._send_string('{"getConfig":true}')
            import time
            time.sleep(1)
            if hasattr(pb, 'ws') and hasattr(pb.ws, 'config'):
                print(f"   Config via custom: {pb.ws.config}")
        else:
            print("   No _send_string method")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Method 5: Check all ws attributes
    print("\n5. All WebSocket attributes:")
    if hasattr(pb, 'ws'):
        for attr in sorted(dir(pb.ws)):
            if not attr.startswith('_'):
                try:
                    val = getattr(pb.ws, attr)
                    if not callable(val):
                        print(f"   ws.{attr} = {val}")
                except:
                    pass

except Exception as e:
    print(f"Failed to connect: {e}")
    import traceback
    traceback.print_exc()