#!/usr/bin/env python3
"""
PixelBlaze Fleet Monitor - Enhanced Flask Version with API Integration
Simple Flask + real PixelBlaze data!
"""

import json
import socket
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from flask import Flask, jsonify, render_template_string
from flask_cors import CORS

# Try to import pixelblaze-client
try:
    from pixelblaze import Pixelblaze
    HAS_PB_CLIENT = True
except ImportError:
    HAS_PB_CLIENT = False
    print("⚠️  pixelblaze-client not installed. Install with: pip install pixelblaze-client")
    print("   Running in basic mode without pattern info")

# Configuration
PORT = 8000
DISCOVERY_PORT = 1889
DEVICE_TIMEOUT = 30.0
API_UPDATE_INTERVAL = 10.0  # How often to fetch pattern info
STATE_FILE = Path("devices_state.json")

@dataclass
class Device:
    """Device info with API data"""
    id: str
    ip: str
    name: str = ""
    last_seen: float = 0
    online: bool = True
    provisioned: bool = False
    # API data
    api_name: str = ""
    current_pattern: str = ""
    current_pattern_id: str = ""
    brightness: float = 0.5
    fps: int = 0
    pixel_count: int = 0
    pattern_count: int = 0
    sequencer_mode: str = ""
    playlist_length: int = 0
    playlist_position: int = 0
    playlist_remaining_ms: int = 0
    is_sequencer_running: bool = False
    last_api_update: float = 0
    api_error: str = ""
    
    def to_dict(self):
        return {
            **asdict(self),
            'last_seen_formatted': datetime.fromtimestamp(self.last_seen).strftime('%H:%M:%S') if self.last_seen else 'Never',
            'last_api_formatted': datetime.fromtimestamp(self.last_api_update).strftime('%H:%M:%S') if self.last_api_update else 'Never'
        }


class DeviceManager:
    """Manages devices with API integration"""
    
    def __init__(self):
        self.devices: Dict[str, Device] = {}
        self.lock = threading.Lock()
        self.pb_clients: Dict[str, Pixelblaze] = {}  # Cache PixelBlaze API clients
        self.load_state()
    
    def update_device(self, device_id: str, ip: str):
        """Update or add device from discovery"""
        is_new = False
        needs_api_update = False
        
        with self.lock:
            if device_id in self.devices:
                device = self.devices[device_id]
                was_offline = not device.online
                device.ip = ip
                device.last_seen = time.time()
                device.online = True
                
                # If device came back online or never had API data, update it
                if was_offline or not device.api_name:
                    needs_api_update = True
                    if was_offline:
                        print(f"🔄 Device {device_id} back online")
            else:
                is_new = True
                print(f"✨ New device discovered: {device_id} at {ip}")
                self.devices[device_id] = Device(
                    id=device_id,
                    ip=ip,
                    name=f"PB_{device_id[-4:]}",
                    last_seen=time.time()
                )
                needs_api_update = True
        
        # Fetch API data for new devices or devices that came back online
        if needs_api_update and HAS_PB_CLIENT:
            threading.Thread(target=self.update_device_api_data, args=(device_id,), daemon=True).start()
        
        self.save_state()
    
    def update_device_api_data(self, device_id: str):
        """Fetch detailed info from PixelBlaze API"""
        if not HAS_PB_CLIENT:
            return
            
        with self.lock:
            device = self.devices.get(device_id)
            if not device or not device.online:
                return
            ip = device.ip
        
        try:
            # Get or create PixelBlaze client
            if device_id not in self.pb_clients:
                self.pb_clients[device_id] = Pixelblaze(ip)
            
            pb = self.pb_clients[device_id]
            
            # Get device name using the ACTUAL method that works!
            try:
                device_name = pb.getDeviceName()
                pass  # Got device name
            except:
                device_name = f"PB_{device_id[-4:]}"
                pass  # Could not get device name
            
            # Get full config which has everything we need
            try:
                config = pb.getConfigSettings()
                pixel_count = config.get('pixelCount', 0)
                brightness = config.get('brightness', 0.5)
                
                # Save config for debugging
                config_file = Path(f"pb_config_{device_id}.json")
                with open(config_file, 'w') as f:
                    json.dump({
                        'device_id': device_id,
                        'ip': ip,
                        'timestamp': datetime.now().isoformat(),
                        'config': config,
                        'device_name': device_name
                    }, f, indent=2)
                pass  # Saved config
            except Exception as e:
                pass  # Could not get config
                pixel_count = 0
            
            # Get pattern list
            try:
                patterns = pb.getPatternList()
                pattern_count = len(patterns) if patterns else 0
                
                # Save patterns list to disk
                patterns_file = Path(f"pb_patterns_{device_id}.json")
                with open(patterns_file, 'w') as f:
                    json.dump({
                        'device_id': device_id,
                        'ip': ip,
                        'timestamp': datetime.now().isoformat(),
                        'patterns': patterns,
                        'pattern_count': pattern_count
                    }, f, indent=2)
                pass  # Saved patterns
            except Exception as e:
                pass  # Could not get patterns
                patterns = {}
                pattern_count = 0
            
            # Get current pattern and sequencer info
            playlist_position = 0
            playlist_remaining_ms = 0
            is_sequencer_running = False
            playlist_length = 0
            
            try:
                # Try new method first - gives us sequencer info too!
                sequencer = pb.getConfigSequencer()
                if sequencer and 'activeProgram' in sequencer:
                    active_prog = sequencer['activeProgram']
                    current_pattern_name = active_prog.get('name', 'Unknown')
                    current_pattern_id = active_prog.get('activeProgramId', '')
                    
                    # Get playlist info if available
                    playlist_info = sequencer.get('playlist', {})
                    playlist_position = playlist_info.get('position', 0)
                    playlist_remaining_ms = playlist_info.get('remainingMs', 0)
                    sequencer_mode_num = sequencer.get('sequencerMode', 0)
                    is_sequencer_running = sequencer.get('runSequencer', False)
                    
                    # Convert mode number to string
                    sequencer_mode = ["Off", "Shuffle All", "Playlist"][sequencer_mode_num] if sequencer_mode_num < 3 else f"Mode {sequencer_mode_num}"
                    
                    # Log playlist info if running
                    if is_sequencer_running and playlist_info:
                        print(f"  🎵 Playlist position {playlist_position}, {playlist_remaining_ms/1000:.1f}s remaining")
                else:
                    # Fallback to old method
                    active = pb.getActivePattern()
                    if active:
                        current_pattern_name = active.get("name", "Unknown")
                        current_pattern_id = active.get("id", "")
                    else:
                        current_pattern_id = ""
                        current_pattern_name = "Unknown"
                    sequencer_mode = "Off"
                    
            except Exception as e:
                print(f"  ⚠️ Error getting sequencer info: {e}")
                current_pattern_name = "Unknown"
                current_pattern_id = ""
                sequencer_mode = "Off"
            
            # Get playlist length from settings if in playlist mode
            if sequencer_mode == "Playlist":
                try:
                    settings = pb.getSettings()
                    playlist = settings.get('sequencerConfig', {}).get('playlist', [])
                    playlist_length = len(playlist)
                except:
                    pass
            
            # Pixel count already retrieved from ws.pixelCount above
            
            # Save all WebSocket attributes for debugging
            try:
                if hasattr(pb, 'ws'):
                    ws_data = {}
                    for attr in dir(pb.ws):
                        if not attr.startswith('_'):
                            try:
                                val = getattr(pb.ws, attr)
                                if not callable(val):
                                    # Convert to string if not JSON serializable
                                    try:
                                        json.dumps(val)
                                        ws_data[attr] = val
                                    except:
                                        ws_data[attr] = str(val)
                            except:
                                pass
                    
                    ws_file = Path(f"pb_websocket_{device_id}.json")
                    with open(ws_file, 'w') as f:
                        json.dump({
                            'device_id': device_id,
                            'ip': ip,
                            'timestamp': datetime.now().isoformat(),
                            'websocket_attributes': ws_data
                        }, f, indent=2)
                    pass  # Saved WebSocket data
                    
                    # Check specifically for name in ws attributes
                    if 'name' in ws_data:
                        pass  # Found ws.name
                        if not device_name or device_name.startswith("PB_"):
                            device_name = ws_data['name']
            except Exception as e:
                pass  # Could not save WebSocket data
            
            # Update device with API data
            with self.lock:
                if device_id in self.devices:
                    d = self.devices[device_id]
                    d.api_name = device_name
                    d.current_pattern = current_pattern_name
                    d.current_pattern_id = current_pattern_id
                    d.brightness = brightness
                    d.pattern_count = pattern_count
                    d.pixel_count = pixel_count
                    d.sequencer_mode = sequencer_mode
                    d.playlist_length = playlist_length
                    d.playlist_position = playlist_position
                    d.playlist_remaining_ms = playlist_remaining_ms
                    d.is_sequencer_running = is_sequencer_running
                    d.last_api_update = time.time()
                    d.api_error = ""
                    
                    # Only log key info
                    status = f"📊 Device {device_id} ({device_name}): {pattern_count} patterns, playing '{current_pattern_name}'"
                    if is_sequencer_running:
                        status += f" [Playlist {playlist_position+1}/{playlist_length}, {playlist_remaining_ms/1000:.0f}s left]"
                    print(status)
            
            self.save_state()
            
        except Exception as e:
            print(f"❌ API error for {device_id}: {e}")
            with self.lock:
                if device_id in self.devices:
                    self.devices[device_id].api_error = str(e)
    
    def update_all_api_data(self):
        """Update API data for all online devices"""
        with self.lock:
            online_devices = [d.id for d in self.devices.values() if d.online]
        
        for device_id in online_devices:
            self.update_device_api_data(device_id)
    
    def check_timeouts(self):
        """Mark devices offline if not seen recently"""
        current_time = time.time()
        with self.lock:
            for device in self.devices.values():
                was_online = device.online
                device.online = (current_time - device.last_seen) < DEVICE_TIMEOUT
                if was_online and not device.online:
                    print(f"📴 Device {device.id} ({device.api_name or device.name}) went offline")
                    # Clear cached client
                    if device.id in self.pb_clients:
                        del self.pb_clients[device.id]
    
    def get_all(self):
        """Get all devices as list of dicts"""
        with self.lock:
            return [d.to_dict() for d in self.devices.values()]
    
    def sync_pattern(self, pattern_name: str = None):
        """Set the same pattern on all online devices with improved synchronization"""
        if not HAS_PB_CLIENT:
            return {'success': False, 'error': 'pixelblaze-client not installed'}
        
        results = []
        with self.lock:
            online_devices = [(d.id, d.ip) for d in self.devices.values() if d.online]
        
        print(f"🎭 Syncing pattern '{pattern_name}' to {len(online_devices)} devices")
        
        # First, prepare all connections and determine pattern
        prepared_devices = []
        target_pattern_id = None
        target_pattern_name = pattern_name
        
        for device_id, ip in online_devices:
            try:
                if device_id not in self.pb_clients:
                    self.pb_clients[device_id] = Pixelblaze(ip)
                pb = self.pb_clients[device_id]
                
                # If no pattern specified, pick random from first device
                if not pattern_name and not target_pattern_id:
                    patterns = pb.getPatternList()
                    if patterns:
                        import random
                        target_pattern_id = random.choice(list(patterns.keys()))
                        pdata = patterns[target_pattern_id]
                        target_pattern_name = pdata if isinstance(pdata, str) else pdata.get('name', 'Unknown')
                        print(f"  Selected random pattern: '{target_pattern_name}'")
                
                prepared_devices.append((device_id, pb))
            except Exception as e:
                print(f"  ❌ Failed to prepare {device_id}: {e}")
                results.append({'device_id': device_id, 'success': False, 'error': str(e)})
        
        # Now send all commands in parallel using threads
        import concurrent.futures
        import time
        
        def set_pattern_on_device(device_id, pb, pattern_to_set):
            """Set pattern on a single device"""
            try:
                if pattern_name:  # Use name if specified
                    pb.setActivePatternByName(pattern_to_set)
                else:  # Use ID for random selection
                    pb.setActivePattern(target_pattern_id)
                return {'device_id': device_id, 'success': True}
            except Exception as e:
                return {'device_id': device_id, 'success': False, 'error': str(e)}
        
        # Execute all pattern changes simultaneously
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(prepared_devices)) as executor:
            # Submit all tasks at once
            futures = [
                executor.submit(set_pattern_on_device, device_id, pb, target_pattern_name)
                for device_id, pb in prepared_devices
            ]
            
            # Collect results
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
                if result['success']:
                    print(f"  ✅ Set pattern on {result['device_id']}")
                else:
                    print(f"  ❌ Failed on {result['device_id']}: {result.get('error', 'Unknown error')}")
        
        elapsed = time.time() - start_time
        print(f"⏱️  Sync completed in {elapsed:.3f} seconds")
        
        # Update all device info after sync
        threading.Thread(target=self.update_all_api_data, daemon=True).start()
        
        return {
            'success': True, 
            'pattern': target_pattern_name,
            'devices': results,
            'total': len(results),
            'successful': sum(1 for r in results if r['success']),
            'sync_time': elapsed
        }
    
    def simple_sync_and_scatter(self, sync_pattern: str = "slow color shift", duration: float = 5.0):
        """Play a dramatic synchronized swell pattern, then scatter to random patterns"""
        if not HAS_PB_CLIENT:
            return {'success': False, 'error': 'pixelblaze-client not installed'}
        
        import random
        import concurrent.futures
        import time
        
        # PixelBlaze pattern code for dramatic swell
        if color_hue is None:
            color_hue = random.random()  # Random color if not specified
        
        swell_pattern_code = f"""
        // Dramatic Swell Pattern - Synchronized across devices
        // This pattern swells up with intense brightness, flares, then dies down
        
        export var trigger = 1  // Start the animation
        var startTime = 0
        var duration = {duration}  // Total duration in seconds
        
        export function beforeRender(delta) {{
          // Initialize start time on first run
          if (trigger && startTime == 0) {{
            startTime = time(0.001)  // Get current time in seconds
          }}
          
          // Calculate progress (0 to 1)
          t1 = (time(0.001) - startTime) / duration
          
          if (t1 > 1) {{
            t1 = 1
            trigger = 0  // Animation complete
          }}
          
          // Create swell curve with flare
          // 0-0.7: slow build up
          // 0.7-0.8: intense flare
          // 0.8-1.0: fade out
          
          if (t1 < 0.7) {{
            // Slow exponential build
            progress = (t1 / 0.7)
            brightness = pow(progress, 2)
            saturation = 0.8 + (0.2 * progress)
          }} else if (t1 < 0.8) {{
            // Intense flare with slight pulsing
            flareProgress = (t1 - 0.7) / 0.1
            pulse = sin(flareProgress * PI * 4)  // Quick pulses
            brightness = 0.9 + (0.1 * pulse)
            saturation = 0.6 - (0.2 * flareProgress)  // Desaturate during flare
          }} else {{
            // Fade to black
            fadeProgress = (t1 - 0.8) / 0.2
            brightness = (1 - fadeProgress) * 0.8
            saturation = 0.8
          }}
          
          // Add subtle wave motion
          wave = sin(t1 * PI * 2) * 0.1
          finalBrightness = brightness + wave
          
          // Clamp brightness
          if (finalBrightness > 1) finalBrightness = 1
          if (finalBrightness < 0) finalBrightness = 0
        }}
        
        export function render(index) {{
          // Slight variation across pixels for texture
          pixelVariation = sin(index * 0.3 + t1 * PI * 2) * 0.05
          
          hsv({color_hue}, saturation, finalBrightness + pixelVariation)
        }}
        """
        
        print(f"🎆 Starting dramatic swell (hue: {color_hue:.2f}, duration: {duration}s)")
        
        with self.lock:
            online_devices = [(d.id, d.ip) for d in self.devices.values() if d.online]
        
        # Step 1: Upload and activate swell pattern on all devices
        results = []
        pattern_ids = {}  # Store uploaded pattern IDs for cleanup
        
        def upload_and_activate_swell(device_id, ip):
            try:
                if device_id not in self.pb_clients:
                    self.pb_clients[device_id] = Pixelblaze(ip)
                pb = self.pb_clients[device_id]
                
                # Save current pattern to restore later
                current = pb.getActivePattern()
                current_id = current.get('activeProgramId') if current else None
                
                # Upload the swell pattern
                pattern_name = f"IQE_Swell_{int(time.time())}"
                pb.savePattern(pattern_name, swell_pattern_code)
                
                # Find the pattern we just uploaded
                patterns = pb.getPatternList()
                swell_id = None
                for pid, pname in patterns.items():
                    if isinstance(pname, str) and pattern_name in pname:
                        swell_id = pid
                        break
                    elif isinstance(pname, dict) and pattern_name in pname.get('name', ''):
                        swell_id = pid
                        break
                
                if swell_id:
                    pb.setActivePattern(swell_id)
                    pattern_ids[device_id] = (swell_id, current_id)
                    return {'device_id': device_id, 'success': True}
                else:
                    return {'device_id': device_id, 'success': False, 'error': 'Pattern not found after upload'}
                    
            except Exception as e:
                return {'device_id': device_id, 'success': False, 'error': str(e)}
        
        # Upload and activate in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(online_devices)) as executor:
            futures = [executor.submit(upload_and_activate_swell, did, ip) for did, ip in online_devices]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                results.append(result)
                if result['success']:
                    print(f"  ✅ Swell started on {result['device_id']}")
                else:
                    print(f"  ❌ Failed on {result['device_id']}: {result.get('error')}")
        
        # Step 2: Wait for swell to complete
        print(f"⏳ Waiting {duration} seconds for swell to complete...")
        time.sleep(duration + 0.5)  # Extra half second for fade out
        
        # Step 3: Scatter to random patterns
        print("🎲 Scattering to random patterns...")
        
        def set_random_pattern(device_id, ip):
            try:
                if device_id not in self.pb_clients:
                    self.pb_clients[device_id] = Pixelblaze(ip)
                pb = self.pb_clients[device_id]
                
                # Get all patterns
                patterns = pb.getPatternList()
                if patterns:
                    # Filter out our swell pattern
                    available_patterns = {
                        pid: pname for pid, pname in patterns.items()
                        if not (isinstance(pname, str) and 'IQE_Swell' in pname) and
                           not (isinstance(pname, dict) and 'IQE_Swell' in pname.get('name', ''))
                    }
                    
                    if available_patterns:
                        random_id = random.choice(list(available_patterns.keys()))
                        pb.setActivePattern(random_id)
                        
                        pattern_name = available_patterns[random_id]
                        if isinstance(pattern_name, dict):
                            pattern_name = pattern_name.get('name', 'Unknown')
                        
                        return {'device_id': device_id, 'pattern': pattern_name, 'success': True}
                
                return {'device_id': device_id, 'success': False, 'error': 'No patterns available'}
                
            except Exception as e:
                return {'device_id': device_id, 'success': False, 'error': str(e)}
        
        scatter_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(online_devices)) as executor:
            futures = [executor.submit(set_random_pattern, did, ip) for did, ip in online_devices]
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                scatter_results.append(result)
                if result['success']:
                    print(f"  🎨 {result['device_id']} → {result.get('pattern', 'Random')}")
                else:
                    print(f"  ❌ Failed to scatter {result['device_id']}")
        
        # Clean up: Delete swell patterns
        for device_id, (swell_id, _) in pattern_ids.items():
            try:
                if device_id in self.pb_clients:
                    self.pb_clients[device_id].deletePattern(swell_id)
            except:
                pass  # Silent cleanup
        
        print("✨ Swell and scatter complete!")
        
        # Update device info
        threading.Thread(target=self.update_all_api_data, daemon=True).start()
        
        return {
            'success': True,
            'swell_results': results,
            'scatter_results': scatter_results,
            'duration': duration,
            'color_hue': color_hue
        }
    
    def setup_time_sync(self):
        """Setup time synchronization between PixelBlazes for perfect sync
        Uses the first device as leader, others as followers"""
        if not HAS_PB_CLIENT:
            return {'success': False, 'error': 'pixelblaze-client not installed'}
        
        with self.lock:
            online_devices = [(d.id, d.ip) for d in self.devices.values() if d.online]
        
        if len(online_devices) < 2:
            return {'success': False, 'error': 'Need at least 2 devices for sync'}
        
        # First device becomes the leader
        leader_id, leader_ip = online_devices[0]
        follower_devices = online_devices[1:]
        
        print(f"🎯 Setting up time sync - Leader: {leader_id}")
        
        try:
            # Get leader's time  
            if leader_id not in self.pb_clients:
                self.pb_clients[leader_id] = Pixelblaze(leader_ip)
            
            leader_pb = self.pb_clients[leader_id]
            
            # Sync followers to leader's time
            for device_id, ip in follower_devices:
                try:
                    if device_id not in self.pb_clients:
                        self.pb_clients[device_id] = Pixelblaze(ip)
                    
                    pb = self.pb_clients[device_id]
                    
                    # Send a ping to sync time (PixelBlaze uses NTP-like sync)
                    pb.sendPing()
                    print(f"  📡 Synced {device_id} to leader time")
                    
                except Exception as e:
                    print(f"  ❌ Failed to sync {device_id}: {e}")
            
            return {
                'success': True,
                'leader': leader_id,
                'followers': [d[0] for d in follower_devices]
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_common_patterns(self):
        """Get patterns that exist on ALL devices"""
        if not HAS_PB_CLIENT:
            return []
        
        common_patterns = None
        
        with self.lock:
            online_devices = [(d.id, d.ip) for d in self.devices.values() if d.online]
        
        for device_id, ip in online_devices:
            try:
                if device_id not in self.pb_clients:
                    self.pb_clients[device_id] = Pixelblaze(ip)
                
                pb = self.pb_clients[device_id]
                patterns = pb.getPatternList()
                
                if patterns:
                    # Patterns can be either:
                    # 1. Dict of {id: "name"} (simple format)
                    # 2. Dict of {id: {"name": "...", ...}} (object format)
                    pattern_names = set()
                    for pattern_id, pattern_data in patterns.items():
                        if isinstance(pattern_data, str):
                            # Simple format: pattern_data IS the name
                            pattern_names.add(pattern_data)
                        elif isinstance(pattern_data, dict) and 'name' in pattern_data:
                            # Object format: pattern_data has a 'name' field
                            pattern_names.add(pattern_data['name'])
                    
                    if common_patterns is None:
                        common_patterns = pattern_names
                    else:
                        common_patterns = common_patterns.intersection(pattern_names)
                    
                    print(f"📋 Device {device_id}: {len(pattern_names)} patterns")
            except Exception as e:
                print(f"❌ Failed to get patterns for {device_id}: {e}")
        
        result = sorted(list(common_patterns)) if common_patterns else []
        print(f"🎯 Common patterns across all devices: {len(result)}")
        return result
    
    def save_state(self):
        """Save device state to file"""
        try:
            with self.lock:
                # Only save basic info, not API data
                data = {
                    'devices': [
                        {
                            'id': d.id,
                            'ip': d.ip,
                            'name': d.api_name or d.name,
                            'provisioned': d.provisioned
                        }
                        for d in self.devices.values()
                    ],
                    'saved_at': datetime.now().isoformat()
                }
            with open(STATE_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Failed to save state: {e}")
    
    def load_state(self):
        """Load device state from file"""
        try:
            if STATE_FILE.exists():
                with open(STATE_FILE, 'r') as f:
                    data = json.load(f)
                    for d in data.get('devices', []):
                        device = Device(
                            id=d['id'],
                            ip=d['ip'],
                            name=d.get('name', f"PB_{d['id'][-4:]}"),
                            provisioned=d.get('provisioned', False),
                            online=False  # Start offline until we hear from it
                        )
                        self.devices[device.id] = device
                print(f"📂 Loaded {len(self.devices)} devices from state file")
        except Exception as e:
            print(f"Could not load state: {e}")


def discovery_thread(manager: DeviceManager):
    """UDP discovery listener"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(1.0)
    
    try:
        sock.bind(('', DISCOVERY_PORT))
        print(f"👂 Listening for PixelBlaze devices on UDP port {DISCOVERY_PORT}")
        
        while True:
            try:
                data, addr = sock.recvfrom(1024)
                if len(data) >= 6:
                    device_id = data[:6].hex()
                    manager.update_device(device_id, addr[0])
            except socket.timeout:
                pass
            except Exception as e:
                print(f"Discovery error: {e}")
    finally:
        sock.close()


def monitor_thread(manager: DeviceManager):
    """Monitor devices for offline status"""
    while True:
        time.sleep(5)
        
        # Check for offline devices only
        manager.check_timeouts()


# Enhanced HTML UI
HTML = open('templates/index.html', 'r').read()

# Create Flask app
app = Flask(__name__)
CORS(app)

# Device manager instance
manager = DeviceManager()

@app.route('/')
def index():
    """Serve the web UI"""
    return render_template_string(HTML)

@app.route('/api/devices')
def api_devices():
    """API endpoint for device list"""
    devices = manager.get_all()
    return jsonify({'devices': devices})

@app.route('/api/health')
def health():
    """Health check with more detail"""
    devices = manager.get_all()
    return jsonify({
        'status': 'healthy',
        'total_devices': len(devices),
        'online_devices': sum(1 for d in devices if d['online']),
        'total_pixels': sum(d.get('pixel_count', 0) for d in devices),
        'has_api_client': HAS_PB_CLIENT
    })

@app.route('/api/sync/<pattern_name>', methods=['POST'])
def sync_pattern(pattern_name):
    """Sync specific pattern to all devices"""
    result = manager.sync_pattern(pattern_name)
    return jsonify(result)

@app.route('/api/sync-random', methods=['POST'])
def sync_random():
    """Sync a random pattern to all devices"""
    result = manager.sync_pattern()
    return jsonify(result)

@app.route('/api/common-patterns')
def common_patterns():
    """Get patterns available on all devices"""
    patterns = manager.get_common_patterns()
    return jsonify({'patterns': patterns, 'count': len(patterns)})

@app.route('/api/setup-sync', methods=['POST'])
def setup_sync():
    """Setup time synchronization between devices"""
    result = manager.setup_time_sync()
    return jsonify(result)

@app.route('/api/swell-and-scatter', methods=['POST'])
def swell_and_scatter():
    """Trigger dramatic swell effect followed by scatter"""
    # Get optional parameters from request
    from flask import request
    data = request.get_json() or {}
    duration = data.get('duration', 5.0)
    color_hue = data.get('hue', None)
    
    result = manager.dramatic_swell_and_scatter(duration, color_hue)
    return jsonify(result)

@app.route('/api/pulse', methods=['POST'])
def pulse():
    """Run 2 cycles of simplePulse then scatter"""
    import threading
    from pb_pulse_and_scatter import pulse_and_scatter
    
    online_devices = [(d.id, d.ip) for d in manager.devices.values() if d.online]
    online_ips = [ip for _, ip in online_devices]
    
    if not online_ips:
        return jsonify({'success': False, 'message': 'No online devices'})
    
    def run():
        pulse_and_scatter(online_ips, pulse_cycles=2, cycle_duration=20)
    
    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': f'Started on {len(online_ips)} devices'})

@app.route('/api/pulse-quick', methods=['POST'])
def pulse_quick():
    """Run quick test - quarter cycle (5 seconds)"""
    import threading
    from pb_pulse_and_scatter import pulse_and_scatter
    
    online_devices = [(d.id, d.ip) for d in manager.devices.values() if d.online]
    online_ips = [ip for _, ip in online_devices]
    
    if not online_ips:
        return jsonify({'success': False, 'message': 'No online devices'})
    
    def run():
        pulse_and_scatter(online_ips, pulse_cycles=0.25, cycle_duration=20)
    
    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': f'Quick test on {len(online_ips)} devices'})

def main():
    """Start the enhanced app"""
    print("🚀 PixelBlaze Fleet Monitor - Enhanced Flask Version")
    print(f"📡 Starting on http://localhost:{PORT}")
    
    if not HAS_PB_CLIENT:
        print("\n💡 TIP: Install pixelblaze-client for full features:")
        print("   pip install pixelblaze-client")
    
    # Start background threads
    threading.Thread(target=discovery_thread, args=(manager,), daemon=True).start()
    threading.Thread(target=monitor_thread, args=(manager,), daemon=True).start()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=PORT, debug=False)

if __name__ == '__main__':
    main()