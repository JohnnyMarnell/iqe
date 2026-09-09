# In Queso Emergency — justfile
# Usage: just <recipe>        (`just` alone lists everything)
#
# Every way this repo's subsystems can be run, catalogued 2026-09-09 from a
# read-only audit. Companion doc with ports, env setup, and what is known to
# be broken: docs/RUNNING.md. Nothing here was executed while writing it, so
# the first run of any recipe is a test — fix and commit as you go.
#
# Conventions:
#   - Recipes run from the repo root (just does that for you).
#   - Python recipes use the uv venv at ./.venv (see `just venv`); the one
#     that was there is dead (its base interpreter was uninstalled).
#   - Node sub-packages are npm workspaces of the root package.json.

default:
    @just --list --unsorted

# ── Paths / constants ────────────────────────────────────────────────────────

LX_JAR      := "./target/iqe-1.0-SNAPSHOT-jar-with-dependencies.jar"
VENDOR_JAR  := "./vendor/glxstudio.jar"
LX_MAIN     := "heronarts.lx.studio.ChromatikIQE"
# -XstartOnFirstThread is required by GLX/LWJGL on macOS only.
JAVA_OPTS   := if os() == "macos" { "-XstartOnFirstThread -XX:-OmitStackTraceInFastThrow" } else { "-XX:-OmitStackTraceInFastThrow" }
PY          := justfile_directory() + "/.venv/bin/python"
STAFF       := env_var_or_default("STAFF_INFECTION", justfile_directory() + "/../staff-infection")
FLAMECASTER := env_var_or_default("FLAMECASTER", justfile_directory() + "/../Flamecaster")
# Pknight ArtNet→DMX node feeding the 8 par cans (see docs/DMX-PARCANS.md).
PKNIGHT     := env_var_or_default("CONTROLLER_IP", "10.10.42.68")

# ── Java / LX Studio (Chromatik) ─────────────────────────────────────────────

# Build the fat jar (target/iqe-1.0-SNAPSHOT-jar-with-dependencies.jar).
# Prints a "ToDo: upgrade to Chromatik v1.0.0" line from the no-op download
# script wired into the maven initialize phase; that is expected.
[doc("Build the fat jar (target/iqe-1.0-SNAPSHOT-jar-with-dependencies.jar).")]
build:
    ./mvnw clean package -DskipTests

# Same but `install` (what the root CLAUDE.md documents). Either works.
build-install:
    ./mvnw clean install -DskipTests

# Run LX/Chromatik on a project from Projects/. Needs `just build` first.
# The iqe jar MUST precede the vendor jar so the patched LXPattern wins.
# Project file resolves as Projects/<name>; logs land in Logs/.
[doc("Run LX/Chromatik on a project from Projects/. Needs `just build` first.")]
lx project="iqe.lxp":
    java {{JAVA_OPTS}} -cp {{LX_JAR}}:{{VENDOR_JAR}} {{LX_MAIN}} {{project}}

# Build then run.
lx-build project="iqe.lxp": build (lx project)

# Headless LX with output forced on (no window). Useful for feeding the
# ArtNet simulator or the real PixLite from a box with no GPU.
[doc("Headless LX, output forced on (no window) — feed the simulator or PixLite.")]
lx-headless project="iqe.lxp":
    java {{JAVA_OPTS}} -cp {{LX_JAR}}:{{VENDOR_JAR}} {{LX_MAIN}} --headless --force-output {{project}}

# LX without the IQE plugin (stock Chromatik behaviour, for bisecting).
lx-clean project="iqe.lxp":
    java {{JAVA_OPTS}} -cp {{LX_JAR}}:{{VENDOR_JAR}} {{LX_MAIN}} --clean {{project}}

# LX with a JDWP listener on :5005 so IntelliJ's "Already Running" remote
# config (.run/Already Running.run.xml) can attach.
[doc("LX with JDWP on :5005 so IntelliJ's \"Already Running\" config can attach.")]
lx-debug project="iqe.lxp":
    java {{JAVA_OPTS}} -agentlib:jdwp=transport=dt_socket,server=y,suspend=n,address=5005 -cp {{LX_JAR}}:{{VENDOR_JAR}} {{LX_MAIN}} {{project}}

# Maven tests. Both test classes exist but every @Test is @Disabled, so this
# currently runs 0 effective tests — a known gap, not a pass.
[doc("Maven tests — every @Test is currently @Disabled, so 0 effective tests.")]
test-java:
    ./mvnw test

# The Finder/double-click flow: Flamecaster (currently broken, see
# docs/RUNNING.md) + control UI + build + LX, all from RUN.sh.
[doc("The Finder double-click flow via RUN.sh (Flamecaster step is broken).")]
run-all:
    ./RUN.sh

# Show which JDK is active and what .sdkmanrc wants (17.0.6-tem). `sdk` is a
# shell function, so switch in your own shell: `sdk env`.
[doc("Show the active JDK vs what .sdkmanrc wants (17.0.6-tem).")]
jdk:
    @echo "wanted:  $(cat .sdkmanrc | grep java)"
    @echo "on PATH: $(java -version 2>&1 | head -1)"

# The main class has no source in the tree (baked into vendor/glxstudio.jar).
# Print the last committed copy.
[doc("Print the last committed source of the main class (now only in vendor jar).")]
lx-main-src:
    git show 78ecb18^:src/main/java/heronarts/lx/studio/ChromatikIQE.java

# ── Project file (Projects/iqe.lxp) ──────────────────────────────────────────

# Histogram of fixture classes and hosts in the project file.
lxp-fixtures project="Projects/iqe.lxp":
    #!/usr/bin/env python3
    import json, collections
    d = json.load(open("{{project}}"))
    fx = d["model"]["fixtures"]
    print(f"{len(fx)} fixtures")
    for k, n in collections.Counter(f["class"].split(".")[-1] for f in fx).items(): print(f"  {n:4} {k}")
    print("hosts:")
    for k, n in collections.Counter(str(f.get("parameters", {}).get("host")) for f in fx).items(): print(f"  {n:4} {k}")

# DANGER: regenerates the 72 ceiling strips (and 32 Flamecaster netStrips)
# in Projects/iqe.lxp IN PLACE from src/nodejs/buildProject.js, resetting
# strip host to 10.10.42.80 and discarding per-fixture UI edits. Quit LX
# first. Parcan fixtures are preserved. Also dumps ~3 MB of JSON to stdout.
[doc("DANGER: regenerate the 72 strips in Projects/iqe.lxp in place (resets host).")]
lxp-regen:
    cd src/nodejs && node buildProject.js > /dev/null

# Point the 72 ceiling strips at a host. Known values: advatek-local
# (127.0.0.1 via /etc/hosts, the simulator), advatek (10.10.42.80), or an IP.
# Backs up to Projects/iqe.lxp.bak-<ts>. Quit LX first.
[doc("Point the 72 ceiling strips at a host (advatek-local | advatek | IP).")]
lxp-strip-host host:
    cp Projects/iqe.lxp "Projects/iqe.lxp.bak-$(date +%Y%m%d-%H%M%S)"
    sed -i '' -E 's/"host": "(advatek-local|advatek|10\.10\.42\.80|127\.0\.0\.1)"/"host": "{{host}}"/g' Projects/iqe.lxp
    @echo "strip hosts now:" && grep -c '"host": "{{host}}"' Projects/iqe.lxp

# Regenerate the 8 parcan fixtures → Projects/iqe_modified.lxp (never
# touches iqe.lxp; diff and copy by hand). tsx lives in control-ui's deps.
[doc("Regenerate the 8 parcan fixtures → Projects/iqe_modified.lxp.")]
parcan-surgery:
    ./src/control-ui/node_modules/.bin/tsx parcan-surgery.ts

# ── Control UI (src/control-ui, TypeScript) ──────────────────────────────────
# Browser → WS :8080 → OSC UDP → LX plugin bridge :3232 (replies on :3333).

# Dev: Vite on http://localhost:8282 (LAN-exposed) + the OSC/WS bridge.
control:
    cd src/control-ui && npm run control

# Prod: build dist/ and serve it from the unified server on :8282 + bridge.
# Plain `npm start` is bridge-only since Dec 2025 (no HTTP) — don't use it
# expecting a page.
[doc("Prod: build dist/ and serve it from the unified server on :8282 + bridge.")]
control-prod:
    cd src/control-ui && npm run build && NODE_ENV=production npm start

# Bridge only (WS :8080 ↔ OSC 3232/3333), no web server.
control-bridge:
    cd src/control-ui && npm start

control-build:
    cd src/control-ui && npm run build

# MIDI CC 21 (any channel) → /lx/mixer/master/effect/1/speed. Picks the
# first non-IAC input it finds.
[doc("MIDI CC 21 → /lx/mixer/master/effect/1/speed via OSC 3232.")]
midi:
    cd src/control-ui && npm run midi

# ── Legacy web app + OSC bridge (src/nodejs, 2023) ───────────────────────────
# Superseded by control-ui for control, but still has the /state cache and
# the Launchkey MIDI relay. Do NOT run alongside control-ui: both bind
# WS :8080 and UDP :3333.

# Serve remote-control.html on :8181 (its own npm start uses port 80).
# The committed dist/osc-js symlink is dangling under npm workspaces, so the
# page may fail to load osc.min.js; see docs/RUNNING.md.
[doc("Serve remote-control.html on :8181 (its own npm start uses port 80).")]
legacy-web:
    cd src/nodejs && IQE_WEB_PORT=8181 IQE_OSC_WS_PORT=8080 IQE_APP_OSC_TO_PORT=3232 IQE_APP_OSC_FROM_PORT=3333 node scripts.js bridge

# One-shot OSC via the legacy bridge's WebSocket (bridge must be running).
# Example: just legacy-send /lx/tempo/tap '[1]'
[doc("One-shot OSC via the legacy bridge's WebSocket (bridge must be running).")]
legacy-send path args:
    cd src/nodejs && node scripts.js send {{path}} '{{args}}'

# ── OSC helpers (no deps, stdlib python3) ────────────────────────────────────

# Send one OSC message to LX's IQE bridge on UDP 3232. Args auto-typed:
# int → i, float → f, anything else → s. Env OSC_HOST / OSC_PORT override.
# Examples:
#   just osc /lx/mixer/master/effect/1/speed 0.5
#   just osc /iqe/cmd "solo visuals"
#   just osc /lx/osc-query 1          # LX dumps every parameter to :3333
[doc("Send one OSC message to LX's bridge (UDP 3232); args auto-typed i/f/s.")]
[positional-arguments]
osc address *args:
    #!/usr/bin/env python3
    import os, socket, struct, sys
    def pad(b): return b + b"\0" * ((4 - len(b) % 4) % 4)
    addr, args = sys.argv[1], sys.argv[2:]
    tags, data = ",", b""
    for a in args:
        try: v = int(a); tags += "i"; data += struct.pack(">i", v); continue
        except ValueError: pass
        try: v = float(a); tags += "f"; data += struct.pack(">f", v); continue
        except ValueError: pass
        tags += "s"; data += pad(a.encode() + b"\0")
    msg = pad(addr.encode() + b"\0") + pad(tags.encode() + b"\0") + data
    host, port = os.environ.get("OSC_HOST", "127.0.0.1"), int(os.environ.get("OSC_PORT", "3232"))
    socket.socket(socket.AF_INET, socket.SOCK_DGRAM).sendto(msg, (host, port))
    print(f"→ {host}:{port} {addr} {tags} {args}")

# Flip every parcan fixture's `deactivate` (the kill switch). Stateless.
parcans-toggle:
    just osc /iqe/cmd toggleparcans

# Solo a mixer channel by (case-insensitive substring of) label.
solo name:
    just osc /iqe/cmd "solo {{name}}"

# Global pattern speed-up, 0 = normal, 1 = 21×.
speed value:
    just osc /lx/mixer/master/effect/1/speed {{value}}

# Dump every LX parameter to the :3333 stream (watch with `just osc-sniff`).
osc-query:
    just osc /lx/osc-query 1

# Print everything LX emits on the client bridge (UDP 3333). Ctrl-C to stop.
# Conflicts with a running control-ui/legacy bridge (they own 3333).
[doc("Print everything LX emits on the client bridge (UDP 3333). Ctrl-C to stop.")]
osc-sniff port="3333":
    #!/usr/bin/env python3
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.bind(("0.0.0.0", {{port}}))
    print("listening UDP :{{port}}")
    while True:
        d, a = s.recvfrom(65535)
        addr = d.split(b"\0", 1)[0].decode(errors="replace")
        print(addr, d[len(addr):].lstrip(b"\0")[:80])

# ── Python environment (uv) ──────────────────────────────────────────────────

# Recreate ./.venv (Python 3.10, matching the last env that worked) with the
# PixelBlaze-monitor deps from requirements.txt plus click (needed by
# src/pixelblaze/pb.py and missing from the file).
[doc("Recreate ./.venv (uv, Python 3.10) with the PixelBlaze-monitor deps + click.")]
venv:
    uv venv --python 3.10 .venv
    uv pip install -r requirements.txt click

# Add the audio-analysis stack. requirements.txt lost these in Aug 2025;
# src/audio-tooling/old.requirements.txt is the pinned set that worked.
[doc("Add the audio-analysis stack (pyaudio/librosa/python-osc) to ./.venv.")]
venv-audio:
    brew list portaudio >/dev/null 2>&1 || brew install portaudio
    uv pip install -r src/audio-tooling/old.requirements.txt sounddevice scipy

# Add the video scene-detection stack (src/scripts/detect_*.py).
venv-video:
    brew list ffmpeg >/dev/null 2>&1 || brew install ffmpeg
    uv pip install opencv-python scipy numpy

# Add the ArtNet simulator's matplotlib (src/touch-designer/iqe_render.py).
venv-sim:
    uv pip install matplotlib numpy

# Add Flamecaster's deps (sibling repo).
venv-flamecaster:
    uv pip install -r {{FLAMECASTER}}/requirements.txt

# Everything above.
venv-all: venv venv-audio venv-video venv-sim venv-flamecaster

# ── Audio analysis → LX tempo (src/audio-tooling) ────────────────────────────

# Real-time beat detection (librosa) on a loopback device, sending
# /lx/tempo/beat|bpm|clockSource to LX on UDP 3232. Needs BlackHole (or any
# input whose name contains `input`) and LX running. --pipe echoes audio to
# `output` so you can hear it.
[doc("Real-time beat detection → /lx/tempo/* on UDP 3232 (needs BlackHole + LX).")]
beat input="BlackHole 2ch" output="Speakers" *args:
    cd src/audio-tooling && {{PY}} beat_detective.py -i "{{input}}" -o "{{output}}" {{args}}

# Same, silent (no audio echo).
beat-quiet input="BlackHole 2ch":
    cd src/audio-tooling && {{PY}} beat_detective.py -i "{{input}}" --no-pipe

# PyAudio device list + loopback smoke test (BlackHole 2ch → Speakers).
audio-devices:
    cd src/audio-tooling && {{PY}} pyaudio_utils.py

# Jupyter Lab (:8888, no token) + kernel server (:8889, token=a) with librosa,
# for src/audio-tooling/jupyter/tempo.ipynb. Needs Docker Desktop, which is
# not currently installed on this laptop.
[doc("Jupyter Lab :8888 + kernel :8889 via docker compose (Docker not installed now).")]
jupyter:
    cd src/audio-tooling/jupyter && docker compose up

# Re-export tempo.ipynb → tempo.html (container must be up).
jupyter-export:
    cd src/audio-tooling/jupyter && docker compose exec -it jupyter-lab jupyter nbconvert --to html --output-dir /out '*.ipynb'

# ── PixelBlaze fleet monitor (src/pb) ────────────────────────────────────────
# Flask app on http://localhost:8000: UDP 1889 discovery, per-device status,
# sync/pulse/swell endpoints. Must run with cwd = src/pb (template path).

# The live one (pbfleet_enhanced.py). The FastAPI pbfleet.py and README
# describing it are the abandoned earlier attempt.
[doc("The live PixelBlaze fleet monitor (Flask, http://localhost:8000).")]
pb-monitor:
    cd src/pb && {{PY}} pbfleet_enhanced.py

# Minimal Flask variant (inline HTML).
pb-monitor-simple:
    cd src/pb && {{PY}} pbfleet_simple.py

# Standalone one-button "pulse all" page on http://localhost:5000.
pb-button:
    cd src/pb && {{PY}} pb_web_button.py

# Devices the monitor currently knows about.
pb-devices:
    curl -s localhost:8000/api/devices | python3 -m json.tool

# Fire the monitor's endpoints.
pb-sync-random:
    curl -s -X POST localhost:8000/api/sync-random
pb-pulse-quick:
    curl -s -X POST localhost:8000/api/pulse-quick
pb-swell duration="20" hue="0.6":
    curl -s -X POST localhost:8000/api/swell-and-scatter -H 'content-type: application/json' -d '{"duration": {{duration}}, "hue": {{hue}}}'

# Direct pulse-and-scatter across devices (needs a pattern named simplePulse
# already on each). Example: just pb-pulse 192.168.0.96 192.168.0.241
[doc("Pulse-and-scatter across devices by IP (needs simplePulse on each).")]
pb-pulse *ips:
    cd src/pb && {{PY}} pb_pulse_and_scatter.py {{ips}}

# Dump every getX() of one device to src/pb/pb_test_*.json.
pb-info ip:
    cd src/pb && {{PY}} test_device_info.py {{ip}}

# ── PixelBlaze WiFi provisioning from the Mac (src/pixelblaze/pb.py) ─────────
# Scans for Pixelblaze_XXXXXX APs via system_profiler (the deprecated
# `airport` binary is never used), joins one, opens http://192.168.4.1.
# Read NETWORKING-NOTES.md first: macOS Internet Sharing + a second adapter
# will eat your internet.

pb-scan *args:
    cd src/pixelblaze && {{PY}} pb.py scan {{args}}

# Needs sudo (reorders network services, fixes routes).
pb-connect *args:
    cd src/pixelblaze && sudo {{PY}} pb.py connect {{args}}

# Walk each discovered PB's AP and hand you the config page for `ssid`.
pb-flash ssid *args:
    cd src/pixelblaze && {{PY}} pb.py flash --ssid "{{ssid}}" {{args}}

pb-list:
    cd src/pixelblaze && {{PY}} pb.py list

pb-status:
    cd src/pixelblaze && {{PY}} pb.py status

# Raw WiFi scan JSON (what pb.py parses).
wifi:
    system_profiler SPAirPortDataType -json

# Just the visible SSIDs.
wifi-ssids:
    system_profiler SPAirPortDataType -json | python3 -c "import sys, json; d = json.load(sys.stdin); [print(n.get('_name', '?')) for i in d.get('SPAirPortDataType', []) for iface in i.get('spairport_airport_interfaces', []) for n in iface.get('spairport_airport_other_local_wireless_networks', [])]"

# Snapshot of routes/interfaces/reachability when ethernet kills internet.
net-diag:
    bash src/pixelblaze/network_diagnostic.sh

# Force the default route back through the home router (hard-coded
# 192.168.0.1 in the script; sudo inside).
[doc("Force default route back through the home router (sudo inside).")]
net-fix:
    bash src/pixelblaze/fix_network.sh

# The /etc/hosts aliases the project file and docs rely on.
hosts:
    @grep -nE 'advatek|pknight|swidervision' /etc/hosts || echo "no iqe aliases in /etc/hosts"

# ── Flamecaster (ArtNet → PixelBlaze corners, sibling repo) ──────────────────
# LX's FlamecasterFixtures send to 127.0.0.1:6455; Flamecaster relays to the
# PixelBlazes over WebSocket. Web UI on :8585. Config is the JSON here, not
# the flamecaster-config.conf that RUN.sh asks for (that file never existed
# on master).

flamecaster conf="src/main/resources/flamecaster.json":
    cd {{FLAMECASTER}} && {{PY}} Flamecaster.py --file {{justfile_directory()}}/{{conf}}

# Regenerate the config from live devices. Example:
#   just flamecaster-conf "192.168.0.79 192.168.0.229" "400 400"
[doc("Regenerate flamecaster.json from live PixelBlazes (args: ip-list, pixel-list).")]
flamecaster-conf ips counts out="src/main/resources/flamecaster.json":
    {{PY}} src/scripts/flamecaster_conf.py "{{ips}}" "{{counts}}" > {{out}}

# ── DMX par cans (src/dmx, stdlib python) ────────────────────────────────────
# Bench tools that hand-roll ArtNet to the Pknight node. Full story:
# docs/DMX-PARCANS.md. Order that worked: scan → dimmer → test → LX.

# Interactive 2-can colour / rainbow / flash tester (7-ch, dimmer=255).
parcan-test:
    CONTROLLER_IP={{PKNIGHT}} UNIVERSE=1 python3 src/dmx/parcan_tester.py

# Walk DMX channels one at a time to identify a can's channel map.
parcan-scan:
    CONTROLLER_IP={{PKNIGHT}} UNIVERSE=1 python3 src/dmx/dmx_channel_scanner.py

# Does the dimmer channel need re-sending every packet? (Answer was yes.)
parcan-dimmer:
    CONTROLLER_IP={{PKNIGHT}} python3 src/dmx/dimmer_test.py

# Legacy RGB-only tester; only option 7 (manual 7-channel) is still useful.
parcan-raw:
    CONTROLLER_IP={{PKNIGHT}} UNIVERSE=1 python3 src/dmx/test_parcans.py

# ── ArtNet simulator / TouchDesigner (src/touch-designer) ────────────────────
# Receivers that decode LX's 72-universe ceiling output on UDP 6454 and draw
# the 24×420 grid. Point LX's strips at 127.0.0.1 first
# (`just lxp-strip-host advatek-local` + the /etc/hosts alias). Story and
# the unfinished TD sender: docs/TOUCHDESIGNER.md.

# Electron visualizer (the good simulator). Builds TS then launches.
sim:
    cd src/touch-designer/iqe-artnet-electron && npm start

# Same with tsc --watch.
sim-dev:
    cd src/touch-designer/iqe-artnet-electron && npm run dev

# Dec 2025 "sniffer" variant with fake parcan floods (its parcan universes
# don't match the real ones yet).
[doc("Dec 2025 sniffer variant with fake parcan floods (universes don't match yet).")]
sim-sniffer:
    cd src/touch-designer/iqe-artnet-electron && ./start-sniffer.sh

# The original matplotlib simulator. --spaced draws rafter gaps.
sim-py *args:
    {{PY}} src/touch-designer/iqe_render.py --ip 0.0.0.0 --port 6454 {{args}}

# 10 s capture: non-zero pixels per universe vs the expected 10,080.
artnet-count:
    python3 src/touch-designer/count_pixels.py

# 5 s capture: bytes per universe, grouped by rafter (1-based universes).
artnet-universes:
    python3 src/touch-designer/debug_universe_data.py

# First 100 raw packets (binds 127.0.0.1 — only sees loopback traffic).
artnet-raw:
    python3 src/touch-designer/debug_artnet.py

# Bare Node UDP listener that prints ArtNet headers as they arrive.
artnet-listen:
    node src/touch-designer/test-udp.js

# ── PixelBlaze emulator + gallery (sibling repo staff-infection) ─────────────
# The browser emulator already has the IQE ceiling as fixture `grid`
# (24 rows × 420 cols = 10,080 px). Wiring plan: docs/PIXELBLAZE-EMULATOR-LX.md.
# Override the checkout with STAFF_INFECTION=/path.

# Emulator + emulated PixelBlaze device (http://:8080, ws://:81) booted on the
# ceiling shape. Then open http://localhost:8080/gallery.html.
[doc("staff-infection emulator + emulated PixelBlaze on the 24×420 ceiling shape.")]
pb-emu *args:
    cd {{STAFF}} && just dev --shape grid --rows 24 --cols 420 --pixels 10080 {{args}}

# Render a pattern (fuzzy name) on the ceiling shape to an mp4.
# Example: just pb-emu-render fire --duration 10
[doc("Render a pattern (fuzzy name) on the ceiling shape to an mp4.")]
pb-emu-render *args:
    cd {{STAFF}} && just render-patterns --shape grid {{args}}

# List canonical 2D patterns from the gallery index (name, source, controls).
pb-emu-2d:
    #!/usr/bin/env python3
    import json
    idx = json.load(open("{{STAFF}}/src/patterns/index.json"))
    rows = [p for p in idx["patterns"] if "2D" in p.get("dimensions", []) and not p.get("duplicateOf")]
    for p in sorted(rows, key=lambda p: p["name"].lower()):
        print(f'{p["name"]:50} {p["source"]:16} {",".join(c["fn"] for c in p.get("controls", []))}')
    print(f"{len(rows)} canonical 2D patterns")

# ── Video prep for VideoPattern (src/scripts) ────────────────────────────────
# Needs `just venv-video`. Outputs go next to the input unless -o given.

# Detect scene transitions / loops → <stem>_scenes.json.
scenes video *args:
    {{PY}} src/scripts/detect_video_scenes.py "{{video}}" {{args}}

# Hard-cut detector via motion jumps → <stem>_motion_cuts.json.
motion-cuts video *args:
    {{PY}} src/scripts/detect_motion_cuts.py "{{video}}" {{args}}

# Split a video into per-scene files with ffmpeg (stream copy).
extract-scenes video json out="src/main/resources/videos/scenes":
    {{PY}} src/scripts/extract_scenes.py "{{video}}" "{{json}}" -o {{out}}

# Drop N frames from the start / end → <stem>-trimmed.<ext>.
trim video start="0" end="0":
    {{PY}} src/scripts/trim_video.py "{{video}}" -s {{start}} -e {{end}}

# ── Node setup / housekeeping ────────────────────────────────────────────────

# npm install at the root and in every workspace.
npm-install:
    npm run install:all

# rm -rf every node_modules.
npm-clean:
    npm run clean

# Who is holding the ports this repo uses.
ports:
    -lsof -nP -iUDP:3030 -iUDP:3131 -iUDP:3232 -iUDP:3333 -iUDP:6454 -iUDP:6455 -iUDP:1889 -iTCP:8080 -iTCP:8181 -iTCP:8282 -iTCP:8000 -iTCP:5000 -iTCP:81 2>/dev/null | grep -v '^COMMAND' || echo "nothing listening"

# Kill whatever is on the control-UI ports (what RUN.sh's cleanup does).
kill-ports:
    -lsof -ti:8282 | xargs kill -9 2>/dev/null
    -lsof -ti:8080 | xargs kill -9 2>/dev/null
    @echo "8282/8080 cleared"

# Open the docs index.
docs:
    @ls -1 docs/ README.md CLAUDE.md PIXELBLAZE_FLEET.md NETWORKING-NOTES.md SPEED_CONTROL_README.md
