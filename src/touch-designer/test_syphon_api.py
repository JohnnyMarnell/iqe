#!/usr/bin/env python3
"""
Test what's actually in the syphon-python library
"""

try:
    import syphon
    print("syphon module imported successfully")
    print("\nAvailable in syphon module:")
    
    # List all non-private attributes
    attrs = [x for x in dir(syphon) if not x.startswith('_')]
    for attr in sorted(attrs):
        obj = getattr(syphon, attr)
        print(f"  {attr}: {type(obj).__name__}")
    
    # Check for common patterns
    print("\nChecking for client classes:")
    client_attrs = [x for x in attrs if 'client' in x.lower()]
    print(f"  Client-related: {client_attrs}")
    
    print("\nChecking for server/directory classes:")
    server_attrs = [x for x in attrs if 'server' in x.lower() or 'directory' in x.lower()]
    print(f"  Server-related: {server_attrs}")
    
    # Try to use what we find
    if 'SyphonMetalClient' in attrs:
        print("\nFound SyphonMetalClient - trying to use it:")
        try:
            client = syphon.SyphonMetalClient()
            print(f"  Created client: {client}")
            print(f"  Client methods: {[x for x in dir(client) if not x.startswith('_')]}")
        except Exception as e:
            print(f"  Error: {e}")
    
    if 'SyphonMetalServer' in attrs:
        print("\nFound SyphonMetalServer")
        
except ImportError as e:
    print(f"Failed to import syphon: {e}")
    print("\nMake sure to install:")
    print("  pip install syphon-python")