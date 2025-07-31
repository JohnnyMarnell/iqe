#!/usr/bin/env python3
"""
NDI Video Receiver using PyNDI and OpenCV
Receives NDI stream from TouchDesigner and displays it

Installation:
    pip install opencv-python numpy
    pip install ndi-python  # or PyNDI2
"""

import cv2
import numpy as np
import sys
import time

# Try to import NDI library
try:
    import NDIlib as ndi
except ImportError:
    print("ERROR: NDI library not found!")
    print("\nTo install:")
    print("  Option 1: pip install ndi-python")
    print("  Option 2: Download NDI SDK from https://www.ndi.tv/sdk/")
    print("\nNote: You may need to install the NDI runtime first:")
    print("  https://www.ndi.tv/tools/")
    sys.exit(1)

def find_ndi_sources(timeout=5.0):
    """Find available NDI sources on the network"""
    print("Searching for NDI sources...")
    
    # Create NDI finder
    find = ndi.find_create_v2()
    if find is None:
        return []
    
    # Wait for sources
    sources = []
    start = time.time()
    
    while time.time() - start < timeout:
        # Update sources
        ndi.find_wait_for_sources(find, 100)
        sources = ndi.find_get_current_sources(find)
        
        if sources:
            print(f"\nFound {len(sources)} NDI source(s):")
            for i, src in enumerate(sources):
                print(f"  [{i}] {src.ndi_name} @ {src.url_address}")
            break
        
        time.sleep(0.1)
    
    # Clean up finder
    ndi.find_destroy(find)
    
    return sources

def receive_ndi_stream(source_name="TouchDesigner", timeout=10.0):
    """Receive and display NDI stream"""
    
    # Initialize NDI
    if not ndi.initialize():
        print("Failed to initialize NDI")
        return
    
    # Find sources
    sources = find_ndi_sources(timeout)
    if not sources:
        print("No NDI sources found!")
        return
    
    # Find our source
    selected_source = None
    for src in sources:
        if source_name in src.ndi_name:
            selected_source = src
            break
    
    if not selected_source:
        print(f"\nSource '{source_name}' not found. Using first available source.")
        selected_source = sources[0]
    
    print(f"\nConnecting to: {selected_source.ndi_name}")
    
    # Create receiver
    recv_create = ndi.RecvCreateV3()
    recv_create.color_format = ndi.RECV_COLOR_FORMAT_RGBX_RGBA
    
    recv = ndi.recv_create_v3(recv_create)
    if recv is None:
        print("Failed to create receiver")
        return
    
    # Connect to source
    ndi.recv_connect(recv, selected_source)
    
    # Create OpenCV window
    cv2.namedWindow('NDI Stream', cv2.WINDOW_NORMAL)
    
    print("\nReceiving... Press 'q' to quit")
    print("Waiting for video frames...")
    
    frame_count = 0
    fps_start = time.time()
    
    while True:
        # Receive frame
        t = ndi.recv_capture_v2(recv, 100)  # 100ms timeout
        
        # Check what we received
        if t == ndi.FRAME_TYPE_VIDEO:
            # Get video frame
            video_frame = ndi.recv_get_video_frame(recv)
            
            # Get frame data
            width = video_frame.xres
            height = video_frame.yres
            stride = video_frame.line_stride_in_bytes
            
            # Convert to numpy array
            # NDI provides RGBA or RGBX format
            if video_frame.FourCC == ndi.FOURCC_VIDEO_TYPE_RGBA:
                channels = 4
            else:
                channels = 4  # RGBX also has 4 channels
            
            # Create numpy array from data
            frame_data = np.frombuffer(video_frame.data, dtype=np.uint8)
            
            # Reshape to image
            if stride == width * channels:
                # Simple case - no padding
                frame = frame_data.reshape((height, width, channels))
            else:
                # Handle stride padding
                frame = np.zeros((height, width, channels), dtype=np.uint8)
                for y in range(height):
                    row_start = y * stride
                    row_end = row_start + (width * channels)
                    frame[y] = frame_data[row_start:row_end].reshape((width, channels))
            
            # Convert RGBA to BGR for OpenCV
            frame_bgr = cv2.cvtColor(frame[:, :, :3], cv2.COLOR_RGB2BGR)
            
            # Scale up if small (like 420x24)
            if width < 500 or height < 100:
                scale = max(2, min(1920 // width, 1080 // height))
                new_width = width * scale
                new_height = height * scale
                frame_bgr = cv2.resize(frame_bgr, (new_width, new_height), 
                                     interpolation=cv2.INTER_NEAREST)
                if frame_count == 0:
                    print(f"Scaling {width}x{height} → {new_width}x{new_height}")
            
            # Add info overlay
            info = f"NDI: {width}x{height} | Frame: {frame_count}"
            cv2.putText(frame_bgr, info, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Display
            cv2.imshow('NDI Stream', frame_bgr)
            
            # Return frame to pool
            ndi.recv_free_video_v2(recv, video_frame)
            
            frame_count += 1
            
            # Calculate FPS
            if frame_count % 30 == 0:
                elapsed = time.time() - fps_start
                fps = 30 / elapsed
                print(f"FPS: {fps:.1f} | Total frames: {frame_count}")
                fps_start = time.time()
        
        elif t == ndi.FRAME_TYPE_AUDIO:
            # Free audio frame if received
            audio_frame = ndi.recv_get_audio_frame_v2(recv)
            ndi.recv_free_audio_v2(recv, audio_frame)
        
        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cv2.destroyAllWindows()
    ndi.recv_destroy(recv)
    ndi.destroy()
    
    print(f"\nStopped. Total frames received: {frame_count}")

def main():
    """Main entry point"""
    print("NDI Video Receiver")
    print("=" * 50)
    
    # Parse arguments
    source_name = "TouchDesigner"
    if len(sys.argv) > 1:
        source_name = sys.argv[1]
    
    try:
        receive_ndi_stream(source_name)
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()