#!/usr/bin/env python3
"""
PixelBlaze Fleet Monitor - Cleaned and Improved Version
Real-time monitoring and control for PixelBlaze LED controllers
"""

import asyncio
import json
import logging
import os
import platform
import signal
import socket
import sys
import threading
import time
from contextlib import asynccontextmanager, closing
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from collections import deque

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Configure logging with rotation support
logging.basicConfig(
    level=logging.getLevelName(os.environ.get('PB_LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            'pbfleet.log', maxBytes=10*1024*1024, backupCount=3
        ) if os.environ.get('PB_LOG_FILE') else logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    'DISCOVERY_PORT': int(os.environ.get('PB_DISCOVERY_PORT', 1889)),
    'WEB_PORT': int(os.environ.get('PB_FLEET_PORT', 8000)),
    'WEB_HOST': os.environ.get('PB_FLEET_HOST', '0.0.0.0'),
    'DEVICE_TIMEOUT': float(os.environ.get('PB_DEVICE_TIMEOUT', 30.0)),
    'API_UPDATE_INTERVAL': float(os.environ.get('PB_API_UPDATE_INTERVAL', 10.0)),
    'MAX_QUEUE_SIZE': int(os.environ.get('PB_MAX_QUEUE_SIZE', 1000)),
    'PROVISION_STATE_FILE': Path(os.environ.get('PB_STATE_FILE', 'provisioned_devices.json')),
}

@dataclass
class PixelBlazeDevice:
    """Device information with thread-safe access"""
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
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            **asdict(self),
            'last_seen_formatted': datetime.fromtimestamp(self.last_seen).strftime('%H:%M:%S') if self.last_seen else 'Never',
            'provision_date_formatted': datetime.fromtimestamp(self.provision_date).strftime('%Y-%m-%d %H:%M:%S') if self.provision_date else None
        }


class ThreadSafeDeviceStore:
    """Thread-safe storage for device information"""
    
    def __init__(self):
        self._devices: Dict[str, PixelBlazeDevice] = {}
        self._lock = threading.RLock()
    
    def get(self, device_id: str) -> Optional[PixelBlazeDevice]:
        """Get device by ID"""
        with self._lock:
            return self._devices.get(device_id)
    
    def set(self, device_id: str, device: PixelBlazeDevice) -> None:
        """Set or update device"""
        with self._lock:
            self._devices[device_id] = device
    
    def remove(self, device_id: str) -> bool:
        """Remove device"""
        with self._lock:
            if device_id in self._devices:
                del self._devices[device_id]
                return True
            return False
    
    def get_all(self) -> List[PixelBlazeDevice]:
        """Get all devices"""
        with self._lock:
            return list(self._devices.values())
    
    def get_all_dicts(self) -> List[dict]:
        """Get all devices as dictionaries"""
        with self._lock:
            return [d.to_dict() for d in self._devices.values()]
    
    def exists(self, device_id: str) -> bool:
        """Check if device exists"""
        with self._lock:
            return device_id in self._devices
    
    def update_last_seen(self, device_id: str, timestamp: float) -> bool:
        """Update device last seen time"""
        with self._lock:
            if device_id in self._devices:
                self._devices[device_id].last_seen = timestamp
                self._devices[device_id].online = True
                return True
            return False
    
    def mark_offline(self, device_id: str) -> bool:
        """Mark device as offline"""
        with self._lock:
            if device_id in self._devices:
                self._devices[device_id].online = False
                self._devices[device_id].api_connected = False
                return True
            return False


class ConnectionManager:
    """WebSocket connection manager with proper cleanup"""
    
    def __init__(self):
        self._connections: Set[WebSocket] = set()
        self._lock = threading.Lock()
    
    async def connect(self, websocket: WebSocket):
        """Accept and track new connection"""
        await websocket.accept()
        with self._lock:
            self._connections.add(websocket)
        logger.info(f"Client connected. Total: {len(self._connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove connection"""
        with self._lock:
            self._connections.discard(websocket)
        logger.info(f"Client disconnected. Total: {len(self._connections)}")
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        with self._lock:
            connections = list(self._connections)
        
        if not connections:
            return
        
        # Send to all connections concurrently
        tasks = []
        for conn in connections:
            tasks.append(self._send_safe(conn, message))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Remove failed connections
        disconnected = [conn for conn, result in zip(connections, results) if result is False]
        if disconnected:
            with self._lock:
                for conn in disconnected:
                    self._connections.discard(conn)
    
    async def _send_safe(self, websocket: WebSocket, message: dict) -> bool:
        """Send message to single connection safely"""
        try:
            await websocket.send_json(message)
            return True
        except Exception:
            return False
    
    def close_all(self):
        """Close all connections"""
        with self._lock:
            self._connections.clear()


class ProvisioningManager:
    """Manages device provisioning with persistence"""
    
    def __init__(self, force_provision: bool = False):
        self.force_provision = force_provision
        self.provisioned_devices = self._load_state() if not force_provision else set()
        self._lock = threading.Lock()
        
        if force_provision:
            logger.info("Force provisioning mode enabled")
    
    def _load_state(self) -> Set[str]:
        """Load provisioned device IDs from file"""
        try:
            if CONFIG['PROVISION_STATE_FILE'].exists():
                with open(CONFIG['PROVISION_STATE_FILE'], 'r') as f:
                    data = json.load(f)
                    return set(data.get('provisioned_devices', []))
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load provision state: {e}")
        return set()
    
    def _save_state(self):
        """Save provisioned device IDs to file"""
        try:
            # Atomic write with temp file
            temp_file = CONFIG['PROVISION_STATE_FILE'].with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump({
                    'provisioned_devices': list(self.provisioned_devices),
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
            temp_file.replace(CONFIG['PROVISION_STATE_FILE'])
        except (IOError, OSError) as e:
            logger.error(f"Failed to save provision state: {e}")
    
    def is_provisioned(self, device_id: str) -> bool:
        """Check if device has been provisioned"""
        with self._lock:
            return device_id in self.provisioned_devices
    
    def mark_provisioned(self, device_id: str):
        """Mark device as provisioned"""
        with self._lock:
            self.provisioned_devices.add(device_id)
            self._save_state()
        logger.info(f"Device {device_id} marked as provisioned")


class PixelBlazeDiscovery:
    """UDP discovery service with proper resource management"""
    
    def __init__(self, device_store: ThreadSafeDeviceStore, 
                 connection_manager: ConnectionManager,
                 provisioning_manager: ProvisioningManager):
        self.device_store = device_store
        self.connection_manager = connection_manager
        self.provisioning_manager = provisioning_manager
        self.running = False
        self._threads = []
        self._socket = None
        self._update_queue = asyncio.Queue(maxsize=CONFIG['MAX_QUEUE_SIZE'])
    
    def start(self):
        """Start discovery service"""
        self.running = True
        
        # Start threads
        self._threads = [
            threading.Thread(target=self._discovery_loop, daemon=True, name="Discovery"),
            threading.Thread(target=self._monitor_loop, daemon=True, name="Monitor"),
        ]
        
        for thread in self._threads:
            thread.start()
        
        # Start async broadcast task
        asyncio.create_task(self._broadcast_loop())
        
        logger.info("Discovery service started")
    
    def stop(self):
        """Stop discovery service"""
        self.running = False
        if self._socket:
            try:
                self._socket.close()
            except:
                pass
        logger.info("Discovery service stopped")
    
    def _discovery_loop(self):
        """UDP discovery listener with proper socket management"""
        while self.running:
            try:
                with closing(socket.socket(socket.AF_INET, socket.SOCK_DGRAM)) as sock:
                    self._socket = sock
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sock.settimeout(1.0)
                    sock.bind(('', CONFIG['DISCOVERY_PORT']))
                    
                    logger.info(f"Listening on UDP port {CONFIG['DISCOVERY_PORT']}")
                    
                    while self.running:
                        try:
                            data, addr = sock.recvfrom(1024)
                            self._process_discovery_packet(data, addr[0])
                        except socket.timeout:
                            continue
                        except OSError as e:
                            if self.running:
                                logger.error(f"Socket error: {e}")
                                break
            except Exception as e:
                if self.running:
                    logger.error(f"Discovery loop error: {e}")
                    time.sleep(5)  # Retry after delay
    
    def _process_discovery_packet(self, data: bytes, ip: str):
        """Process discovery packet"""
        try:
            if len(data) < 6:
                return
            
            device_id = data[:6].hex()
            current_time = time.time()
            
            # Check if new device
            if not self.device_store.exists(device_id):
                logger.info(f"New PixelBlaze discovered: {device_id} at {ip}")
                
                device = PixelBlazeDevice(
                    id=device_id,
                    ip=ip,
                    name=f"PB_{device_id[-4:]}",
                    last_seen=current_time,
                    online=True,
                    provisioned=self.provisioning_manager.is_provisioned(device_id)
                )
                
                self.device_store.set(device_id, device)
                
                # Queue update
                asyncio.run_coroutine_threadsafe(
                    self._queue_update(device.to_dict()),
                    asyncio.get_event_loop()
                )
            else:
                # Update existing device
                device = self.device_store.get(device_id)
                if device:
                    was_offline = not device.online
                    device.ip = ip
                    device.last_seen = current_time
                    device.online = True
                    
                    if was_offline:
                        logger.info(f"PixelBlaze {device_id} back online")
                        asyncio.run_coroutine_threadsafe(
                            self._queue_update(device.to_dict()),
                            asyncio.get_event_loop()
                        )
        
        except Exception as e:
            logger.error(f"Packet processing error: {e}")
    
    def _monitor_loop(self):
        """Monitor devices for timeout"""
        while self.running:
            try:
                current_time = time.time()
                
                for device in self.device_store.get_all():
                    if device.online and (current_time - device.last_seen) > CONFIG['DEVICE_TIMEOUT']:
                        logger.info(f"Device {device.id} went offline")
                        self.device_store.mark_offline(device.id)
                        
                        asyncio.run_coroutine_threadsafe(
                            self._queue_update(device.to_dict()),
                            asyncio.get_event_loop()
                        )
                
                time.sleep(5)
            
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                time.sleep(5)
    
    async def _queue_update(self, device_dict: dict):
        """Queue device update for broadcast"""
        try:
            await asyncio.wait_for(
                self._update_queue.put(device_dict),
                timeout=1.0
            )
        except asyncio.TimeoutError:
            logger.warning("Update queue full, dropping update")
    
    async def _broadcast_loop(self):
        """Process update queue and broadcast to clients"""
        while self.running:
            try:
                # Get update from queue
                device_dict = await asyncio.wait_for(
                    self._update_queue.get(),
                    timeout=1.0
                )
                
                # Broadcast to all clients
                await self.connection_manager.broadcast({
                    "type": "device_update",
                    "device": device_dict
                })
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                await asyncio.sleep(0.1)


# HTML UI (minified version)
HTML_UI = '''<!DOCTYPE html>
<html><head><title>PB Fleet</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui;background:linear-gradient(135deg,#667eea,#764ba2);min-height:100vh;padding:1rem}
.container{max-width:1200px;margin:0 auto}
h1{color:#fff;text-align:center;margin-bottom:1rem}
.controls{background:#fff;border-radius:8px;padding:1rem;margin-bottom:1rem}
.btn{background:#667eea;color:#fff;border:none;padding:0.5rem 1rem;border-radius:4px;cursor:pointer;margin:0.25rem}
.btn:hover{opacity:0.9}
.status{text-align:center;margin-top:0.5rem;color:#666}
.status.connected{color:#48bb78}
.devices{display:grid;gap:1rem;grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}
.device{background:#fff;border-radius:8px;padding:1rem;position:relative}
.device.offline{opacity:0.5}
.device-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem}
.device-status{width:10px;height:10px;border-radius:50%;background:#f56565}
.device-status.online{background:#48bb78}
.device-info{font-size:0.875rem;color:#666}
.no-devices{text-align:center;color:#fff;padding:2rem}
</style></head><body>
<div class="container">
<h1>PixelBlaze Fleet Monitor</h1>
<div class="controls">
<button class="btn" onclick="refresh()">Refresh</button>
<div class="status" id="status">Connecting...</div>
</div>
<div id="devices" class="devices">
<div class="no-devices">Searching for devices...</div>
</div>
</div>
<script>
let ws,devices=new Map();
function connect(){
ws=new WebSocket((location.protocol==='https:'?'wss:':'ws:')+'//'+location.host+'/ws');
ws.onopen=()=>{
document.getElementById('status').textContent='Connected';
document.getElementById('status').className='status connected';
};
ws.onmessage=(e)=>{
const data=JSON.parse(e.data);
if(data.type==='device_update')updateDevice(data.device);
else if(data.type==='devices_list')data.devices.forEach(d=>updateDevice(d));
};
ws.onerror=()=>console.error('WebSocket error');
ws.onclose=()=>{
document.getElementById('status').textContent='Reconnecting...';
document.getElementById('status').className='status';
setTimeout(connect,2000);
};
}
function updateDevice(d){devices.set(d.id,d);render();}
function render(){
const c=document.getElementById('devices');
if(devices.size===0){
c.innerHTML='<div class="no-devices">No devices found</div>';
return;
}
c.innerHTML=Array.from(devices.values()).map(d=>`
<div class="device ${d.online?'':'offline'}">
<div class="device-header">
<strong>${d.name}</strong>
<div class="device-status ${d.online?'online':''}"></div>
</div>
<div class="device-info">
<div>ID: ${d.id}</div>
<div>IP: ${d.ip}</div>
<div>Pattern: ${d.current_pattern||'N/A'}</div>
<div>Brightness: ${Math.round(d.brightness*100)}%</div>
${d.provisioned?'<div>✓ Provisioned</div>':'<div>⏳ Provisioning...</div>'}
</div>
</div>`).join('');
}
function refresh(){if(ws&&ws.readyState===1)ws.send(JSON.stringify({type:'get_devices'}));}
connect();
setInterval(refresh,10000);
</script></body></html>'''


# Global instances
manager = ConnectionManager()
provisioning = ProvisioningManager(force_provision="--force-provision" in sys.argv)
device_store = ThreadSafeDeviceStore()
discovery = PixelBlazeDiscovery(device_store, manager, provisioning)

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    discovery.start()
    logger.info(f"PixelBlaze Fleet Monitor started on {CONFIG['WEB_HOST']}:{CONFIG['WEB_PORT']}")
    yield
    discovery.stop()
    manager.close_all()
    logger.info("Shutdown complete")

# Create FastAPI app
app = FastAPI(
    title="PixelBlaze Fleet Monitor",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if os.environ.get('PB_ENABLE_DOCS') else None
)

# Configure CORS
allowed_origins = os.environ.get(
    'CORS_ORIGINS', 
    'http://localhost:*,http://127.0.0.1:*,http://192.168.*:*,http://10.*:*'
).split(',')

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve web UI"""
    return HTML_UI

@app.get("/api/devices")
async def get_devices():
    """Get all devices via REST API"""
    devices = device_store.get_all_dicts()
    return {"devices": devices, "count": len(devices)}

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "devices": len(device_store.get_all()),
        "connections": len(manager._connections),
        "uptime": time.time()
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    
    try:
        # Send initial devices after short delay
        await asyncio.sleep(0.5)
        devices = device_store.get_all_dicts()
        await websocket.send_json({
            "type": "devices_list",
            "devices": devices
        })
        
        # Handle incoming messages
        while True:
            try:
                data = await websocket.receive_json()
                
                if data.get("type") == "get_devices":
                    await websocket.send_json({
                        "type": "devices_list",
                        "devices": device_store.get_all_dicts()
                    })
                
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received from client")
            
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)


def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("Shutdown signal received")
    sys.exit(0)


if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Parse arguments
    dev_mode = "--dev" in sys.argv
    
    # Log startup info
    logger.info(f"Starting PixelBlaze Fleet Monitor v2.0")
    logger.info(f"Platform: {platform.system()} {platform.machine()}")
    
    # Run server
    uvicorn.run(
        "pbfleet_clean:app" if dev_mode else app,
        host=CONFIG['WEB_HOST'],
        port=CONFIG['WEB_PORT'],
        reload=dev_mode,
        log_level="info" if dev_mode else "warning",
        access_log=dev_mode
    )