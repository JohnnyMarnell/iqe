#!/usr/bin/env python3
"""
Test the syphon.client module
"""

import syphon
from syphon import client

print("Checking syphon.client module...")
print("\nAvailable in syphon.client:")
attrs = [x for x in dir(client) if not x.startswith('_')]
for attr in attrs:
    obj = getattr(client, attr)
    print(f"  {attr}: {type(obj).__name__}")

# Also check SyphonServerDirectory more carefully
print("\n\nTesting SyphonServerDirectory:")
directory = syphon.SyphonServerDirectory()

print("Directory methods:")
methods = [m for m in dir(directory) if not m.startswith('_')]
for method in methods:
    print(f"  {method}")

# Try to get servers
print("\nTrying to get servers...")
if hasattr(directory, 'servers'):
    servers = directory.servers  # It's a property, not a method!
    print(f"Found {len(servers)} servers")
    for i, server in enumerate(servers):
        print(f"\nServer [{i}]: {server}")
        print(f"  Type: {type(server).__name__}")
        
        # Check server attributes
        for attr in ['app_name', 'name', 'uuid', 'icon', 'machine_name']:
            if hasattr(server, attr):
                print(f"  {attr}: {getattr(server, attr)}")

# Check if there's a simpler client
if hasattr(client, 'Client'):
    print("\n\nFound client.Client class")
    try:
        simple_client = client.Client()
        print("Client methods:", [m for m in dir(simple_client) if not m.startswith('_')])
    except Exception as e:
        print(f"Error creating client.Client: {e}")