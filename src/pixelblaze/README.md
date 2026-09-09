# src/pixelblaze — provisioning new PixelBlazes from the Mac

`pb.py` (click CLI) scans for `Pixelblaze_XXXXXX` access points with `system_profiler
SPAirPortDataType -json` (never the deprecated `airport` binary), joins one with `networksetup`,
opens `http://192.168.4.1` so you can type the camp WiFi creds, then restores your original SSID.
State goes to `./pixelblaze/fleet.json` (relative to this directory) and logs to `./pixelblaze/logs/`.

```bash
just venv                      # needs `click`, which root requirements.txt forgets
just pb-scan [-c] [-i 10]      # continuous scan
just pb-connect [DEVICE_ID]    # sudo: reorders network services, fixes routes, opens the config page
just pb-flash <camp-ssid>      # walk every discovered PB (prompts for the password)
just pb-list | pb-status
```

Read [`../../NETWORKING-NOTES.md`](../../NETWORKING-NOTES.md) first: macOS Internet Sharing (WiFi →
Ethernet for the Pi) plus a second adapter is what kept killing internet during this work. The
transcript `claude-code-convo-wifi-pixelblaze.txt` is that saga (it also has the only notes on
reconfiguring the Pknight DMX node's IP).

Helpers: `network_diagnostic.sh` (`just net-diag`, read-only dump of routes/interfaces/reachability),
`fix_network.sh` (`just net-fix`, forces the default route via the hard-coded home gateway
192.168.0.1), `pb_connect_safe.py` (one-shot variant of `connect`, hard-codes `en10` / `AX88179A`).
`fleet.json` at this level is an older schema; the live one is `pixelblaze/fleet.json`.

The fleet *monitor* (device status, sync, pulse) is in `../pb/` (`just pb-monitor`). The much larger
PixelBlaze emulator/gallery is in `~/src/staff-infection` (see `docs/PIXELBLAZE-EMULATOR-LX.md`).
