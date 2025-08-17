#!/usr/bin/env python3
"""
Simple web server with button to trigger pulse and scatter sequence
"""

from flask import Flask, render_template_string, jsonify
import threading
from pb_pulse_and_scatter import pulse_and_scatter
import socket
import struct
import json
import time

app = Flask(__name__)

# Global state
devices = {}
lock = threading.Lock()

# HTML template with button
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>PixelBlaze Pulse Control</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #1a1a1a;
            color: #fff;
        }
        h1 { color: #ff4444; }
        .button-container {
            display: flex;
            gap: 20px;
            margin: 30px 0;
        }
        button {
            background: #ff4444;
            color: white;
            border: none;
            padding: 20px 40px;
            font-size: 18px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }
        button:hover {
            background: #ff6666;
            transform: scale(1.05);
        }
        button:active {
            transform: scale(0.95);
        }
        button:disabled {
            background: #666;
            cursor: not-allowed;
            transform: scale(1);
        }
        .devices {
            background: #2a2a2a;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .device {
            padding: 8px;
            margin: 5px 0;
            background: #3a3a3a;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
        }
        .online { border-left: 3px solid #4f4; }
        .offline { border-left: 3px solid #666; opacity: 0.5; }
        .status {
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            display: none;
        }
        .status.show { display: block; }
        .status.running { background: #442200; border: 1px solid #ffaa00; }
        .status.complete { background: #004400; border: 1px solid #00ff00; }
        .status.error { background: #440000; border: 1px solid #ff0000; }
    </style>
</head>
<body>
    <h1>🔴 PixelBlaze Pulse Control</h1>
    
    <div class="devices">
        <h3>Discovered Devices:</h3>
        <div id="deviceList">Searching...</div>
    </div>
    
    <div class="button-container">
        <button id="pulseBtn" onclick="startPulse()">
            🔴 Start Pulse & Scatter
        </button>
        <button id="quickBtn" onclick="quickPulse()">
            ⚡ Quick Test (5 sec)
        </button>
    </div>
    
    <div id="status" class="status"></div>
    
    <script>
        let running = false;
        
        function updateDevices() {
            fetch('/api/devices')
                .then(r => r.json())
                .then(devices => {
                    const list = document.getElementById('deviceList');
                    if (Object.keys(devices).length === 0) {
                        list.innerHTML = 'No devices found';
                        return;
                    }
                    
                    list.innerHTML = Object.entries(devices)
                        .map(([id, dev]) => `
                            <div class="device ${dev.online ? 'online' : 'offline'}">
                                <span>${dev.name || id}</span>
                                <span>${dev.ip}</span>
                                <span>${dev.online ? '🟢' : '⚫'}</span>
                            </div>
                        `).join('');
                });
        }
        
        function startPulse() {
            if (running) return;
            
            const btn = document.getElementById('pulseBtn');
            const status = document.getElementById('status');
            
            running = true;
            btn.disabled = true;
            btn.textContent = '⏳ Running (40 sec)...';
            
            status.className = 'status show running';
            status.textContent = '🔴 Running pulse sequence (2 cycles, ~40 seconds)...';
            
            fetch('/api/pulse', { method: 'POST' })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        status.className = 'status show complete';
                        status.textContent = '✅ ' + result.message;
                    } else {
                        status.className = 'status show error';
                        status.textContent = '❌ ' + (result.error || 'Failed');
                    }
                })
                .catch(err => {
                    status.className = 'status show error';
                    status.textContent = '❌ Error: ' + err;
                })
                .finally(() => {
                    running = false;
                    btn.disabled = false;
                    btn.textContent = '🔴 Start Pulse & Scatter';
                    setTimeout(() => {
                        status.className = 'status';
                    }, 5000);
                });
        }
        
        function quickPulse() {
            if (running) return;
            
            const btn = document.getElementById('quickBtn');
            const status = document.getElementById('status');
            
            running = true;
            btn.disabled = true;
            btn.textContent = '⏳ Running...';
            
            status.className = 'status show running';
            status.textContent = '⚡ Running quick test (5 seconds)...';
            
            fetch('/api/pulse-quick', { method: 'POST' })
                .then(r => r.json())
                .then(result => {
                    if (result.success) {
                        status.className = 'status show complete';
                        status.textContent = '✅ ' + result.message;
                    } else {
                        status.className = 'status show error';
                        status.textContent = '❌ ' + (result.error || 'Failed');
                    }
                })
                .catch(err => {
                    status.className = 'status show error';
                    status.textContent = '❌ Error: ' + err;
                })
                .finally(() => {
                    running = false;
                    btn.disabled = false;
                    btn.textContent = '⚡ Quick Test (5 sec)';
                    setTimeout(() => {
                        status.className = 'status';
                    }, 5000);
                });
        }
        
        // Update devices every 2 seconds
        setInterval(updateDevices, 2000);
        updateDevices();
    </script>
</body>
</html>
"""

def discovery_thread():
    """Background thread to discover PixelBlaze devices"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind(('', 1889))
    except OSError:
        # Port in use, probably by another monitor - just skip discovery
        print("⚠️  Discovery port 1889 in use - skipping device discovery")
        return
    sock.settimeout(1.0)
    
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            if len(data) >= 12:
                device_id = data[0:6].hex()
                flash_id = struct.unpack('<I', data[6:10])[0]
                version = struct.unpack('<B', data[10:11])[0]
                
                with lock:
                    devices[device_id] = {
                        'id': device_id,
                        'ip': addr[0],
                        'name': f'PB_{device_id[-4:]}',
                        'online': True,
                        'last_seen': time.time()
                    }
        except socket.timeout:
            # Mark old devices as offline
            with lock:
                now = time.time()
                for device in devices.values():
                    if now - device.get('last_seen', 0) > 10:
                        device['online'] = False

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/devices')
def get_devices():
    with lock:
        return jsonify(devices)

@app.route('/api/pulse', methods=['POST'])
def run_pulse():
    """Run full 2-cycle pulse sequence (40 seconds)"""
    with lock:
        online_ips = [d['ip'] for d in devices.values() if d.get('online')]
    
    if not online_ips:
        return jsonify({'success': False, 'error': 'No online devices'})
    
    def run_sequence():
        pulse_and_scatter(online_ips, pulse_cycles=2, cycle_duration=20)
    
    thread = threading.Thread(target=run_sequence)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'message': f'Started pulse sequence on {len(online_ips)} devices'
    })

@app.route('/api/pulse-quick', methods=['POST'])
def run_quick_pulse():
    """Run quick test - half cycle (5 seconds)"""
    with lock:
        online_ips = [d['ip'] for d in devices.values() if d.get('online')]
    
    if not online_ips:
        return jsonify({'success': False, 'error': 'No online devices'})
    
    def run_sequence():
        pulse_and_scatter(online_ips, pulse_cycles=0.25, cycle_duration=20)
    
    thread = threading.Thread(target=run_sequence)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'message': f'Started quick test on {len(online_ips)} devices'
    })

if __name__ == '__main__':
    # Start discovery thread
    discovery = threading.Thread(target=discovery_thread)
    discovery.daemon = True
    discovery.start()
    
    print("\n🔴 PixelBlaze Pulse Control Server")
    print("📡 Visit http://localhost:5000")
    print("Press Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=5000, debug=False)