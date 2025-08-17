#!/usr/bin/env python3
"""
Test what methods are actually available in pixelblaze-client
"""

import sys
from pixelblaze import Pixelblaze

if len(sys.argv) < 2:
    print("Usage: python test_pb_methods.py <IP_ADDRESS>")
    sys.exit(1)

ip = sys.argv[1]
print(f"Connecting to PixelBlaze at {ip}...")

try:
    pb = Pixelblaze(ip)
    
    # List all methods
    print("\nAvailable methods on Pixelblaze object:")
    for attr in dir(pb):
        if not attr.startswith('_'):
            obj = getattr(pb, attr)
            if callable(obj):
                print(f"  - pb.{attr}()")
    
    # Check for config-related methods
    print("\nTrying config-related methods:")
    
    # These are the actual methods in pixelblaze-client
    config_methods = [
        'getConfig',
        'getSysConfig', 
        'getSettings',
        'controlExists',
        'variableExists',
        'getColorOrder',
        'getPixelCount',
        'getBrightnessLimit',
        'getCpuSpeed',
        'getNetworkPowerSave',
        'getLearningUiMode'
    ]
    
    for method_name in config_methods:
        if hasattr(pb, method_name):
            try:
                result = getattr(pb, method_name)()
                print(f"  pb.{method_name}() = {result}")
            except Exception as e:
                print(f"  pb.{method_name}() - Error: {e}")
    
    # Check WebSocket attributes
    print("\nWebSocket attributes:")
    if hasattr(pb, 'ws'):
        attrs = ['name', 'ver', 'fps', 'exp', 'pixelCount', 'ledType', 'dataSpeed', 
                 'colorOrder', 'brightness', 'maxBrightness', 'masterBrightness']
        for attr in attrs:
            if hasattr(pb.ws, attr):
                print(f"  ws.{attr} = {getattr(pb.ws, attr)}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()