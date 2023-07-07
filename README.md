# In Queso Emergency

Mainly LX Studio / Chromatik project and Java code for Burning Man IQE HQ shade structure LEDznutz.

Also contains python code and Jupyter notebooks for audio analysis with
[Librosa](https://librosa.org/doc/latest/index.html),
e.g. real time beat detection and sync.

Plus Node.JS OSC backed web app control system.

![Chromatik](src/audio-tooling/chromatik-project-screenshot.png)

# Use

Prerequisites:
1. Java 17 Temurin / Eclipse is installed from here: https://adoptium.net/

Then find and double-click the `IQE.command` here in this repo / folder. (Note: until annoying-ass Maven is sorted, 
before very first `./mvnw` CLI use, need to have clicked above or run its scripts).

You can import this repo as project (select pom.xml) in IntelliJ IDEA, and just click the dropdown near Play and Debug
buttons to select ready-to-go easy run configuration, ready to run (or debug, with hot reload, useful!) via those buttons.

Or examples with sperminal:
```bash
./src/scripts/download_chromatik.sh # do once, to fetch LX / Chromatik per arch binary jar
./mvnw clean package -DskipTests ; # to (re-)build

# and run
eval "java $( [[ $(uname) == 'Darwin' ]] && echo "-XstartOnFirstThread" ) \
    -cp ./target/iqe-1.0-SNAPSHOT-jar-with-dependencies.jar:./vendor/glxstudio.jar \
    heronarts.lx.studio.ChromatikIQE iqe.lxp \
    --classpath-plugin org.iqe.LXPluginIQE"
```
# PixelBlaze

Some PixelBlaze functionality has been ported (with permission). Currently there is a `PixelBlazeBlowser` pattern with
a `script` knob. Changing it will cycle some PB patterns, some with controls / sliders, and not all render.

Much of this is twerk-in-brogress and needs vetting for what is potentially useful. As with a lot of the code
and intent here, it would be great if we could get more "stock" /  crowdsourced patterns working given time constraints. 

# Web / Controls

TODO: these docs and notes.

Node.JS app from [./src/nodejs](./src/nodejs). Able to control LX via OSC, from any device (e.g. mobile phone
connected to Playa RaspberryPi ad hoc wifi network).

# Audio analysis

The [audio-tooling](./src/audio-tooling/) directory here contains python code, and experiments
with real time audio analysis (like beat detection and sync).

You can easily run the Jupyter notebooks as long as you have [Docker](https://www.docker.com/) installed,
```bash
cd src/audio-tooling/jupyter
docker-compose up
```
And visit [localhost:8888](http://localhost:8888) for locally running Jupyter Labs notebook UI.
(Or point an IDE (like
[VS Code](https://code.visualstudio.com/docs/datascience/jupyter-notebooks#_connect-to-a-remote-jupyter-server), tested)
to Jupyter server and python kernel with URL: `http://localhost:8889?token=a`).

TODO: Look into SuperCollider https://depts.washington.edu/dxscdoc/Help/Classes/BeatTrack.html , as well as if
MaxMSP can run on Pi, and BeatSeeker Ableton M4L can run? (Although is this only for drums, not full track?)
https://www.ableton.com/en/packs/beatseeker/

# Special Thanks

Big thank you to kind souls, especially of Titanic's End, Pixelblaze, SymmetryLabs, who've helped us!
- [Mark Slee](https://heronarts.com/)
- [Ben Hencke](https://www.bhencke.com/)
- [Jeff Vyduna](https://ngnr.org/)
- [Justin K Belcher](https://www.instagram.com/jkb_studio)
