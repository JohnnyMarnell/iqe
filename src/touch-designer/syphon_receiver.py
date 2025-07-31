#!/usr/bin/env python3
"""
Syphon Video Receiver for macOS
Receives video from TouchDesigner's SyphonSpoutOut TOP

Installation:
    pip install syphon-python opencv-python numpy
"""

import cv2
import numpy as np
import time
import sys

try:
    import syphon
except ImportError:
    print("ERROR: syphon-python not installed!")
    print("\nInstall with:")
    print("  pip install syphon-python")
    print("\nNote: Syphon only works on macOS")
    sys.exit(1)

def receive_syphon(server_name="TouchDesigner"):
    """Receive and display Syphon stream"""
    
    print(f"Starting Syphon receiver...")
    print(f"Looking for server: {server_name}")
    
    # Check what's available in syphon module
    print("\nAvailable syphon classes:", [x for x in dir(syphon) if 'Client' in x])
    
    # Create Syphon client using correct class
    try:
        # Try different client classes
        if hasattr(syphon, 'SyphonClient'):
            client = syphon.SyphonClient()
        elif hasattr(syphon, 'BaseSyphonClient'):
            client = syphon.BaseSyphonClient()
        elif hasattr(syphon, 'Client'):
            client = syphon.Client()
        else:
            # Try direct server listing
            print("\nTrying direct server listing...")
            if hasattr(syphon, 'SyphonServerDirectory'):
                directory = syphon.SyphonServerDirectory()
                servers = directory.servers()
            elif hasattr(syphon, 'ServerDirectory'):
                directory = syphon.ServerDirectory()
                servers = directory.servers()
            else:
                print("Cannot find Syphon client or directory class!")
                print("Available in syphon module:", dir(syphon))
                return
                
            if servers:
                print(f"\nFound {len(servers)} server(s):")
                for server in servers:
                    print(f"  - {server}")
            else:
                print("No servers found")
            return
            
    except Exception as e:
        print(f"Error creating client: {e}")
        return
    
    # Find available servers
    print("\nSearching for Syphon servers...")
    
    try:
        if hasattr(client, 'servers'):
            servers = client.servers()
        elif hasattr(client, 'available_servers'):
            servers = client.available_servers()
        else:
            print("Client has no server listing method")
            print("Client methods:", [x for x in dir(client) if not x.startswith('_')])
            return
    except Exception as e:
        print(f"Error getting servers: {e}")
        return
    
    if not servers:
        print("No Syphon servers found!")
        print("\nMake sure:")
        print("1. TouchDesigner is running")
        print("2. SyphonSpoutOut TOP is active")
        return
    
    print(f"\nFound {len(servers)} Syphon server(s):")
    for server in servers:
        print(f"  - {server}")
    
    # Connect to server
    connected = False
    for server in servers:
        if server_name in str(server):
            if hasattr(client, 'setup'):
                client.setup(server)
            elif hasattr(client, 'connect'):
                client.connect(server)
            connected = True
            print(f"\nConnected to: {server}")
            break
    
    if not connected:
        # Use first available
        if hasattr(client, 'setup'):
            client.setup(servers[0])
        elif hasattr(client, 'connect'):
            client.connect(servers[0])
        print(f"\nConnected to first available: {servers[0]}")
    
    # Create OpenCV window
    cv2.namedWindow('Syphon Stream', cv2.WINDOW_NORMAL)
    print("\nReceiving... Press 'q' to quit")
    
    frame_count = 0
    fps_start = time.time()
    
    while True:
        # Get frame from Syphon
        frame = client.new_frame_image()
        
        if frame is not None:
            # Convert to numpy array
            # Syphon returns PIL Image or similar
            if hasattr(frame, 'size'):
                width, height = frame.size
                # Convert to numpy array
                frame_np = np.array(frame)
                
                # Ensure BGR format for OpenCV
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
                
                # Add info
                info = f"Syphon: {width}x{height} | Frame: {frame_count}"
                cv2.putText(frame_bgr, info, (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                
                # Display
                cv2.imshow('Syphon Stream', frame_bgr)
                
                frame_count += 1
                
                # FPS counter
                if frame_count % 30 == 0:
                    elapsed = time.time() - fps_start
                    fps = 30 / elapsed
                    print(f"FPS: {fps:.1f} | Total frames: {frame_count}")
                    fps_start = time.time()
        
        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cv2.destroyAllWindows()
    client.stop()
    
    print(f"\nStopped. Total frames received: {frame_count}")

def main():
    """Main entry point"""
    print("Syphon Video Receiver (macOS)")
    print("=" * 50)
    
    server_name = "TouchDesigner"
    if len(sys.argv) > 1:
        server_name = sys.argv[1]
    
    try:
        receive_syphon(server_name)
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()