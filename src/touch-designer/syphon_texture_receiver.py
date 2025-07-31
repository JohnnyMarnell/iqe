#!/usr/bin/env python3
"""
Syphon receiver that handles Metal textures
"""

import cv2
import numpy as np
import time
import sys

try:
    import syphon
    from syphon.client import SyphonMetalClient
    # Try to import Metal/CoreImage for texture handling
    try:
        import Metal
        import CoreImage
        from PIL import Image
        HAS_METAL = True
    except:
        HAS_METAL = False
        print("Warning: Metal/CoreImage not available, trying alternative methods")
except ImportError:
    print("ERROR: syphon-python not installed!")
    print("Install with: pip install syphon-python")
    sys.exit(1)

def texture_to_numpy(texture):
    """Convert Metal texture to numpy array"""
    if not HAS_METAL:
        return None
        
    try:
        # Get texture properties
        width = texture.width
        height = texture.height
        
        # Create a buffer to read pixels
        bytes_per_pixel = 4  # RGBA
        bytes_per_row = width * bytes_per_pixel
        total_bytes = height * bytes_per_row
        
        # Read texture data
        buffer = bytearray(total_bytes)
        texture.get_bytes(
            buffer,
            bytesPerRow=bytes_per_row,
            from_region=Metal.MTLRegionMake2D(0, 0, width, height),
            mipmapLevel=0
        )
        
        # Convert to numpy
        arr = np.frombuffer(buffer, dtype=np.uint8)
        arr = arr.reshape((height, width, 4))  # RGBA
        
        return arr
        
    except Exception as e:
        print(f"Texture conversion error: {e}")
        return None

def receive_syphon():
    """Main receiver"""
    print("Syphon Texture Receiver")
    print("=" * 50)
    
    # Find server
    directory = syphon.SyphonServerDirectory()
    time.sleep(1)  # Wait for servers
    
    servers = directory.servers
    if not servers:
        print("No Syphon servers found!")
        return
    
    print(f"\nFound {len(servers)} server(s):")
    for server in servers:
        print(f"  {server.app_name} - {server.name}")
    
    # Connect to first server
    server = servers[0]
    print(f"\nConnecting to: {server.app_name} - {server.name}")
    
    # Create client
    client = SyphonMetalClient(server)
    print("✓ Connected")
    
    # Check what we can access
    print("\nClient info:")
    print(f"  Has new_frame_image: {hasattr(client, 'new_frame_image')}")
    print(f"  Type of new_frame_image: {type(client.new_frame_image) if hasattr(client, 'new_frame_image') else 'N/A'}")
    
    # Alternative: Use OpenGL client instead of Metal
    if not HAS_METAL:
        print("\nTrying OpenGL client instead...")
        from syphon.client import SyphonOpenGLClient
        client.stop()
        client = SyphonOpenGLClient(server)
        print("✓ Switched to OpenGL client")
    
    cv2.namedWindow('Syphon Stream', cv2.WINDOW_NORMAL)
    print("\nReceiving... Press 'q' to quit")
    
    frame_count = 0
    last_texture = None
    
    while True:
        try:
            # Get the current texture/frame
            if hasattr(client, 'new_frame_image'):
                texture = client.new_frame_image
                
                # Check if it's a new frame
                if texture is not None and texture != last_texture:
                    last_texture = texture
                    
                    # Debug first frame
                    if frame_count == 0:
                        print(f"\nTexture info:")
                        print(f"  Type: {type(texture)}")
                        print(f"  Attributes: {[a for a in dir(texture) if not a.startswith('_')][:10]}")
                    
                    # Try to convert texture
                    frame_np = None
                    
                    # Method 1: Direct numpy conversion if available
                    if hasattr(texture, 'to_numpy'):
                        frame_np = texture.to_numpy()
                    
                    # Method 2: Manual Metal texture conversion
                    elif HAS_METAL and hasattr(texture, 'width'):
                        frame_np = texture_to_numpy(texture)
                    
                    # Method 3: Check if it's already an image
                    elif hasattr(texture, 'save') or hasattr(texture, 'convert'):
                        # It's a PIL Image
                        frame_np = np.array(texture)
                    
                    if frame_np is not None:
                        # Convert color
                        if len(frame_np.shape) == 3:
                            if frame_np.shape[2] == 4:
                                frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGBA2BGR)
                            else:
                                frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
                        else:
                            frame_bgr = frame_np
                        
                        # Get dimensions
                        height, width = frame_bgr.shape[:2]
                        
                        # Scale if small
                        if width < 500 or height < 100:
                            scale = max(2, min(1920 // width, 1080 // height))
                            frame_bgr = cv2.resize(frame_bgr, (width * scale, height * scale),
                                                 interpolation=cv2.INTER_NEAREST)
                        
                        # Display
                        cv2.imshow('Syphon Stream', frame_bgr)
                        frame_count += 1
                        
                        if frame_count % 30 == 0:
                            print(f"Frames: {frame_count}")
            
            # Alternative: Try frame property
            elif hasattr(client, 'frame'):
                frame = client.frame
                if frame is not None:
                    # Process frame...
                    pass
                    
        except Exception as e:
            print(f"Error: {e}")
            break
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cv2.destroyAllWindows()
    client.stop()
    print(f"\nTotal frames: {frame_count}")

if __name__ == "__main__":
    try:
        receive_syphon()
    except KeyboardInterrupt:
        print("\nStopped")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()