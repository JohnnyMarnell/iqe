#!/usr/bin/env python3
"""
Fixed NDI receiver using cyndilib
"""

import cv2
import numpy as np
import time
import sys

try:
    from cyndilib.wrapper.ndi_recv import RecvColorFormat, RecvBandwidth
    from cyndilib.finder import Finder
    from cyndilib.receiver import Receiver
    from cyndilib.video_frame import VideoFrameSync
except ImportError:
    print("ERROR: cyndilib not installed!")
    print("Install with: pip install cyndilib")
    sys.exit(1)

def receive_ndi():
    """Receive NDI stream"""
    print("NDI Receiver (cyndilib)")
    print("=" * 50)
    
    # Create finder
    finder = Finder()
    finder.open()
    
    print("Searching for NDI sources...")
    
    # Give finder time to discover sources
    time.sleep(2)
    
    # Get sources using correct API
    num_sources = finder.num_sources
    if num_sources == 0:
        print("No NDI sources found!")
        print("\nMake sure:")
        print("1. TouchDesigner is running")
        print("2. NDI Out TOP is active")
        return
    
    source_names = finder.get_source_names()
    print(f"\nFound {num_sources} source(s):")
    for name in source_names:
        print(f"  {name}")
    
    # Get first source (or find TD_VideoStream)
    selected_source = None
    selected_name = source_names[0]
    
    for name in source_names:
        if 'TD_VideoStream' in name:
            selected_name = name
            break
    
    # Get the actual source object
    for i, source in enumerate(finder.iter_sources()):
        if i == 0 or source.name == selected_name:
            selected_source = source
            break
    
    print(f"\nConnecting to: {selected_name}")
    
    # Create receiver
    receiver = Receiver(
        color_format=RecvColorFormat.RGBX_RGBA,
        bandwidth=RecvBandwidth.highest,
        source=selected_source
    )
    
    # Create video frame sync
    vf = VideoFrameSync(receiver)
    
    # Create window
    cv2.namedWindow('NDI Stream', cv2.WINDOW_NORMAL)
    print("\nReceiving... Press 'q' to quit")
    
    frame_count = 0
    fps_start = time.time()
    
    while True:
        try:
            # Get frame
            frame = vf.get_frame()
            
            if frame is not None:
                # Get frame data as numpy array
                frame_data = np.array(frame.data, copy=False)
                height = frame.height
                width = frame.width
                
                # Reshape if needed
                if frame_data.ndim == 1:
                    # RGBA format - 4 channels
                    frame_data = frame_data.reshape((height, width, 4))
                
                # Convert RGBA to BGR for OpenCV
                frame_bgr = cv2.cvtColor(frame_data, cv2.COLOR_RGBA2BGR)
                
                # Scale up small videos
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
                
                # FPS counter
                if frame_count % 30 == 0:
                    elapsed = time.time() - fps_start
                    fps = 30 / elapsed
                    print(f"FPS: {fps:.1f} | Frames: {frame_count}")
                    fps_start = time.time()
            
        except Exception as e:
            if frame_count == 0:
                print(f"Error getting frame: {e}")
            # Continue trying
            
        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cv2.destroyAllWindows()
    vf.close()
    receiver.close()
    finder.close()
    
    print(f"\nTotal frames received: {frame_count}")

def main():
    try:
        receive_ndi()
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()