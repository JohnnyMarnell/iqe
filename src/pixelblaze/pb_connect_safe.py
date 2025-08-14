#!/usr/bin/env python3
"""
Connect to PixelBlaze WiFi WITHOUT breaking ethernet internet
"""

import subprocess
import time
import sys

def run_cmd(cmd):
    """Run command and return output"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.returncode

def check_internet():
    """Check if internet works"""
    out, code = run_cmd("ping -c 1 8.8.8.8")
    return code == 0

def get_ethernet_gateway():
    """Get ethernet gateway IP"""
    out, _ = run_cmd("netstat -rn | grep '^default.*en10' | awk '{print $2}' | head -1")
    return out

def main():
    print("PixelBlaze Safe Connect")
    print("=" * 40)
    
    # Check initial state
    if not check_internet():
        print("❌ No internet connection! Fix ethernet first.")
        sys.exit(1)
    
    print("✅ Internet working via ethernet")
    
    # Get ethernet gateway
    gateway = get_ethernet_gateway()
    if not gateway:
        print("❌ Can't find ethernet gateway")
        sys.exit(1)
    
    print(f"Ethernet gateway: {gateway}")
    
    # Turn on WiFi
    print("\nTurning on WiFi...")
    run_cmd("networksetup -setairportpower en0 on")
    time.sleep(2)
    
    # CRITICAL: Set ethernet as primary BEFORE connecting WiFi
    print("Setting network service order (ethernet first)...")
    run_cmd("networksetup -ordernetworkservices 'AX88179A' 'Wi-Fi'")
    
    # Scan for PixelBlaze
    print("\nScanning for PixelBlaze...")
    out, _ = run_cmd("system_profiler SPAirPortDataType -json 2>/dev/null | grep -o '\"_name\": \"[^\"]*\"' | grep -i pixel")
    
    if not out:
        print("❌ PixelBlaze not found. Make sure it's in AP mode.")
        sys.exit(1)
    
    # Extract SSID
    import re
    match = re.search(r'"_name": "([^"]*)"', out)
    if match:
        ssid = match.group(1)
        print(f"Found: {ssid}")
    else:
        print("❌ Could not parse PixelBlaze SSID")
        sys.exit(1)
    
    # Connect to PixelBlaze
    print(f"\nConnecting to {ssid}...")
    out, code = run_cmd(f"networksetup -setairportnetwork en0 '{ssid}'")
    
    if code != 0:
        print(f"❌ Failed to connect: {out}")
        sys.exit(1)
    
    time.sleep(3)
    
    # Force route through ethernet for internet
    print("\nFixing routes to maintain internet...")
    run_cmd(f"sudo route delete default 2>/dev/null")
    run_cmd(f"sudo route add default {gateway}")
    
    # Verify
    print("\nVerifying connections:")
    
    # Check WiFi
    out, _ = run_cmd("networksetup -getairportnetwork en0")
    print(f"WiFi: {out}")
    
    # Check internet
    if check_internet():
        print("✅ Internet still working!")
    else:
        print("⚠️  Internet broken - you may need to manually fix routes")
        print(f"Run: sudo route add default {gateway}")
    
    # Check PixelBlaze
    out, code = run_cmd("curl -s -m 2 http://192.168.4.1/ | head -c 100")
    if out:
        print(f"✅ PixelBlaze accessible at http://192.168.4.1")
    else:
        print("⚠️  Can't reach PixelBlaze web interface yet")
    
    print("\n" + "=" * 40)
    print("Connected! You should now have:")
    print("1. Internet via ethernet")
    print("2. PixelBlaze access via WiFi")
    print("\nPixelBlaze URL: http://192.168.4.1")

if __name__ == "__main__":
    main()