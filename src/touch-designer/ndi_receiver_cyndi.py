#!/usr/bin/env python3
"""
NDI Receiver using cyndilib - corrected API usage
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

def receive_ndi(source_name="TouchDesigner"):
    """Receive NDI stream using cyndilib"""
    
    # Create finder
    finder = Finder()
    
    print("Searching for NDI sources...")
    
    # Let finder run for a bit to discover sources
    time.sleep(2)
    
    # Get sources
    sources = finder.get_sources()
    
    if not sources:
        print("No NDI sources found!")
        print("\nMake sure:")
        print("1. TouchDesigner is running")
        print("2. NDI Out TOP is active")
        print("3. You're on the same network")
        return
    
    print(f"\nFound {len(sources)} source(s):")
    for i, (key, source) in enumerate(sources.items()):
        print(f"  [{i}] {source.name} @ {source.address}")
    
    # Find our source
    selected_key = None
    selected_source = None
    
    for key, source in sources.items():
        if source_name.lower() in source.name.lower():
            selected_key = key
            selected_source = source
            break
    
    if not selected_source:
        # Use first source
        selected_key = list(sources.keys())[0]
        selected_source = sources[selected_key]
        print(f"\nSource '{source_name}' not found, using: {selected_source.name}")
    else:
        print(f"\nConnecting to: {selected_source.name}")
    
    # Create receiver
    receiver = Receiver(
        color_format=RecvColorFormat.RGBX_RGBA,
        bandwidth=RecvBandwidth.highest,
        source=selected_source
    )
    
    # Create video frame handler
    vf = VideoFrameSync(receiver)
    
    # Create OpenCV window
    cv2.namedWindow('NDI Stream (cyndilib)', cv2.WINDOW_NORMAL)
    
    print("\nReceiving... Press 'q' to quit")
    
    frame_count = 0
    fps_start = time.time()
    last_frame_time = time.time()
    scaled = False
    
    while True:
        try:
            # Get frame with timeout
            frame_obj = vf.get_frame(timeout=1.0)
            
            if frame_obj is not None:
                # Get frame data
                frame_data = np.array(frame_obj.data, copy=False)
                height = frame_obj.height
                width = frame_obj.width
                
                # Reshape if needed (cyndilib may return flat array)
                if frame_data.ndim == 1:
                    # RGBA format
                    frame_data = frame_data.reshape((height, width, 4))
                
                # Convert RGBA to BGR for OpenCV
                frame_bgr = cv2.cvtColor(frame_data, cv2.COLOR_RGBA2BGR)
                
                # Scale up small videos
                if width < 500 or height < 100 and not scaled:
                    scale = max(2, min(1920 // width, 1080 // height))
                    cv2.resizeWindow('NDI Stream (cyndilib)', width * scale, height * scale)
                    scaled = True
                    print(f"Video size: {width}x{height}, scaling {scale}x for display")
                
                if scaled:
                    scale = max(2, min(1920 // width, 1080 // height))
                    frame_bgr = cv2.resize(frame_bgr, (width * scale, height * scale),
                                         interpolation=cv2.INTER_NEAREST)
                
                # Add info overlay
                info = f"NDI: {width}x{height} | Frame: {frame_count}"
                cv2.putText(frame_bgr, info, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # Display
                cv2.imshow('NDI Stream (cyndilib)', frame_bgr)
                
                frame_count += 1
                last_frame_time = time.time()
                
                # FPS counter
                if frame_count % 30 == 0:
                    elapsed = time.time() - fps_start
                    fps = 30 / elapsed
                    print(f"FPS: {fps:.1f} | Total frames: {frame_count}")
                    fps_start = time.time()
            
            else:
                # No frame received
                if time.time() - last_frame_time > 3.0:
                    print("No frames for 3 seconds...")
                    last_frame_time = time.time()
        
        except Exception as e:
            print(f"Frame error: {e}")
            time.sleep(0.1)
        
        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cv2.destroyAllWindows()
    vf.close()
    receiver.close()
    
    print(f"\nStopped. Total frames received: {frame_count}")

def main():
    """Main entry point"""
    print("NDI Receiver (cyndilib)")
    print("=" * 50)
    
    source_name = "TouchDesigner"
    if len(sys.argv) > 1:
        source_name = sys.argv[1]
    
    try:
        receive_ndi(source_name)
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()