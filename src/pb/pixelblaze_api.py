#!/usr/bin/env python3
"""
PixelBlaze API Client
Handles WebSocket communication with PixelBlaze devices
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any
import websockets
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

@dataclass
class PatternInfo:
    """Information about a pattern"""
    id: str
    name: str
    
@dataclass
class PixelBlazeState:
    """Current state of a PixelBlaze device"""
    name: str = "Unknown"
    current_pattern_id: str = ""
    current_pattern_name: str = ""
    brightness: float = 0.5
    fps: int = 0
    patterns: List[PatternInfo] = field(default_factory=list)
    playlist: List[str] = field(default_factory=list)
    sequencer_mode: str = "off"
    last_update: float = 0
    
    def to_dict(self):
        return {
            "name": self.name,
            "current_pattern_id": self.current_pattern_id,
            "current_pattern_name": self.current_pattern_name,
            "brightness": self.brightness,
            "fps": self.fps,
            "patterns": [{"id": p.id, "name": p.name} for p in self.patterns],
            "playlist": self.playlist,
            "sequencer_mode": self.sequencer_mode,
            "last_update": self.last_update
        }


class PixelBlazeAPI:
    """WebSocket API client for a single PixelBlaze"""
    
    def __init__(self, ip: str, port: int = 81):
        self.ip = ip
        self.port = port
        self.ws_url = f"ws://{ip}:{port}"
        self.ws = None
        self.state = PixelBlazeState()
        self.connected = False
        
    async def connect(self):
        """Connect to PixelBlaze WebSocket"""
        try:
            self.ws = await websockets.connect(self.ws_url, ping_interval=None)
            self.connected = True
            logger.info(f"Connected to PixelBlaze at {self.ip}")
            
            # Get initial state
            await self.get_config()
            await self.get_patterns()
            
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.ip}: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from PixelBlaze"""
        if self.ws:
            await self.ws.close()
            self.connected = False
            
    async def send_command(self, command: dict) -> Optional[dict]:
        """Send command and get response"""
        if not self.connected or not self.ws:
            return None
            
        try:
            await self.ws.send(json.dumps(command))
            
            # Some commands don't return responses, so timeout quickly
            try:
                response = await asyncio.wait_for(self.ws.recv(), timeout=0.5)
                
                # Try to parse as JSON
                if response:
                    try:
                        return json.loads(response)
                    except json.JSONDecodeError:
                        # Some responses are not JSON (like "ok" or binary data)
                        logger.debug(f"Non-JSON response from {self.ip}: {response[:50]}")
                        return {"raw": response}
                return None
            except asyncio.TimeoutError:
                # Many commands don't send responses, this is normal
                return None
                
        except Exception as e:
            logger.error(f"Command error for {self.ip}: {e}")
            self.connected = False
            return None
    
    async def get_config(self):
        """Get device configuration including name"""
        response = await self.send_command({"getConfig": True})
        if response:
            # The actual device name is usually in the root response
            if "name" in response:
                self.state.name = response["name"]
            elif isinstance(response, dict):
                # Sometimes it's nested
                for key, value in response.items():
                    if key == "name" and isinstance(value, str):
                        self.state.name = value
                        break
            
            self.state.brightness = response.get("brightness", 1.0)
            logger.info(f"Got config for {self.state.name} at {self.ip}")
            
    async def get_patterns(self):
        """Get list of patterns"""
        # Try the correct command - it might be getPatternList
        response = await self.send_command({"getPatternList": True})
        
        if not response or response.get("raw"):
            # Fallback to listPrograms
            response = await self.send_command({"listPrograms": True})
        
        # Log what we got back for debugging
        if response:
            logger.info(f"Pattern list response from {self.ip}: {list(response.keys())[:10] if isinstance(response, dict) else str(response)[:100]}")
        
        if response and not response.get("raw"):
            self.state.patterns = []
            
            # Skip config fields that aren't patterns
            config_fields = {"name", "brandName", "colorOrder", "timezone", "autoOffStart", "autoOffEnd", "ver", "brightness"}
            
            for pattern_id, pattern_data in response.items():
                if pattern_id == "raw" or pattern_id in config_fields:
                    continue
                    
                # These should be actual patterns
                if isinstance(pattern_data, dict) and "n" in pattern_data:
                    self.state.patterns.append(
                        PatternInfo(id=pattern_id, name=pattern_data["n"])
                    )
                elif isinstance(pattern_data, str) and pattern_id not in config_fields:
                    # Sometimes pattern data is just the name
                    self.state.patterns.append(
                        PatternInfo(id=pattern_id, name=pattern_data)
                    )
            
            logger.info(f"Got {len(self.state.patterns)} patterns from {self.ip} (filtered from {len(response)} items)")
        else:
            logger.warning(f"No valid pattern response from {self.ip}")
            
    async def get_current_pattern(self):
        """Get currently running pattern"""
        response = await self.send_command({"getActivePattern": True})
        if response and "activeProgramId" in response:
            self.state.current_pattern_id = response["activeProgramId"]
            
            # Find pattern name
            for pattern in self.state.patterns:
                if pattern.id == self.state.current_pattern_id:
                    self.state.current_pattern_name = pattern.name
                    break
                    
    async def set_pattern(self, pattern_id: str):
        """Set active pattern"""
        await self.send_command({"activeProgramId": pattern_id})
        self.state.current_pattern_id = pattern_id
        
    async def set_brightness(self, brightness: float):
        """Set brightness (0.0 to 1.0)"""
        brightness = max(0.0, min(1.0, brightness))
        await self.send_command({"brightness": brightness})
        self.state.brightness = brightness
        
    async def get_playlist(self):
        """Get current playlist"""
        response = await self.send_command({"getPlaylist": True})
        if response and "playlist" in response:
            self.state.playlist = response["playlist"]
            self.state.sequencer_mode = response.get("runSequencer", "off")
            
    async def upload_pattern(self, name: str, code: str):
        """Upload a new pattern"""
        # Generate a unique ID for the pattern
        pattern_id = f"iqe_{int(time.time() * 1000)}"
        
        command = {
            "putProgram": {
                "id": pattern_id,
                "n": name,
                "code": code
            }
        }
        
        response = await self.send_command(command)
        # Most upload commands don't return a response or return "ok"
        # We consider it successful if no exception was thrown
        
        logger.info(f"Uploaded pattern '{name}' to {self.ip} with ID {pattern_id}")
        
        # Give the device a moment to process
        await asyncio.sleep(0.1)
        
        # Refresh patterns list to confirm
        await self.get_patterns()
        
        # Check if pattern was added
        for pattern in self.state.patterns:
            if pattern.id == pattern_id or pattern.name == name:
                return pattern_id
                
        # Even if not in list yet, return the ID (it may take time to appear)
        return pattern_id
        
    async def update_state(self):
        """Update all state information"""
        if not self.connected:
            if not await self.connect():
                return False
                
        await self.get_current_pattern()
        await self.get_playlist()
        
        # Get real-time stats if available
        stats = await self.send_command({"getStats": True})
        if stats:
            self.state.fps = stats.get("fps", 0)
            
        self.state.last_update = time.time()
        return True


class PixelBlazeFleet:
    """Manages multiple PixelBlaze devices"""
    
    def __init__(self):
        self.devices: Dict[str, PixelBlazeAPI] = {}
        
    def add_device(self, device_id: str, ip: str):
        """Add a device to the fleet"""
        if device_id not in self.devices:
            self.devices[device_id] = PixelBlazeAPI(ip)
            logger.info(f"Added device {device_id} at {ip}")
            
    def remove_device(self, device_id: str):
        """Remove a device from the fleet"""
        if device_id in self.devices:
            del self.devices[device_id]
            
    async def update_all(self):
        """Update state for all devices"""
        tasks = []
        for device_id, api in self.devices.items():
            tasks.append(api.update_state())
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any errors
        for device_id, result in zip(self.devices.keys(), results):
            if isinstance(result, Exception):
                logger.error(f"Failed to update {device_id}: {result}")
                
    async def sync_pattern(self, pattern_id: str):
        """Set the same pattern on all devices"""
        tasks = []
        for api in self.devices.values():
            if api.connected:
                tasks.append(api.set_pattern(pattern_id))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
    async def sync_brightness(self, brightness: float):
        """Set the same brightness on all devices"""
        tasks = []
        for api in self.devices.values():
            if api.connected:
                tasks.append(api.set_brightness(brightness))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        
    async def upload_to_all(self, name: str, code: str) -> Dict[str, str]:
        """Upload pattern to all devices, returns device_id -> pattern_id mapping"""
        pattern_ids = {}
        
        for device_id, api in self.devices.items():
            if api.connected:
                pattern_id = await api.upload_pattern(name, code)
                if pattern_id:
                    pattern_ids[device_id] = pattern_id
                    
        return pattern_ids
        
    def get_all_states(self) -> Dict[str, dict]:
        """Get state of all devices"""
        states = {}
        for device_id, api in self.devices.items():
            states[device_id] = api.state.to_dict()
        return states