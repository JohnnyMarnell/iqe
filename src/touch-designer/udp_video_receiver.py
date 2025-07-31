#!/usr/bin/env python3
"""
UDP Video Stream Receiver for TouchDesigner
Receives 420x24 RGBA pixel data over UDP and displays it
"""

import socket
import numpy as np
import cv2
import struct
import time

# Configuration
UDP_IP = "127.0.0.1"
UDP_PORT = 12345
WIDTH = 420
HEIGHT = 24
CHANNELS = 4  # RGBA
BUFFER_SIZE = WIDTH * HEIGHT * CHANNELS
FPS = 30

def main():
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    sock.settimeout(1.0)  # 1 second timeout
    
    print(f"UDP Video Receiver started on {UDP_IP}:{UDP_PORT}")
    print(f"Expecting {WIDTH}x{HEIGHT} RGBA frames ({BUFFER_SIZE} bytes)")
    print("Press 'q' to quit\n")
    
    # Create window
    cv2.namedWindow('TouchDesigner Stream', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('TouchDesigner Stream', WIDTH * 2, HEIGHT * 10)  # Scale up for visibility
    
    frame_count = 0
    total_frames = 0
    start_time = time.time()
    last_data_time = time.time()
    
    while True:
        try:
            # Receive data
            data, addr = sock.recvfrom(BUFFER_SIZE + 1024)  # Extra buffer for headers
            
            # Debug first packet
            if total_frames == 0:
                print(f"First packet received: {len(data)} bytes from {addr}")
            
            # Check if we got the expected amount of data
            if len(data) == BUFFER_SIZE:
                # Convert to numpy array
                pixels = np.frombuffer(data, dtype=np.uint8)
                
                # Reshape to image format (HEIGHT, WIDTH, CHANNELS)
                frame = pixels.reshape((HEIGHT, WIDTH, CHANNELS))
                
                # Convert RGBA to BGR for OpenCV
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
                
                # Scale up for better visibility
                frame_scaled = cv2.resize(frame_bgr, (WIDTH * 2, HEIGHT * 10), 
                                        interpolation=cv2.INTER_NEAREST)
                
                # Add text overlay with stats
                cv2.putText(frame_scaled, f"Frame: {total_frames}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                # Display
                cv2.imshow('TouchDesigner Stream', frame_scaled)
                
                frame_count += 1
                total_frames += 1
                last_data_time = time.time()
                
                # Print stats every second
                elapsed = time.time() - start_time
                if elapsed >= 1.0:
                    fps = frame_count / elapsed
                    print(f"FPS: {fps:.2f}, Total frames: {total_frames}")
                    frame_count = 0
                    start_time = time.time()
            else:
                print(f"Unexpected data size: {len(data)} bytes (expected {BUFFER_SIZE})")
        
        except socket.timeout:
            if time.time() - last_data_time > 2.0:
                print("No data received for 2+ seconds... Is TouchDesigner streaming?")
                last_data_time = time.time()
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        
        # Check for quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Cleanup
    cv2.destroyAllWindows()
    sock.close()
    print(f"\nReceiver stopped. Total frames received: {total_frames}")

if __name__ == "__main__":
    main()