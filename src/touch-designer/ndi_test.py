#!/usr/bin/env python3
"""
Minimal NDI test - just list sources
"""

import time

# Try to find which NDI library we have
try:
    from cyndilib.finder import Finder
    print("Found cyndilib")
    
    # Create finder
    finder = Finder()
    
    print("Waiting for NDI sources...")
    
    # Check multiple times
    for i in range(5):
        time.sleep(1)
        
        # Try to get source by index or iterate
        try:
            # Check if finder has sources
            source_count = 0
            sources = []
            
            # Try to get sources by index
            idx = 0
            while True:
                try:
                    source = finder.get_source(idx)
                    if source:
                        sources.append(source)
                        idx += 1
                    else:
                        break
                except:
                    break
            
            if sources:
                print(f"\nFound {len(sources)} NDI source(s):")
                for source in sources:
                    print(f"  - Name: {source.name if hasattr(source, 'name') else 'Unknown'}")
                    if hasattr(source, 'address'):
                        print(f"    Address: {source.address}")
                break
            else:
                print(f"  Attempt {i+1}/5: No sources yet...")
                
        except Exception as e:
            print(f"  Error checking sources: {e}")
    
    if not sources:
        print("\nNo NDI sources found!")
        print("Make sure:")
        print("1. TouchDesigner is running")
        print("2. NDI Out TOP is active")
        print("3. Both are on same network/machine")

except ImportError as e:
    print(f"cyndilib import error: {e}")
    
    # Try another library
    try:
        import NDIlib as ndi
        print("\nFound NDIlib")
        
        if not ndi.initialize():
            print("Failed to initialize NDI")
        else:
            find = ndi.find_create_v2()
            if find:
                print("Waiting for sources...")
                
                for i in range(5):
                    ndi.find_wait_for_sources(find, 1000)
                    sources = ndi.find_get_current_sources(find)
                    
                    if sources:
                        print(f"\nFound {len(sources)} source(s):")
                        for src in sources:
                            print(f"  - {src.ndi_name}")
                        break
                    else:
                        print(f"  Attempt {i+1}/5: No sources yet...")
                        
                ndi.find_destroy(find)
            ndi.destroy()
            
    except ImportError:
        print("\nNo NDI Python library found!")
        print("Try installing:")
        print("  pip install cyndilib")
        print("  pip install ndi-python")