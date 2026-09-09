# DMX Par Cans — catalog, what happened at the 2025 burn, next steps

Written 2026-09-09 from a read-only audit of the repo at `master` = `dc67bec`
(2025-12-08). Nothing here was executed; everything is from source, project
JSON, git history, and the notes/transcripts in the repo.

The par cans were a last-minute add in the two weeks before Burning Man 2025
(first commit 2025-08-14 06:55 "dmx failz", last pre-departure commit
2025-08-24 18:59 "spatial average parcan"). Eight battery U'King RGB par cans
on the ceiling perimeter, driven from LX through a separate ArtNet→DMX node,
so patterns on the strip grid spill onto the cans as ambient wash.

Related: [`RUNNING.md`](RUNNING.md) (justfile recipes `parcan-*`),
[`TOUCHDESIGNER.md`](TOUCHDESIGNER.md) (the ArtNet sniffer that also draws
fake parcans), [`../NETWORKING-NOTES.md`](../NETWORKING-NOTES.md).

---

## 1. Hardware and signal path

```
LX / Chromatik  (laptop, USB-ethernet dongle @ 10.10.42.11)
   │  8 × SmoothDMXParCanFixture, each a 1-point StripFixture
   │  8 separate ArtNet OpOutput datagrams per frame, unicast
   ▼
10.10.42.68 : 6454, universe 1        Pknight ArtNet2-CR021R (2-port ArtNet→DMX node, Swider's)
   │  DMX512 daisy chain
   ▼
8 × U'King battery par cans, 7-channel mode, DMX addresses 1, 8, 15, 22, 29, 36, 43, 50
```

- **Not through the PixLite.** The Advatek E16-S Mk3 config
  (`PixLite E16-S Mk3-In Queso Emergency.conf` ~line 350) has its single aux/DMX
  port set to `Off`, and its pixel ports start at universe 2. Universe 1 is
  free for the Pknight.
- **Pknight.** Model ArtNet2-CR021R, MAC `02:4d:48:0a:2a:44`. Shipped at
  `192.168.1.95`; reconfigured to `10.10.42.68` via its LCD + 4 buttons
  (narrative in `src/pixelblaze/claude-code-convo-wifi-pixelblaze.txt`
  ~lines 2390–2990). No web UI. The scripts and fixtures send **universe 1 in
  the packet**; treat that as canonical regardless of the "device is
  0-based" note in that transcript.
- **Laptop.** USB ethernet dongle manually set to `10.10.42.11/24`. See
  `NETWORKING-NOTES.md` "Setting Up Manual IP for Direct Device Connection"
  and the routing-priority pain that goes with it.
- **Par can model.** README says U'King **ZQ01104**; `src/dmx/parcan_tester.py`
  says **ZQ01047**. One is a typo. Check the sticker on a can and fix both.

### 7-channel DMX map (what every encoder in the repo assumes)

| Offset | DMX ch (can @ addr 1) | Function        | What we send            |
|-------:|----------------------:|-----------------|-------------------------|
| +0     | 1                     | Dimmer (master) | 255, or scaled (see §3) |
| +1     | 2                     | Red             | gamma-corrected R       |
| +2     | 3                     | Green           | gamma-corrected G       |
| +3     | 4                     | Blue            | gamma-corrected B       |
| +4     | 5                     | Strobe          | 0                       |
| +5     | 6                     | Function/modes  | 0                       |
| +6     | 7                     | Colour speed    | 0                       |

Two source comments (`SpatialAveragingByteEncoder.java` ~189–196 and the
Electron sniffer `artnet-sniffer.ts` ~299) label +4..+6 as "Amber, White, UV".
That is wrong for these cans; it is comment-only, all encoders write zeros.

---

## 2. What is in the project file

`Projects/iqe.lxp` at HEAD has **8 × `org.iqe.SmoothDMXParCanFixture`**
(ids 3001–3008). All share: `host 10.10.42.68`, `port 6454`, `protocol` ArtNet,
`artNetUniverse 1`, `numPoints 1`, `y 720` (ceiling plane), `scale 10`,
`tags "dmx parcan surface"`, `Smoothing 0.745`.

| id   | label        | x     | z     | dmxChannel (0-idx) | DMX addr | Where          |
|------|--------------|------:|------:|-------------------:|---------:|----------------|
| 3001 | DMX ParCan 1 | -2400 | -1980 | 0                  | 1        | SE corner      |
| 3002 | DMX ParCan 2 | 60    | -1980 | 7                  | 8        | NE corner      |
| 3003 | DMX ParCan 3 | 60    | -1580 | 14                 | 15       | north edge     |
| 3004 | DMX ParCan 4 | 60    | -1180 | 21                 | 22       | north edge     |
| 3005 | DMX ParCan 5 | 60    | -780  | 28                 | 29       | north edge     |
| 3006 | DMX ParCan 6 | 60    | -380  | 35                 | 36       | north edge     |
| 3007 | DMX ParCan 7 | 60    | 20    | 42                 | 43       | NW corner      |
| 3008 | DMX ParCan 8 | -2400 | 20    | 49                 | 50       | SW corner      |

Axes per README: X+ = north (road side), Z+ = west. So the layout is
**4 corners + 4 evenly spaced (400 units) along the north/road edge** — six
cans facing the road, two on the back corners. The README's "Parcans at
corners" undersells it.

Colour source: there is no explicit sampling code. Each parcan is a 1-point
`StripFixture`; the point sits at (x, 720, z) in the model, patterns render
to it like any pixel, and the fixture outputs the mixer colour at that
coordinate. Each can therefore mirrors the nearest ceiling-edge pixel.

Project-file lineage (all under `Projects/`):

| File                                  | Parcans           | Note                                                        |
|---------------------------------------|-------------------|-------------------------------------------------------------|
| `bak.iqe.lxp` (Aug 16)                | 4, Smoothing 0.94 | first four corners                                          |
| `iqe-hadFourWorkingParcanCorners.lxp` | 4 (NE/NW/SW/SE, ch 0/7/14/21) | "these four verified working" baseline, Aug 17  |
| `iqe_modified.lxp`                    | 8                 | output of `parcan-surgery.ts`, hand-copied into `iqe.lxp`   |
| `iqe-prePlayaSurgery-2025.lxp`        | 8                 | Aug 23 backup before the last IP flip                       |
| `iqe.lxp`                             | 8                 | **the real one**; strips currently point at `advatek-local` |
| `defShouldntDoThis-iqe.lxp`           | 8                 | Dec 8 post-playa copy; parcan config identical to pre-departure |

Important: when the 4-corner layout became 8, the ordering restarted at SE and
every DMX address changed (NE went from address 1 to 8). **The physical
address on each can must match the table above.**

---

## 3. Java: three fixture classes, one in use

All in `src/main/java/org/iqe/`, registered in `LXPluginIQE.java` (~lines
91–93). All three `extends heronarts.lx.structure.StripFixture`, force
`protocol = ARTNET`, and in `buildSegment()` swap LX's private RGB
`byteEncoder` for a 7-bytes-per-pixel encoder using
`org.springframework.test.util.ReflectionTestUtils.setField`. That is why
`spring-test` is a runtime dependency in `pom.xml` (~lines 29–33).

| Class                          | Encoder                       | Dimmer byte                  | RGB                              | Extra params                       | In `iqe.lxp` |
|--------------------------------|-------------------------------|------------------------------|----------------------------------|------------------------------------|--------------|
| `DMXParCanFixture`             | `ParCanByteEncoder` (static)  | 255                          | direct, gamma                    | none                               | no           |
| `SmoothDMXParCanFixture`       | `SmoothParCanByteEncoder`     | 255, or `255·V/40` when V<40 | HSV rate-limited EMA, gamma      | `Smoothing` 0.70–0.99 (def 0.85)   | **yes × 8**  |
| `SpatialAveragingParCanFixture`| `SpatialAveragingByteEncoder` | 255                          | direct (averaging is a no-op)    | `SampleRadius`, `BrightWeight` (unused) | no      |

### SmoothDMXParCanFixture (the one that shipped)

Per frame, per fixture (`SmoothParCanByteEncoder.writeBytes`):

1. Target HSV from the mixer colour.
2. Delta vs. the smoothed state, hue wrapped ±180.
3. **Rate limit**: hue ±15°/frame, sat ±8/frame, val ±10/frame.
4. **EMA**: `s = (1-a)·(s+delta) + a·s`, `a` = Smoothing clamped to [0.7, 0.99]. Higher is slower.
5. Near black (V<5) pull hue/sat 10% toward target so hue doesn't spin.
6. **Smart dimmer** (commit "use dimmer channel too!"): if V<40, dimmer =
   `255·V/40` (min 1) and RGB brightness is boosted by `min(4, 40/V)`. Keeps
   the RGB bytes high where the can's PWM is smoother, uses the dimmer for
   the low end.
7. Emit dimmer, gamma RGB, 0, 0, 0.

Caveats: no `deltaMs`, so smoothing is frame-rate dependent; the per-offset
`HashMap` state never clears.

`Smoothing` is mirrored by a global knob: `GlobalControls.parcanSmoothing`
(a `@Hidden` effect on the Master channel, `GlobalControls.java`). In the
project it is master effect index 1 (OSC path
`/lx/mixer/master/effect/1/parcanSmoothing`), saved at 0.745. Tuning history:
0.94 (Aug 16) → 0.85 → 0.745 (Aug 23–24).

### SpatialAveragingParCanFixture (never used, and can't work as written)

Committed 2025-08-24 18:59, **22 minutes after the last save of `iqe.lxp`**
before departure, so it was never in the project. The idea: average the
nearest N% of model points around the can instead of one pixel. The flaw:
`lastFrameColors` is only populated from the encoder's own `writeBytes`
call, and a `ByteEncoder` only ever sees the bytes LX asks it to encode for
its own fixture. Neighbour colours are never captured, every neighbour reads
0 and is skipped, and the code falls through to "output the direct colour".
Net effect: same as `DMXParCanFixture` plus an O(N log N) sort per radius
change. `brightnessWeight` is declared and never read.

The control UI's "ParCan Spatial Radius" slider (added Aug 22, two days
before the fixture existed) writes `parcanSpatialRadius` on GlobalControls
and does nothing on the real rig.

### Other loose ends in the Java

- `DMXParCanFixture.java` ~line 80 logs the literal string `not_a_field_Claude`.
- `GlobalControls` parameters are `static`; each fixture constructor adds a
  listener that is never removed, so every project reload leaks one.
- No custom UI class; the fixtures use stock `UIStripFixture` plus the
  Global Controls device on Master.

---

## 4. Control surface

**Toggle Parcans** (the kill switch, added Aug 19):

1. `src/control-ui/src/main.ts` ~89–96: button → `sendCommand('toggleparcans')`.
2. `osc-client-unified.ts` ~124–137: JSON `{address:'/iqe/cmd', args:['toggleparcans ']}` over WebSocket `:8080`.
3. `server.ts`: forwards as OSC UDP to `localhost:3232`; LX replies on `3333`.
4. `OscBridge.java`: Java receiver 3232 / transmitter 3333.
5. `LXPluginIQE.handleToggleParcans()` (~377–414): every fixture whose class
   name contains "parcan" gets `deactivate` set to the opposite of the first
   one's current value. Replies `/iqe/cmd/response success|error`.

Notes: it uses `deactivate` (removes the fixture from the model and rebuilds)
rather than `enabled` (just stops output). The button is stateless; the UI
cannot show whether cans are currently on. There is no UI for `Smoothing`;
tune it in the LX GUI under Master → Global Controls.

---

## 5. Bench tools (`src/dmx/`, stdlib-only Python)

Each hand-rolls an Art-Net OpOutput v14 packet and fires one UDP datagram per
update to `CONTROLLER_IP:6454`. No third-party deps.

| Script                   | Purpose                                                            | Env / defaults                                   | Status |
|--------------------------|--------------------------------------------------------------------|--------------------------------------------------|--------|
| `parcan_tester.py`       | 2-can interactive tester: R/G/B/W, rainbow, per-can, flash, custom | `CONTROLLER_IP=10.10.42.68`, `UNIVERSE=1`        | current |
| `dmx_channel_scanner.py` | walk channels one at a time to discover a can's mapping            | `CONTROLLER_IP`, `UNIVERSE` **defaults to 0** — pass 1 | current |
| `dimmer_test.py`         | does the dimmer channel persist between packets?                   | `CONTROLLER_IP`; universe hard-coded 1           | current; result drove the "send dimmer every frame" rule |
| `test_parcans.py`        | first attempt, writes RGB to ch 1–3 (no dimmer) — wrong for 7-ch mode | `UNIVERSE` defaults to 0                       | obsolete; option 7 (manual 7-ch) still handy |
| `add_dmx_parcans.py`     | appends two hard-coded fixtures to `Projects/iqe.lxp` **in place**, no dedupe, old channel map | run from repo root       | **destructive, obsolete — do not run** |

`parcan-surgery.ts` (repo root, `tsx`/`bun`): removes every fixture whose
class contains "parcan" from `Projects/iqe.lxp`, regenerates the 8-can
layout in §2 using the first match as template, and writes
`Projects/iqe_modified.lxp`. It never touches `iqe.lxp`; diff and copy by
hand. There is no npm script for it; `tsx` is only installed inside
`src/control-ui/node_modules`. See `just parcan-surgery`.

Bench order that worked in Aug 2025: `parcan-scan` → `parcan-dimmer` →
`parcan-test` → LX with the 4-corner project → LX with all 8.

---

## 6. Timeline, and what the burn trial looked like

| Date (2025)  | Commit                                  | What                                                                 |
|--------------|-----------------------------------------|----------------------------------------------------------------------|
| 08-14 06:55  | `232bfb6` dmx failz                     | first `DMXParCanFixture` (stock 3-byte RGB, assumed RGB at ch 2–4); README "On Playa" section |
| 08-14 16:12  | `ab46d5e` **Parcans working**           | 7-byte encoder + reflection swap; bench scripts. Verified at home against the Pknight |
| 08-14 16:27  | `b8efc3e` smoothed parcans              | `SmoothDMXParCanFixture` (RGB EMA at first)                          |
| 08-14 16:35  | `246ea6c` parcan smoothing controllable | `GlobalControls.parcanSmoothing`                                     |
| 08-15 20:00  | `13ad4ec` hsv smoothing                 | encoder rewritten to HSV + rate limiting                             |
| 08-15 20:04  | `6bfef49` use dimmer channel too!       | smart dimmer                                                         |
| 08-15 20:29  | `4988f12` parcan, god help us           | `parcan-surgery.ts`                                                  |
| 08-15 20:49  | `9fd766f` revive control, plus toggle   | `/iqe/cmd toggleparcans`, unified control server                     |
| 08-17 16:52  | `bfa5451` place all 8 parcans           | 8-can layout; `iqe-hadFourWorkingParcanCorners.lxp` backup           |
| 08-17 19:04  | `bc20994` more parcans                  | 8 cans into `iqe.lxp`                                                |
| 08-19 12:19  | `099aa1d` added parcan toggle to UI     | web button                                                           |
| 08-22 20:41  | `43c7b7b` mindshow yolo                 | Mindshow effect + "ParCan Spatial Radius" slider (no fixture yet)    |
| 08-24 18:37  | `1fe321a` oplaya ip                     | strips → 10.10.42.80; **last project save before departure**         |
| 08-24 18:59  | `e46273f` spatial average parcan        | never in the project                                                 |
| 12-08        | `b5b1492` playa code??                  | strips → `advatek-local`; Electron ArtNet sniffer with 8 fake parcans on universes 100–107 |

**On playa:** there are no commits between Aug 24 and Dec 8, `Logs/` is
empty, and no notes describe the result. What the repo does show: the
post-playa project copy has a parcan config byte-identical to the
pre-departure one, so either it worked as-is or it was abandoned via the
toggle, and nothing was changed afterward. The Toggle Parcans kill switch and
the Smoothing walk-down from 0.94 to 0.745 are the only field-tuning evidence.
The 4-corner file's name says four cans were verified lighting at home; eight
were never explicitly verified in git.

**Fill this in from memory** (things only you know): did all 8 light? Was
the north-edge row addressed correctly? Flicker? Battery life over a night?
Did the Pknight hold its IP through power cycles? Was the toggle used?

---

## 7. Known problems

1. **One full-universe packet per fixture.** LX sends 8 separate 512-byte
   universe-1 datagrams per frame, each with only its own 7 bytes non-zero.
   If the Pknight treats each as a full refresh, every packet momentarily
   zeroes the other seven cans. It evidently worked at home, but it is a
   flicker and brightness-loss risk, and the strongest argument for one
   8-point fixture (single 56-byte frame).
2. `10.10.42.68` hard-coded in 8 fixture blobs, 5 Python defaults, README,
   NETWORKING-NOTES. Strips already use a hostname (`advatek` /
   `advatek-local` in `/etc/hosts`); parcans should too.
3. `SpatialAveragingParCanFixture` and its UI slider are dead weight (§3).
4. `add_dmx_parcans.py` is destructive and obsolete.
5. Model number mismatch ZQ01104 vs ZQ01047.
6. Spring `ReflectionTestUtils` in production code to reach a private field.
7. The Dec 2025 sniffer's fake parcans are on universes 100–107, channel 0;
   they will never show the real ones (universe 1, ch 7·i).

---

## 8. Next steps

### Hygiene (small, do first)
- Add `pknight` to `/etc/hosts` (home and playa variants) and change the 8
  fixtures' `host` to it, same as the strips' `advatek` flip.
- Delete `add_dmx_parcans.py`; fix the ZQ model number; fix the Amber/White/UV
  comments; remove the `not_a_field_Claude` log.
- Either delete `SpatialAveragingParCanFixture` + the UI slider, or
  re-implement it properly as a master `LXEffect` / `LXOutput` hook that
  snapshots the mixer buffer and feeds the encoder.
- Fix the sniffer's parcan universes/channels so home dev can see the cans.

### Correctness
- Convert to a **single `numPoints=8` fixture** with a custom
  `computePointGeometry` placing each point at its can's coordinates, so one
  universe-1 frame carries all 56 bytes. This removes problem 1 and makes
  addressing a single table.
- Make smoothing time-based (`deltaMs`) so it behaves the same at 30 and 60 fps.
- Give the toggle a state query (`/iqe/parcans/state`) so the button can show on/off.

### Lightkey on the Mac, iPad as a sidecar

Facts verified 2026-09-09 (lightkeyapp.com): Lightkey is **macOS-only**.
There is no iPhone/iPad version. It outputs Art-Net (one node, up to four
universes on the free/standard tier), sACN, and USB DMX interfaces. It
accepts DMX-In, MIDI, and OSC for external control, and 5.1 added an
External Control Log. The two supported ways to put it on an iPad are
(a) a second-display app for the Live view — Apple's own **Sidecar**, Duet,
or Luna Display — giving you a touch surface for the cue/fader grid, and
(b) **TouchOSC** on the iPad sending OSC/MIDI to Lightkey for a custom
control panel. "Sidecar deployment on iPad" therefore means: Lightkey runs
on the laptop, the iPad is its touch front end.

Two integration shapes, in order of effort:

**A. Lightkey owns the par cans; LX hands off.** Zero Java. Point Lightkey's
Art-Net output at the Pknight (`10.10.42.68`, universe 1) with eight generic
"dimmer + RGB (7ch)" fixtures at addresses 1/8/…/50 matching §2, and
`deactivate` the eight LX fixtures (the existing `toggleparcans` OSC command
is exactly this). The two apps must not transmit on universe 1 at the same
time; ArtNet nodes merge HTP/LTP unpredictably and the Pknight has no
documented merge policy. Keep the toggle as the arbitration switch and add
`just parcans-off` / `parcans-on` so it is scriptable. The iPad then becomes
a hands-on par-can console (Sidecar or TouchOSC) independent of the pattern
engine, which is the obvious win for a DJ set.

**B. Lightkey as an input to LX; LX still owns the cans.** LX 0.4-era has no
Art-Net *input*, and binding a second listener on 6454 collides with LX's
own ArtNet socket unless it is on another interface/port (the same class of
hack as the README's "alternate ArtNet port" saga). OSC is the cheap ingress:
Lightkey can send OSC, and LX already listens on 3232 (`OscBridge`) plus its
native `/lx/...` tree. A `/iqe/parcan/<n>/rgb` handler in `LXPluginIQE`
writing a per-fixture override into the encoder, plus Lightkey faders mapped
to `/lx/mixer/master/effect/1/parcanSmoothing`, gets most of the value of A
while patterns keep running. Do A first; only do B if you actually miss the
patterns on the cans while a human is driving them.

Network prerequisite either way: iPad on the `10.10.42.x` camp WiFi, laptop
running Lightkey on the same L2 as the Pknight (dongle at `.11`). Build and
save the Lightkey show file at home against the bench Pknight; do not design
it on playa.

---

## Appendix — reference paths

- Python: `src/dmx/{add_dmx_parcans,dimmer_test,dmx_channel_scanner,parcan_tester,test_parcans}.py`
- Surgery: `parcan-surgery.ts` (root), `package.json`
- Java: `src/main/java/org/iqe/{DMXParCanFixture,ParCanByteEncoder,SmoothDMXParCanFixture,SmoothParCanByteEncoder,SpatialAveragingParCanFixture,SpatialAveragingByteEncoder,GlobalControls,LXPluginIQE,OscBridge}.java`, `pom.xml` ~29–33
- Projects: `Projects/{iqe,iqe-prePlayaSurgery-2025,iqe-hadFourWorkingParcanCorners,iqe_modified,defShouldntDoThis-iqe,bak.iqe}.lxp`
- Control: `src/control-ui/src/{main,osc-client-unified,server}.ts`, `src/nodejs/buildProject.js` ~520–526 (preserves parcans when regenerating strips)
- Network: `NETWORKING-NOTES.md`, `README.md` "Important / On Playa", `PixLite E16-S Mk3-In Queso Emergency.conf` ~350–378, `/etc/hosts`, `src/pixelblaze/claude-code-convo-wifi-pixelblaze.txt` ~2390–2990
- Sniffer: `src/touch-designer/iqe-artnet-electron/src/artnet-sniffer.ts` ~30–117, ~295–345
