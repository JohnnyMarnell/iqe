# src/audio-tooling — beat detection → LX tempo

The one real tool is **`beat_detective.py`**: PyAudio reads a loopback input (default device name
containing `BlackHole 2ch`), librosa `beat_track` over a 10 s window every 10 s plus a 1.5 s phase
check every second, and OSC to `127.0.0.1:3232` (the IQE plugin's `OscBridge`):

- `/lx/tempo/beat 1.0` per predicted beat
- `/lx/tempo/bpm <f>` then `/lx/tempo/clockSource 0` on tempo update (BPM ≥160 is halved)
- `/lx/tempo/clockSource 2` on clear

```bash
just venv && just venv-audio         # uv venv (py3.10) + brew portaudio + old.requirements.txt
just beat                            # = cd src/audio-tooling && python beat_detective.py -i "BlackHole 2ch" -o "Speakers"
just beat-quiet                      # --no-pipe (don't echo audio to the output device)
just audio-devices                   # pyaudio_utils.py: list devices + loopback smoke test
```

Run it from this directory (it imports `pyaudio_utils` relatively). LX must be running. Requires
BlackHole (or any loopback device) routed from your player.

**Requirements:** `requirements.txt` here is a symlink to the root file, which since Aug 2025 holds
the PixelBlaze-monitor deps, not audio. `old.requirements.txt` (PyAudio 0.2.13, numpy 1.23.5,
librosa 0.10.0.post2, python-osc 1.8.3) is the pinned set that worked; `just venv-audio` installs it
plus `sounddevice scipy` for the scratch scripts.

**Everything else here is 2023 scratch:** `pyaudio_*test*.py`, `sd.audio_test.py` (sounddevice
variant + rtmidi2 click), `sound.py` (librosa on files), `synth.py` (pygame.midi → sine).
`audio_test.py` is broken (uses `sd` without importing it). None emit OSC.

**Jupyter:** `jupyter/compose.yaml` runs Lab on :8888 (no token) and a kernel server on :8889
(token `a`) with librosa; `tempo.ipynb` is the exploration behind the beat detector.
`just jupyter` / `just jupyter-export` (`docker compose`; Docker Desktop is currently uninstalled).
