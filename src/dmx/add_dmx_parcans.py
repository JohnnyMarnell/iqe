#!/usr/bin/env python3
"""
Add DMX ParCan fixtures to the iqe.lxp project
"""

import json
import sys

# Read the project file
with open('Projects/iqe.lxp', 'r') as f:
    project = json.load(f)

# Create two DMX ParCan fixtures
parcan1 = {
    "id": 3001,
    "class": "org.iqe.DMXParCanFixture",
    "internal": {
        "modulationColor": 0,
        "modulationControlsExpanded": True,
        "modulationsExpanded": True
    },
    "parameters": {
        "label": "DMX ParCan 1",
        "x": -200.0,  # Near NE corner (negative X)
        "y": 0.0,     # Ground level
        "z": -200.0,  # Near front (negative Z)
        "yaw": 0.0,
        "pitch": 90.0,  # Pointing up
        "roll": 0.0,
        "scale": 10.0,  # Make it larger visually
        "selected": False,
        "deactivate": False,
        "enabled": True,
        "brightness": 1.0,
        "identify": False,
        "mute": False,
        "solo": False,
        "tags": "dmx parcan ground",
        "protocol": 1,  # ArtNet
        "byteOrder": 0,
        "transport": 0,
        "reverse": False,
        "host": "10.10.42.68",  # Pknight controller IP
        "port": 6454,  # Standard ArtNet port
        "dmxChannel": 1,  # Channel 2 (0-indexed, so 1 = channel 2)
        "artNetUniverse": 1,
        "artNetSequenceEnabled": False,
        "opcChannel": 0,
        "opcOffset": 0,
        "ddpDataOffset": 0,
        "kinetPort": 1,
        "numPoints": 1,  # Single pixel
        "spacing": 1.0
    },
    "children": {}
}

parcan2 = {
    "id": 3002,
    "class": "org.iqe.DMXParCanFixture",
    "internal": {
        "modulationColor": 0,
        "modulationControlsExpanded": True,
        "modulationsExpanded": True
    },
    "parameters": {
        "label": "DMX ParCan 2",
        "x": -200.0,  # Near NW corner (negative X)
        "y": 0.0,     # Ground level
        "z": 200.0,   # Near back (positive Z for NW)
        "yaw": 0.0,
        "pitch": 90.0,  # Pointing up
        "roll": 0.0,
        "scale": 10.0,  # Make it larger visually
        "selected": False,
        "deactivate": False,
        "enabled": True,
        "brightness": 1.0,
        "identify": False,
        "mute": False,
        "solo": False,
        "tags": "dmx parcan ground",
        "protocol": 1,  # ArtNet
        "byteOrder": 0,
        "transport": 0,
        "reverse": False,
        "host": "10.10.42.68",  # Pknight controller IP
        "port": 6454,  # Standard ArtNet port
        "dmxChannel": 8,  # Channel 9 (0-indexed, so 8 = channel 9)
        "artNetUniverse": 1,
        "artNetSequenceEnabled": False,
        "opcChannel": 0,
        "opcOffset": 0,
        "ddpDataOffset": 0,
        "kinetPort": 1,
        "numPoints": 1,  # Single pixel
        "spacing": 1.0
    },
    "children": {}
}

# Add the fixtures to the project
if 'fixtures' not in project['model']:
    project['model']['fixtures'] = []

project['model']['fixtures'].append(parcan1)
project['model']['fixtures'].append(parcan2)

# Write the updated project file
with open('Projects/iqe.lxp', 'w') as f:
    json.dump(project, f, indent=2)

print("Added 2 DMX ParCan fixtures to iqe.lxp:")
print(f"  - ParCan 1: Universe 1, Channel 2 (DMX channel index 1)")
print(f"  - ParCan 2: Universe 1, Channel 9 (DMX channel index 8)")
print(f"  - Controller IP: 10.10.42.68")
print(f"  - Positioned at ground level near corner drapes")