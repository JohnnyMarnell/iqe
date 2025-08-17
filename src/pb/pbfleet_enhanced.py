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
        with self.lock:
            if device_id in self.devices:
                self.devices[device_id].ip = ip
                self.devices[device_id].last_seen = time.time()
                self.devices[device_id].online = True
            else:
                is_new = True
                print(f"✨ New device discovered: {device_id} at {ip}")
                self.devices[device_id] = Device(
                    id=device_id,
                    ip=ip,
                    name=f"PB_{device_id[-4:]}",
                    last_seen=time.time()
                )
        
        # Fetch API data for new devices immediately
        if is_new and HAS_PB_CLIENT:
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
                print(f"✨ Got device name: {device_name}")
            except:
                device_name = f"PB_{device_id[-4:]}"
                print(f"⚠️  Could not get device name for {device_id}, using default")
            
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
                print(f"💾 Saved config to {config_file}")
            except Exception as e:
                print(f"Could not get config: {e}")
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
                print(f"💾 Saved {pattern_count} patterns to {patterns_file}")
            except Exception as e:
                print(f"⚠️  Could not get patterns for {device_id}: {e}")
                patterns = {}
                pattern_count = 0
            
            # Get current pattern
            try:
                active = pb.getActivePattern()
                if active:
                    current_pattern_name = active.get("name", "Unknown")
                    current_pattern_id = active.get("id", "")
                else:
                    # Fallback: look up in pattern list
                    current_pattern_id = pb.ws.activePatternId if hasattr(pb, 'ws') else ""
                    current_pattern_name = patterns.get(current_pattern_id, {}).get("name", "Unknown")
            except:
                current_pattern_name = "Unknown"
                current_pattern_id = ""
            
            # Brightness already retrieved from config above
            
            # Get sequencer info
            sequencer_mode = "Off"
            playlist_length = 0
            try:
                # This is device-specific, might not work on all
                if hasattr(pb, 'ws') and hasattr(pb.ws, 'sequencerMode'):
                    modes = ["Off", "Shuffle All", "Playlist"]
                    mode_idx = pb.ws.sequencerMode
                    sequencer_mode = modes[mode_idx] if 0 <= mode_idx < len(modes) else "Unknown"
                    
                    if hasattr(pb.ws, 'playlist'):
                        playlist_length = len(pb.ws.playlist)
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
                    print(f"💾 Saved WebSocket data to {ws_file}")
                    
                    # Check specifically for name in ws attributes
                    if 'name' in ws_data:
                        print(f"✨ Found ws.name: {ws_data['name']}")
                        if not device_name or device_name.startswith("PB_"):
                            device_name = ws_data['name']
            except Exception as e:
                print(f"Could not save WebSocket data: {e}")
            
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
                    d.last_api_update = time.time()
                    d.api_error = ""
                    print(f"📊 Updated {device_id}: {device_name}, pattern: {current_pattern_name}, {pattern_count} patterns")
            
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
        """Set the same pattern on all online devices"""
        if not HAS_PB_CLIENT:
            return {'success': False, 'error': 'pixelblaze-client not installed'}
        
        results = []
        with self.lock:
            online_devices = [(d.id, d.ip) for d in self.devices.values() if d.online]
        
        print(f"🎭 Syncing pattern '{pattern_name}' to {len(online_devices)} devices")
        
        for device_id, ip in online_devices:
            try:
                if device_id not in self.pb_clients:
                    self.pb_clients[device_id] = Pixelblaze(ip)
                
                pb = self.pb_clients[device_id]
                
                if pattern_name:
                    # Use the ACTUAL method that exists
                    pb.setActivePatternByName(pattern_name)
                    print(f"  Setting pattern by name: '{pattern_name}'")
                else:
                    # Pick a random pattern
                    patterns = pb.getPatternList()
                    if patterns:
                        import random
                        pattern_id = random.choice(list(patterns.keys()))
                        # Use setActivePattern with the ID
                        pb.setActivePattern(pattern_id)
                        # Get the pattern name for logging
                        pdata = patterns[pattern_id]
                        if isinstance(pdata, str):
                            pattern_name = pdata
                        else:
                            pattern_name = pdata.get('name', 'Unknown')
                        print(f"  Set random pattern: '{pattern_name}' (ID: {pattern_id})")
                
                results.append({'device_id': device_id, 'success': True})
                print(f"  ✅ Set pattern on {device_id}")
                
            except Exception as e:
                results.append({'device_id': device_id, 'success': False, 'error': str(e)})
                print(f"  ❌ Failed on {device_id}: {e}")
        
        # Update all device info after sync
        threading.Thread(target=self.update_all_api_data, daemon=True).start()
        
        return {
            'success': True, 
            'pattern': pattern_name,
            'devices': results,
            'total': len(results),
            'successful': sum(1 for r in results if r['success'])
        }
    
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
    """Monitor devices and update API data"""
    last_api_update = 0
    
    while True:
        time.sleep(5)
        
        # Check for offline devices
        manager.check_timeouts()
        
        # Update API data periodically
        current_time = time.time()
        if current_time - last_api_update > API_UPDATE_INTERVAL:
            print("🔄 Updating device API data...")
            manager.update_all_api_data()
            last_api_update = current_time


# Enhanced HTML UI
HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>PixelBlaze Fleet</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, system-ui, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { 
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2rem;
        }
        .stats {
            background: white;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .controls {
            background: white;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
            justify-content: center;
        }
        .btn {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, opacity 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
            opacity: 0.9;
        }
        .btn:active {
            transform: translateY(0);
        }
        .btn.sync {
            background: linear-gradient(135deg, #f59e0b, #ef4444);
        }
        select {
            padding: 10px;
            border-radius: 6px;
            border: 1px solid #e5e7eb;
            font-size: 0.9rem;
        }
        .devices {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 20px;
        }
        .device {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .device:hover { transform: translateY(-2px); }
        .device.offline { opacity: 0.6; }
        .device-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f3f4f6;
        }
        .device-name { 
            font-weight: 600; 
            font-size: 1.2rem;
            color: #1f2937;
        }
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #ef4444;
            flex-shrink: 0;
        }
        .status-dot.online {
            background: #10b981;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .device-info {
            color: #6b7280;
            font-size: 0.9rem;
            line-height: 1.6;
        }
        .device-info > div {
            display: flex;
            justify-content: space-between;
            padding: 4px 0;
            border-bottom: 1px solid #f9fafb;
        }
        .device-info > div:last-child { border-bottom: none; }
        .label { 
            font-weight: 500;
            color: #374151;
        }
        .value { 
            font-family: monospace;
            text-align: right;
        }
        .pattern-name {
            color: #8b5cf6;
            font-weight: 600;
        }
        .brightness-bar {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .brightness-fill {
            flex: 1;
            height: 6px;
            background: #e5e7eb;
            border-radius: 3px;
            overflow: hidden;
        }
        .brightness-level {
            height: 100%;
            background: linear-gradient(90deg, #fbbf24, #f59e0b);
            transition: width 0.3s;
        }
        .no-devices {
            grid-column: 1 / -1;
            text-align: center;
            color: white;
            font-size: 1.2rem;
            padding: 40px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
        }
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .error { color: #ef4444; font-size: 0.8rem; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌟 PixelBlaze Fleet Monitor</h1>
        <div class="stats">
            <span id="stats">Loading...</span>
        </div>
        <div class="controls">
            <button class="btn sync" onclick="syncRandom()">🎲 Sync Random Pattern</button>
            <select id="patternSelect">
                <option value="">Loading patterns...</option>
            </select>
            <button class="btn" onclick="syncSelected()">🎭 Sync Selected</button>
            <button class="btn" onclick="updateDevices()">🔄 Refresh</button>
        </div>
        <div class="devices" id="devices">
            <div class="no-devices">
                <div class="loading"></div>
                <p>Searching for PixelBlaze devices...</p>
            </div>
        </div>
    </div>
    
    <script>
        let devices = new Map();
        
        function updateDevices() {
            fetch('/api/devices')
                .then(r => {
                    if (!r.ok) throw new Error(`HTTP ${r.status}`);
                    return r.json();
                })
                .then(data => {
                    console.log('Got devices:', data);
                    // Update device map
                    data.devices.forEach(d => devices.set(d.id, d));
                    
                    // Update stats
                    const online = data.devices.filter(d => d.online).length;
                    const total = data.devices.length;
                    const totalPixels = data.devices.reduce((sum, d) => sum + (d.pixel_count || 0), 0);
                    document.getElementById('stats').innerHTML = 
                        `${online} online / ${total} total devices | ${totalPixels} pixels | Last update: ${new Date().toLocaleTimeString()}`;
                    
                    // Render devices
                    const container = document.getElementById('devices');
                    
                    if (data.devices.length === 0) {
                        container.innerHTML = `
                            <div class="no-devices">
                                <div class="loading"></div>
                                <p>Searching for PixelBlaze devices...</p>
                                <p style="font-size:0.9rem;margin-top:10px">Make sure devices are powered on and on the same network</p>
                            </div>`;
                        return;
                    }
                    
                    // Sort: online first, then by name
                    const sorted = data.devices.sort((a, b) => {
                        if (a.online !== b.online) return b.online - a.online;
                        const nameA = a.api_name || a.name;
                        const nameB = b.api_name || b.name;
                        return nameA.localeCompare(nameB);
                    });
                    
                    container.innerHTML = sorted.map(d => {
                        const displayName = d.api_name || d.name;
                        const brightnessPercent = Math.round((d.brightness || 0.5) * 100);
                        
                        return `
                        <div class="device ${d.online ? '' : 'offline'}">
                            <div class="device-header">
                                <div class="device-name">${displayName}</div>
                                <div class="status-dot ${d.online ? 'online' : ''}"></div>
                            </div>
                            <div class="device-info">
                                <div>
                                    <span class="label">Pattern:</span>
                                    <span class="value pattern-name">${d.current_pattern || 'Unknown'}</span>
                                </div>
                                <div>
                                    <span class="label">Brightness:</span>
                                    <span class="value">${brightnessPercent}%</span>
                                </div>
                                <div class="brightness-bar">
                                    <div class="brightness-fill">
                                        <div class="brightness-level" style="width: ${brightnessPercent}%"></div>
                                    </div>
                                </div>
                                ${d.pattern_count ? `
                                <div>
                                    <span class="label">Patterns:</span>
                                    <span class="value">${d.pattern_count} available</span>
                                </div>` : ''}
                                ${d.sequencer_mode && d.sequencer_mode !== 'Off' ? `
                                <div>
                                    <span class="label">Sequencer:</span>
                                    <span class="value">${d.sequencer_mode}${d.playlist_length ? ` (${d.playlist_length})` : ''}</span>
                                </div>` : ''}
                                ${d.pixel_count ? `
                                <div>
                                    <span class="label">Pixels:</span>
                                    <span class="value">${d.pixel_count}</span>
                                </div>` : ''}
                                <div>
                                    <span class="label">IP:</span>
                                    <span class="value">${d.ip}</span>
                                </div>
                                <div>
                                    <span class="label">ID:</span>
                                    <span class="value" style="font-size:0.8rem">${d.id}</span>
                                </div>
                                <div>
                                    <span class="label">Last seen:</span>
                                    <span class="value">${d.last_seen_formatted}</span>
                                </div>
                                ${d.api_error ? `
                                <div class="error">API Error: ${d.api_error}</div>` : ''}
                            </div>
                        </div>`;
                    }).join('');
                })
                .catch(err => {
                    console.error('Update error:', err);
                    document.getElementById('stats').innerHTML = 
                        `❌ Connection error | ${new Date().toLocaleTimeString()}`;
                });
        }
        
        // Load common patterns
        function loadPatterns() {
            fetch('/api/common-patterns')
                .then(r => r.json())
                .then(data => {
                    const select = document.getElementById('patternSelect');
                    if (data.patterns && data.patterns.length > 0) {
                        select.innerHTML = '<option value="">Select a pattern...</option>' +
                            data.patterns.map(p => `<option value="${p}">${p}</option>`).join('');
                    } else {
                        select.innerHTML = '<option value="">No common patterns found</option>';
                    }
                })
                .catch(err => console.error('Failed to load patterns:', err));
        }
        
        // Sync random pattern to all devices
        function syncRandom() {
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = '⏳ Syncing...';
            
            fetch('/api/sync-random', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    console.log('Sync result:', data);
                    if (data.success) {
                        btn.textContent = `✅ Synced to ${data.successful} devices`;
                        setTimeout(updateDevices, 1000);
                    } else {
                        btn.textContent = '❌ Sync failed';
                        console.error('Sync failed:', data.error);
                    }
                    setTimeout(() => {
                        btn.disabled = false;
                        btn.textContent = '🎲 Sync Random Pattern';
                    }, 2000);
                })
                .catch(err => {
                    console.error('Sync error:', err);
                    btn.textContent = '❌ Error';
                    setTimeout(() => {
                        btn.disabled = false;
                        btn.textContent = '🎲 Sync Random Pattern';
                    }, 2000);
                });
        }
        
        // Sync selected pattern to all devices
        function syncSelected() {
            const select = document.getElementById('patternSelect');
            const pattern = select.value;
            
            if (!pattern) {
                return;
            }
            
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = '⏳ Syncing...';
            
            fetch(`/api/sync/${encodeURIComponent(pattern)}`, { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    console.log('Sync result:', data);
                    if (data.success) {
                        btn.textContent = `✅ Synced ${data.successful}`;
                        setTimeout(updateDevices, 1000);
                    } else {
                        btn.textContent = '❌ Failed';
                        console.error('Sync failed:', data.error);
                    }
                    setTimeout(() => {
                        btn.disabled = false;
                        btn.textContent = '🎭 Sync Selected';
                    }, 2000);
                })
                .catch(err => {
                    console.error('Sync error:', err);
                    btn.textContent = '❌ Error';
                    setTimeout(() => {
                        btn.disabled = false;
                        btn.textContent = '🎭 Sync Selected';
                    }, 2000);
                });
        }
        
        // Initial load and refresh every 3 seconds
        updateDevices();
        loadPatterns();
        setInterval(updateDevices, 3000);
        // Reload patterns occasionally in case new devices come online
        setInterval(loadPatterns, 30000);
    </script>
</body>
</html>
'''

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