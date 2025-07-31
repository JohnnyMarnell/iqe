#!/usr/bin/env python3
"""
Test all available video streams from TouchDesigner
"""

import subprocess
import time
import sys

def test_with_vlc():
    """Test streams using VLC if available"""
    print("\n=== Testing with VLC ===")
    
    streams = [
        ("RTSP", "rtsp://127.0.0.1:554/tdvidstream"),
        ("NDI", "ndi://TD_VideoStream"),
    ]
    
    for name, url in streams:
        print(f"\nTesting {name}: {url}")
        try:
            # Try to open with VLC
            subprocess.run(["vlc", "--intf", "dummy", "--vout", "dummy", 
                          "--run-time=2", "--quit-after-run", url], 
                          capture_output=True, timeout=5)
            print(f"  ✓ {name} stream detected")
        except FileNotFoundError:
            print("  VLC not installed")
            break
        except subprocess.TimeoutExpired:
            print(f"  ✗ {name} timeout")
        except Exception as e:
            print(f"  ✗ {name} error: {e}")

def test_with_ffmpeg():
    """Test streams using ffmpeg/ffprobe if available"""
    print("\n=== Testing with ffmpeg/ffprobe ===")
    
    streams = [
        ("RTSP", "rtsp://127.0.0.1:554/tdvidstream"),
    ]
    
    for name, url in streams:
        print(f"\nTesting {name}: {url}")
        try:
            # Try ffprobe
            result = subprocess.run(["ffprobe", "-v", "error", "-show_streams", 
                                   "-show_format", url], 
                                   capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"  ✓ {name} stream active")
                # Parse output for video info
                for line in result.stdout.split('\n'):
                    if 'width=' in line or 'height=' in line or 'codec_name=' in line:
                        print(f"    {line}")
            else:
                print(f"  ✗ {name} not accessible")
                print(f"    Error: {result.stderr}")
        except FileNotFoundError:
            print("  ffprobe not installed")
            break
        except subprocess.TimeoutExpired:
            print(f"  ✗ {name} timeout")
        except Exception as e:
            print(f"  ✗ {name} error: {e}")

def test_ndi_tools():
    """Check if NDI tools can see the stream"""
    print("\n=== Testing NDI ===")
    
    # Check if NDI test tool exists
    ndi_paths = [
        "/Applications/NDI Tools/NDI Test.app/Contents/MacOS/NDI Test",
        "/Applications/NDI 5 Tools/NDI Test.app/Contents/MacOS/NDI Test",
        "~/Applications/NDI Tools/NDI Test.app/Contents/MacOS/NDI Test",
    ]
    
    for path in ndi_paths:
        try:
            expanded_path = subprocess.os.path.expanduser(path)
            if subprocess.os.path.exists(expanded_path):
                print(f"Found NDI Test at: {expanded_path}")
                print("You can run it manually to check for 'TD_VideoStream'")
                break
        except:
            pass
    else:
        print("NDI Test tool not found")
        print("Download NDI Tools from: https://www.ndi.tv/tools/")

def main():
    print("Testing Video Streams from TouchDesigner")
    print("=" * 50)
    
    print("\nMake sure TouchDesigner is running with:")
    print("- NDI Out TOP (broadcasting as 'TD_VideoStream')")
    print("- Video Stream Out TOP (RTSP on port 554)")
    print("- SyphonSpout Out TOP (as 'TD_VideoStream')")
    
    input("\nPress Enter to start tests...")
    
    # Run tests
    test_with_vlc()
    test_with_ffmpeg()
    test_ndi_tools()
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("- RTSP: Use 'python rtsp_receiver.py' if ffmpeg detected stream")
    print("- NDI: Use NDI Test app or try 'python ndi_receiver_simple.py'")
    print("- Syphon: Complex due to Metal textures on macOS")

if __name__ == "__main__":
    main()