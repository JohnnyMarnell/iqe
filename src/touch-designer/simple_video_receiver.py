#!/usr/bin/env python3
"""
Simple video receiver that tries multiple methods
"""

import cv2
import time
import sys

def try_rtsp():
    """Try RTSP stream"""
    print("\n1. Trying RTSP stream...")
    url = "rtsp://127.0.0.1:554/tdvidstream"
    
    cap = cv2.VideoCapture(url)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    if cap.isOpened():
        print(f"✓ RTSP connected to {url}")
        return cap
    else:
        print("✗ RTSP failed")
        return None

def try_http():
    """Try HTTP stream"""
    print("\n2. Trying HTTP stream...")
    urls = [
        "http://127.0.0.1:8080/video",
        "http://127.0.0.1:8080/stream",
        "http://127.0.0.1:8080/"
    ]
    
    for url in urls:
        cap = cv2.VideoCapture(url)
        if cap.isOpened():
            print(f"✓ HTTP connected to {url}")
            return cap
    
    print("✗ HTTP failed")
    return None

def try_direct_capture():
    """Try direct capture devices"""
    print("\n3. Checking capture devices...")
    
    # Try first few device indices
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"  Device {i}: {width}x{height}")
            
            # Check if it might be virtual/syphon
            if width == 420 and height == 24:
                print(f"✓ Found matching resolution on device {i}!")
                return cap
            cap.release()
    
    print("✗ No matching capture device")
    return None

def main():
    print("Simple Video Receiver")
    print("=" * 50)
    print("Trying different methods to receive video from TouchDesigner...")
    
    # Try different methods
    methods = [
        try_rtsp,
        try_http,
        try_direct_capture
    ]
    
    cap = None
    for method in methods:
        cap = method()
        if cap:
            break
    
    if not cap:
        print("\nNo video source found!")
        print("\nMake sure TouchDesigner has one of these active:")
        print("- Video Stream Out TOP (RTSP mode)")
        print("- NDI Out TOP")
        print("- SyphonSpoutOut TOP")
        return
    
    # Display video
    cv2.namedWindow('Video Stream', cv2.WINDOW_NORMAL)
    print("\nReceiving video... Press 'q' to quit")
    
    frame_count = 0
    fps_start = time.time()
    
    while True:
        ret, frame = cap.read()
        
        if ret:
            height, width = frame.shape[:2]
            
            # Scale if small
            if width < 500 or height < 100:
                scale = max(2, min(1920 // width, 1080 // height))
                frame = cv2.resize(frame, (width * scale, height * scale),
                                 interpolation=cv2.INTER_NEAREST)
            
            # Info overlay
            info = f"Size: {width}x{height} | Frame: {frame_count}"
            cv2.putText(frame, info, (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            cv2.imshow('Video Stream', frame)
            frame_count += 1
            
            # FPS
            if frame_count % 30 == 0:
                elapsed = time.time() - fps_start
                fps = 30 / elapsed
                print(f"FPS: {fps:.1f}")
                fps_start = time.time()
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print(f"\nTotal frames: {frame_count}")

if __name__ == "__main__":
    main()