# IQE ArtNet LED Visualizer - Electron/TypeScript Version

A TypeScript/Electron port of the Python IQE ArtNet visualizer, displaying a 420x24 LED grid with proper universe mapping for the IQE ceiling array.

## Features
- Real-time ArtNet packet reception on port 6454
- 420x24 pixel grid visualization using HTML5 Canvas
- Spaced mode showing realistic 25'×21' geometry
- Horizontal and vertical flip to match LX Studio coordinate system
- Live statistics display
- Grid and label overlays

## Installation

```bash
cd iqe-artnet-electron
npm install
```

## Running

```bash
# Development mode
npm run dev

# Production mode
npm start
```

## Building

```bash
# Build distributable
npm run dist
```

## Architecture

- **Main Process** (`main.ts`): Handles Electron window and UDP ArtNet receiver
- **ArtNet Receiver** (`artnet-receiver.ts`): Processes ArtNet packets and manages pixel buffer
- **Renderer** (`renderer.ts`): Canvas visualization and UI controls
- **Preload** (`preload.ts`): Secure IPC bridge between main and renderer

## Universe Mapping
- 72 universes total (1-72)
- 3 universes per row × 24 rows
- Pattern per row:
  - Universe N+0: 170 pixels
  - Universe N+1: 170 pixels
  - Universe N+2: 80 pixels
  - Total: 420 pixels per row

## Coordinate System
- Horizontal flip applied (pixel 0 → 419)
- Vertical flip applied (Row 1 at bottom, Row 24 at top)
- Matches LX Studio physical layout