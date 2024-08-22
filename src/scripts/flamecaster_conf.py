import pixelblaze
import json
import sys

pixelblaze_ips = sys.argv[-2].split(" ")
pixel_counts = [int(s) for s in sys.argv[-1].split(" ")]

pixels_per_device = 400

cfg = {
    "system": {
        "maxFps": 30,
        # "statusUpdateIntervalMs": 3000,
        "statusUpdateIntervalMs": 2000,
        "updateInterval": 3000,
        "pixelsPerUniverse": 170,
        "ipArtnet": "127.0.0.1",
        "portArtnet": 6455,
        "ipWebInterface": "127.0.0.1",
        "portWebInterface": 8585,
    },
    "devices": {},
}

pixels_per_universe = 10
universe = 0

for device_index, ip in enumerate(pixelblaze_ips):
    print(f"Attempting to connect to Pixelblaze at {ip}", file=sys.stderr)
    pb = pixelblaze.Pixelblaze(ip)
    assert pb.connected, f"Pixelblaze at {ip} is not connected"
    name, pixels = pb.getDeviceName(), pb.getPixelCount()
    print(
        f"Connected to Pixelblaze at {ip} {name}, {pixels} total pixels",
        file=sys.stderr,
    )

    data = {}
    pixels_mapped = 0
    i = 0

    while pixels_mapped < pixel_counts[device_index]:
        segment_pixels = min(170, pixels - pixels_mapped)
        data[str(i)] = {
            "net": 0,
            "subnet": 0,
            "universe": universe,
            "startChannel": 0,
            # "destIndex": i * 20,
            "destIndex": pixels_mapped,
            "pixelCount": pixels_per_universe,
        }
        pixels_mapped += pixels_per_universe
        universe += 1
        i += 1

    cfg["devices"][str(device_index + 1)] = {
        "name": name,
        "ip": ip,
        "pixelCount": pixel_counts[device_index],
        # "maxFps": 30,
        "deviceStyle": "pixels",
        "data": data,
    }

cfg_json = json.dumps(cfg, indent=4)
print(cfg_json)
