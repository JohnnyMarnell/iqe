#!/usr/bin/env python3
"""
Minimal NDI receiver based on cyndilib examples
"""

import cv2
import numpy as np
import time

from cyndilib.wrapper.ndi_recv import RecvColorFormat, RecvBandwidth
from cyndilib.finder import Finder
from cyndilib.receiver import Receiver
from cyndilib.video_frame import VideoFrameSync

def main():
    print("Minimal NDI Receiver")
    print("=" * 50)
    
    # Create finder
    finder = Finder()
    
    # Wait for sources
    print("Waiting for NDI sources...")
    time.sleep(2)
    
    # Try to create receiver with source name directly
    print("\nAttempting direct connection to 'TD_VideoStream'...")
    
    try:
        # Create receiver - try without specifying source first
        receiver = Receiver(
            color_format=RecvColorFormat.RGBX_RGBA,
            bandwidth=RecvBandwidth.highest
        )
        
        print("Receiver created")
        
        # Now try to find and set source
        # Check if receiver has methods to find sources
        if hasattr(receiver, 'get_sources'):
            sources = receiver.get_sources()
            print(f"Found sources: {sources}")
        
        # Create video frame sync
        vf = VideoFrameSync(receiver)
        
        print("\nAttempting to receive frames...")
        print("Press 'q' to quit")
        
        cv2.namedWindow('NDI', cv2.WINDOW_NORMAL)
        
        frame_count = 0
        for i in range(300):  # Try for 10 seconds
            try:
                frame = vf.get_frame()
                
                if frame is not None:
                    # Get frame info
                    print(f"\nGot frame! Size: {frame.width}x{frame.height}")
                    
                    # Convert to numpy
                    data = np.array(frame.data, copy=False)
                    
                    # Reshape based on format
                    if data.ndim == 1:
                        # Assume RGBA
                        data = data.reshape((frame.height, frame.width, 4))
                    
                    # Convert to BGR
                    bgr = cv2.cvtColor(data, cv2.COLOR_RGBA2BGR)
                    
                    # Scale if small
                    if frame.width < 500:
                        scale = 2
                        bgr = cv2.resize(bgr, (frame.width * scale, frame.height * scale))
                    
                    cv2.imshow('NDI', bgr)
                    frame_count += 1
                    
                    if frame_count % 10 == 0:
                        print(f"Frames: {frame_count}")
                else:
                    if i % 30 == 0:
                        print(".", end="", flush=True)
                
            except Exception as e:
                if i == 0:
                    print(f"Frame error: {e}")
                    
            if cv2.waitKey(33) & 0xFF == ord('q'):
                break
                
        print(f"\n\nTotal frames: {frame_count}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        cv2.destroyAllWindows()
        try:
            vf.close()
            receiver.close()
            finder.close()
        except:
            pass

if __name__ == "__main__":
    main()