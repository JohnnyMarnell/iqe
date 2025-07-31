#!/usr/bin/env python3
"""
Final NDI Receiver using cyndilib
Based on correct API usage
"""

import cv2
import numpy as np
import time
import sys

def main():
    try:
        from cyndilib.finder import Finder
        from cyndilib.receiver import Receiver, ReceiveFrameType
        from cyndilib.wrapper.ndi_recv import RecvColorFormat, RecvBandwidth
    except ImportError:
        print("ERROR: cyndilib not installed")
        print("Install with: pip install cyndilib")
        return

    print("NDI Receiver (TouchDesigner 420x24)")
    print("=" * 50)
    
    # 1. Find sources
    finder = Finder()
    finder.open()
    
    print("Searching for NDI sources...")
    attempts = 0
    source = None
    
    while attempts < 5:
        if finder.num_sources > 0:
            for s in finder.iter_sources():
                print(f"Found: {s}")
                source = s
                break
            if source:
                break
        time.sleep(1)
        attempts += 1
    
    if not source:
        print("No NDI sources found!")
        return
    
    # 2. Create receiver
    print(f"\nConnecting to: {source}")
    receiver = Receiver()
    
    # 3. Connect
    receiver.connect_to(source)
    
    # Wait for connection
    connected = False
    for i in range(10):
        if receiver.is_connected():
            connected = True
            print("Connected!")
            break
        time.sleep(0.5)
    
    if not connected:
        print("Failed to connect")
        return
    
    # 4. Create window
    cv2.namedWindow('TouchDesigner NDI', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('TouchDesigner NDI', 840, 240)  # 2x scale
    
    print("\nReceiving video stream...")
    print("Press 'q' to quit")
    
    frame_count = 0
    last_frame_time = time.time()
    fps_timer = time.time()
    
    # 5. Main receive loop
    while True:
        # Request video frame
        frame_type = receiver.receive(ReceiveFrameType.recv_video, 100)
        
        # Check if we got video
        if frame_type == ReceiveFrameType.recv_video:
            # Get the video frame
            video_frame = receiver.video_frame
            
            if video_frame:
                try:
                    # Get frame properties
                    width = video_frame.width
                    height = video_frame.height
                    
                    # Get frame data as array
                    frame_data = video_frame.get_array()
                    
                    # Handle different data formats
                    if isinstance(frame_data, memoryview):
                        frame_data = np.array(frame_data, copy=False)
                    elif not isinstance(frame_data, np.ndarray):
                        # Try to get raw data
                        frame_data = np.frombuffer(video_frame.data, dtype=np.uint8)
                    
                    # Reshape to image
                    if frame_data.ndim == 1:
                        # Calculate stride
                        expected_size = width * height * 4  # RGBA
                        if len(frame_data) >= expected_size:
                            frame_data = frame_data[:expected_size]
                            frame_data = frame_data.reshape((height, width, 4))
                        else:
                            continue
                    
                    # Convert RGBA to BGR for OpenCV
                    frame_bgr = cv2.cvtColor(frame_data, cv2.COLOR_RGBA2BGR)
                    
                    # Scale up 2x for visibility
                    frame_bgr = cv2.resize(frame_bgr, (width * 2, height * 10), 
                                         interpolation=cv2.INTER_NEAREST)
                    
                    # Add status text
                    status = f"NDI: {width}x{height} | Frame: {frame_count}"
                    cv2.putText(frame_bgr, status, (10, 30), 
                              cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    # Display
                    cv2.imshow('TouchDesigner NDI', frame_bgr)
                    
                    frame_count += 1
                    last_frame_time = time.time()
                    
                    # Print FPS every 30 frames
                    if frame_count % 30 == 0:
                        elapsed = time.time() - fps_timer
                        fps = 30 / elapsed
                        print(f"FPS: {fps:.1f} | Total frames: {frame_count}")
                        fps_timer = time.time()
                        
                except Exception as e:
                    print(f"Frame processing error: {e}")
                    
        # Check for timeout
        elif time.time() - last_frame_time > 3:
            print("No frames for 3 seconds...")
            last_frame_time = time.time()
        
        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # 6. Cleanup
    print("\nCleaning up...")
    cv2.destroyAllWindows()
    receiver.disconnect()
    finder.close()
    
    print(f"Total frames received: {frame_count}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()