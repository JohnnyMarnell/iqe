#!/usr/bin/env python3
"""
Syphon Metal Client for receiving video from TouchDesigner
Uses the correct syphon-python API
"""

import cv2
import numpy as np
import time
import sys

try:
    import syphon
except ImportError:
    print("ERROR: syphon-python not installed!")
    print("Install with: pip install syphon-python")
    sys.exit(1)

def receive_syphon():
    """Receive video using SyphonMetalClient"""
    
    print("Syphon Metal Receiver")
    print("=" * 50)
    
    # First, use SyphonServerDirectory to find available servers
    print("Searching for Syphon servers...")
    directory = syphon.SyphonServerDirectory()
    
    # Get list of servers
    servers = directory.servers()
    
    if not servers:
        print("No Syphon servers found!")
        print("\nMake sure:")
        print("1. TouchDesigner is running")
        print("2. SyphonSpoutOut TOP is active")
        print("3. Both apps are on the same machine")
        return
    
    print(f"\nFound {len(servers)} Syphon server(s):")
    for i, server in enumerate(servers):
        print(f"  [{i}] {server}")
        # Check if it's a SyphonServerDescription
        if hasattr(server, 'app_name'):
            print(f"      App: {server.app_name}")
        if hasattr(server, 'name'):
            print(f"      Name: {server.name}")
    
    # Select server (use first or look for TouchDesigner)
    selected_server = servers[0]
    for server in servers:
        if hasattr(server, 'app_name') and 'touch' in server.app_name.lower():
            selected_server = server
            break
        elif hasattr(server, 'name') and 'TD' in server.name:
            selected_server = server
            break
    
    print(f"\nConnecting to: {selected_server}")
    
    # Create Metal client with the server description
    try:
        client = syphon.SyphonMetalClient(selected_server)
        print("✓ Created SyphonMetalClient")
    except Exception as e:
        print(f"Failed to create client: {e}")
        return
    
    # Create window
    cv2.namedWindow('Syphon Stream', cv2.WINDOW_NORMAL)
    print("\nReceiving... Press 'q' to quit")
    
    frame_count = 0
    fps_start = time.time()
    last_frame_time = time.time()
    
    while True:
        try:
            # Get new frame
            # Check available methods
            if hasattr(client, 'new_frame_image'):
                frame = client.new_frame_image()
            elif hasattr(client, 'get_frame'):
                frame = client.get_frame()
            elif hasattr(client, 'capture'):
                frame = client.capture()
            else:
                print("Client methods:", [m for m in dir(client) if not m.startswith('_')])
                break
            
            if frame is not None:
                # Convert frame to numpy array
                # Frame might be a Metal texture or PIL image
                if hasattr(frame, 'texture'):
                    # It's a Metal texture, need to read pixels
                    # This is complex - might need to use Metal APIs
                    print("Got Metal texture - conversion needed")
                    continue
                    
                elif hasattr(frame, 'size'):
                    # PIL Image
                    width, height = frame.size
                    frame_np = np.array(frame)
                    
                elif isinstance(frame, np.ndarray):
                    # Already numpy
                    frame_np = frame
                    height, width = frame_np.shape[:2]
                    
                else:
                    print(f"Unknown frame type: {type(frame)}")
                    continue
                
                # Ensure BGR for OpenCV
                if len(frame_np.shape) == 3:
                    if frame_np.shape[2] == 4:  # RGBA
                        frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGBA2BGR)
                    elif frame_np.shape[2] == 3:  # RGB
                        frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
                    else:
                        frame_bgr = frame_np
                else:
                    frame_bgr = frame_np
                
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
                last_frame_time = time.time()
                
                # FPS
                if frame_count % 30 == 0:
                    elapsed = time.time() - fps_start
                    fps = 30 / elapsed
                    print(f"FPS: {fps:.1f} | Frames: {frame_count}")
                    fps_start = time.time()
            
            else:
                # No frame
                if time.time() - last_frame_time > 2.0:
                    print("No frames for 2 seconds...")
                    last_frame_time = time.time()
                    
        except Exception as e:
            print(f"Frame error: {e}")
            import traceback
            traceback.print_exc()
            break
        
        # Check quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cv2.destroyAllWindows()
    
    # Stop client if it has the method
    if hasattr(client, 'stop'):
        client.stop()
    elif hasattr(client, 'release'):
        client.release()
    
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