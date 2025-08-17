# PixelBlaze Fleet Management

## Overview
This project manages a fleet of PixelBlaze LED controllers on the IQE network, providing real-time monitoring and control capabilities.

## Technologies

### Firestorm
**Firestorm** is the official centralized control console for multiple PixelBlaze devices. It provides:
- Synchronized animations across multiple controllers
- Pattern management and deployment
- Time synchronization (NTP-like)
- HTTP API for automation
- Automatic network discovery

We should consider using Firestorm for:
- Large-scale synchronization needs
- Central pattern management
- When running on dedicated hardware (e.g., Raspberry Pi)

GitHub: https://github.com/simap/Firestorm

### PixelBlaze Python Client
For custom Python integration, we'll use the `pixelblaze-client` library:
- WebSocket-based communication
- Synchronous API for easy programming
- Multi-device support
- Pattern control and parameter adjustment

Installation:
```bash
pip install pixelblaze-client websocket-client
```

GitHub: https://github.com/zranger1/pixelblaze-client

## Network Architecture

### Device Discovery
- PixelBlaze devices broadcast on UDP port 1889
- Each device has a unique ID and hostname
- Devices can be in AP mode or client mode on camp WiFi

### Communication
- WebSocket API on port 81 (default)
- HTTP API for pattern uploads and basic control
- Real-time telemetry and sensor data streaming

## Live Monitoring Web App

### Features
- Real-time device status (online/offline)
- Auto-discovery of new devices
- Pattern information display
- Basic control interface
- WebSocket/SSE for live updates

### Architecture
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Web Browser│────▶│  Python Flask│────▶│ PixelBlaze  │
│  (Dashboard)│◀────│  + WebSocket │◀────│  Devices    │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   Discovery  │
                    │   Service    │
                    └──────────────┘
```

## Implementation Plan

1. **Device Discovery Service**
   - UDP listener on port 1889
   - Periodic network scan
   - Device registry with status tracking

2. **Web Dashboard**
   - Flask/FastAPI backend
   - WebSocket/SSE for real-time updates
   - Simple HTML/JS frontend with live device grid

3. **Integration Options**
   - Standalone monitoring app
   - Firestorm integration for advanced control
   - OSC bridge for LX Studio communication

## Quick Start

```bash
# Install dependencies
pip install pixelblaze-client flask flask-socketio

# Run monitoring app
python pixelblaze_monitor.py

# Access dashboard
# http://localhost:5000
```

## Device Management

### Current IQE PixelBlaze Devices
- NE Corner: IP TBD (on discovery)
- NW Corner: IP TBD (on discovery)
- Additional devices auto-discovered

### Pattern Deployment
- Use same pattern names for group control
- Firestorm handles sync across devices
- Python client for custom automation

## Integration with LX Studio

### Current Setup
- Flamecaster bridges ArtNet to PixelBlaze
- Alternative: Direct WebSocket control
- OSC commands can trigger PixelBlaze patterns

### Proposed Enhancement
- Live status display in web UI
- Automatic failover detection
- Pattern sync verification

## Troubleshooting

### Common Issues
1. **Devices not discovered**: Check WiFi network, ensure on same subnet
2. **WebSocket connection failed**: Verify port 81 is accessible
3. **Pattern sync issues**: Use Firestorm for multi-device sync
4. **Network timeouts**: PixelBlaze may be in AP mode

### Debug Commands
```python
# Test device connection
from pixelblaze import Pixelblaze
pb = Pixelblaze("192.168.x.x")
print(pb.getHardwareConfig())
```

## Links & Resources
- [PixelBlaze WebSocket API](https://electromage.com/docs/websockets-api/)
- [Firestorm GitHub](https://github.com/simap/Firestorm)
- [pixelblaze-client PyPI](https://pypi.org/project/pixelblaze-client/)
- [ElectroMage Forum](https://forum.electromage.com/)