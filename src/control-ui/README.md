# LX Control UI

TypeScript webapp for controlling LX parameters via OSC.

## Setup

```bash
cd src/control-ui
npm install
```

## Running

```bash
npm start
```

Then open http://localhost:8282 in your browser (or on tablet).

## Notes

- The webapp runs on port 8282 (different from main webapp on 8181)
- Connects to OSC WebSocket on port 8080
- Currently controls the speedUp parameter at `/lx/mixer/master/effect/1/speed`
- Responsive design optimized for tablets and mobile devices
- Large vertical slider on the left side for speedUp control
- Designed to be extended with additional controls