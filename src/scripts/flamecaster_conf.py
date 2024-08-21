import pixelblaze
import json
from pathlib import Path

pixelblaze_ips = "192.168.0.79 192.168.0.229".split(" ")
pixelblaze_ips = ["192.168.0.79"]

cfg = {
    "system": {
        "maxFps": 30,
        "statusUpdateIntervalMs": 3000,
        "pixelsPerUniverse": 170,
        "ipArtnet": "0.0.0.0",
        "portArtnet": 6454,
        "ipWebInterface": "127.0.0.1",
        "portWebInterface": 8585,
    },
    "devices": {},
}

for device_index, ip in enumerate(pixelblaze_ips):
    print(f"Attempting to connect to Pixelblaze at {ip}")
    pb = pixelblaze.Pixelblaze(ip)
    assert pb.connected, f"Pixelblaze at {ip} is not connected"
    name, pixels = pb.getDeviceName(), pb.getPixelCount()
    print(f"Connected to Pixelblaze at {ip} {name} {pixels} pixels")

    data = {}
    pixels_mapped = 0
    start_universe = 4096
    i = 0

    while pixels_mapped < pixels:
        segment_pixels = min(170, pixels - pixels_mapped)
        data[str(i)] = {
            "net": 0,
            "subnet": 0,
            "universe": start_universe + i,
            "startChannel": 0,
            # "destIndex": i * 20,
            "destIndex": pixels_mapped,
            "pixelCount": segment_pixels,
        }
        pixels_mapped += segment_pixels
        i += 1

    cfg["devices"][str(device_index)] = {
        "name": name,
        "ip": ip,
        "pixelCount": pixels,
        "maxFps": 30,
        "deviceStyle": "pixels",
        "data": data,
    }

cfg_json = json.dumps(cfg, indent=2)
print(cfg_json)
with open(f"{Path(__file__).parent}/../main/resources/flamecaster.json", "w") as f:
    f.write(cfg_json)
