# TouchDesigner ArtNet Automation Plan for Claude Code MCP

## Objective
Automate TouchDesigner node creation and configuration to output ArtNet packets from a 420x24 pixel video source to PixLite controllers. Use native TouchDesigner components exclusively, controlled via Python scripting through the MCP server.

## System Requirements
- **Input**: 420x24 pixel video source (TOP)
- **Output**: ArtNet packets via DMX Out CHOP
- **Total pixels**: 10,080 RGB pixels
- **Channels needed**: 30,240 (10,080 × 3 RGB channels)
- **Universes required**: 60 (512 channels per universe)

## TouchDesigner Node Architecture

### Core Node Chain
```
[Video Source TOP 420x24] → [TOP to CHOP] → [DMX Out CHOP] → ArtNet Output
```

### Python Implementation for MCP

```python
def create_artnet_pipeline(comp):
    """
    Creates complete ArtNet pipeline in TouchDesigner
    Call this function via MCP to build the node network
    """
    
    # Create TOP to CHOP converter
    toptochop = comp.create(topToCHOP, 'video_to_dmx')
    toptochop.par.resolution = 420, 24
    toptochop.par.pixelformat = 'rgb'
    toptochop.par.rotate = 0
    
    # Create DMX Out CHOP for ArtNet
    dmxout = comp.create(dmxoutCHOP, 'artnet_output')
    dmxout.par.protocol = 'artnet'
    dmxout.par.artnetsubnet = 0
    dmxout.par.artnetuniverse = 0
    dmxout.par.artnetbroadcast = True
    dmxout.par.artnetip = '192.168.1.255'  # Broadcast address
    dmxout.par.active = True
    
    # Connect TOP to CHOP to DMX Out
    dmxout.inputConnectors[0].connect(toptochop)
    
    return toptochop, dmxout

def configure_universe_mapping(dmxout_node, total_universes=60):
    """
    Configure DMX Out CHOP for multiple universe output
    """
    # Enable multi-universe mode
    dmxout_node.par.universes = total_universes
    dmxout_node.par.universesize = 512
    
    # Set channel mapping for RGB pixel data
    dmxout_node.par.channelstart = 1
    dmxout_node.par.channelend = 30240  # Total channels needed
    
    return dmxout_node

def setup_video_source_connection(video_source_op, toptochop_node):
    """
    Connect existing video source to the ArtNet pipeline
    """
    toptochop_node.inputConnectors[0].connect(video_source_op)
    
    # Ensure video source is correct resolution
    video_source_op.par.w = 420
    video_source_op.par.h = 24
    
    return True

def optimize_performance_settings(toptochop_node):
    """
    Apply performance optimizations for real-time output
    """
    # TOP to CHOP optimization
    toptochop_node.par.stretch = 'fit'
    toptochop_node.par.pixelformat = 'rgb'
    toptochop_node.par.interleave = 'pixel'
    
    # Enable GPU acceleration if available
    toptochop_node.par.gpumem = True
    
    return toptochop_node

def create_universe_splitter(comp, source_chop, num_universes=60):
    """
    Create individual DMX Out CHOPs for each universe
    Needed for stable high-universe-count output
    """
    dmx_outputs = []
    
    for universe_id in range(num_universes):
        # Create select CHOP for this universe's channels
        select_chop = comp.create(selectCHOP, f'universe_{universe_id}_select')
        
        # Calculate channel range for this universe
        start_chan = universe_id * 512
        end_chan = min(start_chan + 511, 30239)
        
        select_chop.par.channames = f'chan{start_chan}:chan{end_chan}'
        select_chop.inputConnectors[0].connect(source_chop)
        
        # Create DMX Out for this specific universe
        dmx_out = comp.create(dmxoutCHOP, f'artnet_universe_{universe_id}')
        dmx_out.par.protocol = 'artnet'
        dmx_out.par.artnetsubnet = 0
        dmx_out.par.artnetuniverse = universe_id
        dmx_out.par.artnetbroadcast = True
        dmx_out.par.artnetip = '192.168.1.255'
        dmx_out.par.active = True
        
        # Connect select to DMX out
        dmx_out.inputConnectors[0].connect(select_chop)
        
        dmx_outputs.append((select_chop, dmx_out))
    
    return dmx_outputs

def setup_network_configuration(dmx_nodes, target_ip='192.168.1.255'):
    """
    Configure network settings for all DMX outputs
    """
    for node in dmx_nodes:
        if hasattr(node, 'par'):
            node.par.artnetip = target_ip
            node.par.artnetport = 6454  # Standard ArtNet port
            node.par.artnetbroadcast = True
    
    return True

def create_monitoring_system(comp, dmx_outputs):
    """
    Create monitoring nodes to track ArtNet output status
    """
    # Create info CHOP to monitor frame rates
    info_chop = comp.create(infoCHOP, 'artnet_monitor')
    info_chop.par.fps = True
    info_chop.par.framecount = True
    
    # Create text TOP for status display
    status_text = comp.create(textTOP, 'artnet_status')
    status_text.par.text = f'ArtNet Output: {len(dmx_outputs)} universes'
    status_text.par.fontsize = 20
    
    return info_chop, status_text

def apply_pixel_mapping_420x24(toptochop_node):
    """
    Configure pixel mapping for 420x24 LED matrix layout
    Assumes row-major order with 24 rows of 420 pixels each
    """
    toptochop_node.par.resolution = 420, 24
    toptochop_node.par.pixelformat = 'rgb'
    
    # Set channel naming for proper DMX mapping
    toptochop_node.par.chanprefix = 'chan'
    toptochop_node.par.channelsuffix = ''
    
    # Configure for sequential RGB channel output
    toptochop_node.par.interleave = 'pixel'  # R1G1B1R2G2B2...
    
    return toptochop_node

def full_automation_setup(comp, video_source_name):
    """
    Complete automation function to call via MCP
    Creates entire ArtNet pipeline from video source
    """
    # Get existing video source
    video_source = comp.op(video_source_name)
    if not video_source:
        raise Exception(f"Video source '{video_source_name}' not found")
    
    # Create main pipeline
    toptochop, dmx_out = create_artnet_pipeline(comp)
    
    # Connect video source
    setup_video_source_connection(video_source, toptochop)
    
    # Apply pixel mapping
    apply_pixel_mapping_420x24(toptochop)
    
    # Optimize performance
    optimize_performance_settings(toptochop)
    
    # Create multi-universe setup for stability
    universe_outputs = create_universe_splitter(comp, toptochop, 60)
    
    # Configure networking
    all_dmx_nodes = [dmx_out] + [node[1] for node in universe_outputs]
    setup_network_configuration(all_dmx_nodes)
    
    # Create monitoring
    monitor_info, status_display = create_monitoring_system(comp, universe_outputs)
    
    # Organize nodes in network editor
    organize_nodes_layout(comp, toptochop, universe_outputs, monitor_info, status_display)
    
    return {
        'toptochop': toptochop,
        'main_dmx': dmx_out,
        'universe_outputs': universe_outputs,
        'monitor': monitor_info,
        'status': status_display
    }

def organize_nodes_layout(comp, toptochop, universe_outputs, monitor, status):
    """
    Organize nodes in clean layout for debugging
    """
    # Position main conversion node
    toptochop.nodeX = 0
    toptochop.nodeY = 0
    
    # Position universe outputs in grid
    for i, (select_chop, dmx_out) in enumerate(universe_outputs):
        row = i // 10
        col = i % 10
        
        select_chop.nodeX = col * 200
        select_chop.nodeY = -200 - (row * 100)
        
        dmx_out.nodeX = col * 200
        dmx_out.nodeY = -300 - (row * 100)
    
    # Position monitoring nodes
    monitor.nodeX = 1000
    monitor.nodeY = 0
    
    status.nodeX = 1200
    status.nodeY = 0

# MCP Integration Commands
def execute_setup_command(video_source_name="your_video_source"):
    """
    Main command for MCP to execute complete setup
    """
    try:
        result = full_automation_setup(op('/project1'), video_source_name)
        return f"ArtNet setup complete: {len(result['universe_outputs'])} universes configured"
    except Exception as e:
        return f"Setup failed: {str(e)}"

def update_target_ip(new_ip):
    """
    Update ArtNet target IP for all DMX outputs
    """
    dmx_nodes = [op for op in ops('*') if op.type == dmxoutCHOP]
    setup_network_configuration(dmx_nodes, new_ip)
    return f"Updated {len(dmx_nodes)} DMX outputs to IP: {new_ip}"

def toggle_artnet_output(enabled=True):
    """
    Enable/disable all ArtNet outputs
    """
    dmx_nodes = [op for op in ops('*') if op.type == dmxoutCHOP]
    for node in dmx_nodes:
        node.par.active = enabled
    return f"ArtNet output {'enabled' if enabled else 'disabled'} for {len(dmx_nodes)} universes"
```

## MCP Execution Strategy

### Initial Setup Command
```python
# Execute via MCP to create complete pipeline
result = execute_setup_command("your_video_top_name")
print(result)
```

### Runtime Control Commands
```python
# Update network configuration
update_target_ip("192.168.1.100")

# Toggle output
toggle_artnet_output(True)

# Monitor performance
monitor_node = op('artnet_monitor')
fps = monitor_node['fps']
print(f"Current FPS: {fps}")
```

## Network Configuration

### PixLite Controller Setup
- **IP Range**: 192.168.1.x
- **ArtNet Port**: 6454 (standard)
- **Universe Assignment**: Sequential 0-59
- **Protocol**: ArtNet v4

### TouchDesigner Network Settings
- **Broadcast IP**: 192.168.1.255
- **Dedicated NIC**: Recommended for high universe count
- **Firewall**: Allow UDP port 6454 outbound

## Performance Optimization

### TOP to CHOP Settings
- **Resolution**: Exact 420x24
- **Pixel Format**: RGB (no alpha channel)
- **GPU Memory**: Enabled
- **Interleave**: Pixel-based (RGB sequential)

### DMX Output Optimization
- **Universe Splitting**: Separate DMX Out CHOPs for each universe
- **Active Monitoring**: Frame rate and error checking
- **Channel Mapping**: Direct 1:1 pixel to channel mapping

## Validation Steps

1. **Node Creation**: Verify all 60 DMX Out CHOPs created
2. **Channel Count**: Confirm 30,240 total channels mapped
3. **Network Output**: Check ArtNet packets on network interface
4. **PixLite Reception**: Verify controller receives all universes
5. **Frame Rate**: Maintain target FPS for audio reactivity

## Troubleshooting Commands

```python
# Check DMX output status
def check_artnet_status():
    dmx_nodes = [op for op in ops('*') if op.type == dmxoutCHOP]
    active_count = sum(1 for node in dmx_nodes if node.par.active.eval())
    return f"{active_count}/{len(dmx_nodes)} universes active"

# Reset all ArtNet outputs
def reset_artnet_pipeline():
    dmx_nodes = [op for op in ops('*') if op.type == dmxoutCHOP]
    for node in dmx_nodes:
        node.par.active = False
        node.par.active = True
    return "ArtNet pipeline reset complete"
```

This automation plan enables Claude Code to build and configure the complete TouchDesigner ArtNet pipeline programmatically, handling your 420x24 pixel matrix with native TouchDesigner components and proper universe distribution.