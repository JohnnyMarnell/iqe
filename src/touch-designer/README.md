# src/touch-designer

State, history, and the plan to finish the 24×420 TouchDesigner → ArtNet test:
[`../../docs/TOUCHDESIGNER.md`](../../docs/TOUCHDESIGNER.md).

What works today is the **ArtNet simulator**, validated against LX (not TD):

```bash
just sim            # iqe-artnet-electron: Electron receiver on UDP 6454, draws the 24×420 grid
just sim-py         # iqe_render.py, the original matplotlib version (just venv-sim)
just artnet-count   # count_pixels.py: lit pixels per universe over 10 s
just artnet-universes | artnet-raw | artnet-listen
```

Point LX's strips at localhost first (`Projects/iqe.lxp` already uses `advatek-local` → 127.0.0.1
via /etc/hosts). Known gap: both simulators expect universes 1–72 contiguous and don't handle the
rafter-16 → 73/74/75 remap in the real project.

The TD-side senders (`artnet_automation.py`, `create_universes.py`, `dmx_converter.py`,
`verify_artnet.py`) run *inside* TouchDesigner, target a 60-universe layout that does not match the
hardware, and were never validated. The NDI/Syphon/RTSP/UDP receivers are display-only. `CLAUDE.md`
here is a TD-Python cookbook from the audio-reactive "jelly beans" project; `touchdesigner-mcp-td/`
is the TD half of 8beeeaaat/touchdesigner-mcp (not configured on this machine).
