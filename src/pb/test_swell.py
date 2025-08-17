#!/usr/bin/env python3
"""
Test the dramatic swell and scatter effect
"""

import sys
import requests
import time

# Default to localhost
host = sys.argv[1] if len(sys.argv) > 1 else "localhost"
port = sys.argv[2] if len(sys.argv) > 2 else "8000"

url = f"http://{host}:{port}/api/swell-and-scatter"

print("🎆 Triggering Dramatic Swell & Scatter Effect")
print(f"   URL: {url}")
print(f"   Duration: 5 seconds")
print(f"   Color: Random")
print("-" * 40)

try:
    response = requests.post(url, json={
        "duration": 5.0,
        "hue": None  # Random color
    })
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✅ Swell started successfully!")
            print(f"   Color hue: {data.get('color_hue', 'Unknown')}")
            print(f"   Devices: {len(data.get('swell_results', []))}")
            
            print("\n⏳ Waiting for effect to complete...")
            time.sleep(6)
            
            print("\n🎲 Scatter results:")
            for result in data.get('scatter_results', []):
                if result['success']:
                    print(f"   ✅ {result['device_id']} → {result.get('pattern', 'Unknown')}")
                else:
                    print(f"   ❌ {result['device_id']} failed")
        else:
            print(f"❌ Failed: {data.get('error', 'Unknown error')}")
    else:
        print(f"❌ HTTP Error {response.status_code}")
        print(response.text)

except requests.exceptions.ConnectionError:
    print(f"❌ Could not connect to {url}")
    print("   Make sure pbfleet_enhanced.py is running")
except Exception as e:
    print(f"❌ Error: {e}")