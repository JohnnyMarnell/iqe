# PixelBlaze emulator + gallery (staff-infection) → LX Studio / Chromatik

Written 2026-09-09 from a read-only audit of `~/src/staff-infection`
(branch `feat-render-audio`, HEAD `b86ef4f`, 130 commits 2026-03-26 →
2026-09-09) and of the PixelBlaze-in-Java code here. Nothing was executed.

Short version: staff-infection now contains a **complete PixelBlaze runtime
in dependency-free JS**, a **Node process that impersonates a real PixelBlaze
over its WebSocket protocol**, a **596-pattern vendored library with a
deduped index**, a **headless mp4 render pipeline**, and a **gallery** —
and the IQE ceiling is already in it as fixture `grid` (24 × 420 = 10,080 px).
The Java port in this repo (`titanicsend.pattern.pixelblaze` + `glue.js`)
implements a small subset of the PB API by comparison. The cheapest useful
wiring is a **sidecar**: run the emulated device next to LX and add one LX
pattern that consumes its preview frames.

Related: [`RUNNING.md`](RUNNING.md) (`just pb-emu*`),
[`TOUCHDESIGNER.md`](TOUCHDESIGNER.md) (the same "external renderer into LX"
shape).

---

## 1. What "the side renderer" is

There is no literal "side renderer" in either repo. The two things that fit
the description, both in staff-infection:

1. **`HeadlessRenderer`** in `src/emulator/device-host.js` (~161–242). A
   Node-side `PatternEngine` with a `setTimeout` rAF polyfill, created by
   `server.js` and handed to the emulated device as `renderer`. It renders the
   active pattern *beside* the WebSocket server whether or not a browser tab
   is open, and its `getFrame()` is what the device pushes as PixelBlaze
   `previewFrame` binary packets (type 5, RGB bytes) at 30 Hz to any client
   that sent `{"sendUpdates":true}`. Methods: `load(source,name)`,
   `loadBytecode(bytes,name)`, `setPixelCount(n)`, `setVar`, `setControl`,
   `getVars`, `getFrame()` → `Uint8Array(pixelCount*3)`, `getStats()`,
   `start/stop`, `brightness`. Added 2026-09-04 ("pixelblaze emulator impl,
   first pass").
2. **`preview-worker.js`** in `src/emulator/js/` — a Web Worker that loads
   the engine with no canvas and posts a `Float32Array [r,g,b,…]` per frame
   (the gallery's hover live preview, 2026-09-02).

Both are exactly the shape LX needs: pattern in, RGB array out, no canvas.
Number 1 already ships frames over a socket.

---

## 2. The emulator

### 2.1 Core (dependency-free ES5, runs in browser, worker, Node, Bun)

| File (`src/emulator/js/`) | Role |
|---|---|
| `pixelblaze-api.js` | Every documented PB builtin as one `api` object: math, trig, `time/wave/triangle/square/smoothstep/mix/bezier*`, `perlin*`/`prng*`, `hsv/hsv24/rgb`, `setPalette/paint`, all `array*`, transforms (`translate/scale/rotate*`), map queries, clock, GPIO/sequencer stubs. `time(interval)` = `(t / (65.536·interval)) % 1`, matching hardware. State is module-global → **one engine per JS realm**. |
| `pattern-engine.js` | `PatternEngine({pixelCount, fps, brightness, onFrame, onControls, onError})`. `loadPattern(src)` rewrites `export var/function`, adds `= 0` default args, pre-declares every identifier as 0 (PB semantics), builds slider/toggle/trigger/picker controls. `_renderFrame(ts)` calls `beforeRender(delta)` then the best of `render3D/render2D/render` per pixel with map coords. `setPixelMap(map)`, `setFixture(type, opts)`, `setControl`, `setVar` (whole arrays only, like firmware), `getPreviewData()` → `Uint8Array` RGB with brightness applied, `pixels[i] = {r,g,b}` floats. |
| `fixtures.js` | Map generators returning normalized `[x,y(,z)]` in 0..1 (same convention as PB hardware and LX's `xn/yn/zn`): `strip`, `ring`, `fibonacci`, `blob`, `matrix`, **`grid` (`{rows:24, cols:420}` zigzag, cell-centred — the IQE ceiling)**, `helix`, `cube`, `prism`, `cylinder`; `normalizeMap`, `parseMapSource` (JSON array **or** a PB Mapper-tab function body). |
| `pb-vm.js`, `pb-isa.js`, `pb-disasm.js` | 16.16 fixed-point bytecode VM for compiled PB programs; ISA extracted from the stock compiler. Hardware-faithful on fractional indices where the source engine is not. |
| `pb-compiler.js` | Wraps the stock compiler bundle (`pixelblaze-exploring/compiler/3.70.js`) → `{bytecode, exports}`. |
| `pb-device.js`, `pbp.js`, `lz-string.js` | The PixelBlaze v3 WebSocket protocol, transport-agnostic; PBP container parse/build. |
| `led-renderer.js`, `live-preview.js`, `preview-worker.js` | Canvas glow renderer with 3D camera; gallery hover preview. |
| `pb-live-push.js` | Browser → real PixelBlazes: discovers devices, keeps `ws://ip:81` open, pushes patterns/vars/controls (compiles in-browser if the device lacks the pattern). |
| `audio-sensor.js` | Web Audio → 32-bin sensor-board frames at 40 Hz (`frequencyData`, `energyAverage`, `maxFrequency`, …), gain/AGC, and an offline `analyseBuffer(pcm, rate)`. |

### 2.2 The emulated device (`just dev` in staff-infection)

`bun src/emulator/server.js` → HTTP **:8080** (emulator page, gallery, APIs)
and **`ws://localhost:81`** speaking the real protocol. The stock PB IDE,
the `pb` CLI (`--ip 127.0.0.1`), pixelblaze-client, Firestorm-style tools
all treat it as hardware. Implemented: `getConfig`, `sendUpdates`, all
settings keys, `setVars/getVars`, `setControls/getControls`, sequencer and
playlist commands, `listPrograms` (binary 7), `activeProgramId`, `getSources`,
`putSourceCode` (PBP upload → `.emulator-store/patterns/`), `putByteCode`
(runs in the VM), `putPixelMap` (stored, see gap), `previewFrame` out
(binary 5, `[0x05][r,g,b × pixelCount]`, 30 Hz), stats JSON ~1 Hz. Not
implemented: HTTP device endpoints on :80, sync groups, OTA, crossfade, UDP
discovery beacons.

HTTP on :8080: `/api/patterns`, `/api/pattern/<file>` (GET/PUT),
`/patterns/index.json`, `/api/renders`, `/renders/<file>`, `/api/pixelblazes`
(pb CLI cache), `/api/pixelmap?ip=`, `POST /api/sensor` (sensor-board JSON →
`setVars`), `/compiler/3.70.js`, `/ide/*` (the unpacked stock IDE).

**Gap that matters here:** the headless device does not apply a pixel map —
`_receivePixelMap` stores the bytes but never calls `engine.setPixelMap`, and
`server.js` passes only `pixels`/`brightness` to `HeadlessRenderer`, not
`--shape/--rows/--cols`. So over the socket, 2D patterns get synthetic 1D
coords until a ~5-line patch (§5 step 2).

### 2.3 Gallery and pattern library

- `src/patterns/sources.json` registers 14 sources (Electromage patterndb
  scrape, pb-examples, the user's fork of zranger1's PixelblazePatterns,
  Titanic's End's te-pixelblaze, jasoncoon fibonacci, pbbeacon, glowflow, …).
  `just fetch` vendors them into `src/patterns/<key>/`; `just sync` also
  scrapes Electromage, infers metadata from source (**`dimensions` from which
  of `render/render2D/render3D` is exported**, `controls[{fn,name,type}]`,
  `exportVars`, `features`, description/author/votes), dedupes, and writes
  `src/patterns/index.json` (592 entries, 113 marked `duplicateOf` →
  **479 canonical; ≈239 declare `render2D`**), then renders whatever the
  gallery is missing.
- `renders/` holds 816 mp4 + 816 posters. Suffixes: none = 100-px strip,
  **`_grid` = the 24×420 ceiling (220 clips)**, `_prism` = 8³, `_fibonacci`.
  (`0JG-`/`1JG-` prefixes are Jon Garrison's own pattern names, not a
  convention.)
- `gallery.html`: masonry of tiles with posters, hover live preview, multi
  mode (one tile per dimension), search DSL, facets, a broadcast drawer that
  live-pushes to real PixelBlazes on hover. Tile click deep-links the
  emulator: `#pattern=<name>&shape=grid&pixels=10080`.
- Hosted: `just export-web` → static bundle into the j5 app repo
  (`~/src/app/public/pixelblaze-emulator`, Vercel, login-gated).

### 2.4 Render pipeline

`tests/e2e/render-patterns.js` (`just render-patterns`) drives the engine in
headless Chromium with **fake timestamps** (`engine.running = true;
engine._renderFrame(ts += 1000/fps)`), pipes JPEG frames to ffmpeg. Flags
for shape/pixels/sliders/dims/audio (`--audio track.mp3 --agc` runs the
sensor-board analysis offline and applies 40 Hz frames via `setVar`, then
muxes the track). `--auto` renders only missing variants. 5 s of video ≈ 1 s
wall.

---

## 3. Versus the Java port in this repo

| | iqe (`titanicsend.pattern.pixelblaze.Wrapper` + `glue.js`) | staff-infection |
|---|---|---|
| Engine | Nashorn 15.4 from `vendor/glxstudio.jar`, ES6 flag | V8/JSC (browser, Bun, Node); pure JS files |
| API coverage | `random array time wave triangle clamp hypot hsv rgb rgba paint swatch` + TE audio extras | whole documented API incl. perlin*, transforms, palettes, arrays*, smoothstep/mix/bezier, sensor vars, clock |
| PB semantics | none (plain JS) | zero-init identifiers, missing-arg → 0, `export var` get/set, whole-array `setVars` |
| Bytecode / `.pbb` / `.epe` | no | VM + PBP decode |
| Catalog | `patternData.json.gz` (1.5 MB dump, name → source) + 115 loose files | 14 sources, deduped index with dimensions/controls/metadata |
| Previews | none | 816 clips incl. 220 on the ceiling shape |
| Speed at 10,080 px | unknown, Nashorn has no comparable JIT | 30 fps in Chromium for grid renders |
| Concurrency | one Nashorn `Bindings` per pattern instance | one engine per JS realm (api singletons) |

The Java port's known gaps (`PixelblazeHelper` TODOs: palettes are a fixed
cyan→magenta, some 3D scripts render nothing) are exactly what the emulator
already has.

---

## 4. Three ways to wire it in

### (i) Reuse the catalog and gallery to *choose* patterns for LX — do first, no runtime change

- Read `~/src/staff-infection/src/patterns/index.json` in iqe (or copy it into
  `src/main/resources/`): filter `dimensions` includes `"2D"` and no
  `duplicateOf` (≈239), expose `name`, `file`, `controls[]` (auto-build LX
  `CompoundParameter`s from `slider*` names — `PixelBlazeBlowser` already does
  this for `glue.js` sliders), `exportVars`, `features`, `description`.
  Replace or augment `patternData.json.gz` in `PixelBlazeBlowser`. Load
  sources from `src/patterns/<file>`. `just pb-emu-2d` lists them.
- Use the gallery as the picker: `_grid` tiles are literal ceiling previews;
  `just pb-emu` then `http://localhost:8080/gallery.html`.
- Bulk-preview a shortlist on the ceiling: `just pb-emu-render --dim 2 --all`,
  or `just pb-emu-render fire spark --slider "speed=0.3"`, or with a track
  for sound-reactive ones (`--audio set.mp3 --agc`).

### (ii) Sidecar process feeding LX — recommended for a working ceiling quickly

Keep LX as the mixer (autopilot, transitions, effects, par cans stay
coherent). Two variants.

**(ii-a) Use the emulated device as-is and make LX a PixelBlaze client.**

Staff-infection patch (small): in `server.js` pass the boot shape to the
headless engine (`renderer.engine.setFixture(shape, {rows, cols})`), and in
`pb-device.js _receivePixelMap` decode the map and call
`renderer.engine.setPixelMap(map)`. Then in iqe:

```
PixelblazeSidecarPattern extends LXPattern
  - java.net.http.WebSocket (Java 17 built-in) to ws://127.0.0.1:81
  - on open: {"pixelCount":<model.points.length>}, {"activeProgramId":<id>}, {"sendUpdates":true}
  - on binary frame with bytes[0]==5: colors[points[i].index] = rgb(bytes[1+3i..])
  - DiscreteParameter `script` populated from GET http://127.0.0.1:8080/api/patterns
    (id = sha1(file path) base64 → 17 alnum chars, or from listPrograms binary 7)
  - LX parameter listeners → {"setControls":{"sliderX":v}}
  - iqe audio (TEAudioPattern bands) → {"setVars":{"frequencyData":[…32…],"energyAverage":…,"light":0}}
```

30 KB/frame × 30 Hz ≈ 0.9 MB/s over loopback. Bonus: the `pb` CLI, the
gallery's broadcast drawer, and the stock IDE can all drive the same device,
so "push from the gallery → it shows on the ceiling in LX" needs no extra
code. Run with `just pb-emu` (boots `--shape grid --rows 24 --cols 420
--pixels 10080`) next to `just lx`.

**Map fidelity.** `grid` is an idealized row-major zigzag. LX's point order
is the model order (rafter 1 strip 1 → 3, rafter 2 …), and the physical
zigzag is whatever `buildProject.js` decided. Rather than trusting `grid`,
export the real map from LX (`[[p.xn, p.zn]]` for the top-down ceiling plane,
or `[[xn,yn,zn]]`) as JSON and push it with `putPixelMap` / the
`parseMapSource` path, so the emulator renders the actual geometry.

**(ii-b) Tiny dedicated Node sidecar → raw UDP → LX sink pattern.**

~60 lines using the engine directly:

```js
globalThis.requestAnimationFrame = () => {};                 // drive manually
const { PatternEngine } = require('./src/emulator/js/pattern-engine.js');
const fx = require('./src/emulator/js/fixtures.js');
const engine = new PatternEngine({ pixelCount: 10080, brightness: 1 });
engine.setPixelMap(JSON.parse(fs.readFileSync('iqe-map.json')));   // from LX, or fx.fixtures.grid(10080,{rows:24,cols:420})
engine.loadPattern(fs.readFileSync(patternFile, 'utf8'));
engine.running = true;
let ts = 0;
setInterval(() => { ts += 1000/40; engine._renderFrame(ts);
  const u8 = engine.getPreviewData();                               // Uint8Array 10080*3
  /* chunk into ≤ 1680-px datagrams with a {seq, offset} header → udp 127.0.0.1:<port> */ }, 1000/40);
```

iqe `UdpFramePattern` reassembles into `colors[]`. Pattern/slider control over
OSC (`/iqe/cmd`, already plumbed) or a second UDP channel. Loses the free
`pb`/gallery integration of (ii-a); wins by not needing the WS protocol.

**Not recommended:** sidecar → ArtNet straight to the PixLite. It bypasses LX
(no mixing, transitions, effects, autopilot), fights LX for the same
universes, and would have to replicate `buildProject.js`'s universe striping.
Only useful as a smoke test.

**Concurrency:** one pattern per sidecar process (api singletons). N LX
channels → N sidecars on N ports.

### (iii) Port the runtime into Java

- **Drop-in experiment first (a day):** `pixelblaze-api.js` and
  `pattern-engine.js` are DOM-free ES5. `engine.eval(pixelblaze-api.js)` +
  `eval(pattern-engine.js)` in the existing Nashorn ES6 engine (they export
  onto the global), then per LX frame call `engine._renderFrame(nowMs)` via
  `Invocable`/`JSObject` and read `getPreviewData()` → `byte[]`. That replaces
  `glue.js` with the full API and PB semantics, and `fixtures.normalizeMap`
  handles LX points. Risks: Nashorn ES6 gaps (the engine emits `a = 0` default
  params, so `--language=es6` is mandatory), and Nashorn speed at 10k px.
- **GraalJS** (`org.graalvm.js:js` + `js-scriptengine`) runs the same files
  with a real JIT; benchmark against Nashorn on the grid at 60 fps before
  committing.
- **Java port of `pb-vm.js`** (~22 KB stack machine + generated ISA table):
  runs `.pbb`/`.epe` bytecode with hardware-exact fixed-point math and no JS
  engine at all. Bigger effort; only if JS-in-JVM performance is inadequate.

---

## 5. Ordered next steps

1. **Catalog in LX (no runtime change).** Read `index.json`, filter 2D +
   canonical, feed `PixelBlazeBlowser`'s dropdown, auto-create sliders from
   `controls[]`, load sources from `src/patterns/<file>`. Preview with the
   `_grid` tiles.
2. **Patch staff-infection's headless map** (`server.js` shape → engine;
   `putPixelMap` → `setPixelMap`) and add an LX pixel-map export
   (`[[xn, zn]]` per point, JSON) so the emulator renders the real ceiling
   geometry instead of the idealized grid. Add a `just` recipe here that
   writes the map from a running LX (OSC or a tiny pattern that dumps it).
3. **`PixelblazeSidecarPattern` in iqe** per (ii-a). Java 17's
   `java.net.http.WebSocket`, `previewFrame` → `colors[]`, parameters →
   `setControls`, iqe audio → `setVars`. Run `just pb-emu` alongside `just lx`;
   consider adding it to `RUN.sh`.
4. **Measure.** fps of the sidecar at 10,080 px on a few heavy 2D patterns
   (perlin-based) vs the Nashorn `PBXorcery` path. Decide whether (iii) is
   worth it for in-process use.
5. **Longer term:** Java `pb-vm` port for exact `.pbb`/`.epe` playback; use
   `render-patterns --audio` clips as the review artifact for sound-reactive
   ceiling patterns.

---

## 6. State of staff-infection (for context)

- Active: 2026-09-09 landed "drive sound-reactive patterns from an audio
  file"; a 5-line uncommitted timeout tweak in `render-patterns.js`.
- Tests: 16 Node unit files (~274 tests incl. 60 for the device protocol and
  a differential VM ratchet), 9 Playwright specs, ~133 pytest. Last
  Playwright run passed.
- Known limitations: one engine per realm; headless device ignores pixel
  maps (above); source engine differs from hardware on fractional indices
  and 16.16 wrap (the VM path is faithful but only used for bytecode
  uploads); no crossfade/sync groups/HTTP endpoints/discovery beacons;
  `setPixelCount` caps at 12,000.
- Open items from `docs/bytecode-vm-plan.md`: hardware oracle for
  fixed-point edge cases, `arrayReplaceAt` bytecode, perlin/prng exactness,
  compile-and-run-VM by default.
- Siblings: `~/src/staff-infection-ui` is a stale second checkout (May 2026,
  merged). `~/src/pbjs` is a 229-file Electromage scrape superseded by the
  `electromage.com` source. `~/src/pixelblaze-client` is the user's fork with
  the `pb` CLI (active 2026-09-08). `~/src/PixelblazePatterns` is the fork
  with the CCA infinite-loop fix that `sources.json` vendors.

---

## Appendix — paths (staff-infection)

- Engine: `src/emulator/js/{pixelblaze-api,pattern-engine,fixtures,pb-vm,pb-isa,pb-disasm,pb-compiler,pbp,lz-string}.js`
- Device/server: `src/emulator/js/pb-device.js`, `src/emulator/device-host.js`, `src/emulator/server.js`
- Gallery/preview: `src/emulator/gallery.html`, `src/emulator/js/{live-preview,preview-worker,led-renderer,pb-live-push,audio-sensor,search-query}.js`
- Catalog: `src/patterns/{sources.json,sources.lock.json,index.json,dedupe-overrides.json}`, `src/python/scrapers/{sync,sources,dedupe}.py`
- Renders: `tests/e2e/render-patterns.js`, `scripts/{generate-posters,shrink-gallery-renders,render-manifest,export-web}.mjs`, `renders/manifest.json`
- Specs: `CLAUDE.md`, `PIXELBLAZE_API.md`, `PLAN.md`, `docs/{architecture,bytecode-vm-plan,mapping,more-sources-plan}.md`, `justfile`
- iqe side: `src/main/java/titanicsend/pattern/pixelblaze/{Wrapper,PixelblazePattern}.java`, `src/main/java/org/iqe/pattern/pixelblaze/{PixelBlazeBlowser,PixelblazePatterns,PixelblazeHelper,UIPixelblazePattern}.java`, `src/main/resources/pixelblaze/{glue,moarPaste}.js`, `src/main/resources/patternData.json.gz`
