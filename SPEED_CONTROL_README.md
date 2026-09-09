# IQE Speed Control Web Interface

> **Corrected 2026-09-09.** Since commit `dc67bec` (Dec 2025) `npm start` in `src/control-ui` runs the
> OSC/WebSocket bridge **only**; the HTTP server on 8282 is opened only with `NODE_ENV=production` (or
> `--production`). So `./start-control.sh` no longer serves a page. Use `just control` (Vite dev server
> on 8282 + bridge) or `just control-prod` (built `dist/` on 8282 + bridge). `start-speed-control.sh`
> is broken (starts the legacy bridge *and* this one, both on WS 8080 / UDP 3333) — don't use it.
> Port 3232 is opened by the IQE plugin's `OscBridge` whenever the plugin loads; it is not the LX OSC
> panel setting (that is 3030/3131).

## Quick Start

1. **Start LX/Chromatik** first (using IQE.command, RUN.sh, or `just lx`)

2. **Start the Speed Control System**:
   ```bash
   just control          # dev: vite :8282 + bridge   (or: cd src/control-ui && npm run control)
   just control-prod     # prod: build + serve dist on :8282 + bridge
   ```

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
npm run build                      # Build the frontend
NODE_ENV=production npm start      # Start the unified server WITH the web page on 8282
npm start                          # bridge only (WS 8080 ↔ OSC 3232/3333), no page
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

The speed control sends to: `/lx/mixer/master/effect/1/speed` (GlobalControls is master effect 1).

Other controls in the same page: `transitionAll`, `color`, `pauseTransitions` triggers on effect 1;
`/lx/mixer/master/effect/5/enabled` + `/sensitivity` (Mindshow); `/iqe/cmd "solo visuals"`,
`"pong1 <v>"`, `"pong2 <v>"`, `"toggleparcans"`. Without any Node: `just osc <address> <args>`.

MIDI: `npm run midi` / `just midi` maps **CC 21** (not 22) on any channel to the speed path.
