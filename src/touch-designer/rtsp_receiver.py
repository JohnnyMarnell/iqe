#!/usr/bin/env python3
"""
RTSP Video Stream Receiver using OpenCV
Receives video stream from TouchDesigner Video Stream Out TOP

No special libraries needed - just OpenCV!
"""

import cv2
import sys
import time

def receive_rtsp_stream(url="rtsp://127.0.0.1:554/tdvidstream"):
    """Receive and display RTSP stream"""
    
    print(f"Connecting to RTSP stream: {url}")
    print("This may take a few seconds...")
    
    # Create video capture from RTSP URL
    cap = cv2.VideoCapture(url)
    
    # Set buffer size to reduce latency
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    # Check if opened successfully
    if not cap.isOpened():
        print("Error: Could not open RTSP stream")
        print("\nMake sure:")
        print("1. TouchDesigner is running")
        print("2. Video Stream Out TOP is active")
        print("3. Mode is set to 'RTSP Server'")
        print("4. No firewall is blocking port 554")
        return
    
    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    
    print(f"\nStream connected: {width}x{height} @ {fps:.1f} FPS")
    print("Press 'q' to quit")
    
    # Create window
    cv2.namedWindow('RTSP Stream', cv2.WINDOW_NORMAL)
    
    # Scale factor for small videos
    scale = 1
    if width < 500 or height < 100:
        scale = max(2, min(1920 // width, 1080 // height))
        cv2.resizeWindow('RTSP Stream', width * scale, height * scale)
        print(f"Scaling {width}x{height} → {width*scale}x{height*scale}")
    
    frame_count = 0
    fps_start = time.time()
    last_frame_time = time.time()
    
    while True:
        # Read frame
        ret, frame = cap.read()
        
        if ret:
            # Scale if needed
            if scale > 1:
                frame = cv2.resize(frame, (width * scale, height * scale), 
                                 interpolation=cv2.INTER_NEAREST)
            
            # Add info overlay
            info = f"RTSP: {width}x{height} | Frame: {frame_count}"
            cv2.putText(frame, info, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # Display
            cv2.imshow('RTSP Stream', frame)
            
            frame_count += 1
            last_frame_time = time.time()
            
            # Calculate FPS
            if frame_count % 30 == 0:
                elapsed = time.time() - fps_start
                actual_fps = 30 / elapsed
                print(f"FPS: {actual_fps:.1f} | Total frames: {frame_count}")
                fps_start = time.time()
        else:
            # Check if stream died
            if time.time() - last_frame_time > 5.0:
                print("Stream timeout - no frames for 5 seconds")
                break
        
        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"\nStopped. Total frames received: {frame_count}")

def main():
    """Main entry point"""
    print("RTSP Video Stream Receiver")
    print("=" * 50)
    
    # Default RTSP URL
    url = "rtsp://127.0.0.1:554/tdvidstream"
    
    # Allow custom URL
    if len(sys.argv) > 1:
        url = sys.argv[1]
    
    try:
        receive_rtsp_stream(url)
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()