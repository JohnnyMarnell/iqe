# PixelBlaze Fleet Management

> **Corrected 2026-09-09.** This doc was written as a plan in Aug 2025. What actually shipped is
> `src/pb/pbfleet_enhanced.py` (Flask, HTTP polling, port **8000**). Firestorm integration, WebSocket/SSE
> live updates, and the OSC bridge to LX were never built. Sections below are marked accordingly.
> Run it with `just pb-monitor`; the Mac-side WiFi provisioning CLI is `src/pixelblaze/pb.py`
> (`just pb-scan`, `just pb-connect`, `just pb-flash <ssid>`). See docs/RUNNING.md §8.

## Overview
This project manages a fleet of PixelBlaze LED controllers on the IQE network, providing real-time monitoring and control capabilities.

## Technologies

### Firestorm (not integrated — aspirational)
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

### Features (as built in `src/pb/pbfleet_enhanced.py`)
- Real-time device status (online/offline, 30 s timeout)
- Auto-discovery of new devices (UDP 1889 beacons)
- Pattern information display (name, pattern list, active pattern, sequencer mode/playlist, brightness, fps, pixel count via `pixelblaze-client`, polled every 10 s)
- Basic control interface: `POST /api/sync/<pattern>`, `/api/sync-random`, `/api/setup-sync`, `/api/swell-and-scatter`, `/api/pulse`, `/api/pulse-quick`; `GET /api/devices`, `/api/health`, `/api/common-patterns`
- Browser polls `/api/devices` (plain HTTP; no WebSocket/SSE)
- State persisted to `src/pb/devices_state.json`; per-device dumps `pb_config_<id>.json` etc.

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

## Implementation Plan (historical — items 1 and 2 done as Flask, item 3 not done)

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
just venv                    # uv venv + requirements.txt (flask, flask-cors, pixelblaze-client, ...) + click
just pb-monitor              # = cd src/pb && python pbfleet_enhanced.py  (cwd must be src/pb: template path)
# http://localhost:8000

just pb-devices              # curl /api/devices
just pb-sync-random          # POST /api/sync-random
just pb-pulse-quick          # POST /api/pulse-quick
```

Other variants in `src/pb/`: `pbfleet_simple.py` (Flask, inline HTML), `pbfleet.py` (FastAPI, abandoned;
its `--dev` references a module that doesn't exist), `old_pbfleet.py` (dead), `pb_web_button.py`
(standalone one-button page on :5000). `src/pb/README.md` describes the FastAPI one.

Raspberry Pi: `src/pb/pixelblaze-monitor.service` runs `/home/pi/iqe/pixelblaze_monitor_pi.py`, which
does not exist anywhere in the repo, and `install_pi_service.sh` installs the FastAPI stack. Broken as
committed; fix the path to `pbfleet_enhanced.py` and the pip line before relying on it.

## Device Management

### Current IQE PixelBlaze Devices
- Home LAN, last seen Aug 2025 (`devices_state.json`): `johnny5` 192.168.0.96 (2a000000a401), `colorPalette` 192.168.0.241 (2a0000005608)
- Flamecaster corners in `flamecaster.json`: NECorner 192.168.0.79, NWCorner 192.168.0.229 (400 px each); playa 2024 they were 10.10.42.102/.103 (`playa2024` branch)
- Additional devices auto-discovered

### Pattern Deployment
- Use same pattern names for group control (`/api/sync/<name>` only switches to patterns already on each device; no upload)
- `pb_pulse_and_scatter.py` needs a pattern named `simplePulse` on every device (`src/pb/patterns/simplePulse.js`, upload via the PB web UI)
- Python client for custom automation

## Integration with LX Studio

### Current Setup
- Flamecaster bridges ArtNet to PixelBlaze (LX `FlamecasterFixtures` → 127.0.0.1:6455 → `~/src/Flamecaster` → ws://pb:81); `just flamecaster`
- Alternative: Direct WebSocket control
- OSC commands can trigger PixelBlaze patterns (not wired up; would go via `/iqe/cmd` in `LXPluginIQE`)
- The far more complete PixelBlaze runtime/gallery now lives in `~/src/staff-infection` — see docs/PIXELBLAZE-EMULATOR-LX.md

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