#!/usr/bin/env python3
"""
Play simplePulse pattern for 2 cycles, then scatter to random patterns
"""

import time
import random
import concurrent.futures
from pixelblaze import Pixelblaze


def pulse_and_scatter(device_ips, pulse_cycles=2, cycle_duration=20):
    """
    Sync all devices to simplePulse, wait for N cycles, then scatter
    
    Args:
        device_ips: List of IP addresses
        pulse_cycles: Number of pulse cycles to play
        cycle_duration: Duration of one pulse cycle in seconds (based on time(0.05))
    """
    
    print(f"\n🔴 Starting pulse and scatter sequence...")
    print(f"  Devices: {len(device_ips)}")
    print(f"  Pulse cycles: {pulse_cycles}")
    print(f"  Total duration: {pulse_cycles * cycle_duration} seconds")
    
    # Connect to all devices
    pb_clients = {}
    available_patterns = {}
    
    for ip in device_ips:
        try:
            pb = Pixelblaze(ip)
            pb_clients[ip] = pb
            
            device_name = pb.getDeviceName()
            patterns = pb.getPatternList()
            available_patterns[ip] = patterns
            
            print(f"  ✅ Connected to '{device_name}' at {ip}")
        except Exception as e:
            print(f"  ❌ Failed to connect to {ip}: {e}")
    
    if not pb_clients:
        print("❌ No devices connected!")
        return
    
    # Phase 1: Sync all to simplePulse
    print(f"\n🔴 Phase 1: Synchronizing all devices to 'simplePulse'...")
    
    def sync_to_simple_pulse(ip, pb):
        try:
            # Try to set by name first
            pb.setActivePatternByName("simplePulse")
            return True, "simplePulse"
        except:
            # If that fails, search for it
            try:
                patterns = available_patterns[ip]
                for pid, pname in patterns.items():
                    if isinstance(pname, str) and "simplepulse" in pname.lower():
                        pb.setActivePattern(pid)
                        return True, pname
                return False, "Pattern 'simplePulse' not found"
            except Exception as e:
                return False, str(e)
    
    # Execute sync in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(pb_clients)) as executor:
        futures = {
            executor.submit(sync_to_simple_pulse, ip, pb): ip 
            for ip, pb in pb_clients.items()
        }
        
        for future in concurrent.futures.as_completed(futures):
            ip = futures[future]
            success, result = future.result()
            if success:
                print(f"  ✅ {ip} synced to '{result}'")
            else:
                print(f"  ❌ {ip} failed: {result}")
    
    # Phase 2: Let simplePulse play for N cycles
    total_duration = pulse_cycles * cycle_duration
    print(f"\n⏱️ Phase 2: Playing pulse for {pulse_cycles} cycles ({total_duration} seconds)...")
    
    for i in range(int(total_duration)):
        time.sleep(1)
        remaining = int(total_duration) - i - 1
        if remaining > 0 and remaining % 5 == 0:  # Print every 5 seconds
            cycles_left = remaining / cycle_duration
            print(f"  {remaining} seconds ({cycles_left:.1f} cycles remaining)...")
    
    # Phase 3: Scatter to random patterns
    print(f"\n🎆 Phase 3: Scattering to random patterns...")
    
    def scatter_to_random(ip, pb):
        try:
            patterns = available_patterns[ip]
            if patterns:
                # Exclude simplePulse from random selection
                pattern_choices = {
                    pid: pname for pid, pname in patterns.items()
                    if not (isinstance(pname, str) and "simplepulse" in pname.lower())
                }
                
                if pattern_choices:
                    random_pid = random.choice(list(pattern_choices.keys()))
                    pattern_name = pattern_choices[random_pid]
                    if not isinstance(pattern_name, str):
                        pattern_name = "Unknown"
                    
                    pb.setActivePattern(random_pid)
                    return True, pattern_name
                else:
                    # All patterns are simplePulse? Just pick any
                    random_pid = random.choice(list(patterns.keys()))
                    pb.setActivePattern(random_pid)
                    return True, "Random pattern"
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
        print("Usage: python pb_pulse_and_scatter.py <IP1> [IP2] [IP3] ...")
        print("Example: python pb_pulse_and_scatter.py 192.168.0.79 192.168.0.229")
        sys.exit(1)
    
    ips = sys.argv[1:]
    
    print(f"Devices: {ips}")
    
    # Run with 2 cycles of simplePulse (40 seconds total at time(0.05))
    pulse_and_scatter(ips, pulse_cycles=2, cycle_duration=20)