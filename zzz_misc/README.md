# OUTDATED, pre-Chromatik alpha builds
# OUTDATED, pre-Chromatik alpha builds
# OUTDATED, pre-Chromatik alpha builds

This old outdated dir was for how to build LX Studio IDE + Processing 4 run.

# In Queso Emergency

LED control code, via LX Studio.

# Top Notes

Currently, [./chromatik](./chromatik/) is primary directory, runnable using alpha builds of new
LX Studio (Chromatik).

# Setup

LX Studio requires Processing, install via web or Home Brew:
```bash
brew install --cask processing
```

# Standalone Command line

```bash
sdk env ; mvn -version
( cd LXStudio-IDE ; mvn clean validate ; mvn dependency:build-classpath install -Dmdep.outputFile=/tmp/cp )
( cd LXStudio-IDE ; java -cp $(cat /tmp/cp):target/classes \
    -Djava.library.path=lib/processing-4.0.1/macos-$([[ $(uname -m) == "arm64" ]] && echo "aarch64" || uname -m) heronarts.lx.app.LXStudioApp ../iqe.lxp )
cat *slee* | node scripts/scripts.js > /tmp/f.lxp ; java -XstartOnFirstThread -cp glxs*.jar heronarts.lx.studio.Chromatik /tmp/f.lxp

# add --headless for decapitaishe
```

# With Processing UI

To start LX Studio UI, open Processing App, then LX Studio Processing file,
or via command line:
```
./run-lx-studio.sh
```

Then click Open button and browse to this folder's main LX Studio project file: [iqe.lxp]

# Links
- [Standford course involving LX Studio](https://code.stanford.edu/plevis/ee185/-/tree/master/software/FlightGui)

# To Do
- Add base pre-requisites, sdkman, maven, java 17 Temurin
- Re-organize this repository (dont use submodule for IDE?), submit PR to LXStudio-IDE with sdkmanrc, improved os + arch inference, for now cd

# Scratch area

Scrape a bunch of test files
```bash
youtube_dl_mp3  'Monolink (live) - Mayan Warrior - Burning Man 2022'  'Keinemusik Mayan Bruning Man'  'ed sheeran bad habits'  'Chill EDM Slow Dance Mix'  'SLOW TRANCE • Downtempo EDM Background Track'  'dua lipa levitating'  "dua don't "  "dua new rules "  "lady gaga poker face " '120 bpm metronome' '126 bpm metronome'
```