# Running IQE — every subsystem, how, and what's broken

Companion to the root [`justfile`](../justfile) (`just` lists every recipe).
Written 2026-09-09 from a read-only audit of `master` = `dc67bec` (Dec 2025);
nothing was executed, so treat the first run of anything as a test.

Other docs: [`DMX-PARCANS.md`](DMX-PARCANS.md), [`TOUCHDESIGNER.md`](TOUCHDESIGNER.md),
[`PIXELBLAZE-EMULATOR-LX.md`](PIXELBLAZE-EMULATOR-LX.md), [`../NETWORKING-NOTES.md`](../NETWORKING-NOTES.md),
[`../PIXELBLAZE_FLEET.md`](../PIXELBLAZE_FLEET.md), [`../SPEED_CONTROL_README.md`](../SPEED_CONTROL_README.md).

---

## 1. Map

| Subsystem | Where | Lang | Status | Start with |
|---|---|---|---|---|
| LX / Chromatik + IQE plugin | `src/main/java`, `Projects/iqe.lxp`, `vendor/glxstudio.jar` | Java 17 | **live**, the main thing | `just build && just lx` |
| Control web UI + OSC bridge | `src/control-ui` | TS (Vite, tsx) | **live** (Dec 2025) | `just control` |
| Legacy web app + OSC bridge | `src/nodejs` | JS | superseded, partly broken | `just legacy-web` |
| Project-file generator | `src/nodejs/buildProject.js` | JS | works, out of sync with `iqe.lxp` | `just lxp-regen` (danger) |
| Par can surgery | `parcan-surgery.ts` | TS | works | `just parcan-surgery` |
| Beat detection → LX tempo | `src/audio-tooling` | Python | works (2023), env must be rebuilt | `just beat` |
| Jupyter tempo notebook | `src/audio-tooling/jupyter` | Docker | Docker not installed here | `just jupyter` |
| PixelBlaze fleet monitor | `src/pb` | Python (Flask) | works (Aug 2025), docs wrong | `just pb-monitor` |
| PixelBlaze WiFi provisioning | `src/pixelblaze` | Python (click) | works, needs `click` | `just pb-scan` |
| Flamecaster bridge (PB corners) | `src/scripts/flamecaster_conf.py`, `../Flamecaster` | Python | RUN.sh path broken | `just flamecaster` |
| DMX par cans bench tools | `src/dmx` | Python stdlib | works | `just parcan-test` |
| ArtNet simulator (Electron) | `src/touch-designer/iqe-artnet-electron` | TS/Electron | **works** | `just sim` |
| ArtNet simulator (matplotlib) | `src/touch-designer/iqe_render.py` | Python | works | `just sim-py` |
| TouchDesigner sender | `src/touch-designer/*.toe`, `*.py` | TD | never finished | see TOUCHDESIGNER.md |
| Video scene tools | `src/scripts/detect_*.py` | Python | works | `just scenes` |
| PixelBlaze emulator/gallery | `~/src/staff-infection` | JS/Python | sibling repo, live | `just pb-emu` |
| Raspberry Pi service | `src/pb/install_pi_service.sh` | systemd | **broken** (script missing) | — |
| `zzz_misc/` | | | dead, pre-Chromatik | — |

---

## 2. Environment setup

**Java.** JDK 17 Temurin (`.sdkmanrc` = `17.0.6-tem`, IntelliJ run config pins
`temurin-17`). Maven wrapper 3.9.1 is committed. Nothing in `RUN.sh` runs
`sdk env`, so whatever `java` is first on PATH gets used (currently a JDK 21;
class files target 17 so it still runs). `just jdk` shows both.

**Chromatik.** `vendor/glxstudio.jar` is LX **0.4.2-SNAPSHOT** (alpha built
2023-07-18) committed as a plain 10 MB blob, bundled with Nashorn 15.4. The
main class `heronarts.lx.studio.ChromatikIQE` lives **only** in that jar; its
source was deleted in commit `78ecb18` (2025-07-23). `just lx-main-src` prints
it. It overrides `getPermissions()` to bypass Chromatik licensing, adds
`org.iqe.LXPluginIQE` as a classpath plugin, and accepts `--headless`,
`--force-output`, `--clean`, `--opengl`, `--warnings`, `--disable-zeroconf`,
`--disable-preferences`, `--require-license`, `<file>.lxp` (resolved as
`Projects/<file>`). `src/scripts/download_chromatik.sh` is a no-op (`exit 0`
on line 2) still wired into Maven's `initialize` phase, hence the "ToDo:
upgrade to Chromatik v1.0.0" line on every build. `binaries/glxstudio-1.0.0-jar-with-dependencies.jar.gz`
is the never-adopted 1.0.0.

**Node.** Root `package.json` declares npm workspaces `src/control-ui`,
`src/nodejs`, `src/touch-designer/iqe-artnet-electron`, so a root
`npm install` hoists shared deps to the root `node_modules`. `.nvmrc`:
`src/control-ui` wants **v24**, `src/nodejs` wants **v18.16.1**, root has
none. `tsx` and `vite` are only in `src/control-ui/node_modules`.
`just npm-install` runs `npm run install:all`.

**Python.** The committed story (README: conda, python 3.11) does not match
the machine. The `.venv` that exists is a **uv** venv on Python 3.10.14 whose
base interpreter (`~/miniforge3`) has been uninstalled, so it is dead.
`requirements.txt` was overwritten in Aug 2025 with the PixelBlaze-monitor
deps; `src/audio-tooling/requirements.txt` is a symlink to it and therefore
no longer lists librosa/pyaudio. The pinned audio set that worked is
`src/audio-tooling/old.requirements.txt`. Rebuild with:

```
just venv          # PB monitor + pb.py deps (adds click, missing from the file)
just venv-audio    # + pyaudio/librosa/python-osc (brew portaudio)
just venv-video    # + opencv/scipy (brew ffmpeg)
just venv-sim      # + matplotlib
just venv-all
```

**Other tools.** `just` (brew), `uv` (brew, 0.8.11 present), `ffmpeg` for the
video tools, BlackHole for beat detection, Docker Desktop for Jupyter (the
`/usr/local/bin/docker*` symlinks are dangling — it was uninstalled).

---

## 3. Ports and network

| Port | Proto | Owner | Notes |
|---|---|---|---|
| 3030 | OSC UDP in | LX native (`iqe.lxp` engine.osc receivePort) | |
| 3131 | OSC UDP out | LX native transmit | Java `OscBridge` also *listens* here to tap everything LX emits |
| **3232** | OSC UDP in | IQE plugin `OscBridge` | what every client sends to (control-ui, midi, beat_detective, `just osc`) |
| **3333** | OSC UDP out | IQE plugin `OscBridge` | relayed LX stream + `/iqe/*` replies; control-ui and legacy bridge bind this |
| 8080 | WebSocket | control-ui `server.ts` **or** legacy `scripts.js` | mutually exclusive |
| 8282 | HTTP | control-ui: Vite dev, or `server.ts` only with `NODE_ENV=production` | |
| 8181 | HTTP | legacy web app, only when `IQE_WEB_PORT=8181` (its own `npm start` uses **80**) | |
| 6454 | ArtNet UDP | PixLite (`advatek` = 10.10.42.80), Pknight (10.10.42.68), simulator on localhost | |
| 6455 | ArtNet UDP | Flamecaster (LX's `FlamecasterFixtures` override the port) | |
| 7890 | — | `port` on the 72 strip fixtures | vestigial OPC default, ignored for ArtNet |
| 1889 | UDP | PixelBlaze discovery beacons | fleet monitor listens |
| 81 | WebSocket | real PixelBlazes, and staff-infection's emulated device | |
| 8000 | HTTP | PixelBlaze fleet monitor (`pbfleet_enhanced.py`) | `PIXELBLAZE_FLEET.md` said 5000, wrong |
| 5000 | HTTP | `pb_web_button.py` only | |
| 8585 | HTTP | Flamecaster web UI | |
| 5005 | JDWP | `just lx-debug` | IntelliJ "Already Running" config |
| 8888 / 8889 | HTTP | Jupyter lab / kernel server | |

**Home vs playa.** The 72 ceiling strips in `Projects/iqe.lxp` point at
hostname `advatek-local`. On this laptop `/etc/hosts` has
`127.0.0.1 advatek-local` and `10.10.42.80 advatek`, so **the committed
project currently sends the ceiling to localhost** (the simulator). To go
live either edit `/etc/hosts` or `just lxp-strip-host advatek`. Par cans are
hard-wired to `10.10.42.68` in the project; the same hostname trick would
make that a one-line flip too. `just hosts` shows the aliases.

Playa addressing (README): router `10.10.42.1`, PixLite `10.10.42.80`,
Pknight DMX node `10.10.42.68`, laptop dongle static `10.10.42.11`.

---

## 4. LX / Chromatik

```
just build                 # ./mvnw clean package -DskipTests → 60 MB fat jar
just lx                    # java -XstartOnFirstThread -cp <fat>:<vendor> ChromatikIQE iqe.lxp
just lx other.lxp          # any file in Projects/
just lx-headless           # --headless --force-output
just lx-debug              # JDWP :5005
just run-all               # RUN.sh: Flamecaster (broken) + control UI + build + LX
```

Facts that matter:

- **Classpath order matters.** The iqe jar must precede `vendor/glxstudio.jar`
  because `src/main/java/heronarts/lx/pattern/LXPattern.java` is a patched
  copy of LX's class (adds the global `speed` time-scale in `onLoop`). The fat
  jar has no `Main-Class`; the main class comes from the vendor jar.
- **cwd must be the repo root.** Project resolves to `Projects/<arg>`, logs to
  `Logs/`, `ImagePattern`/`VideoPattern` defaults are cwd-relative
  (`src/main/resources/images/heart-8075.png`, `videos/sample2-24p-120fps.mp4`).
- `Projects/iqe.lxp` has **111 fixtures**: 72 `NagBugglerSaberOfLightFixture`
  (ceiling, 140 px each, 3 per rafter × 24), **31** `FlamecasterFixtures$PatchedStripFixture`
  netStrips (→ 127.0.0.1:6455, enabled), 8 `SmoothDMXParCanFixture`.
  `just lxp-fixtures` prints the histogram. The root CLAUDE.md's "72 strips
  only / removed 32 netStrips" was wrong.
- There is no "Test" channel any more; it is **"Visuals"** (~line 41800).
  Channels: Foreground[group], FG Pattern, PB Patterns, Color, Background[group],
  BG Pattern, Color, Visuals, Pong, ignore_FX, ignore_FXold.
- Registered patterns (19, `LXPluginIQE.java` ~65–87): ZipStrip, HolyTrinities,
  PillarFire, BouncingDots, PianoRoll, MindLikeWater, EqVisualizer, Pong,
  PongOSC, Image, Video, PBXorcery, PBAudio1, PBFireworkNova, PixelBlazeBlowser,
  PBTemp, DiagnosticColorCycle, Diagnostics, BassBreath. On disk but not
  registered: `PixelblazeSandbox`, `PixelblazeParallel`. `NagBugglerSaberOfLightFixture`
  is not registered either (loads by class name from the project, won't appear
  in the add-fixture menu).
- `VideoPattern` uses JavaCV with **macOS arm64 natives only** (`pom.xml`).
- `pom.xml` pulls `spring-test` at compile scope purely for `ReflectionTestUtils`
  (used to poke LX privates in fixtures and `LXUtils`). Breaks on LX upgrade.
- Tests: `src/test/java/.../VideoPattern*Test.java` exist, all four methods
  `@Disabled`. `just test-java` runs 0 effective tests.

**PixelBlaze inside LX.** `titanicsend.pattern.pixelblaze.Wrapper` runs PB JS
in Nashorn (ES6) with `src/main/resources/pixelblaze/glue.js` as a partial PB
API shim. `PixelBlazeBlowser` exposes every entry of
`src/main/resources/patternData.json.gz` (1.5 MB Electromage dump) plus the
115 files under `pixelblaze-patterns/` as a `script` dropdown, with PB sliders
mapped to LX params. `PBTemp` hot-reloads `resources/pixelblaze/tmp.js`
(symlink → `Eye_of_Sauron.js`) for live editing. Missing vs. real PB: perlin,
transforms, palettes, most `array*`, `export var` set/get, sensor vars. See
[`PIXELBLAZE-EMULATOR-LX.md`](PIXELBLAZE-EMULATOR-LX.md) for the plan to close
that gap.

**Audio.** LX's own audio meter feeds `TEAudioPattern` each frame; derived
levels/ratios/EMAs are the global modulators registered by `AudioModulators`
(`GlobalClick`, `BootsClick`, `BassLevel`, … category "Anal-yzed"). Tempo can
come from LX's internal clock or the Python beat detector over OSC.

**Autopilot.** `AutopilotIQE` (Justin K Belcher's library) generates LFOs for
the parameters listed in `LXPluginIQE.initializeAutopilot`, drives
transitions/auto-cycle, and handles solo. UI section "AUTOPILOT" in the left
pane.

**IntelliJ.** `.run/Run.run.xml` = main class + `iqe.lxp` + `-XstartOnFirstThread`;
`.run/Already Running.run.xml` = remote attach to :5005 (use `just lx-debug`).

---

## 5. Control UI (`src/control-ui`) and the OSC contract

```
just control        # Vite :8282 + WS :8080 + OSC bridge (npm run control)
just control-prod   # build dist/ then NODE_ENV=production npm start (:8282 + bridge)
just control-bridge # bridge only — plain `npm start` is this since Dec 2025
just midi           # CC 21 → speed
```

Flow: browser → `ws://<host>:8080` JSON `{address, args}` → `server.ts` →
OSC UDP `localhost:3232` → Java `OscBridge` → either `/iqe/*` handled by the
plugin or forwarded to `lx.engine.handleOscMessage`. Everything LX emits on
3131 is re-broadcast to 3333 → WS clients.

Controls in `main.ts`: Speed Up slider (`/lx/mixer/master/effect/1/speed`),
Transition All, Color Change, Hold 30s, Solo Visuals (`/iqe/cmd solo visuals`),
Pong P1/P2 sliders (`/iqe/cmd pong1 <v>`), Toggle Parcans, Mindshow on/off +
sensitivity (`/lx/mixer/master/effect/5/...`), ParCan Spatial Radius (no-op on
the real rig), Debug: Query OSC Paths.

Master effect indices in `iqe.lxp`: 1 GlobalControls, 2 Audio NO_TOUCHY,
3 Strobe, 4 Blur, 5 Mindshow. `Orchestrator.java` hard-codes effect 1.

`/iqe/cmd` commands (`LXPluginIQE.java`): `solo <substr>`, `toggleparcans`,
`pong1 <0..1>`, `pong2 <0..1>`. Replies on `/iqe/cmd/response`.

Without any Node at all: `just osc <address> <args…>` sends a raw OSC packet to
3232 (stdlib python), `just osc-sniff` prints the 3333 stream.

Known issues: `osc-client-unified.ts` connects twice (constructor + explicit
`connect()`), harmless. `midi-bridge.ts` sorts the DAW device last, not
first. `osc-client.ts` is the unreferenced original.

---

## 6. Legacy web app (`src/nodejs`)

The 2023 "IQE LED Command Staishe" page (jQuery + Tailwind + XY pad) served
by `scripts.js bridge`. Its `npm start` binds **port 80**; README's 8181 only
happens via `start-speed-control.sh`, which is itself broken (starts this
*and* control-ui, both on WS 8080/UDP 3333). `just legacy-web` runs it on 8181
with the right OSC ports.

Two reasons it still exists: `GET /state` (last value per OSC address, used
to seed the page) and the Launchkey Mini MK3 MIDI relay (`/iqe/midi` →
`PianoRollPattern`). Its channel-index controls (channel 1 "Form", 2 "Color")
target stale indices (1 is now the Foreground group). The committed
`dist/osc-js` symlink dangles under npm workspaces (osc-js got hoisted), so
the page may 404 on `osc.min.js`.

`buildProject.js` (`just lxp-regen`) regenerates the strip fixtures from
geometry constants: 24 rows × 3 columns, 140 px × 5 units, rows 105 apart,
`y=700`, `yaw=-90`; ArtNet 3 universes per rafter, base `1,4,7,…` with rafter
16 remapped to 73/74 (the README's "semi wonky jump"), strips at
`(u,0) (u,420) (u+1,330)`. It **overwrites `Projects/iqe.lxp` in place**,
resets host to `10.10.42.80`, re-adds 32 netStrips, and preserves parcans.
Quit LX first; diff afterwards.

---

## 7. Audio analysis (`src/audio-tooling`)

`beat_detective.py` is the one real tool: PyAudio reads a loopback device
(default input name containing "BlackHole 2ch"), librosa `beat_track` over a
10 s window every 10 s plus a 1.5 s phase check every second, and OSC to
`127.0.0.1:3232`: `/lx/tempo/beat 1.0` per beat, `/lx/tempo/bpm <f>` +
`/lx/tempo/clockSource 0` on tempo update, `clockSource 2` on clear. BPM ≥160
is halved. Run from its own directory (`just beat`). Everything else in the
directory is 2023 scratch (`audio_test.py` is broken — references `sd`
without importing it).

Jupyter: `compose.yaml` has `jupyter-lab` (:8888, no token) and
`jupyter-server` (:8889, token `a`) with librosa; `tempo.ipynb` is the
exploration that produced the beat detector. `docker compose` (v2 syntax),
and Docker is not currently installed.

---

## 8. PixelBlaze fleet (`src/pb`, `src/pixelblaze`)

**Monitor.** `pbfleet_enhanced.py` (Flask, **:8000**, cwd must be `src/pb`)
is the live app: UDP 1889 discovery thread, 10 s polling via
`pixelblaze-client` (name, patterns, active pattern, sequencer, brightness,
fps), `devices_state.json`, endpoints `/api/devices`, `/api/health`,
`/api/sync/<pattern>`, `/api/sync-random`, `/api/common-patterns`,
`/api/setup-sync`, `/api/swell-and-scatter`, `/api/pulse`, `/api/pulse-quick`.
`pbfleet.py` (FastAPI) and `old_pbfleet.py` are abandoned earlier versions;
`src/pb/README.md` describes the FastAPI one and is therefore mostly wrong
(its `--dev` references a nonexistent module). No Firestorm integration
exists anywhere despite `PIXELBLAZE_FLEET.md`.

**Pi.** `pixelblaze-monitor.service` runs `/home/pi/iqe/pixelblaze_monitor_pi.py`,
a file that has never existed in the repo. `install_pi_service.sh` installs
the FastAPI stack, not Flask. Broken by construction. `pi-boot-backups/` is a
stock Pi OS client on the home WiFi; nothing checked in makes the Pi an AP.
**Its `wpa_supplicant.conf` backup contains a plaintext WPA PSK — scrub it.**

**Provisioning.** `src/pixelblaze/pb.py` (click): `scan`, `connect` (sudo),
`flash --ssid`, `list`, `label`, `status`, `cleanup`. Uses `system_profiler`
for scanning, `networksetup` to join APs, and writes state to
`src/pixelblaze/pixelblaze/fleet.json`. The transcript
`claude-code-convo-wifi-pixelblaze.txt` is the saga that produced
`NETWORKING-NOTES.md`. `pb_connect_safe.py` hard-codes `en10`/`AX88179A`;
`fix_network.sh` hard-codes gateway `192.168.0.1`.

**Flamecaster.** `~/src/Flamecaster` (fork of zranger1's ArtNet→PixelBlaze
router). Config is `src/main/resources/flamecaster.json` (ArtNet in
`127.0.0.1:6455`, web UI 8585, 20 px per universe); regenerate with
`just flamecaster-conf "<ip> <ip>" "<px> <px>"`. `RUN.sh` asks for
`flamecaster-config.conf`, which only ever existed on the `playa2024` branch,
so that background step fails on master. The LX side is
`FlamecasterFixtures.NECorner/NWCorner` + the 31 netStrips.

**Marimapper.** README describes camera-mapping LED positions with
`marimapper` (PB pattern `src/main/resources/marimapper.{js,epe}`, outputs in
`binger-bag/`, `j5-bag.csv`). No marimapper checkout exists on this machine
(`~/src/wtf` is a dangling symlink); `~/src/led-map` (Swift/iOS, active Sept
2026) is its successor.

---

## 9. DMX par cans

See [`DMX-PARCANS.md`](DMX-PARCANS.md). `just parcan-scan|dimmer|test|raw`,
`just parcans-toggle`, `just parcan-surgery`.

---

## 10. ArtNet simulator and TouchDesigner

See [`TOUCHDESIGNER.md`](TOUCHDESIGNER.md). `just sim` (Electron, works),
`just sim-py`, `just artnet-count|universes|raw|listen`.

---

## 11. Video tools (`src/scripts`)

For `VideoPattern` clips: `just scenes <video>` (histogram/edge/flow scene
detection → `<stem>_scenes.json`), `just motion-cuts`, `just extract-scenes
<video> <json>` (ffmpeg stream-copy split, default out
`src/main/resources/videos/scenes`), `just trim`. `SCENE_DETECTION_ANALYSIS.md`
records the tuning. Needs `just venv-video` + ffmpeg. The committed
`videos/scenes/1min_scene0N_*.webm.mp4` are outputs of this flow and are
referenced by `iqe.lxp`.

---

## 12. Things that are dead, stale, or dangerous

Safe to delete (nothing runs them):
- `src/speedup-control/` — a Vite cache dir committed by accident.
- `start-speed-control.sh` — double-binds 8080/3333.
- `src/dmx/add_dmx_parcans.py` — destructive, obsolete channel map.
- `zzz_misc/` symlinks into the missing `zzz_extinct/` tree; `.gitmodules`
  (four entries, none initialised, path doesn't exist).
- `src/pb/old_pbfleet.py`, `provisioned_devices.pkl`, root `__pycache__/`.
- `src/audio-tooling/audio_test.py` (NameError on import).
- `src/main/java/.../SpatialAveragingParCanFixture.java` + encoder (can't work as written).

Broken but referenced:
- `RUN.sh` Flamecaster line (wrong config filename).
- `src/pb/pixelblaze-monitor.service` (missing script).
- `src/scripts/download_chromatik.sh` (no-op by design; remove from the pom or
  finish the 1.0.0 upgrade).
- `src/pb/pbfleet.py --dev`.

Security: `pi-boot-backups/wpa_supplicant.conf.20250816_183604` has a
plaintext home-WiFi PSK in git history.

Doc drift fixed in this pass: README (controls ports, python env, file
names), CLAUDE.md (fixture counts, channel name, hosts), PIXELBLAZE_FLEET.md
(port, script name, aspirational sections), SPEED_CONTROL_README.md and
`src/control-ui/README.md` (`npm start` behaviour, CC number), `src/pb/README.md`.
