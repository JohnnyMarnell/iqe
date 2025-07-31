#!/usr/bin/env python3
"""
Working Syphon receiver for TouchDesigner output
"""

import cv2
import numpy as np
import time
import sys
from pathlib import Path

try:
    import syphon
    from syphon.client import SyphonMetalClient
except ImportError:
    print("ERROR: syphon-python not installed!")
    print("Install with: pip install syphon-python")
    sys.exit(1)

def find_touchdesigner_server():
    """Find TouchDesigner Syphon server"""
    directory = syphon.SyphonServerDirectory()
    
    # Wait a bit for servers to appear
    print("Searching for Syphon servers", end="", flush=True)
    for _ in range(5):
        servers = directory.servers  # It's a property!
        if servers:
            break
        print(".", end="", flush=True)
        time.sleep(0.5)
    print()
    
    if not servers:
        return None
    
    print(f"\nFound {len(servers)} Syphon server(s):")
    for i, server in enumerate(servers):
        print(f"  [{i}] App: {server.app_name}, Name: {server.name}")
    
    # Look for TouchDesigner
    for server in servers:
        if 'touch' in server.app_name.lower() or 'TD' in server.name:
            return server
    
    # Return first server if no TD found
    return servers[0]

def receive_syphon():
    """Main receiver function"""
    print("Syphon Video Receiver")
    print("=" * 50)
    
    # Find server
    server = find_touchdesigner_server()
    if not server:
        print("\nNo Syphon servers found!")
        print("Make sure TouchDesigner SyphonSpoutOut TOP is active")
        return
    
    print(f"\nConnecting to: {server.app_name} - {server.name}")
    
    # Create Metal client
    try:
        client = SyphonMetalClient(server)
        print("✓ Created SyphonMetalClient")
    except Exception as e:
        print(f"Failed to create client: {e}")
        return
    
    # Check client methods
    print("\nClient capabilities:")
    methods = [m for m in dir(client) if not m.startswith('_') and callable(getattr(client, m))]
    print(f"  Methods: {methods}")
    
    # Create window
    cv2.namedWindow('Syphon Stream', cv2.WINDOW_NORMAL)
    print("\nReceiving... Press 'q' to quit")
    
    frame_count = 0
    fps_start = time.time()
    
    # Check available attributes/properties
    attrs = [a for a in dir(client) if not a.startswith('_')]
    print(f"  Attributes: {attrs}")
    
    while True:
        try:
            # Try different ways to get the frame
            frame = None
            
            # Method 1: Direct property access
            if hasattr(client, 'new_frame_image'):
                frame = client.new_frame_image  # It's a property, not a method!
                if frame is not None:
                    print(f"Got frame type: {type(frame).__name__}")
                    
            # Method 2: Try other properties
            elif hasattr(client, 'frame'):
                frame = client.frame
            elif hasattr(client, 'texture'):
                frame = client.texture
            
            if frame is not None:
                # Convert to numpy/OpenCV format
                if hasattr(frame, 'save'):
                    # It's a PIL Image
                    frame_np = np.array(frame)
                    height, width = frame_np.shape[:2]
                    
                    # Convert color if needed
                    if len(frame_np.shape) == 3:
                        if frame_np.shape[2] == 4:  # RGBA
                            frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGBA2BGR)
                        else:  # RGB
                            frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
                    else:
                        frame_bgr = frame_np
                    
                elif isinstance(frame, np.ndarray):
                    frame_bgr = frame
                    height, width = frame_bgr.shape[:2]
                    
                else:
                    # Try to extract data
                    print(f"Unknown frame type: {type(frame)}")
                    if hasattr(frame, 'texture'):
                        print("  Has texture attribute - Metal texture needs conversion")
                    continue
                
                # Scale if small
                if width < 500 or height < 100:
                    scale = max(2, min(1920 // width, 1080 // height))
                    frame_bgr = cv2.resize(frame_bgr, (width * scale, height * scale),
                                         interpolation=cv2.INTER_NEAREST)
                    if frame_count == 0:
                        print(f"Scaling {width}x{height} → {width*scale}x{height*scale}")
                
                # Info overlay
                info = f"Syphon: {width}x{height} | Frame: {frame_count}"
                cv2.putText(frame_bgr, info, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                cv2.imshow('Syphon Stream', frame_bgr)
                frame_count += 1
                
                # FPS
                if frame_count % 30 == 0:
                    elapsed = time.time() - fps_start
                    fps = 30 / elapsed
                    print(f"FPS: {fps:.1f} | Frames: {frame_count}")
                    fps_start = time.time()
                    
        except Exception as e:
            print(f"Frame error: {e}")
            break
        
        # Check quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cv2.destroyAllWindows()
    if hasattr(client, 'stop'):
        client.stop()
    
    print(f"\nTotal frames: {frame_count}")

def main():
    try:
        receive_syphon()
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()