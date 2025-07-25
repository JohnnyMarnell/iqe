This repo uses java software Chromatik / LX Studio,
javadoc api here: https://chromatik.co/api/

LX is like Ableton Live but for LEDs, there are channels,
plugins, layers, etc., and resultant pixels are pushed
as ArtNet network packets to an Advatek PixLite controller.

See also:
@README.md

There is also a sub-layer enabling [PixelBlaze](https://electromage.com/pixelblaze) patterns
(crowd sourced javascript files) animation capability as well.

There's also a NodeJS element for some OSC communication and control,
as well as some python for real-time audio analysis like
beat detection and event emitting via OSC. Also an experiment
using python libraries to take ArtNet packets and push them over
WiFi to PixelBlaze hardware. But the primary focus is Java patterns
here in LX ecosystem.

# Bash
- ./mvnw clean install -DskipTests : Build the project
- See @RUN.sh for java run and other commands
