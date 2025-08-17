#!/usr/bin/env python3
"""
PixelBlaze Fleet Monitor - Raspberry Pi Zero Optimized
Lightweight version for resource-constrained devices
Works on Pi Zero W and other ARM devices
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
from contextlib import asynccontextmanager
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class PixelBlazeDevice:
    """Represents a discovered PixelBlaze device"""
    id: str
    ip: str
    name: str = "Unknown"
    last_seen: float = 0
    online: bool = False
    
    def to_dict(self):
        return {
            **asdict(self),
            'last_seen_formatted': datetime.fromtimestamp(self.last_seen).strftime('%H:%M:%S')
        }


class ConnectionManager:
    """Lightweight WebSocket connection manager"""
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
        
        # Clean up disconnected clients
        if disconnected:
            with self.lock:
                for conn in disconnected:
                    if conn in self.active_connections:
                        self.active_connections.remove(conn)


class PixelBlazeDiscovery:
    """Lightweight discovery for PixelBlaze devices"""
    
    DISCOVERY_PORT = 1889
    DEVICE_TIMEOUT = 30.0
    
    def __init__(self, connection_manager: ConnectionManager):
        self.devices: Dict[str, PixelBlazeDevice] = {}
        self.lock = threading.Lock()
        self.running = False
        self.discovery_thread = None
        self.monitor_thread = None
        self.broadcast_thread = None
        self.connection_manager = connection_manager
        self.update_queue = queue.Queue()
        
    def start(self):
        """Start discovery and monitoring threads"""
        self.running = True
        self.discovery_thread = threading.Thread(target=self._discovery_loop, daemon=True)
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self.discovery_thread.start()
        self.monitor_thread.start()
        self.broadcast_thread.start()
        logger.info("PixelBlaze discovery started")
        
    def stop(self):
        """Stop discovery and monitoring"""
        self.running = False
        if self.discovery_thread:
            self.discovery_thread.join(timeout=2)
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        if self.broadcast_thread:
            self.broadcast_thread.join(timeout=2)
            
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
        """Process discovery packet"""
        try:
            if len(data) >= 6:
                device_id = data[:6].hex()
                
                with self.lock:
                    is_new = device_id not in self.devices
                    
                    if is_new:
                        logger.info(f"New PixelBlaze: {device_id} at {ip}")
                        device = PixelBlazeDevice(
                            id=device_id,
                            ip=ip,
                            name=f"PB_{device_id[-4:]}",
                            last_seen=time.time(),
                            online=True
                        )
                        self.devices[device_id] = device
                    else:
                        device = self.devices[device_id]
                        was_offline = not device.online
                        device.ip = ip
                        device.last_seen = time.time()
                        device.online = True
                        
                        if was_offline:
                            logger.info(f"PixelBlaze {device_id} back online")
                    
                    # Queue update for async broadcast
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
                            # Queue update for async broadcast
                            self.update_queue.put(device.to_dict())
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                        
    def _broadcast_loop(self):
        """Thread to handle async broadcasts from queue"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def process_updates():
            while self.running:
                try:
                    # Check for updates with timeout
                    try:
                        device_dict = self.update_queue.get(timeout=0.1)
                        await self.connection_manager.broadcast({
                            "type": "device_update",
                            "device": device_dict
                        })
                    except queue.Empty:
                        await asyncio.sleep(0.1)
                except Exception as e:
                    logger.error(f"Broadcast error: {e}")
                    await asyncio.sleep(0.1)
        
        loop.run_until_complete(process_updates())
        loop.close()
        
    def get_devices(self):
        """Get all discovered devices"""
        with self.lock:
            return [device.to_dict() for device in self.devices.values()]


def get_network_info():
    """Get network info that works on Pi and other Linux systems"""
    try:
        # Try to get a real network IP by connecting to a public DNS
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        try:
            # Connect to Google DNS (doesn't actually send data)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip, '.'.join(local_ip.split('.')[:-1])
        except:
            s.close()
    except:
        pass
    
    # Fallback for Linux systems
    try:
        import subprocess
        
        # Try ip command (modern Linux)
        try:
            result = subprocess.run(
                ['ip', 'addr', 'show'], 
                capture_output=True, 
                text=True, 
                timeout=2
            )
            import re
            # Look for inet addresses (not localhost)
            for line in result.stdout.split('\n'):
                match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', line)
                if match:
                    ip = match.group(1)
                    if not ip.startswith('127.'):
                        return ip, '.'.join(ip.split('.')[:-1])
        except:
            pass
        
        # Try ifconfig (older Linux/Unix)
        try:
            result = subprocess.run(
                ['ifconfig'], 
                capture_output=True, 
                text=True, 
                timeout=2
            )
            import re
            ips = re.findall(r'inet (?:addr:)?(\d+\.\d+\.\d+\.\d+)', result.stdout)
            for ip in ips:
                if not ip.startswith('127.'):
                    return ip, '.'.join(ip.split('.')[:-1])
        except:
            pass
    except:
        pass
    
    # Final fallback
    return "192.168.0.1", "192.168.0"


# Global instances
manager = ConnectionManager()
discovery = PixelBlazeDiscovery(manager)

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    discovery.start()
    
    # Log system info
    logger.info(f"Platform: {platform.machine()} - {platform.system()}")
    local_ip, subnet = get_network_info()
    logger.info(f"Network: {local_ip} (subnet: {subnet}.0/24)")
    
    yield
    
    # Shutdown
    discovery.stop()

# Create FastAPI app
app = FastAPI(
    title="PixelBlaze Fleet Monitor", 
    lifespan=lifespan,
    docs_url=None,  # Disable docs to save memory
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

# Minimal mobile HTML
MOBILE_HTML = '''
<!DOCTYPE html>
<html>
<head>
<title>PB Monitor</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;padding:8px}
.container{max-width:100%;margin:0 auto}
h1{color:#fff;text-align:center;font-size:1.3rem;margin-bottom:10px;text-shadow:1px 1px 2px rgba(0,0,0,0.2)}
.controls{background:#fff;border-radius:6px;padding:10px;margin-bottom:10px;box-shadow:0 2px 4px rgba(0,0,0,0.1);display:flex;gap:8px;flex-wrap:wrap}
.controls button{background:#667eea;color:#fff;border:none;padding:8px 12px;border-radius:4px;font-size:13px;font-weight:500;flex:1;min-width:80px}
.controls button:active{background:#5a67d8;transform:scale(0.98)}
.status{flex:1 100%;text-align:center;color:#666;font-size:12px;margin-top:4px}
.status.connected{color:#48bb78;font-weight:500}
.devices{display:flex;flex-direction:column;gap:8px}
.device{background:#fff;border-radius:6px;padding:10px;box-shadow:0 2px 4px rgba(0,0,0,0.1);position:relative}
.device.offline{opacity:0.6;background:#f9f9f9}
.device-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
.device-name{font-size:14px;font-weight:600;color:#333}
.device-status{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.device-status.online{background:#48bb78;animation:pulse 2s infinite}
.device-status.offline{background:#f56565}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(72,187,120,0.7)}70%{box-shadow:0 0 0 6px rgba(72,187,120,0)}100%{box-shadow:0 0 0 0 rgba(72,187,120,0)}}
.device-info{color:#666;font-size:12px;line-height:1.4}
.device-row{display:flex;justify-content:space-between;margin-bottom:2px}
.device-ip{font-family:monospace;font-size:13px;background:#f0f0f0;padding:1px 4px;border-radius:3px}
.device-id{font-family:monospace;font-size:10px;color:#999}
.no-devices{text-align:center;color:#fff;padding:20px;background:rgba(255,255,255,0.1);border-radius:6px;font-size:13px}
.new{animation:slideIn 0.3s ease-out}
@keyframes slideIn{from{opacity:0;transform:translateY(-10px)}to{opacity:1;transform:translateY(0)}}
@media(max-width:320px){body{padding:6px}h1{font-size:1.2rem}.controls button{font-size:12px;padding:6px 10px}}
</style>
</head>
<body>
<div class="container">
<h1>PixelBlaze Monitor</h1>
<div class="controls">
<button onclick="scan()">Scan</button>
<button onclick="refresh()">Refresh</button>
<div class="status" id="status">Connecting...</div>
</div>
<div id="devices" class="devices">
<div class="no-devices">Searching for devices...</div>
</div>
</div>
<script>
let ws=null,devices=new Map(),reconnectTimer=null;
function connect(){
const wsUrl=(location.protocol==='https:'?'wss:':'ws:')+'//'+location.host+'/ws';
ws=new WebSocket(wsUrl);
ws.onopen=()=>{
document.getElementById('status').innerHTML='Connected ✓';
document.getElementById('status').className='status connected';
if(reconnectTimer){clearTimeout(reconnectTimer);reconnectTimer=null;}
ws.send(JSON.stringify({type:'get_devices'}));
};
ws.onmessage=(e)=>{
const data=JSON.parse(e.data);
if(data.type==='device_update'){updateDevice(data.device);}
else if(data.type==='devices_list'){data.devices.forEach(d=>updateDevice(d));}
};
ws.onerror=(e)=>console.error('WS error:',e);
ws.onclose=()=>{
document.getElementById('status').innerHTML='Reconnecting...';
document.getElementById('status').className='status';
if(!reconnectTimer){reconnectTimer=setTimeout(()=>{reconnectTimer=null;connect();},2000);}
};
}
function updateDevice(d){
const isNew=!devices.has(d.id);
devices.set(d.id,d);
render();
if(isNew&&d.online){
setTimeout(()=>{
const card=document.querySelector(`[data-id="${d.id}"]`);
if(card)card.classList.add('new');
},10);
}
}
function render(){
const c=document.getElementById('devices');
if(devices.size===0){
c.innerHTML='<div class="no-devices">Searching for devices...</div>';
return;
}
const sorted=Array.from(devices.values()).sort((a,b)=>{
if(a.online!==b.online)return b.online-a.online;
return a.id.localeCompare(b.id);
});
c.innerHTML=sorted.map(d=>`
<div class="device ${d.online?'':'offline'}" data-id="${d.id}">
<div class="device-header">
<div class="device-name">${d.name}</div>
<div class="device-status ${d.online?'online':'offline'}"></div>
</div>
<div class="device-info">
<div class="device-row">
<span>IP:</span>
<span class="device-ip">${d.ip}</span>
</div>
<div class="device-row">
<span>Status:</span>
<span>${d.online?'Online':'Offline'}</span>
</div>
<div class="device-row">
<span>Last:</span>
<span>${d.last_seen_formatted}</span>
</div>
<div class="device-id">ID: ${d.id}</div>
</div>
</div>
`).join('');
}
function scan(){
if(ws&&ws.readyState===WebSocket.OPEN){
document.getElementById('status').innerHTML='Scanning...';
ws.send(JSON.stringify({type:'scan_network'}));
setTimeout(()=>{
if(document.getElementById('status').innerHTML==='Scanning...'){
document.getElementById('status').innerHTML='Connected ✓';
}
},5000);
}
}
function refresh(){
if(ws&&ws.readyState===WebSocket.OPEN){
ws.send(JSON.stringify({type:'get_devices'}));
}
}
connect();
setInterval(refresh,10000);
let lastTouchEnd=0;
document.addEventListener('touchend',(e)=>{
const now=Date.now();
if(now-lastTouchEnd<=300){e.preventDefault();}
lastTouchEnd=now;
},false);
</script>
</body>
</html>
'''

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve dashboard"""
    return MOBILE_HTML

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint"""
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
            
            elif data.get("type") == "scan_network":
                # Network scan for Pi
                local_ip, subnet = get_network_info()
                logger.info(f"Scan requested for subnet: {subnet}")
                # Note: Active scanning disabled on Pi Zero to save resources
                # Relying on passive UDP discovery instead
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    import sys
    
    # Detect if running on Pi
    is_pi = platform.machine().startswith('arm') or os.path.exists('/proc/device-tree/model')
    
    if is_pi:
        logger.info("Running on Raspberry Pi - using optimized settings")
        # Pi optimized settings
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="warning",  # Less logging
            access_log=False,      # No access logs
            loop="asyncio",        # Explicit loop
            limit_concurrency=10   # Limit connections
        )
    else:
        # Development mode
        dev_mode = "--dev" in sys.argv
        logger.info(f"Running on {platform.system()} - dev mode: {dev_mode}")
        
        if dev_mode:
            uvicorn.run(
                "pixelblaze_monitor_pi:app",
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