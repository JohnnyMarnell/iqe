# src/dmx/lightkey — Lightkey show files (2025 burn)

[Lightkey](https://lightkeyapp.com) is the macOS DMX console we used alongside LX for the par
cans. Both files here were saved on **2025-08-19**, the week of departure, and lived in
`~/Downloads` on the laptop until 2026-11-13. They are `NSKeyedArchiver` binary plists, so git
can't diff them — open them with Lightkey (`/Applications/Lightkey.app`, 5.3.3) to read them.

| File | Original name | Saved | Personality | Addresses (1-based) |
|---|---|---|---|---|
| `burning-man-2025.lightkeyproj` | `Burning Man 2025.lightkeyproj` | 14:40 | U'King **18 PCS PAR Light** (8 ch) | 1, 9, 17, 25, 33, 41, 49, 57 + MH1 @ 65 |
| `burning-man-2025-new.lightkeyproj` | `Burning Man 2025 (New).lightkeyproj` | 15:08 | U'King **36 LED PAR Light** (7 ch) | 1, 8, 15, 22, 29, 36, 43, 50 + MH1 @ 57 |

Both patch nine fixtures on **universe index 1**, refresh 40 Hz: `P1`–`P8` (the par cans) plus
`MH1`, a U'King *LED Kaleidoscope Moving Head (with LED Ring)* that appears nowhere in the LX
project — so Lightkey, not LX, is the only thing that ever drove the moving head.

What's in each, beyond the patch:

- **`burning-man-2025`** — a Control Panel with 9 buttons wired to 9 cues/presets: *Confetti*,
  *Cop light*, *Colors Gradate*, *Colors Jump Change*, *Colors Pulse Change*, *Different Colors
  Output*, *Sound-Active*, *Color Effects*, plus a hexagon beam layout for the stage view.
  This is the one with actual looks in it.
- **`burning-man-2025-new`** — no cues; 6 MIDI triggers bound to cuelist transport
  (`StartStopCuelist`, `NextCue`, `PreviousCue`, `PauseResumeCuelist`, `SelectLivePage`,
  `DeactivateAllCues`). A re-patch, apparently abandoned mid-setup.

## Two gotchas before reusing either

1. **Only the `-new` file's addressing matches the repo.** Everything in LX — the fixtures in
   `Projects/iqe.lxp`, `SmoothParCanByteEncoder`, the `src/dmx/` bench scripts — assumes the
   7-channel map at **1/8/15/22/29/36/43/50** (see
   [`../../../docs/DMX-PARCANS.md`](../../../docs/DMX-PARCANS.md) §1). The 8-channel
   `18 PCS PAR Light` patch in the other file is off by one channel from can 2 onward, so its
   cues will land on the wrong fixtures unless the cans are re-addressed to match it.
2. **Neither file has an output device bound.** The universe's `plugInID` is 0 and `deviceID`
   is null — no Art-Net node, no USB interface saved. Pointing Lightkey at the Pknight
   (`10.10.42.68`, universe 1) is still to do, and LX must be off universe 1 while it does
   (`just parcans-toggle`) — the two apps must never transmit on it at once.

Integration plan (Lightkey owns the cans vs. Lightkey as OSC input to LX), and the iPad
sidecar question: `docs/DMX-PARCANS.md` §8 "Lightkey on the Mac, iPad as a sidecar".
