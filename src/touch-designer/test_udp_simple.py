#!/usr/bin/env python3
"""
Simple UDP test to verify basic connectivity
"""

import socket
import time

# Test sender
def test_sender():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    test_message = b"Hello from TouchDesigner test!"
    
    print("Sending test UDP packets to 127.0.0.1:12345...")
    for i in range(5):
        sock.sendto(test_message + f" {i}".encode(), ("127.0.0.1", 12345))
        print(f"Sent packet {i}")
        time.sleep(0.5)
    
    sock.close()
    print("Test complete")

# Test receiver
def test_receiver():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("127.0.0.1", 12345))
    sock.settimeout(2.0)
    
    print("Listening on 127.0.0.1:12345...")
    
    try:
        for i in range(5):
            try:
                data, addr = sock.recvfrom(1024)
                print(f"Received: {data.decode()} from {addr}")
            except socket.timeout:
                print("Timeout - no data received")
    finally:
        sock.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "send":
        test_sender()
    else:
        test_receiver()