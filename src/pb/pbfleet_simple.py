#!/usr/bin/env python3
"""
PixelBlaze Fleet Monitor - Dead Simple Flask Version
No async, no complexity, just works!
"""

import json
import socket
import threading
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict

from flask import Flask, jsonify, render_template_string
from flask_cors import CORS

# Simple configuration
PORT = 8000
DISCOVERY_PORT = 1889
DEVICE_TIMEOUT = 30.0
STATE_FILE = Path("devices_state.json")

@dataclass
class Device:
    """Simple device info"""
    id: str
    ip: str
    name: str = ""
    last_seen: float = 0
    online: bool = True
    provisioned: bool = False
    
    def to_dict(self):
        return {
            **asdict(self),
            'last_seen_formatted': datetime.fromtimestamp(self.last_seen).strftime('%H:%M:%S')
        }


class DeviceManager:
    """Manages devices with thread safety"""
    
    def __init__(self):
        self.devices: Dict[str, Device] = {}
        self.lock = threading.Lock()
        self.load_state()
    
    def update_device(self, device_id: str, ip: str):
        """Update or add device"""
        with self.lock:
            if device_id in self.devices:
                self.devices[device_id].ip = ip
                self.devices[device_id].last_seen = time.time()
                self.devices[device_id].online = True
            else:
                print(f"✨ New device discovered: {device_id} at {ip}")
                self.devices[device_id] = Device(
                    id=device_id,
                    ip=ip,
                    name=f"PB_{device_id[-4:]}",
                    last_seen=time.time()
                )
        # Save state outside the lock
        self.save_state()
    
    def check_timeouts(self):
        """Mark devices offline if not seen recently"""
        current_time = time.time()
        with self.lock:
            for device in self.devices.values():
                was_online = device.online
                device.online = (current_time - device.last_seen) < DEVICE_TIMEOUT
                if was_online and not device.online:
                    print(f"📴 Device {device.id} went offline")
    
    def get_all(self):
        """Get all devices as list of dicts"""
        with self.lock:
            return [d.to_dict() for d in self.devices.values()]
    
    def save_state(self):
        """Save device state to file"""
        try:
            with self.lock:
                data = {
                    'devices': [d.to_dict() for d in self.devices.values()],
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
                        device = Device(**{k: v for k, v in d.items() if k in Device.__dataclass_fields__})
                        device.online = False  # Mark offline until we hear from it
                        self.devices[device.id] = device
                print(f"📂 Loaded {len(self.devices)} devices from state file")
        except Exception as e:
            print(f"Could not load state: {e}")


def discovery_thread(manager: DeviceManager):
    """UDP discovery listener - runs in background thread"""
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
    """Check for offline devices - runs in background thread"""
    while True:
        time.sleep(5)
        manager.check_timeouts()


# HTML UI - Clean and simple
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
        .container { max-width: 1200px; margin: 0 auto; }
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
        .devices {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
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
        .device.offline { opacity: 0.5; }
        .device-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        .device-name { font-weight: 600; font-size: 1.1rem; }
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #ef4444;
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
            border-bottom: 1px solid #f3f4f6;
        }
        .device-info > div:last-child { border-bottom: none; }
        .label { font-weight: 500; }
        .value { font-family: monospace; }
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
    </style>
</head>
<body>
    <div class="container">
        <h1>🌟 PixelBlaze Fleet Monitor</h1>
        <div class="stats">
            <span id="stats">Loading...</span>
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
                    document.getElementById('stats').innerHTML = 
                        `${online} online / ${total} total devices | Last update: ${new Date().toLocaleTimeString()}`;
                    
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
                        return a.name.localeCompare(b.name);
                    });
                    
                    container.innerHTML = sorted.map(d => `
                        <div class="device ${d.online ? '' : 'offline'}">
                            <div class="device-header">
                                <div class="device-name">${d.name}</div>
                                <div class="status-dot ${d.online ? 'online' : ''}"></div>
                            </div>
                            <div class="device-info">
                                <div>
                                    <span class="label">ID:</span>
                                    <span class="value">${d.id}</span>
                                </div>
                                <div>
                                    <span class="label">IP:</span>
                                    <span class="value">${d.ip}</span>
                                </div>
                                <div>
                                    <span class="label">Status:</span>
                                    <span class="value">${d.online ? '🟢 Online' : '🔴 Offline'}</span>
                                </div>
                                <div>
                                    <span class="label">Last seen:</span>
                                    <span class="value">${d.last_seen_formatted}</span>
                                </div>
                            </div>
                        </div>
                    `).join('');
                })
                .catch(err => {
                    console.error('Update error:', err);
                    document.getElementById('stats').innerHTML = 
                        `❌ Connection error | ${new Date().toLocaleTimeString()}`;
                });
        }
        
        // Initial load and refresh every 3 seconds
        updateDevices();
        setInterval(updateDevices, 3000);
    </script>
</body>
</html>
'''

# Create Flask app
app = Flask(__name__)
CORS(app)  # Allow cross-origin requests for development

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
    print(f"📊 API called - returning {len(devices)} devices: {[d['id'] for d in devices]}")
    return jsonify({'devices': devices})

@app.route('/api/health')
def health():
    """Simple health check"""
    devices = manager.get_all()
    return jsonify({
        'status': 'healthy',
        'total_devices': len(devices),
        'online_devices': sum(1 for d in devices if d['online'])
    })

@app.route('/api/pulse', methods=['POST'])
def pulse():
    """Run 2 cycles of simplePulse then scatter"""
    import threading
    from pb_pulse_and_scatter import pulse_and_scatter
    
    devices = manager.get_all()
    online_ips = [d['ip'] for d in devices if d['online']]
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
    """Run quick test - quarter cycle"""
    import threading
    from pb_pulse_and_scatter import pulse_and_scatter
    
    devices = manager.get_all()
    online_ips = [d['ip'] for d in devices if d['online']]
    if not online_ips:
        return jsonify({'success': False, 'message': 'No online devices'})
    
    def run():
        pulse_and_scatter(online_ips, pulse_cycles=0.25, cycle_duration=20)
    
    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()
    
    return jsonify({'success': True, 'message': f'Quick test on {len(online_ips)} devices'})

def main():
    """Start the app"""
    print("🚀 PixelBlaze Fleet Monitor - Simple Flask Version")
    print(f"📡 Starting on http://localhost:{PORT}")
    
    # Start background threads
    threading.Thread(target=discovery_thread, args=(manager,), daemon=True).start()
    threading.Thread(target=monitor_thread, args=(manager,), daemon=True).start()
    
    # Run Flask app
    app.run(host='0.0.0.0', port=PORT, debug=False)

if __name__ == '__main__':
    main()