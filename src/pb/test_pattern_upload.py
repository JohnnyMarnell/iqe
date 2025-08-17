#!/usr/bin/env python3
"""
Test pattern upload to PixelBlaze
"""

import sys
from pixelblaze import Pixelblaze
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: python test_pattern_upload.py <IP_ADDRESS>")
    sys.exit(1)

ip = sys.argv[1]
print(f"Testing pattern upload to PixelBlaze at {ip}...")

# Read the pattern file
pattern_file = Path("patterns/dramatic_swell.js")
if not pattern_file.exists():
    print(f"Pattern file not found: {pattern_file}")
    sys.exit(1)

with open(pattern_file, 'r') as f:
    source_code = f.read()

print(f"Read pattern: {len(source_code)} characters")

try:
    pb = Pixelblaze(ip)
    
    # Method 1: Try compilePattern then savePattern
    print("\nAttempting to compile pattern...")
    try:
        # Try to compile the pattern
        compiled = pb.compilePattern(source_code)
        print(f"  Compilation result type: {type(compiled)}")
        print(f"  Compilation result: {compiled}")
        
        # If compilation returns bytecode, try to save it
        if compiled:
            print("\nAttempting to save compiled pattern...")
            # We need a preview image - just use empty bytes for now
            preview_image = b''
            
            # Try different approaches
            try:
                # Approach 1: savePattern with all params
                pb.savePattern(
                    previewImage=preview_image,
                    sourceCode=source_code,
                    byteCode=compiled
                )
                print("  ✅ Pattern saved using savePattern!")
            except Exception as e:
                print(f"  ❌ savePattern failed: {e}")
                
    except Exception as e:
        print(f"  compilePattern error: {e}")
    
    # Method 2: Try putFile (might work for patterns)
    print("\nAttempting putFile method...")
    try:
        # Patterns might be stored as files
        pattern_name = "IQE_Swell_Test"
        file_path = f"/patterns/{pattern_name}.js"
        
        pb.putFile(file_path, source_code.encode('utf-8'))
        print(f"  ✅ Pattern uploaded as file: {file_path}")
        
        # Check if it appears in pattern list
        patterns = pb.getPatternList()
        found = False
        for pid, pname in patterns.items():
            if isinstance(pname, str) and pattern_name in pname:
                found = True
                print(f"  ✅ Pattern found in list: {pname} (ID: {pid})")
                break
        
        if not found:
            print(f"  ⚠️  Pattern not found in list after upload")
            
    except Exception as e:
        print(f"  putFile error: {e}")
    
    # Method 3: Check what methods actually exist
    print("\nChecking method signatures...")
    import inspect
    
    if hasattr(pb, 'compilePattern'):
        sig = inspect.signature(pb.compilePattern)
        print(f"  compilePattern: {sig}")
    
    if hasattr(pb, 'savePattern'):
        sig = inspect.signature(pb.savePattern)
        print(f"  savePattern: {sig}")
        
    if hasattr(pb, 'putFile'):
        sig = inspect.signature(pb.putFile)
        print(f"  putFile: {sig}")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()