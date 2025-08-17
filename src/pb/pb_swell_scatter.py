#!/usr/bin/env python3
"""
Dramatic swell and scatter for PixelBlaze fleet
Uses existing patterns instead of uploading new ones
"""

import time
import random
import concurrent.futures
from pixelblaze import Pixelblaze


def dramatic_swell_and_scatter(device_ips, duration=5):
    """
    Create a dramatic synchronized swell effect then scatter to random patterns
    
    Args:
        device_ips: List of IP addresses of PixelBlaze devices
        duration: How long to hold the swell pattern (seconds)
    """
    
    print(f"\n🎭 Starting dramatic swell and scatter sequence...")
    print(f"  Devices: {len(device_ips)}")
    print(f"  Duration: {duration} seconds")
    
    # Connect to all devices and get their pattern lists
    pb_clients = {}
    available_patterns = {}
    
    for ip in device_ips:
        try:
            pb = Pixelblaze(ip)
            pb_clients[ip] = pb
            
            # Get device name and patterns
            device_name = pb.getDeviceName()
            patterns = pb.getPatternList()
            available_patterns[ip] = patterns
            
            print(f"  ✅ Connected to '{device_name}' at {ip} ({len(patterns)} patterns)")
        except Exception as e:
            print(f"  ❌ Failed to connect to {ip}: {e}")
    
    if not pb_clients:
        print("❌ No devices connected!")
        return
    
    # Priority list for swell-like patterns
    swell_patterns = [
        'pulse', 'fast pulse', 'slow pulse',
        'color fade pulse', 'blink fade',
        'slow color shift', 'sparkfire',
        'beating heart', 'fireflies',
        'edgeburst', 'firework',
        'breathing', 'heartbeat',
        'fade', 'swell'
    ]
    
    # Find the best swell pattern available on all devices
    selected_pattern = None
    selected_pattern_id = None
    
    print("\n🔍 Finding common swell pattern...")
    
    for pattern_keyword in swell_patterns:
        found_on_all = True
        pattern_ids = {}
        
        for ip, patterns in available_patterns.items():
            found = False
            for pid, pname in patterns.items():
                if isinstance(pname, str) and pattern_keyword.lower() in pname.lower():
                    pattern_ids[ip] = (pid, pname)
                    found = True
                    break
            
            if not found:
                found_on_all = False
                break
        
        if found_on_all:
            selected_pattern = pattern_keyword
            print(f"  ✅ Found common pattern containing '{pattern_keyword}'")
            for ip, (pid, pname) in pattern_ids.items():
                print(f"     {ip}: {pname}")
            break
    
    # Fallback: use any pattern available on first device
    if not selected_pattern:
        print("  ⚠️  No common swell pattern found, using fallback")
        first_ip = list(available_patterns.keys())[0]
        first_patterns = available_patterns[first_ip]
        if first_patterns:
            # Try to find something that might work
            for pid, pname in first_patterns.items():
                if isinstance(pname, str):
                    for keyword in ['color', 'rainbow', 'slow']:
                        if keyword in pname.lower():
                            selected_pattern = pname
                            selected_pattern_id = pid
                            break
                if selected_pattern:
                    break
            
            # Last resort: just use first pattern
            if not selected_pattern:
                selected_pattern_id = list(first_patterns.keys())[0]
                selected_pattern = first_patterns[selected_pattern_id]
                if not isinstance(selected_pattern, str):
                    selected_pattern = "Pattern"
    
    # Phase 1: Sync all devices to the swell pattern
    print(f"\n🌊 Phase 1: Synchronizing all devices to swell pattern...")
    
    def sync_to_pattern(ip, pb):
        try:
            patterns = available_patterns[ip]
            
            # Find and set the pattern
            for pid, pname in patterns.items():
                if isinstance(pname, str) and selected_pattern.lower() in pname.lower():
                    pb.setActivePattern(pid)
                    return True, pname
            
            # Fallback: try setting by name
            pb.setActivePatternByName(selected_pattern)
            return True, selected_pattern
        except Exception as e:
            return False, str(e)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(pb_clients)) as executor:
        futures = {
            executor.submit(sync_to_pattern, ip, pb): ip 
            for ip, pb in pb_clients.items()
        }
        
        for future in concurrent.futures.as_completed(futures):
            ip = futures[future]
            success, result = future.result()
            if success:
                print(f"  ✅ {ip} synced to '{result}'")
            else:
                print(f"  ❌ {ip} failed: {result}")
    
    # Phase 2: Let the swell play
    print(f"\n⏱️ Phase 2: Playing swell for {duration} seconds...")
    for i in range(int(duration)):
        time.sleep(1)
        remaining = int(duration) - i - 1
        if remaining > 0:
            print(f"  {remaining}...")
    
    # Phase 3: Scatter to random patterns
    print(f"\n🎆 Phase 3: Scattering to random patterns...")
    
    def scatter_to_random(ip, pb):
        try:
            patterns = available_patterns[ip]
            if patterns:
                # Pick a random pattern
                random_pid = random.choice(list(patterns.keys()))
                pattern_name = patterns[random_pid]
                if not isinstance(pattern_name, str):
                    pattern_name = "Unknown"
                
                pb.setActivePattern(random_pid)
                return True, pattern_name
            return False, "No patterns"
        except Exception as e:
            return False, str(e)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(pb_clients)) as executor:
        futures = {
            executor.submit(scatter_to_random, ip, pb): ip 
            for ip, pb in pb_clients.items()
        }
        
        for future in concurrent.futures.as_completed(futures):
            ip = futures[future]
            success, result = future.result()
            if success:
                print(f"  ✅ {ip} → {result}")
            else:
                print(f"  ❌ {ip} failed: {result}")
    
    print(f"\n✨ Sequence complete!")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python pb_swell_scatter.py <IP1> [IP2] [IP3] ... [duration]")
        print("Example: python pb_swell_scatter.py 192.168.0.79 192.168.0.229 5")
        sys.exit(1)
    
    # Parse arguments
    ips = []
    duration = 5  # default
    
    for arg in sys.argv[1:]:
        try:
            # Check if it's a duration (number)
            duration = float(arg)
        except ValueError:
            # It's an IP address
            ips.append(arg)
    
    if not ips:
        print("Error: No IP addresses provided")
        sys.exit(1)
    
    print(f"Devices: {ips}")
    print(f"Duration: {duration} seconds")
    
    dramatic_swell_and_scatter(ips, duration)