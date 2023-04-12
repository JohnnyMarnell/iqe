# In Queso Emergency

LED control code, via LX Studio.

# Setup

LX Studio requires Processing, install via web or Home Brew:
```bash
brew install --cask processing
```

# Standalone Command line

```bash
sdk env ; mvn -version
( cd LXStudio-IDE ; mvn clean validate dependency:build-classpath install -Dmdep.outputFile=/tmp/cp )
( cd LXStudio-IDE ; java -cp $(cat /tmp/cp):target/classes -Djava.library.path=lib/processing-4.0.1/macos-$(uname -m) heronarts.lx.app.LXStudioApp ../iqe.lxp )

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