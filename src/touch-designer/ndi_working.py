#!/usr/bin/env python3
"""
Working NDI receiver using cyndilib correct API
"""

import cv2
import numpy as np
import time
import sys

from cyndilib.wrapper.ndi_recv import RecvColorFormat, RecvBandwidth
from cyndilib.finder import Finder
from cyndilib.receiver import Receiver, ReceiveFrameType

def main():
    print("NDI Receiver (Working)")
    print("=" * 50)
    
    # Create and open finder
    finder = Finder()
    finder.open()
    
    print("Searching for NDI sources...")
    time.sleep(2)
    
    # Check sources
    num_sources = finder.num_sources
    if num_sources == 0:
        print("No NDI sources found!")
        return
    
    # Get source names and objects
    source_names = finder.get_source_names()
    print(f"\nFound {num_sources} source(s): {source_names}")
    
    # Get first source
    source = None
    for s in finder.iter_sources():
        source = s
        break
    
    print(f"Connecting to: {source}")
    
    # Create receiver
    receiver = Receiver(
        color_format=RecvColorFormat.RGBX_RGBA,
        bandwidth=RecvBandwidth.highest
    )
    
    # Connect to source
    receiver.connect_to(source)
    
    # Wait for connection
    print("Waiting for connection...")
    for i in range(50):
        if receiver.is_connected():
            print("Connected!")
            break
        time.sleep(0.1)
    else:
        print("Failed to connect")
        return
    
    # Create window
    cv2.namedWindow('NDI Stream', cv2.WINDOW_NORMAL)
    print("\nReceiving... Press 'q' to quit")
    
    frame_count = 0
    fps_start = time.time()
    
    while True:
        # Receive frame (request video, timeout 100ms)
        result = receiver.receive(ReceiveFrameType.recv_video, 100)
        
        # Check if we got video
        if result == ReceiveFrameType.recv_video:
            # Get the video frame
            video_frame = receiver.video_frame
            
            if video_frame is not None:
                # Get frame data
                width = video_frame.width
                height = video_frame.height
                
                # Get frame as array
                frame_data = video_frame.get_array()
                
                # Convert to numpy
                if isinstance(frame_data, np.ndarray):
                    frame_np = frame_data
                else:
                    # Convert memoryview to numpy
                    frame_np = np.array(frame_data, copy=False)
                
                # Reshape if needed
                if frame_np.ndim == 1:
                    frame_np = frame_np.reshape((height, width, 4))
                
                # Convert RGBA to BGR
                frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGBA2BGR)
                
                # Scale if small
                if width < 500 or height < 100:
                    scale = max(2, min(1920 // width, 1080 // height))
                    frame_bgr = cv2.resize(frame_bgr, (width * scale, height * scale),
                                         interpolation=cv2.INTER_NEAREST)
                    if frame_count == 0:
                        print(f"Scaling {width}x{height} → {width*scale}x{height*scale}")
                
                # Add info
                info = f"NDI: {width}x{height} | Frame: {frame_count}"
                cv2.putText(frame_bgr, info, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # Display
                cv2.imshow('NDI Stream', frame_bgr)
                
                frame_count += 1
                
                # FPS
                if frame_count % 30 == 0:
                    elapsed = time.time() - fps_start
                    fps = 30 / elapsed
                    print(f"FPS: {fps:.1f} | Frames: {frame_count}")
                    fps_start = time.time()
        
        # Check quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cv2.destroyAllWindows()
    receiver.disconnect()
    finder.close()
    
    print(f"\nTotal frames: {frame_count}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()