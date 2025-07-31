#!/usr/bin/env python3
"""
Test what's actually in cyndilib Finder
"""

from cyndilib.finder import Finder
import time

finder = Finder()

print("Finder attributes:")
attrs = [a for a in dir(finder) if not a.startswith('_')]
for attr in attrs:
    print(f"  {attr}")

# Try to get sources different ways
print("\n\nTrying to get sources...")

# Method 1: Direct attribute access
for attr in attrs:
    try:
        val = getattr(finder, attr)
        if 'source' in attr.lower() or isinstance(val, (list, dict)):
            print(f"\n{attr}: {type(val)}")
            if callable(val):
                try:
                    result = val()
                    print(f"  Calling {attr}() returned: {type(result)}")
                    if result:
                        print(f"  Content: {result}")
                except Exception as e:
                    print(f"  Error calling: {e}")
            else:
                print(f"  Value: {val}")
    except Exception as e:
        pass

# Wait a bit for sources to be discovered
print("\n\nWaiting 2 seconds for source discovery...")
time.sleep(2)

# Try again
print("\nChecking again after wait...")
if hasattr(finder, 'get_sources'):
    try:
        sources = finder.get_sources()
        print(f"get_sources() returned: {sources}")
    except Exception as e:
        print(f"get_sources() error: {e}")

if hasattr(finder, 'sources'):
    try:
        sources = finder.sources
        print(f"sources property: {sources}")
    except Exception as e:
        print(f"sources error: {e}")

# Check internal attributes
print("\n\nInternal attributes (starting with _):")
internals = [a for a in dir(finder) if a.startswith('_') and not a.startswith('__')]
for attr in internals:
    try:
        val = getattr(finder, attr)
        if 'source' in attr.lower():
            print(f"  {attr}: {type(val)}")
    except:
        pass