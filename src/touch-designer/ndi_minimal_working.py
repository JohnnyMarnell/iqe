#!/usr/bin/env python3
"""
Minimal working NDI receiver
"""

import cv2
import numpy as np
import time
from cyndilib.finder import Finder
from cyndilib.receiver import Receiver
from cyndilib.wrapper.ndi_recv import RecvColorFormat, RecvBandwidth

# Open finder
finder = Finder()
finder.open()

# Wait for sources
print("Looking for NDI sources...")
time.sleep(2)

# Get source
source = None
for s in finder.iter_sources():
    print(f"Found: {s}")
    source = s
    break

if not source:
    print("No sources!")
    exit()

# Create receiver - pass all params to constructor
receiver = Receiver(
    source_name=str(source),
    color_format=RecvColorFormat.RGBX_RGBA,
    bandwidth=RecvBandwidth.highest
)

print(f"Created receiver for: {source}")

# Main loop
cv2.namedWindow('NDI', cv2.WINDOW_NORMAL)
frame_count = 0

for i in range(300):  # 10 seconds at 30fps
    # The receiver should automatically receive frames
    # Check if video frame is available
    if hasattr(receiver, 'video_frame') and receiver.video_frame:
        vf = receiver.video_frame
        
        try:
            # Get frame data
            width = vf.width
            height = vf.height
            
            # Get raw data
            data = vf.data
            
            # Convert to numpy
            arr = np.frombuffer(data, dtype=np.uint8)
            arr = arr.reshape((height, width, 4))  # RGBA
            
            # Convert to BGR
            bgr = cv2.cvtColor(arr, cv2.COLOR_RGBA2BGR)
            
            # Scale up
            if width < 500:
                bgr = cv2.resize(bgr, (width*2, height*2))
            
            cv2.imshow('NDI', bgr)
            frame_count += 1
            
            if frame_count % 10 == 0:
                print(f"Frames: {frame_count}")
                
        except Exception as e:
            if frame_count == 0:
                print(f"Error: {e}")
    
    if cv2.waitKey(33) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()
print(f"Total frames: {frame_count}")