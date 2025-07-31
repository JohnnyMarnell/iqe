#!/usr/bin/env python3
"""
Final working NDI receiver for TouchDesigner
"""

import cv2
import numpy as np
import time
import sys

from cyndilib.wrapper.ndi_recv import RecvColorFormat, RecvBandwidth
from cyndilib.finder import Finder
from cyndilib.receiver import Receiver, ReceiveFrameType

def main():
    print("NDI Receiver - Final Version")
    print("=" * 50)
    
    # Create finder
    finder = Finder()
    finder.open()
    
    print("Searching for NDI sources...")
    time.sleep(2)
    
    # Get sources
    source_names = finder.get_source_names()
    if not source_names:
        print("No NDI sources found!")
        return
    
    print(f"Found sources: {source_names}")
    
    # Get first source object
    source = next(finder.iter_sources())
    print(f"Using source: {source}")
    
    # Create receiver with parameters
    receiver = Receiver()
    
    # Set parameters
    receiver.color_format = RecvColorFormat.RGBX_RGBA
    receiver.bandwidth = RecvBandwidth.highest
    
    # Connect to source
    print("Connecting...")
    receiver.connect_to(source)
    
    # Wait for connection
    for i in range(10):
        if receiver.is_connected():
            print("Connected!")
            break
        time.sleep(0.5)
    else:
        print("Failed to connect")
        
    # Create OpenCV window
    cv2.namedWindow('NDI Stream', cv2.WINDOW_NORMAL)
    print("\nReceiving... Press 'q' to quit")
    
    frame_count = 0
    start_time = time.time()
    
    while True:
        # Receive frame
        result = receiver.receive(ReceiveFrameType.recv_video, 100)
        
        if result == ReceiveFrameType.recv_video:
            vf = receiver.video_frame
            
            if vf:
                # Get dimensions
                width = vf.width
                height = vf.height
                
                # Get frame data
                try:
                    # Try get_array first
                    data = vf.get_array()
                except:
                    # Fall back to raw data
                    data = vf.data
                
                # Convert to numpy
                if not isinstance(data, np.ndarray):
                    data = np.frombuffer(data, dtype=np.uint8)
                
                # Reshape
                if data.ndim == 1:
                    # Calculate expected size
                    expected_size = width * height * 4  # RGBA
                    if len(data) >= expected_size:
                        data = data[:expected_size].reshape((height, width, 4))
                    else:
                        print(f"Data size mismatch: {len(data)} vs {expected_size}")
                        continue
                
                # Convert RGBA to BGR
                bgr = cv2.cvtColor(data, cv2.COLOR_RGBA2BGR)
                
                # Scale if small
                if width < 500 or height < 100:
                    scale = max(2, min(1920 // width, 1080 // height))
                    bgr = cv2.resize(bgr, (width * scale, height * scale),
                                   interpolation=cv2.INTER_NEAREST)
                
                # Add info
                info = f"NDI {width}x{height} Frame {frame_count}"
                cv2.putText(bgr, info, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # Show
                cv2.imshow('NDI Stream', bgr)
                frame_count += 1
                
                # Print FPS
                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    fps = frame_count / elapsed
                    print(f"FPS: {fps:.1f} Total: {frame_count}")
        
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