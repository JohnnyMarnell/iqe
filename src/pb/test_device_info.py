#!/usr/bin/env python3
"""
Test all config/info methods to find where the device name is
"""

import sys
import json
from pixelblaze import Pixelblaze

if len(sys.argv) < 2:
    print("Usage: python test_device_info.py <IP_ADDRESS>")
    sys.exit(1)

ip = sys.argv[1]
print(f"Testing all info methods on PixelBlaze at {ip}...\n")

try:
    pb = Pixelblaze(ip)
    
    # Test all the get methods that might have the name
    test_methods = [
        'getDeviceName',
        'getBrandName',
        'getConfigSettings',
        'getConfigSequencer',
        'getConfigExpander',
        'getDiscovery',
        'getVersion',
        'getStatistics',
        'getPeers',
    ]
    
    results = {}
    
    for method_name in test_methods:
        if hasattr(pb, method_name):
            try:
                method = getattr(pb, method_name)
                result = method()
                results[method_name] = result
                print(f"✅ {method_name}(): {result}")
                
                # Save to file for inspection
                with open(f"pb_test_{method_name}.json", 'w') as f:
                    try:
                        json.dump({
                            'method': method_name,
                            'result': result
                        }, f, indent=2)
                    except:
                        f.write(str(result))
                        
            except Exception as e:
                print(f"❌ {method_name}(): {e}")
        else:
            print(f"⚠️  {method_name} not found")
    
    print("\n" + "="*50)
    print("SUMMARY - Where is 'johnny5'?")
    print("="*50)
    
    # Check each result for the name
    for method_name, result in results.items():
        if result and 'johnny' in str(result).lower():
            print(f"🎯 FOUND in {method_name}: {result}")
        elif isinstance(result, dict):
            for key, value in result.items():
                if 'name' in key.lower():
                    print(f"📍 {method_name} has '{key}': {value}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()