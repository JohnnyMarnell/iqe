#!/usr/bin/env python3
"""
Simple NDI Receiver using pyNDI library
Much easier to use than the official NDI SDK!

Installation:
    pip install opencv-python numpy
    pip install pyNDI
    
Or if that doesn't work:
    pip install cyndilib  # Another alternative
"""

import cv2
import numpy as np
import time
import sys

# Try different NDI library options
ndi_lib = None

# Option 1: Try pyNDI (simplest)
try:
    import pyNDI
    ndi_lib = "pyNDI"
    print("Using pyNDI library")
except ImportError:
    pass

# Option 2: Try cyndilib
if not ndi_lib:
    try:
        from cyndilib.wrapper.ndi_recv import RecvColorFormat, RecvBandwidth
        from cyndilib.finder import Finder
        from cyndilib.receiver import Receiver
        from cyndilib.video_frame import VideoFrameSync
        ndi_lib = "cyndilib"
        print("Using cyndilib library")
    except ImportError:
        pass

if not ndi_lib:
    print("ERROR: No NDI library found!")
    print("\nInstall one of these:")
    print("  pip install pyNDI")
    print("  pip install cyndilib")
    print("\nYou may also need the NDI runtime from:")
    print("  https://www.ndi.tv/tools/")
    sys.exit(1)

def receive_with_pyndi(source_name="TouchDesigner"):
    """Receive using pyNDI library"""
    
    finder = pyNDI.NDIFinder()
    finder.start()
    
    print("Searching for NDI sources...")
    time.sleep(2)  # Give time to discover
    
    sources = finder.get_sources()
    if not sources:
        print("No NDI sources found!")
        return
    
    print(f"\nFound {len(sources)} source(s):")
    for i, src in enumerate(sources):
        print(f"  [{i}] {src}")
    
    # Find our source or use first
    selected = None
    for src in sources:
        if source_name in src:
            selected = src
            break
    
    if not selected:
        selected = sources[0]
        print(f"\nUsing first source: {selected}")
    else:
        print(f"\nUsing: {selected}")
    
    # Create receiver
    receiver = pyNDI.NDIReceiver()
    receiver.connect(selected)
    
    cv2.namedWindow('NDI Stream', cv2.WINDOW_NORMAL)
    print("\nReceiving... Press 'q' to quit")
    
    frame_count = 0
    fps_start = time.time()
    
    while True:
        # Get frame
        frame = receiver.read()
        
        if frame is not None:
            # frame is already a numpy array in BGR format for OpenCV
            height, width = frame.shape[:2]
            
            # Scale if small
            if width < 500 or height < 100:
                scale = max(2, min(1920 // width, 1080 // height))
                frame = cv2.resize(frame, (width * scale, height * scale),
                                 interpolation=cv2.INTER_NEAREST)
                if frame_count == 0:
                    print(f"Scaling {width}x{height} → {width*scale}x{height*scale}")
            
            # Add info
            info = f"NDI: {width}x{height} | Frame: {frame_count}"
            cv2.putText(frame, info, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            cv2.imshow('NDI Stream', frame)
            frame_count += 1
            
            # FPS counter
            if frame_count % 30 == 0:
                elapsed = time.time() - fps_start
                fps = 30 / elapsed
                print(f"FPS: {fps:.1f} | Total frames: {frame_count}")
                fps_start = time.time()
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cv2.destroyAllWindows()
    receiver.close()
    finder.stop()
    print(f"\nTotal frames: {frame_count}")

def receive_with_cyndilib(source_name="TouchDesigner"):
    """Receive using cyndilib"""
    
    finder = Finder()
    finder.open()
    
    print("Searching for NDI sources...")
    finder.wait_for_change(2000)  # Wait up to 2 seconds
    
    sources = list(finder.get_sources())
    if not sources:
        print("No NDI sources found!")
        return
    
    print(f"\nFound {len(sources)} source(s):")
    for i, src in enumerate(sources):
        print(f"  [{i}] {src.name}")
    
    # Find our source
    selected = None
    for src in sources:
        if source_name in src.name:
            selected = src
            break
    
    if not selected:
        selected = sources[0]
    
    print(f"\nUsing: {selected.name}")
    
    # Create receiver
    receiver = Receiver(
        color_format=RecvColorFormat.RGBX_RGBA,
        bandwidth=RecvBandwidth.highest
    )
    receiver.open(selected)
    
    # Create video frame sync
    vf = VideoFrameSync(receiver)
    
    cv2.namedWindow('NDI Stream', cv2.WINDOW_NORMAL)
    print("\nReceiving... Press 'q' to quit")
    
    frame_count = 0
    fps_start = time.time()
    
    while True:
        # Get frame
        frame = vf.get_frame()
        
        if frame is not None:
            # Get numpy array
            img = np.array(frame, copy=False)
            height, width = img.shape[:2]
            
            # Convert RGBA to BGR
            img_bgr = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            
            # Scale if small
            if width < 500 or height < 100:
                scale = max(2, min(1920 // width, 1080 // height))
                img_bgr = cv2.resize(img_bgr, (width * scale, height * scale),
                                   interpolation=cv2.INTER_NEAREST)
                if frame_count == 0:
                    print(f"Scaling {width}x{height} → {width*scale}x{height*scale}")
            
            # Add info
            info = f"NDI: {width}x{height} | Frame: {frame_count}"
            cv2.putText(img_bgr, info, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            cv2.imshow('NDI Stream', img_bgr)
            frame_count += 1
            
            # FPS counter
            if frame_count % 30 == 0:
                elapsed = time.time() - fps_start
                fps = 30 / elapsed
                print(f"FPS: {fps:.1f} | Total frames: {frame_count}")
                fps_start = time.time()
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cv2.destroyAllWindows()
    receiver.close()
    finder.close()
    print(f"\nTotal frames: {frame_count}")

def main():
    """Main entry point"""
    print("Simple NDI Receiver")
    print("=" * 50)
    
    source_name = "TouchDesigner"
    if len(sys.argv) > 1:
        source_name = sys.argv[1]
    
    try:
        if ndi_lib == "pyNDI":
            receive_with_pyndi(source_name)
        elif ndi_lib == "cyndilib":
            receive_with_cyndilib(source_name)
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()