# PixelBlaze Fleet Monitor

A real-time web-based monitoring and control system for PixelBlaze LED controllers with automatic pattern provisioning and synchronized effects.

## Features

- **Auto-Discovery**: Automatically discovers PixelBlaze devices on local network
- **Real-time Monitoring**: Live status updates via WebSocket connections
- **Pattern Management**: Upload and synchronize patterns across multiple devices
- **Auto-Provisioning**: Automatically uploads IQE patterns to new devices
- **Synchronized Effects**: Coordinate patterns across entire fleet
- **Web UI**: Responsive interface accessible from any device
- **REST API**: Full API for programmatic control

## Quick Start

### Prerequisites

```bash
# Python 3.8+ required
pip install fastapi uvicorn websockets aiohttp
```

### Basic Usage

```bash
# Start the fleet monitor
python pbfleet.py

# Force re-provision all devices with patterns
python pbfleet.py --force-provision

# Development mode with auto-reload
python pbfleet.py --dev
```

Access the web interface at: http://localhost:8000

## Architecture

### Components

1. **pbfleet.py** - Main web application and fleet coordinator
2. **pixelblaze_api.py** - WebSocket API client for PixelBlaze devices
3. **patterns.py** - Library of synchronized patterns
4. **pb.py** - Command-line fleet management tool

### Network Discovery

The system uses UDP port 1889 for PixelBlaze discovery. Devices broadcast their presence every few seconds with a packet containing:
- 6-byte device ID
- Optional additional metadata

### Communication Flow

```
┌─────────────┐     WebSocket      ┌──────────────┐
│   Browser   │◄──────────────────►│  FastAPI App │
└─────────────┘                     └──────┬───────┘
                                           │
                                    ┌──────▼───────┐
                                    │  Discovery   │
                                    │   Thread     │
                                    └──────┬───────┘
                                           │
                              ┌────────────┼────────────┐
                              ▼            ▼            ▼
                        ┌──────────┐ ┌──────────┐ ┌──────────┐
                        │PixelBlaze│ │PixelBlaze│ │PixelBlaze│
                        └──────────┘ └──────────┘ └──────────┘
```

## API Reference

### WebSocket Commands

Connect to `/ws` endpoint for real-time updates.

#### Get All Devices
```json
{"type": "get_devices"}
```

#### Trigger Sync Pulse
```json
{"type": "sync_pulse"}
```

#### Set Pattern
```json
{
  "type": "set_pattern",
  "device_id": "2a0000005608",
  "pattern_id": "ABC123"
}
```

#### Set Brightness
```json
{
  "type": "set_brightness",
  "device_id": "2a0000005608",
  "brightness": 0.75
}
```

### REST Endpoints

#### GET /api/devices
Returns list of all discovered devices with current status.

```bash
curl http://localhost:8000/api/devices
```

Response:
```json
{
  "devices": [
    {
      "id": "2a0000005608",
      "ip": "192.168.0.241",
      "name": "Living Room",
      "online": true,
      "current_pattern": "Rainbow",
      "brightness": 0.5,
      "fps": 60,
      "provisioned": true
    }
  ],
  "count": 1
}
```

## Pattern Development

### Creating Custom Patterns

Add patterns to `patterns.py`:

```python
PATTERNS["my_pattern"] = {
    "name": "My Custom Pattern",
    "code": """
    export var speed = 0.5
    export function beforeRender(delta) {
      t1 = time(0.001)
    }
    export function render(index) {
      hsv(t1 + index/pixelCount, 1, 1)
    }
    """,
    "description": "Description of pattern"
}
```

### Synchronized Patterns

Patterns can be synchronized across devices using shared time bases:

```javascript
// Get synchronized time across all devices
var syncTime = time(0.001) - startTime

// Use for coordinated effects
var wave = sin(syncTime * speed * PI2)
```

## Deployment

### Raspberry Pi Setup

1. Install on Raspberry Pi:
```bash
sudo ./install_pi_service.sh
```

2. Check service status:
```bash
sudo systemctl status pixelblaze-monitor
```

3. View logs:
```bash
sudo journalctl -u pixelblaze-monitor -f
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "pbfleet.py"]
```

## Configuration

### Environment Variables

- `PB_FLEET_PORT` - Web server port (default: 8000)
- `PB_FLEET_HOST` - Bind address (default: 0.0.0.0)
- `PB_DISCOVERY_PORT` - UDP discovery port (default: 1889)
- `PB_LOG_LEVEL` - Logging level (default: INFO)

### Persistent State

Device provisioning state is stored in `provisioned_devices.pkl`. Delete this file to reset provisioning status.

## Troubleshooting

### Common Issues

1. **No devices found**
   - Check firewall settings for UDP port 1889
   - Ensure devices are on same network segment
   - Verify PixelBlaze devices are powered on

2. **WebSocket connection fails**
   - Check browser console for errors
   - Verify no proxy interfering with WebSocket upgrade
   - Try different browser

3. **Patterns don't upload**
   - Check device has sufficient storage
   - Verify network connectivity to device
   - Check logs for specific error messages

4. **Slow shutdown (Ctrl-C)**
   - Fixed in latest version with proper signal handling
   - Force quit with Ctrl-C twice if needed

### Debug Mode

Enable detailed logging:
```bash
LOG_LEVEL=DEBUG python pbfleet.py
```

## Security Considerations

⚠️ **Warning**: This system is designed for local network use only.

- No authentication implemented
- WebSocket and HTTP traffic unencrypted
- CORS configured for any origin (development convenience)
- Device provisioning uses unencrypted communication

For production deployment:
1. Add authentication middleware
2. Use HTTPS/WSS with proper certificates
3. Restrict CORS origins
4. Implement rate limiting
5. Add input validation and sanitization

## Known Limitations

- Maximum ~100 devices per instance (threading limits)
- Pattern uploads are sequential, not parallel
- No pattern versioning or rollback
- WebSocket reconnection may miss updates
- IPv4 only (no IPv6 support)

## Contributing

### Development Setup

```bash
# Clone repository
git clone <repository>
cd src/pb

# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Format code
black *.py
```

### Code Style

- Follow PEP 8
- Use type hints where appropriate
- Add docstrings to all public functions
- Keep functions under 50 lines
- Write tests for new features

## License

[Specify license here]

## Credits

Built for IQE (In Queso Emergency) art installation at Burning Man.

Based on PixelBlaze API by Ben Hencke (ElectroMage).