"""
Verify ArtNet Configuration for 420x24 LED Matrix
"""

def verify_artnet_setup():
    """Check if ArtNet is properly configured"""
    
    # Check video source
    video_source = op('/project1/resize_to_24')
    if video_source:
        print(f"✓ Video source found: {video_source.width}x{video_source.height}")
    else:
        print("✗ Video source not found")
        return False
    
    # Check TOP to CHOP converter
    video_to_dmx = op('/project1/video_to_dmx')
    if video_to_dmx:
        print(f"✓ TOP to CHOP converter found")
        print(f"  - Channels: {video_to_dmx.numChans}")
        print(f"  - Samples: {video_to_dmx.numSamples}")
        print(f"  - Total values: {video_to_dmx.numChans * video_to_dmx.numSamples}")
    else:
        print("✗ TOP to CHOP converter not found")
        return False
    
    # Check DMX output
    dmx_nodes = [child for child in op('/project1').children if child.type == 'dmxoutCHOP']
    if dmx_nodes:
        print(f"✓ Found {len(dmx_nodes)} DMX output node(s)")
        for dmx in dmx_nodes:
            print(f"  - {dmx.name}:")
            print(f"    Protocol: {dmx.par.interface}")
            print(f"    Network: {dmx.par.netaddress}")
            print(f"    Active: {dmx.par.active}")
    else:
        print("✗ No DMX output nodes found")
        return False
    
    # Calculate expected values
    pixels = 420 * 24
    rgb_channels = pixels * 3
    rgba_channels = pixels * 4
    universes_needed = (rgb_channels + 511) // 512  # Round up
    
    print(f"\nExpected values:")
    print(f"  - Total pixels: {pixels:,}")
    print(f"  - RGB channels needed: {rgb_channels:,}")
    print(f"  - RGBA channels: {rgba_channels:,}")
    print(f"  - Universes needed: {universes_needed}")
    
    return True

def toggle_artnet(enable=True):
    """Enable or disable all ArtNet outputs"""
    dmx_nodes = [child for child in op('/project1').children if child.type == 'dmxoutCHOP']
    for dmx in dmx_nodes:
        dmx.par.active = enable
    print(f"ArtNet output {'enabled' if enable else 'disabled'} for {len(dmx_nodes)} node(s)")

def update_broadcast_ip(new_ip='192.168.1.255'):
    """Update broadcast IP for all DMX nodes"""
    dmx_nodes = [child for child in op('/project1').children if child.type == 'dmxoutCHOP']
    for dmx in dmx_nodes:
        dmx.par.netaddress = new_ip
    print(f"Updated {len(dmx_nodes)} DMX nodes to broadcast to {new_ip}")

# Run verification
print("=== ArtNet Setup Verification ===")
verify_artnet_setup()