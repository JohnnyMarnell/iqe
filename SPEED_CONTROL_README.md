# IQE Speed Control Web Interface

## Quick Start

1. **Start LX/Chromatik** first (using IQE.command or RUN.sh)
   - Make sure OSC is enabled on port 3232

2. **Start the Speed Control System**:
   ```bash
   ./start-control.sh
   ```
   This single command starts both the OSC bridge and web UI server.

3. **Open the control interface**:
   - http://localhost:8282 (on this computer)
   - Or from phone/tablet on same network: http://[computer-name]:8282

## How It Works

The speed control system now uses a **unified TypeScript server** that combines:

1. **LX/Chromatik** - The main LED control software
   - Has a GlobalControls effect on the Master channel
   - The "speedUp" parameter controls animation speed (0 = normal, 1 = 21x speed)
   - Listens for OSC messages on port 3232

2. **Unified Server** (TypeScript) - Single server that handles everything
   - WebSocket server on port 8080 for browser communication
   - OSC UDP bridge to LX on port 3232
   - Web server on port 8282 serving the control UI
   - Located in src/control-ui/src/server.ts

## Manual Setup (if script doesn't work)

```bash
cd src/control-ui
npm install
npm run build  # Build the frontend
npm start      # Start the unified server
```

Or for development with hot reload:
```bash
cd src/control-ui
npm install
npm run start:dev  # Runs both vite dev server and the OSC bridge
```

## Troubleshooting

- **Slider doesn't affect LX**: Check that LX is running and OSC is enabled
- **Can't connect to web UI**: Make sure nothing else is using ports 8080 or 8282
- **Speed seems stuck at 0**: In LX, find Master channel → Effects → Global Controls → speedUp slider and make sure it's responding

## OSC Path

The speed control sends to: `/lx/mixer/master/effect/1/speed`