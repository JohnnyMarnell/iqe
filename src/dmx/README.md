# src/dmx — par can bench tools

Stdlib-only Python that hand-rolls ArtNet `OpOutput` packets to the Pknight ArtNet→DMX node
(`CONTROLLER_IP`, default `10.10.42.68`, UDP 6454) driving the 8 U'King 7-channel par cans.
Full story, channel map, fixture layout, and next steps: [`../../docs/DMX-PARCANS.md`](../../docs/DMX-PARCANS.md).

| Script | `just` | Purpose | Env |
|---|---|---|---|
| `parcan_tester.py` | `parcan-test` | interactive 2-can tester: R/G/B/W, rainbow, per-can, flash, custom RGB | `CONTROLLER_IP`, `UNIVERSE` (1) |
| `dmx_channel_scanner.py` | `parcan-scan` | walk channels one at a time to identify a can's mapping | `UNIVERSE` **defaults to 0** — pass 1 |
| `dimmer_test.py` | `parcan-dimmer` | does the dimmer persist between packets? (no — send it every frame) | universe hard-coded 1 |
| `test_parcans.py` | `parcan-raw` | first attempt, RGB at ch 1–3 (wrong for 7-ch mode); option 7 = manual 7-ch | `UNIVERSE` defaults to 0 |
| `add_dmx_parcans.py` | — | **do not run**: appends obsolete fixtures into `Projects/iqe.lxp` in place, no dedupe | |

7-channel map: dimmer, R, G, B, strobe, function, colour-speed. Fixture addresses 1/8/15/22/29/36/43/50.
Bench order that worked in Aug 2025: scan → dimmer → test → LX (`just lx`) with the parcans enabled.
The LX fixtures are `src/main/java/org/iqe/SmoothDMXParCanFixture.java` + encoder; the kill switch is
`just parcans-toggle` (OSC `/iqe/cmd toggleparcans`).
