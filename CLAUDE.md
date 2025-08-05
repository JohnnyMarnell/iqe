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
- ./mvnw clean install -DskipTests : Build the project
- See @RUN.sh for java run and other commands

# Pattern Development

## Creating New Patterns
- All patterns extend `LXPattern` and go in `org.iqe.pattern` package
- Pattern classes must be named like `FooPattern.java`
- Register patterns in `LXPluginIQE.java` in the `Stream.of()` list around line 62
- Use `@LXCategory(LXCategory.TEST)` annotation (GAME category doesn't exist)
- Main method is `run(double deltaMs)` where deltaMs is milliseconds since last frame
- Use `LXColor.CLEAR` instead of `LXColor.BLACK` for transparency to avoid transition artifacts

## Pattern Examples
- **ImagePattern**: Loads PNG images, handles alpha channel, supports rotation/scaling/bouncing
- **PongPattern**: Classic game with ball physics, AI paddles, score tracking

## Key Pattern Tips
- Calculate model bounds in first run for normalized coordinates
- Use `CompoundParameter` for sliders, `BooleanParameter` for toggles, `DiscreteParameter` for dropdowns
- Access parameter values with `.getValue()`, `.getValueb()`, or `.getValuei()`
- LOG class uses `.info()` and `.error()` (no `.warn()` method)

# Fixture Management

## Current Setup (as of Aug 2024)
- 72 ceiling strips only (24 rafters × 3 strips each)
- Class: `org.iqe.NagBugglerSaberOfLightFixture`
- Removed 32 `FlamecasterFixtures$PatchedStripFixture` netStrips
- Each strip has 140 pixels
- Fixtures stored in JSON under `model.fixtures` in iqe.lxp

## Test Channel
- Located around line 41500+ in iqe.lxp
- Can hold multiple patterns for testing
- Pattern transitions use alpha blending (importance of CLEAR vs BLACK)
