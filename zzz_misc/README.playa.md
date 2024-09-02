# Checklist

## Before Playa

- Make sure GitHub Desktop App is logged in
- pull latest to project
- it's located in Finder at Home directory, src, iqe: ~/src/iqe
- Desktop has link to these notes, and link to Run / Start Command
- Verify LX Starts via clicking command

## On Playa
- Connect power and ethernet for pixlite, router, laptop
  - plug both pixlite and laptop ethernet cables (laptop -> dongle -> ethernet cable -> router) INTO LAN, NOTHING INTO WAN. (i think this was the problem everyone complained about)

- Each of these should get IP's of 10.10.42.xx, plus they should be:
  - PixLite: 10.10.42.80
- If pixLite is not at this IP, every fixture in LX project will have wrong address, need to change everywhere, or, change in ~line 49 of `buildProject.js` here in this repo, and run it in terminal (SAVE CHANGES IN iqe.lxp [MAIN PROJECT] FIRST AND QUIT LX):
```bash
node ~/src/iqe/src/nodejs/buildProject.js
```
- can try [http://10.10.42.80](http://10.10.42.80) in browser, hopefully loads PixLite UI. (Try Advatek Assistant as last resort)
- Looks like jmarnell (thanks so much man, for all your hard work, and great vibes, we love and appreciate you so much <3) set laptlop static IP of `10.10.42.81`. I see that now with random belkin adapter connected directly to pixLite (also at expected IP) playa 2024. Allegedly, the router setup didn't "just work", so trying that now
- The laptop cable was plugged into WAN, first wrong sign...

## 2024
- on boot, PB "NE Corner" was, facing the street, on your right
- ran `nmap -sn 10.10.42.0/24`, it found this PB at `10.10.42.102` (lines up, I
think I set router to count up from 100 for dhcp pool). Paired next PB, tried 103 in the dark and it worked, "NW Corner" (these were originally named for corner screen drapes, i'm moving geometry to about ish the shipping cunt-ainer wall)
- lucked out, west runs to east for original hang, thus just update IPs in Flamecastur conf. might need to flip mother effing direction in LX.
- "all outputs are now wired correctly" , we had to change 16-1,2,3 strips to like universe 46 + 47
- fucking need the conda auto select from bash garbage because it's not defaulting to `iqe` and `conda activate iqe` from bash doesn't work
- 


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