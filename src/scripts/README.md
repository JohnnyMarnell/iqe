# src/scripts

| Script | `just` | What |
|---|---|---|
| `download_chromatik.sh` | — | **no-op** (`exit 0` on line 2). Still wired into Maven's `initialize` phase via antrun, hence the "ToDo: upgrade to Chromatik v1.0.0" line on every build. The rest of the file would download `Chromatik-alpha-$(cat VERSION.chromatik)-<os>-<arch>.zip` into `vendor/`. `vendor/glxstudio.jar` is committed instead. |
| `flamecaster_conf.py` | `flamecaster-conf "<ip> <ip>" "<px> <px>"` | Connects to live PixelBlazes and writes a Flamecaster config (20 px/universe, ArtNet in `127.0.0.1:6455`, web UI 8585) to stdout → `src/main/resources/flamecaster.json`. Needs `pixelblaze-client`. |
| `detect_video_scenes.py` | `scenes <video>` | Scene transitions + loop detection (histogram/edge/gradient/optical flow) → `<stem>_scenes.json`. opencv + scipy. |
| `detect_motion_cuts.py` | `motion-cuts <video>` | Hard cuts via motion jumps → `<stem>_motion_cuts.json`. |
| `extract_scenes.py` | `extract-scenes <video> <json>` | Split into per-scene files with ffmpeg stream copy (default out `src/main/resources/videos/scenes`). |
| `trim_video.py` | `trim <video> [start] [end]` | Drop N frames from start/end → `<stem>-trimmed.<ext>`. ffmpeg/ffprobe. |
| `SCENE_DETECTION_ANALYSIS.md` | | Tuning notes for the above on a 60 s clip. |

The video tools feed `VideoPattern` (`src/main/java/org/iqe/pattern/VideoPattern.java`, JavaCV,
macOS arm64 natives only); the committed `videos/scenes/1min_scene0N_*.webm.mp4` are their output and
are referenced from `Projects/iqe.lxp`. Env: `just venv-video` (opencv, scipy, brew ffmpeg).
