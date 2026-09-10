# LX Control UI

TypeScript webapp for controlling LX parameters via OSC.

## Setup

```bash
cd src/control-ui
npm install
```

## Running

### Web UI
```bash
npm run control                       # Vite dev server on :8282 (LAN-exposed) + the OSC/WS bridge
# or, production:
npm run build && NODE_ENV=production npm start   # serve dist/ on :8282 + bridge
```

Then open http://localhost:8282 in your browser (or on tablet).

Plain `npm start` (= `tsx src/server.ts`) is **bridge-only** since Dec 2025: WS :8080 ↔ OSC UDP
3232/3333, no HTTP unless `NODE_ENV=production` or `--production`. From the repo root: `just control`,
`just control-prod`, `just control-bridge`.

### MIDI Bridge (optional)
To control via MIDI hardware on the server:
```bash
npm run midi
```

This will:
- List available MIDI devices
- Connect to the first MIDI input device
- Map CC 21 (any channel) to the Speed Up parameter
- Send OSC messages to LX on port 3232

## Notes

- The webapp runs on port 8282 (the legacy `src/nodejs` app is on 8181 only via `just legacy-web`; its own `npm start` uses 80). Don't run both: both bind WS 8080 and UDP 3333.
- Connects to OSC WebSocket on port 8080; `server.ts` forwards to LX's IQE bridge on UDP 3232 and listens for replies on 3333
- Controls (`src/main.ts`): Speed Up `/lx/mixer/master/effect/1/speed`, Transition All / Color Change / Hold triggers on effect 1, Solo Visuals + Pong P1/P2 + Toggle Parcans via `/iqe/cmd`, Mindshow on/off + sensitivity on effect 5, ParCan Spatial Radius (no-op on the real rig), Query OSC Paths
- `osc-client-unified.ts` is the live client; `osc-client.ts` is the unreferenced original
- Responsive design optimized for tablets and mobile devices
- Large vertical slider on the left side for speedUp control
- Designed to be extended with additional controls
- MIDI bridge runs server-side only (no browser permissions needed)