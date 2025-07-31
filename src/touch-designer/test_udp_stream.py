#!/usr/bin/env python3
"""
Test script to verify UDP pixel streaming from TouchDesigner
Run this to test the video stream
"""

import subprocess
import time
import sys

def main():
    print("TouchDesigner UDP Video Stream Test")
    print("=" * 40)
    print()
    print("Make sure TouchDesigner is running with the streaming setup!")
    print()
    print("Starting receiver in 3 seconds...")
    time.sleep(3)
    
    # Run the receiver
    try:
        subprocess.run([sys.executable, "udp_video_receiver.py"])
    except KeyboardInterrupt:
        print("\nTest stopped by user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()