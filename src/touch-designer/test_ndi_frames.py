#!/usr/bin/env python3
"""
Test NDI frame reception - exits after 10 frames
"""

from cyndilib.wrapper.ndi_recv import RecvColorFormat, RecvBandwidth
from cyndilib.finder import Finder
from cyndilib.receiver import Receiver, ReceiveFrameType
import time

# Setup
finder = Finder()
finder.open()
time.sleep(1)

# Get source
source = None
for s in finder.iter_sources():
    source = s
    print(f"Found source: {s}")
    break

if not source:
    print("No source found")
    exit(1)

# Create receiver
receiver = Receiver(
    color_format=RecvColorFormat.RGBX_RGBA,
    bandwidth=RecvBandwidth.highest
)
receiver.connect_to(source)

# Wait for connection
for i in range(50):
    if receiver.is_connected():
        print("Connected!")
        break
    time.sleep(0.1)

# Try to get 10 frames
print("\nTrying to receive frames...")
frame_count = 0
for i in range(100):
    result = receiver.receive(ReceiveFrameType.recv_video, 100)
    
    if result == ReceiveFrameType.recv_video:
        video_frame = receiver.video_frame
        if video_frame:
            frame_count += 1
            print(f"Frame {frame_count}: {video_frame.width}x{video_frame.height}")
            
            # Test get_array
            try:
                data = video_frame.get_array()
                print(f"  Data type: {type(data)}, shape: {data.shape if hasattr(data, 'shape') else 'N/A'}")
            except Exception as e:
                print(f"  Error getting array: {e}")
            
            if frame_count >= 10:
                break

print(f"\nReceived {frame_count} frames")
receiver.disconnect()
finder.close()