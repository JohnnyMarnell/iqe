#!/usr/bin/env python3
"""
Correct cyndilib NDI test based on actual API
"""

import time
import sys

try:
    from cyndilib.finder import Finder
    from cyndilib.receiver import Receiver
    from cyndilib.wrapper.ndi_recv import RecvColorFormat, RecvBandwidth
except ImportError:
    print("ERROR: cyndilib not installed!")
    print("Install with: pip install cyndilib")
    sys.exit(1)

def test_ndi():
    # Create finder - it starts automatically
    finder = Finder()
    
    print("Waiting for NDI sources...")
    print("(Make sure TouchDesigner NDI Out TOP is active)")
    
    # Give it time to find sources
    found_any = False
    for attempt in range(10):
        time.sleep(0.5)
        
        # The finder runs in background and populates source_dict
        if hasattr(finder, 'source_dict') and finder.source_dict:
            print(f"\nFound {len(finder.source_dict)} NDI source(s):")
            
            for key, source in finder.source_dict.items():
                print(f"\nSource: {source.name}")
                print(f"  Address: {source.address}")
                print(f"  Key: {key}")
                found_any = True
            break
        else:
            print(f".", end="", flush=True)
    
    if not found_any:
        # Try another approach - create receiver without finder
        print("\n\nNo sources found via finder.")
        print("Trying direct connection to 'TD_VideoStream'...")
        
        try:
            # Create receiver directly
            receiver = Receiver(
                color_format=RecvColorFormat.RGBX_RGBA,
                bandwidth=RecvBandwidth.highest,
                ndi_name="TD_VideoStream"  # The name we set in TouchDesigner
            )
            
            print("Receiver created, attempting to receive frames...")
            
            # Try to get a frame
            for i in range(5):
                frame = receiver.recv_video()
                if frame:
                    print(f"\nSuccess! Received frame: {frame.width}x{frame.height}")
                    break
                else:
                    print(".", end="", flush=True)
                    time.sleep(1)
                    
        except Exception as e:
            print(f"\nDirect connection failed: {e}")

if __name__ == "__main__":
    test_ndi()