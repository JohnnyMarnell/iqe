This repo uses java software Chromatik / LX Studio,
javadoc api here: https://chromatik.co/api/

LX is like Ableton Live but for LEDs, there are channels,
plugins, layers, etc., and resultant pixels are pushed
as ArtNet network packets to an Advatek PixLite controller.

The main project file that specifies channels, settings,
and pattern sets, is in [./Projects/iqe.lxp](./Projects/iqe.lxp) , in json format.

Patterns must be named like FooPattern.java, and included in
bootstrapping, much of which can be traced from:
@src/main/java/org/iqe/LXPluginIQE.java

See also:
@README.md

There is also a sub-layer enabling [PixelBlaze](https://electromage.com/pixelblaze) patterns
(crowd sourced javascript files) animation capability within Chromatik as well.

There's also a NodeJS element for some OSC communication and control,
as well as some python for real-time audio analysis like
beat detection and event emitting via OSC. Also an experiment
using python libraries to take ArtNet packets and push them over
WiFi to PixelBlaze hardware. But the primary focus is Java patterns
here in LX ecosystem.

# Bash
- ./mvnw clean install -DskipTests : Build the project (RUN.sh uses `clean package`; either works)
- See @RUN.sh for java run and other commands
- `just` (root justfile) has a recipe for every subsystem: `just build`, `just lx`, `just control`,
  `just beat`, `just pb-monitor`, `just sim`, `just parcan-test`, `just osc <addr> <args>`, ...
  `just --list` for all. Docs for each in docs/RUNNING.md.
- The main class `heronarts.lx.studio.ChromatikIQE` has no source in the tree; it lives in
  vendor/glxstudio.jar (LX 0.4.2-SNAPSHOT). `just lx-main-src` prints the last committed copy.
- The iqe jar must precede vendor/glxstudio.jar on the classpath: src/main/java/heronarts/lx/pattern/LXPattern.java
  is a patched copy of LX's class (global speed-up in onLoop). RUN.sh and the justfile do this.
- Both JUnit test classes are fully @Disabled; `./mvnw test` runs 0 effective tests.

# Docs
- docs/RUNNING.md — every subsystem, ports, env setup, what's broken/dead
- docs/DMX-PARCANS.md — the 8 U'King par cans via the Pknight ArtNet→DMX node (2025 burn)
- docs/TOUCHDESIGNER.md — TD → ArtNet attempt, the working Electron/python simulators, how to finish
- docs/PIXELBLAZE-EMULATOR-LX.md — ~/src/staff-infection's PixelBlaze emulator + gallery, wiring to LX
- NETWORKING-NOTES.md, PIXELBLAZE_FLEET.md, SPEED_CONTROL_README.md — older, corrected in Sept 2026

# Pattern Development

## Creating New Patterns
- All patterns extend `LXPattern` (the patched one, see above) and go in `org.iqe.pattern` package
  (PixelBlaze-hosted ones live in `org.iqe.pattern.pixelblaze` and `titanicsend.pattern.pixelblaze`)
- Pattern classes are conventionally named like `FooPattern.java` (the PB ones aren't: `PBXorcery`, `PixelBlazeBlowser`)
- Register patterns in `LXPluginIQE.java` in the `Stream.of()` list around lines 65–87
- On disk but NOT registered: `titanicsend.pattern.pixelblaze.PixelblazeSandbox`, `PixelblazeParallel`
- Use `@LXCategory(LXCategory.TEST)` annotation (GAME category doesn't exist)
- Main method is `run(double deltaMs)` where deltaMs is milliseconds since last frame,
  already multiplied by `1 + GlobalControls.speed × 20` by the patched LXPattern
- Use `LXColor.CLEAR` instead of `LXColor.BLACK` for transparency to avoid transition artifacts

## Pattern Examples
- **ImagePattern**: Loads PNG images, handles alpha channel, supports rotation/scaling/bouncing
- **PongPattern**: Classic game with ball physics, AI paddles, score tracking

## Key Pattern Tips
- Calculate model bounds in first run for normalized coordinates
- Use `CompoundParameter` for sliders, `BooleanParameter` for toggles, `DiscreteParameter` for dropdowns
- Access parameter values with `.getValue()`, `.getValueb()`, or `.getValuei()`
- LOG class uses `.info()` and `.error()` (no `.warn()` method)

# Network Tools Note
- DO NOT USE `/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport` - Apple has locked this down and deprecated it
- Use `system_profiler SPAirPortDataType -json` for WiFi scanning instead
- Example to scan for networks:
  ```bash
  system_profiler SPAirPortDataType -json | python3 -c "import sys, json; data = json.load(sys.stdin); [print(n.get('_name', 'Unknown')) for iface in data.get('SPAirPortDataType', []) for n in iface.get('spairport_airport_interfaces', [{}])[0].get('spairport_airport_other_local_wireless_networks', [])]"
  ```
- Our pb.py script in src/pixelblaze/ uses this method

# Fixture Management

## Current Setup (verified 2026-09 against Projects/iqe.lxp at dc67bec)
- 111 fixtures under `model.fixtures`, not 72:
  - 72 ceiling strips `org.iqe.NagBugglerSaberOfLightFixture` (24 rafters × 3), 140 px each, 3 ArtNet
    universes per rafter (base 1,4,7,… with rafter 16 → 73), host `advatek-local`
  - 31 `FlamecasterFixtures$PatchedStripFixture` netStrips (→ 127.0.0.1:6455, still enabled; the
    "removed 32" note from 2024 was wrong)
  - 8 `org.iqe.SmoothDMXParCanFixture` (→ 10.10.42.68:6454 universe 1, ch 0/7/…/49) — see docs/DMX-PARCANS.md
- `just lxp-fixtures` prints this histogram; `just lxp-strip-host <host>` re-points the 72 strips
- Strip host `advatek-local` resolves to 127.0.0.1 via /etc/hosts (the ArtNet simulator); `advatek` = 10.10.42.80
- `NagBugglerSaberOfLightFixture` is not registered in the plugin; it loads by class name from the .lxp
- Regenerating strips: `just lxp-regen` (buildProject.js) — destructive, see README "Project File"

## Test Channel
- There is no channel named "Test" any more; it was renamed "Visuals" (around line 41800 in iqe.lxp)
- Channels: Foreground[group], FG Pattern, PB Patterns, Color, Background[group], BG Pattern, Color,
  Visuals, Pong, ignore_FX, ignore_FXold
- Master effects (1-based, as OSC paths use): 1 GlobalControls, 2 Audio NO_TOUCHY, 3 Strobe, 4 Blur, 5 Mindshow
- Pattern transitions use alpha blending (importance of CLEAR vs BLACK)

# OSC
- LX native: receive 3030 / transmit 3131. IQE plugin `OscBridge`: clients send to **3232**, replies +
  the whole relayed LX stream go out on **3333**. Web UIs sit behind WS 8080.
- `/iqe/cmd "<cmd> <arg>"`: `solo <substr>`, `toggleparcans`, `pong1 <v>`, `pong2 <v>`
- `just osc <address> <args…>` sends one message with no deps; `just osc-sniff` watches 3333

# PixelBlaze Fleet Management
See [PIXELBLAZE_FLEET.md](./PIXELBLAZE_FLEET.md) for:
- Live device monitoring web app (`just pb-monitor` → src/pb/pbfleet_enhanced.py, Flask, :8000)
- Python client library usage
- Network discovery and management
- (No Firestorm integration exists; that section of the doc is aspirational)

# Python env
- Use uv: `just venv` (Python 3.10, requirements.txt + click), `just venv-audio`, `just venv-all`.
  The README's conda instructions are historical. `.venv/bin/python` is what the justfile uses.
