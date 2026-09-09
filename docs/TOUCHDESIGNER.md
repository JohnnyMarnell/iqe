# TouchDesigner → ArtNet → the ceiling: what exists, what's missing, how to finish

Written 2026-09-09 from a read-only audit of `src/touch-designer/` on
`master` = `dc67bec`. Nothing was executed. `.toe` files are opaque binaries;
their contents are inferred from names, sizes, commit messages, and the node
names the Python scripts expect.

Goal as stated: TouchDesigner renders a **24 × 420** texture (one row per
rafter, 420 px = 3 strips × 140) and pushes it as ArtNet/DMX to the same
Advatek PixLite E16-S Mk3 that LX drives, or to a local simulator that
emulates it. **That end-to-end test never ran.** What did get built and
proven is the *simulator* half, validated against LX's output, not TD's.

Related: [`RUNNING.md`](RUNNING.md) (`just sim*`, `just artnet-*`),
[`DMX-PARCANS.md`](DMX-PARCANS.md) (the sniffer's fake parcans).

---

## 1. The actual wire format (what any TD sender must reproduce)

Derived from `src/nodejs/buildProject.js`, `Projects/iqe.lxp`, and the
observations in `IQE_ARTNET_FINDINGS.md`:

| Item | Value |
|---|---|
| Transport | ArtNet `OpOutput` (0x5000) over UDP **6454**, unicast |
| Target | `10.10.42.80` (PixLite), alias `advatek` in `/etc/hosts`; `advatek-local` = `127.0.0.1` for the simulator |
| Universes per rafter | **3**, 1-based |
| Base universe for rafter `r` (0..23) | `B = 3r + 1` → 1, 4, 7, … **except rafter index 15 ("Rafter 16") → 73** (the README's "semi wonky jump"; `buildProject.js` ~27–28) |
| Bytes per rafter | 1260 (420 px × RGB), streamed as **510 / 510 / 240** across `B, B+1, B+2` = 170 / 170 / 80 px |
| Per-strip LX placement | strip 1 `(B, ch 0)`, strip 2 `(B, ch 420)` spilling into `B+1`, strip 3 `(B+1, ch 330)` |
| Universes on the wire | 1–45, 49–72, 73–75 (72 total) |
| Orientation | LX Row 1 has the highest X; the simulators V-flip (`visual_row = 23 - row`) and H-flip (`col = 419 - i`), so row byte 0 is the **rightmost** pixel on screen |
| The `.lxp` `port: 7890` | ignored; stock LX `StripFixture` always uses the protocol default 6454 |

Neither TD plan in the repo matches this:

| | `td-artnet.md` (Jul 31) | `td-plan-for-artnet.md` (Aug 5) | **actual** |
|---|---|---|---|
| px / universe | 170, packed 512 ch | 140 (1 strip = 1 universe) | 170/170/80 per row |
| universes | 60, 0-based | 72, 0-based | 72, 1-based, rafter-16 remap |
| target | `192.168.1.255` broadcast | `192.168.0.79` / `.229` (those are the **PixelBlaze** IPs) | `10.10.42.80` |

Caveat on universe numbering: the 2023 PixLite export
(`PixLite E16-S Mk3-In Queso Emergency.conf`) shows port start-universes
2, 5, 8, … which are LX's 1, 4, 7, … plus one. Either the Advatek UI is
1-based where the wire is 0-based or vice-versa. Confirm against the live
controller before trusting any TD universe field.

---

## 2. What exists

### 2.1 Timeline (git)

| Date (2025) | Commit | What |
|---|---|---|
| 07-26 | `5485394` Touch Designer begun | `iqe.toe`, `iqe-td.json` |
| 07-26 | `277af74` more TD, add MCP | `touchdesigner-mcp-td/`, `.dxt` |
| 07-29/30 | `827c1d0`, `35fbb69`, `2425574` | audio-reactive "jelly beans" experiments, tutorial `.toe`s |
| 07-31 | `c1c3d8c` skynet is alive, touch designer misery | **39 files**: every NDI/Syphon/RTSP/UDP receiver, the DMX-Out builders, `td-artnet.md`, `simple-dmx.toe`, `simple-stream*.toe` |
| 08-02 | `4d8093f` rendering fArtnet, `9ed426b` python artnet renderer working | `iqe_render.py` + debug scripts, `IQE_ARTNET_*.md`, `Projects/localhostedIQE*.lxp` (LX pointed at 127.0.0.1) |
| 08-02 | `a7a5b3f`, `3951da7`, `42099b8` | Electron port of the renderer |
| 08-03 | `99894e0`, `3cd32a3` | spacing slider; `CLAUDE.md`, `utils.py`, `FFTOcean.tox` |
| 08-05 | `3ee2e2f` First pass at video pattern | **`VideoPattern.java` added to LX** (JavaCV) — video on the ceiling without TD |
| 08-05 | `ec3425b` | `td-plan-for-artnet.md` (LLM plan from `muse-led-prompt.md` lines 1–9) |
| 12-08 | `b5b1492` playa code?? | Electron **sniffer** variant with fake parcan floods |

Note: `CLAUDE.md` and `audio_reactive_jellybeans.py` hard-code
`/Users/jmarnell/src/iqe/...` — this was done on a different machine/user.

### 2.2 Simulators (the proven half)

**`iqe-artnet-electron/`** — TypeScript port of `iqe_render.py`. Binds
`0.0.0.0:6454`, decodes `OpOutput`, maps universes 1–72 with the 170/170/80
split, V+H flips, draws on a canvas with spaced-mode row gaps, grid, labels,
auto-scale, pixel radius, glow. `npm start` = `tsc && electron .`; DevTools
always open. `dist/` is gitignored but built locally. **This is the validator
to use.** Known gap: it expects universes 1–72 contiguous and does not handle
the rafter-16 → 73/74/75 remap, so against the real `iqe.lxp` row 16 renders
black (it was validated against `localhostedIQE2024.lxp`, which has no remap).

**`iqe_render.py`** — the original matplotlib version, same mapping,
`--spaced`, `--shift`. Needs matplotlib (`just venv-sim`).

**Sniffer variant** (`main-sniffer.ts`, `artnet-sniffer.ts`, `start-sniffer.sh`,
Dec 2025) — same decoder plus `reuseAddr`, a multicast join attempt, a
"promiscuous" flag that is not real packet capture, and 8 fake par cans
rendered as additive floods. It assumes parcans on **universes 100–107,
channel 0**; the real ones are universe 1, channels 0/7/…/49 on a different
host. So it will never show the real cans and, if sniffing on the LX host,
universe 1 collides with Rafter 1.

**Debug scripts** (standalone Python, all bind 6454 unless noted):
`count_pixels.py` (10 s, non-zero px per universe vs 10,080),
`debug_universe_data.py` (5 s, bytes per universe by rafter, 1-based),
`debug_artnet.py` / `artnet_test_receiver.py` / `debug_dmx_timing.py`
(raw packets; bind `127.0.0.1`, so loopback only), `iqe_render_debug*.py`,
`iqe_universe_analyzer.py` (binds **7890**, the wrong-port era),
`iqe_debug_pixels.py` (arithmetic only), `test-udp.js` (Node listener).
`artnet_receiver.py` is the first visualizer and assumes the TD 60-universe
0-based scheme — useful only for TD output, wrong for LX.

### 2.3 TD-side senders (the unproven half)

All run **inside** TouchDesigner (use `op()`, `dmxoutCHOP`, `root`):

- `artnet_automation.py` — builds `video_to_dmx` (TOP to CHOP) → 60 ×
  `selectCHOP` + `dmxoutCHOP` pairs, universes 0–59, broadcast
  `192.168.1.255:6454`. Uses param names `par.protocol / artnetip / artnetuniverse`.
- `create_universes.py` — loop version of the same. Uses
  `par.interface / netaddress / universe / multicast`. **The two disagree on
  DMX Out CHOP parameter names**, so at least one is wrong; neither was
  validated. `selectCHOP.par.channames = '0-511'` is not valid TD selection
  syntax.
- `dmx_converter.py` — Script CHOP `onCook` that flattens 24 rows × 420
  samples RGBA into one 30,240-sample channel with per-sample `.eval()`
  (~30k Python calls per frame; not real-time). No universe split.
- `verify_artnet.py` — checks that `/project1/resize_to_24`,
  `/project1/video_to_dmx` and any `dmxoutCHOP` exist; prints the 60-universe
  math. Tells us `simple-dmx.toe` had those node names.

### 2.4 The NDI / Syphon / RTSP / UDP detour (Jul 31)

About 25 files trying to get the 420×24 texture *out of TD into Python*:
NDI Out TOP via `cyndilib` / `pyNDI` / `NDIlib` (13 iterations discovering
the cyndilib API; `ndi_minimal_working.py`, `test_ndi_frames.py` got frames),
Syphon Out via `syphon-python` (Metal texture readback, the "nightmare"),
Video Stream Out TOP over RTSP (`rtsp://127.0.0.1:554/tdvidstream`), and a
raw UDP push of 40,320-byte RGBA frames to `:12345`. **None of them packs
ArtNet**; they only `cv2.imshow`. The intended pipeline
TD → NDI → Python → ArtNet stopped before the ArtNet half. Same day, the DMX
Out CHOP approach was started instead.

### 2.5 `.toe` / `.tox` files

| File | Size | Likely contents |
|---|---|---|
| `iqe.toe` | 74 KB | main audio-reactive "jelly beans" chain (`audiodevin1 → audioAnalysis → math/noise → displace1 → out1`); shrank from 153 KB in the `VideoPattern` commit |
| `iqe-test1.toe` | 153 KB | pre-shrink fork; only file with an "ndi" string → NDI Out experiment |
| `simple-dmx.toe` | 43 KB | **the DMX attempt**: `resize_to_24` → `video_to_dmx` → generated `dmxout` nodes |
| `simple-ds.toe` | 31 KB | DMX/Script variant with the `dmx_converter.py` Script CHOP |
| `simple-stream*.toe`, `simplest*.toe`, `tutorial-start.toe` | 6–9 KB | streaming-out and scaffold experiments |
| `Audio Responsive Geometry.toe`, `FFTOcean.tox` | 15 / 24 KB | downloaded demos, visual-source candidates |

`iqe-td.json` (256 KB) is a TouchDesigner operator-tree dump of `/project1`
(1,233 nodes, the jelly-beans project), not a fixture map. Nothing references
it.

### 2.6 MCP

`touchdesigner-mcp-td/` + `touchdesigner-mcp.dxt` are the TD-side half of
**8beeeaaat/touchdesigner-mcp** v0.1.3: a Web Server DAT component
(`mcp_webserver_base.tox`, port 9981) exposing `create_td_node`,
`get_td_nodes`, `execute_python_script`, `update_td_node_parameters`, etc.
The `.dxt` is a Claude Desktop manifest that runs
`npx -y touchdesigner-mcp-server@latest --stdio --port=9981`. It is **not
configured on this machine** (no `mcpServers` anywhere under `~/.claude*`,
none in the repo's `.claude/settings.json`); `.cursorrules` auto-approves it
for Cursor. `CLAUDE.md` in that directory is a TD-Python cookbook from the
jelly-beans project (parameter-name discovery pain, signal flow), nothing
about ArtNet.

### 2.7 Why it stalled (reconstructed)

1. Every TD plan used the wrong universe layout (§1).
2. DMX Out CHOP parameter names were never confirmed in the textport.
3. Per-sample Python in the Script CHOP was too slow.
4. Port confusion (`7890` from the `.lxp` vs actual 6454) cost a day.
5. On Aug 5 `VideoPattern.java` landed in LX, which gave "play VJ video on
   the ceiling" without TD, and TD work stopped. `detect-cuts-prompt.md` and
   `src/scripts/detect_*.py` are the follow-on to that, not to TD.

---

## 3. How to finish the 24×420 test

**Path A — TD `DMX Out CHOP` in Art-Net mode → simulator → PixLite.** Recommended.

1. **Fix the simulator first** (10 minutes): add the rafter-16 remap
   (universe base 73 for row index 15) to `artnet-receiver.ts` (~67–104) and
   `iqe_render.py` (~111–146). Optionally fix the sniffer's parcans to
   universe 1 / channel 7·i with the positions in `DMX-PARCANS.md` §2.
2. **Prove the simulator against LX one more time** on this machine:
   `just lxp-strip-host advatek-local` (already the case at HEAD), `just build`,
   `just sim` in one terminal, `just lx` in another. Expect 72 active
   universes and 10,080 lit pixels (`just artnet-count`). Quit LX before the
   TD test so two senders don't overlap.
3. **In TD, discover the DMX Out CHOP parameter names** in the textport before
   writing any builder: `[p.name for p in op('dmxout1').pars()]`. This is the
   step that was never done and the reason the two builders disagree.
4. **Build the mapping without per-sample Python.** `TOP to CHOP` on the
   420×24 texture (RGB, 420 samples × 72 channels, or 24 channels × 3) → one
   Script CHOP that reshapes with numpy (`scriptOp.copyNumpyArray`) into one
   channel per universe of length 510/510/240 (per rafter `r`: row bytes
   `[0:510]` → `B`, `[510:1020]` → `B+1`, `[1020:1260]` → `B+2`, `B = 3r+1`,
   `r == 15 → B = 73`) → `Select CHOP` + `DMX Out CHOP` per universe
   (72 pairs), or one DMX Out CHOP with multi-universe channel naming if the
   installed build supports it. Remember the simulator's flips: TD row 0 is
   LX Row 24 unless you flip, and row byte 0 is the rightmost pixel.
5. **Target `127.0.0.1` first**, watch the simulator's active-universe list
   (expects 1–45, 49–75), then `10.10.42.80`. Start at a low frame rate and
   raise it; 72 universes × 30 fps ≈ 2,160 packets/s is well within what the
   PixLite and a Mac can do, but TD's DMX Out CHOP throughput on macOS is
   the thing to measure.
6. Commit the working `.toe` with a README line saying which file to open.

**Path B — TD → NDI/Syphon → Python → ArtNet.** Dead end for the stated
goal: doubles the process count, Syphon readback on macOS was the pain point,
and the ArtNet packer was never written. Only revisit if the DMX Out CHOP
cannot sustain 72 universes.

**Path C — TD → LX as an input.** No evidence of NDI/Syphon/Spout input in
this Chromatik build (vendor jar has no such classes; no Java in the repo
mentions them). LX is a sender only. If the real goal is "VJ video on the
ceiling," `VideoPattern` already does that; if it is "TD as the pattern
engine with LX mixing," that needs a new LX pattern that receives ArtNet on a
second port and copies universes into `colors[]` — the same shape as the
PixelBlaze sidecar idea in [`PIXELBLAZE-EMULATOR-LX.md`](PIXELBLAZE-EMULATOR-LX.md),
so build that receiver once and use it for both.

---

## 4. Integration into camp lights (once A works)

- **Ownership.** LX and TD must not both transmit the ceiling universes. Use
  the same arbitration the par cans use: a `just`/OSC switch that disables LX
  output (or points its strips at `advatek-local`) when TD owns the PixLite,
  and vice-versa. ArtNet nodes merge HTP/LTP unpredictably; the PixLite has a
  merge setting, but two 72-universe senders will look like flicker.
- **Alternatively** keep LX as the mixer and give TD its own LX channel via
  the ArtNet-input pattern in Path C. That keeps autopilot, transitions, and
  the par cans coherent, at the cost of one hop of latency and one more
  socket on the laptop.
- **Network.** TD on the laptop's dongle at `10.10.42.11`, PixLite at `.80`.
  Same `/etc/hosts` aliases (`advatek` / `advatek-local`) work for TD if you
  put the hostname in the DMX Out CHOP.
- **Audio.** TD's `audiodevin` + `audioAnalysis` chain (the jelly-beans
  project) is a second beat/level source; LX already has its own audio
  meter and the Python beat detector. Pick one clock. The simplest bridge is
  TD → OSC `/lx/tempo/bpm` on 3232 (the same path `beat_detective.py` uses).
- **Config drift to close.** There is no committed PixLite config matching
  the 2024 rebuild and `10.10.42.80`; export one from the live controller and
  commit it next to the 2023 file.

---

## Appendix — files

- Simulators: `src/touch-designer/iqe-artnet-electron/src/{artnet-receiver,renderer,main,preload}.ts`, `index.html`; `src/touch-designer/iqe_render.py`
- Sniffer: `iqe-artnet-electron/src/{artnet-sniffer,main-sniffer}.ts`, `index-sniffer.html`, `start-sniffer.sh`
- TD senders: `artnet_automation.py`, `create_universes.py`, `dmx_converter.py`, `verify_artnet.py`
- Docs: `td-artnet.md`, `td-plan-for-artnet.md`, `IQE_ARTNET_{SUMMARY,FINDINGS,CORRECTED}.md` (FINDINGS is the final state despite CORRECTED's name), `CLAUDE.md`, `.cursorrules`
- Source of truth for the layout: `src/nodejs/buildProject.js` ~9–38, 44–50, 66–101, 314–351
- LX test rigs with everything on 127.0.0.1: `Projects/localhostedIQE.lxp` (with remap), `Projects/localhostedIQE2024.lxp` (without), `Projects/tmp.lxp`
