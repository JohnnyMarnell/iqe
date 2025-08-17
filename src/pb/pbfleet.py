#!/usr/bin/env python3
"""
PixelBlaze Fleet Monitor with Auto-Provisioning
Complete solution with API integration, pattern management, and device provisioning
"""

import asyncio
import json
import socket
import time
import threading
import logging
import os
import platform
import queue
import random
import pickle
from pathlib import Path
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import PixelBlaze API modules
try:
    from pixelblaze_api import PixelBlazeAPI, PixelBlazeFleet
    from patterns import PATTERNS, get_pattern
except ImportError:
    # Embedded versions if modules not found
    logger = logging.getLogger(__name__)
    logger.warning("Using embedded PixelBlaze modules")
    
    # Embedded pattern definitions
    SYNC_PULSE_PATTERN = """
    export var hue = 0.5
    export var pulseSpeed = 2
    export var minBrightness = 0.1
    export var maxBrightness = 1.0
    var startTime = 0
    var initialized = false
    export function beforeRender(delta) {
      if (!initialized) {
        startTime = time(0.001)
        initialized = true
      }
      t1 = time(0.001) - startTime
      wave = (sin(t1 * pulseSpeed * PI2) + 1) / 2
      pulseBrightness = minBrightness + (maxBrightness - minBrightness) * wave
    }
    export function render(index) {
      hsv(hue, 1, pulseBrightness)
    }
    """
    
    PATTERNS = {
        "sync_pulse": {
            "name": "IQE Sync Pulse",
            "code": SYNC_PULSE_PATTERN,
            "description": "Synchronized breathing pulse"
        }
    }
    
    def get_pattern(key): 
        return PATTERNS.get(key)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Provisioning state file
PROVISION_STATE_FILE = Path("provisioned_devices.pkl")

@dataclass
class PixelBlazeDevice:
    """Enhanced device info with provisioning status"""
    id: str
    ip: str
    name: str = "Unknown"
    last_seen: float = 0
    online: bool = False
    api_connected: bool = False
    current_pattern: str = ""
    patterns: List[dict] = field(default_factory=list)
    brightness: float = 0.5
    fps: int = 0
    provisioned: bool = False
    provision_date: Optional[float] = None
    
    def to_dict(self):
        return {
            **asdict(self),
            'last_seen_formatted': datetime.fromtimestamp(self.last_seen).strftime('%H:%M:%S'),
            'provision_date_formatted': datetime.fromtimestamp(self.provision_date).strftime('%Y-%m-%d %H:%M:%S') if self.provision_date else None
        }


class ProvisioningManager:
    """Manages device provisioning and pattern uploads"""
    
    def __init__(self, force_provision=False):
        self.force_provision = force_provision
        self.provisioned_devices = self.load_provisioned() if not force_provision else set()
        self.provisioned_this_run = set()  # Track what we've done this session
        self.provisioning_queue = queue.Queue()
        self.provisioning_thread = None
        self.running = False
        
        if force_provision:
            logger.info("Force provisioning mode enabled - will provision all devices")
        
    def load_provisioned(self) -> set:
        """Load set of provisioned device IDs"""
        if PROVISION_STATE_FILE.exists():
            try:
                with open(PROVISION_STATE_FILE, 'rb') as f:
                    return pickle.load(f)
            except:
                pass
        return set()
    
    def save_provisioned(self):
        """Save provisioned device IDs"""
        try:
            with open(PROVISION_STATE_FILE, 'wb') as f:
                pickle.dump(self.provisioned_devices, f)
        except Exception as e:
            logger.error(f"Failed to save provision state: {e}")
    
    def is_provisioned(self, device_id: str) -> bool:
        """Check if device has been provisioned"""
        if self.force_provision:
            # In force mode, only consider it provisioned if we did it this run
            return device_id in self.provisioned_this_run
        return device_id in self.provisioned_devices
    
    def mark_provisioned(self, device_id: str):
        """Mark device as provisioned"""
        self.provisioned_devices.add(device_id)
        self.provisioned_this_run.add(device_id)
        self.save_provisioned()
        logger.info(f"Device {device_id} marked as provisioned")
    
    async def provision_device(self, device_id: str, ip: str) -> bool:
        """Provision a new device with IQE patterns"""
        try:
            logger.info(f"Starting provisioning for {device_id} at {ip}")
            
            # Create API connection
            api = PixelBlazeAPI(ip)
            if not await api.connect():
                logger.error(f"Failed to connect to {device_id} for provisioning")
                return False
            
            # Upload all IQE patterns
            uploaded = 0
            for pattern_key, pattern_data in PATTERNS.items():
                try:
                    pattern_id = await api.upload_pattern(
                        pattern_data["name"],
                        pattern_data["code"]
                    )
                    if pattern_id:
                        uploaded += 1
                        logger.info(f"Uploaded {pattern_data['name']} to {device_id}")
                except Exception as e:
                    logger.error(f"Failed to upload {pattern_key} to {device_id}: {e}")
            
            # Disconnect
            await api.disconnect()
            
            if uploaded > 0:
                self.mark_provisioned(device_id)
                logger.info(f"Provisioning complete for {device_id}: {uploaded} patterns uploaded")
                return True
            else:
                logger.error(f"No patterns uploaded to {device_id}")
                return False
                
        except Exception as e:
            logger.error(f"Provisioning error for {device_id}: {e}")
            return False
    
    def start(self):
        """Start provisioning thread"""
        self.running = True
        self.provisioning_thread = threading.Thread(target=self._provisioning_loop, daemon=True)
        self.provisioning_thread.start()
    
    def stop(self):
        """Stop provisioning thread"""
        self.running = False
        if self.provisioning_thread:
            self.provisioning_thread.join(timeout=2)
    
    def _provisioning_loop(self):
        """Process provisioning queue"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def process_queue():
            while self.running:
                try:
                    # Check for devices to provision
                    try:
                        device_id, ip = self.provisioning_queue.get(timeout=1)
                        await self.provision_device(device_id, ip)
                    except queue.Empty:
                        pass
                except Exception as e:
                    logger.error(f"Provisioning loop error: {e}")
                await asyncio.sleep(0.1)
        
        loop.run_until_complete(process_queue())
        loop.close()
    
    def queue_provisioning(self, device_id: str, ip: str):
        """Add device to provisioning queue"""
        if not self.is_provisioned(device_id):
            self.provisioning_queue.put((device_id, ip))
            logger.info(f"Queued {device_id} for provisioning")


class ConnectionManager:
    """WebSocket connection manager"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.lock = threading.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        with self.lock:
            self.active_connections.append(websocket)
        logger.info(f"Client connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        with self.lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        with self.lock:
            connections = self.active_connections.copy()
        
        disconnected = []
        for connection in connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        if disconnected:
            with self.lock:
                for conn in disconnected:
                    if conn in self.active_connections:
                        self.active_connections.remove(conn)


class PixelBlazeDiscovery:
    """Discovery with API integration and auto-provisioning"""
    
    DISCOVERY_PORT = 1889
    DEVICE_TIMEOUT = 30.0
    API_UPDATE_INTERVAL = 10.0
    
    def __init__(self, connection_manager: ConnectionManager, provisioning_manager: ProvisioningManager):
        self.devices: Dict[str, PixelBlazeDevice] = {}
        self.lock = threading.Lock()
        self.running = False
        self.discovery_thread = None
        self.monitor_thread = None
        self.api_thread = None
        self.broadcast_thread = None
        self.connection_manager = connection_manager
        self.provisioning_manager = provisioning_manager
        self.update_queue = queue.Queue()
        self.fleet = PixelBlazeFleet() if 'PixelBlazeFleet' in globals() else None
        self.saved_states = {}
        
    def start(self):
        """Start all threads"""
        self.running = True
        self.discovery_thread = threading.Thread(target=self._discovery_loop, daemon=True)
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        
        if self.fleet:
            self.api_thread = threading.Thread(target=self._api_loop, daemon=True)
            self.api_thread.start()
        
        self.discovery_thread.start()
        self.monitor_thread.start()
        self.broadcast_thread.start()
        
        logger.info("PixelBlaze discovery started with auto-provisioning")
        
    def stop(self):
        """Stop all threads"""
        self.running = False
        for thread in [self.discovery_thread, self.monitor_thread, 
                      self.api_thread, self.broadcast_thread]:
            if thread:
                thread.join(timeout=2)
                
    def _discovery_loop(self):
        """UDP discovery listener"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(1.0)
        
        try:
            sock.bind(('', self.DISCOVERY_PORT))
            logger.info(f"Listening on UDP port {self.DISCOVERY_PORT}")
            
            while self.running:
                try:
                    data, addr = sock.recvfrom(1024)
                    self._process_discovery_packet(data, addr[0])
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        logger.error(f"Discovery error: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to bind socket: {e}")
        finally:
            sock.close()
            
    def _process_discovery_packet(self, data: bytes, ip: str):
        """Process discovery packet and trigger provisioning if needed"""
        try:
            if len(data) >= 6:
                device_id = data[:6].hex()
                
                with self.lock:
                    is_new = device_id not in self.devices
                    
                    if is_new:
                        logger.info(f"New PixelBlaze discovered: {device_id} at {ip}")
                        
                        # Check if provisioned
                        is_provisioned = self.provisioning_manager.is_provisioned(device_id)
                        
                        device = PixelBlazeDevice(
                            id=device_id,
                            ip=ip,
                            name=f"PB_{device_id[-4:]}",
                            last_seen=time.time(),
                            online=True,
                            provisioned=is_provisioned,
                            provision_date=time.time() if is_provisioned else None
                        )
                        self.devices[device_id] = device
                        
                        # Add to fleet if available
                        if self.fleet:
                            self.fleet.add_device(device_id, ip)
                        
                        # Queue for provisioning if needed
                        if not is_provisioned:
                            logger.info(f"New unprovisioned device {device_id} - queuing for provisioning")
                            self.provisioning_manager.queue_provisioning(device_id, ip)
                        else:
                            logger.info(f"Device {device_id} already provisioned")
                        
                        # Always queue update so device appears in UI
                        self.update_queue.put(device.to_dict())
                    else:
                        device = self.devices[device_id]
                        was_offline = not device.online
                        device.ip = ip
                        device.last_seen = time.time()
                        device.online = True
                        
                        if was_offline:
                            logger.info(f"PixelBlaze {device_id} back online")
                            if self.fleet:
                                self.fleet.add_device(device_id, ip)
                        
                        # Always queue update
                        self.update_queue.put(device.to_dict())
                            
        except Exception as e:
            logger.error(f"Packet processing error: {e}")
            
    def _monitor_loop(self):
        """Check for offline devices"""
        while self.running:
            time.sleep(5)
            
            try:
                with self.lock:
                    current_time = time.time()
                    for device_id, device in self.devices.items():
                        if device.online and (current_time - device.last_seen) > self.DEVICE_TIMEOUT:
                            logger.info(f"PixelBlaze {device_id} went offline")
                            device.online = False
                            device.api_connected = False
                            if self.fleet:
                                self.fleet.remove_device(device_id)
                            self.update_queue.put(device.to_dict())
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                
    def _api_loop(self):
        """Update device info via API"""
        if not self.fleet:
            return
            
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def update_loop():
            while self.running:
                try:
                    await self.fleet.update_all()
                    
                    with self.lock:
                        for device_id, api in self.fleet.devices.items():
                            if device_id in self.devices:
                                device = self.devices[device_id]
                                state = api.state
                                
                                device.name = state.name
                                device.current_pattern = state.current_pattern_name
                                device.brightness = state.brightness
                                device.fps = state.fps
                                device.api_connected = api.connected
                                
                                device.patterns = [
                                    {"id": p.id, "name": p.name} 
                                    for p in state.patterns
                                ]
                                
                                # Check provisioning status
                                if not device.provisioned:
                                    # Check if IQE patterns exist
                                    has_iqe_patterns = any(
                                        "IQE" in p.name 
                                        for p in state.patterns
                                    )
                                    if has_iqe_patterns:
                                        device.provisioned = True
                                        device.provision_date = time.time()
                                        self.provisioning_manager.mark_provisioned(device_id)
                                
                                self.update_queue.put(device.to_dict())
                    
                    await asyncio.sleep(self.API_UPDATE_INTERVAL)
                    
                except Exception as e:
                    logger.error(f"API update error: {e}")
                    await asyncio.sleep(5)
        
        loop.run_until_complete(update_loop())
        loop.close()
                        
    def _broadcast_loop(self):
        """Handle async broadcasts from queue"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def process_updates():
            while self.running:
                try:
                    try:
                        device_dict = self.update_queue.get(timeout=0.1)
                        logger.debug(f"Broadcasting device update: {device_dict.get('id', 'unknown')}")
                        await self.connection_manager.broadcast({
                            "type": "device_update",
                            "device": device_dict
                        })
                        logger.debug(f"Broadcast complete for device {device_dict.get('id', 'unknown')}")
                    except queue.Empty:
                        await asyncio.sleep(0.1)
                except Exception as e:
                    logger.error(f"Broadcast error: {e}", exc_info=True)
                    await asyncio.sleep(0.1)
        
        loop.run_until_complete(process_updates())
        loop.close()
        
    def get_devices(self):
        """Get all discovered devices"""
        with self.lock:
            return [device.to_dict() for device in self.devices.values()]
            
    async def sync_pulse(self, duration: float = 5.0):
        """Trigger synchronized pulse on all devices"""
        if not self.fleet:
            logger.error("Fleet API not available")
            return False
            
        try:
            # Save current states
            self.saved_states = {}
            for device_id, api in self.fleet.devices.items():
                if api.connected:
                    self.saved_states[device_id] = api.state.current_pattern_id
            
            # Get sync pulse pattern
            pattern = get_pattern("sync_pulse")
            if not pattern:
                logger.error("Sync pulse pattern not found")
                return False
            
            # Random color for this pulse
            hue = random.random()
            code = pattern["code"].replace("export var hue = 0.5", f"export var hue = {hue}")
            
            # Upload to all devices
            pattern_ids = await self.fleet.upload_to_all(pattern["name"], code)
            
            # Activate pattern on all devices
            tasks = []
            for device_id, pattern_id in pattern_ids.items():
                api = self.fleet.devices.get(device_id)
                if api:
                    tasks.append(api.set_pattern(pattern_id))
            
            await asyncio.gather(*tasks, return_exceptions=True)
            
            logger.info(f"Sync pulse started on {len(pattern_ids)} devices with hue {hue:.2f}")
            
            # Schedule restoration
            asyncio.create_task(self._restore_patterns(duration))
            
            return True
            
        except Exception as e:
            logger.error(f"Sync pulse error: {e}")
            return False
            
    async def _restore_patterns(self, delay: float):
        """Restore original patterns after delay"""
        await asyncio.sleep(delay)
        
        if not self.fleet:
            return
            
        tasks = []
        for device_id, pattern_id in self.saved_states.items():
            api = self.fleet.devices.get(device_id)
            if api and api.connected:
                tasks.append(api.set_pattern(pattern_id))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Restored original patterns")


# Check for force provision flag early (module level)
import sys
force_provision_flag = "--force-provision" in sys.argv

# Global instances - initialized at module level
manager = ConnectionManager()
provisioning = ProvisioningManager(force_provision=force_provision_flag)
discovery = PixelBlazeDiscovery(manager, provisioning)

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    provisioning.start()
    discovery.start()
    logger.info("PixelBlaze Fleet Monitor started with auto-provisioning")
    yield
    discovery.stop()
    provisioning.stop()

# Create FastAPI app at module level
app = FastAPI(
    title="PixelBlaze Fleet Monitor",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Complete HTML with all features
COMPLETE_HTML = '''
<!DOCTYPE html>
<html>
<head>
<title>PB Fleet</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding:8px}
h1{color:#fff;text-align:center;font-size:1.3rem;margin-bottom:10px}
.controls{background:#fff;border-radius:8px;padding:10px;margin-bottom:10px;box-shadow:0 4px 6px rgba(0,0,0,0.1)}
.controls button{background:#667eea;color:#fff;border:none;padding:10px 14px;border-radius:6px;font-size:13px;font-weight:500;margin:4px}
.controls button:active{transform:scale(0.98)}
.sync-btn{background:#e53e3e!important}
.sync-btn:active{background:#48bb78!important}
.status{text-align:center;color:#666;font-size:12px;margin-top:8px}
.status.connected{color:#48bb78}
.devices{display:flex;flex-direction:column;gap:10px}
.device{background:#fff;border-radius:8px;padding:12px;box-shadow:0 4px 6px rgba(0,0,0,0.1);position:relative}
.device.offline{opacity:0.5;background:#f5f5f5}
.device.unprovisioned{border-left:4px solid #f6ad55}
.device-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:8px}
.device-name{font-size:15px;font-weight:600;color:#333}
.device-status{width:10px;height:10px;border-radius:50%}
.device-status.online{background:#48bb78;animation:pulse 2s infinite}
.device-status.offline{background:#f56565}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(72,187,120,0.7)}70%{box-shadow:0 0 0 8px rgba(72,187,120,0)}100%{box-shadow:0 0 0 0 rgba(72,187,120,0)}}
.device-info{font-size:12px;line-height:1.5;color:#666}
.device-row{display:flex;justify-content:space-between;margin:2px 0}
.device-ip{font-family:monospace;background:#f0f0f0;padding:2px 4px;border-radius:3px;font-size:11px}
.pattern-select{width:100%;padding:6px;margin-top:6px;border:1px solid #ddd;border-radius:4px;font-size:12px;background:#fff}
.pattern-current{background:#e6fffa;font-weight:600}
.brightness{display:flex;align-items:center;gap:8px;margin-top:6px}
.brightness input{flex:1}
.provision-badge{background:#f6ad55;color:#fff;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:600}
.no-devices{text-align:center;color:#fff;padding:20px;background:rgba(255,255,255,0.1);border-radius:8px}
</style>
</head>
<body>
<h1>🌟 PixelBlaze Fleet</h1>
<div class="controls">
<button onclick="syncPulse()" class="sync-btn">🔴 Sync Pulse</button>
<button onclick="scan()">Scan</button>
<button onclick="refresh()">Refresh</button>
<div class="status" id="status">Connecting...</div>
</div>
<div id="devices" class="devices">
<div class="no-devices">Searching for PixelBlaze devices...</div>
</div>
<script>
let ws=null,devices=new Map();

function connect(){
ws=new WebSocket((location.protocol==='https:'?'wss:':'ws:')+'//'+location.host+'/ws');
ws.onopen=()=>{
document.getElementById('status').innerHTML='Connected ✓';
document.getElementById('status').className='status connected';
ws.send(JSON.stringify({type:'get_devices'}));
};
ws.onmessage=(e)=>{
const data=JSON.parse(e.data);
if(data.type==='device_update')updateDevice(data.device);
else if(data.type==='devices_list')data.devices.forEach(d=>updateDevice(d));
};
ws.onerror=()=>console.error('WS error');
ws.onclose=()=>{
document.getElementById('status').innerHTML='Reconnecting...';
document.getElementById('status').className='status';
setTimeout(connect,2000);
};
}

function updateDevice(d){
devices.set(d.id,d);
render();
}

function render(){
const c=document.getElementById('devices');
if(devices.size===0){
c.innerHTML='<div class="no-devices">Searching for PixelBlaze devices...</div>';
return;
}
const sorted=Array.from(devices.values()).sort((a,b)=>{
if(a.online!==b.online)return b.online-a.online;
return a.name.localeCompare(b.name);
});
c.innerHTML=sorted.map(d=>`
<div class="device ${d.online?'':'offline'} ${!d.provisioned?'unprovisioned':''}">
<div class="device-header">
<div>
<span class="device-name">${d.name||d.id}</span>
${!d.provisioned?'<span class="provision-badge">NEW</span>':''}
</div>
<div class="device-status ${d.online?'online':'offline'}"></div>
</div>
<div class="device-info">
<div class="device-row">
<span>IP:</span><span class="device-ip">${d.ip}</span>
</div>
<div class="device-row">
<span>Pattern:</span><span style="font-weight:500">${d.current_pattern||'---'}</span>
</div>
${d.provisioned?`<div class="device-row">
<span>Provisioned:</span><span>${d.provision_date_formatted||'Yes'}</span>
</div>`:'<div class="device-row" style="color:#f6ad55">
<span>Status:</span><span>Provisioning...</span>
</div>'}
${d.patterns&&d.patterns.length?`
<select class="pattern-select" onchange="setPattern('${d.id}',this.value)">
<option value="">-- Select Pattern --</option>
${d.patterns.map(p=>`
<option value="${p.id}" ${p.name===d.current_pattern?'selected class="pattern-current"':''}>${p.name}</option>
`).join('')}
</select>
`:''}
<div class="brightness">
<span>Bright:</span>
<input type="range" min="0" max="100" value="${Math.round((d.brightness||0.5)*100)}" 
onchange="setBrightness('${d.id}',this.value/100)">
<span>${Math.round((d.brightness||0.5)*100)}%</span>
</div>
</div>
</div>
`).join('');
}

function syncPulse(){
if(ws&&ws.readyState===1){
ws.send(JSON.stringify({type:'sync_pulse'}));
document.querySelector('.sync-btn').style.background='#48bb78';
setTimeout(()=>{
document.querySelector('.sync-btn').style.background='#e53e3e';
},5000);
}
}

function setPattern(deviceId,patternId){
if(ws&&ws.readyState===1&&patternId){
ws.send(JSON.stringify({type:'set_pattern',device_id:deviceId,pattern_id:patternId}));
}
}

function setBrightness(deviceId,brightness){
if(ws&&ws.readyState===1){
ws.send(JSON.stringify({type:'set_brightness',device_id:deviceId,brightness:brightness}));
}
}

function scan(){if(ws&&ws.readyState===1)ws.send(JSON.stringify({type:'scan'}));}
function refresh(){if(ws&&ws.readyState===1)ws.send(JSON.stringify({type:'get_devices'}));}

connect();
setInterval(refresh,10000);

// Also poll the API endpoint as fallback
setInterval(async () => {
    try {
        const response = await fetch('/api/devices');
        const data = await response.json();
        if (data.devices) {
            data.devices.forEach(d => updateDevice(d));
        }
    } catch (e) {
        console.error('API poll error:', e);
    }
}, 5000);
</script>
</body>
</html>
'''


@app.get("/", response_class=HTMLResponse)
async def index():
    return COMPLETE_HTML

@app.get("/api/devices")
async def get_devices():
    """API endpoint to get all devices"""
    devices = discovery.get_devices()
    logger.info(f"API request for devices, returning {len(devices)} devices")
    return {"devices": devices, "count": len(devices)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    # Send initial devices
    await websocket.send_json({
        "type": "devices_list",
        "devices": discovery.get_devices()
    })
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "get_devices":
                await websocket.send_json({
                    "type": "devices_list",
                    "devices": discovery.get_devices()
                })
                
            elif data.get("type") == "sync_pulse":
                # Trigger synchronized pulse
                if discovery.fleet:
                    success = await discovery.sync_pulse()
                    await websocket.send_json({
                        "type": "sync_pulse_response",
                        "success": success
                    })
                else:
                    logger.warning("Fleet API not available for sync pulse")
                
            elif data.get("type") == "set_pattern":
                # Set pattern on specific device
                if discovery.fleet:
                    device_id = data.get("device_id")
                    pattern_id = data.get("pattern_id")
                    if device_id in discovery.fleet.devices:
                        api = discovery.fleet.devices[device_id]
                        if api.connected:
                            await api.set_pattern(pattern_id)
                        
            elif data.get("type") == "set_brightness":
                # Set brightness on specific device
                if discovery.fleet:
                    device_id = data.get("device_id")
                    brightness = data.get("brightness", 0.5)
                    if device_id in discovery.fleet.devices:
                        api = discovery.fleet.devices[device_id]
                        if api.connected:
                            await api.set_brightness(brightness)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    # Parse command line arguments
    is_pi = platform.machine().startswith('arm') or os.path.exists('/proc/device-tree/model')
    dev_mode = "--dev" in sys.argv
    force_provision = "--force-provision" in sys.argv
    
    logger.info("Starting PixelBlaze Fleet Monitor with Auto-Provisioning")
    if force_provision or force_provision_flag:
        logger.info("FORCE PROVISION MODE - All devices will be re-provisioned")
    logger.info(f"Platform: {platform.system()} on {platform.machine()}")
    logger.info("Access at http://localhost:8000")
    
    if is_pi and not dev_mode:
        # Pi optimized settings
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="warning",
            access_log=False,
            loop="asyncio",
            limit_concurrency=10
        )
    elif dev_mode:
        uvicorn.run(
            "pbfleet:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    else:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )