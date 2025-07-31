"""
ArtNet Automation Functions for TouchDesigner
Creates 420x24 pixel ArtNet output system
"""

def create_artnet_pipeline(comp):
    """
    Creates complete ArtNet pipeline in TouchDesigner
    """
    # Create TOP to CHOP converter
    toptochop = comp.create(topToCHOP, 'video_to_dmx')
    toptochop.par.resolutionw = 420
    toptochop.par.resolutionh = 24
    toptochop.par.dataformat = 'rgb'
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
    toptochop.outputConnectors[0].connect(dmxout)
    
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
    video_source_op.outputConnectors[0].connect(toptochop_node)
    
    # Ensure video source is correct resolution
    if hasattr(video_source_op.par, 'resolutionw'):
        video_source_op.par.resolutionw = 420
        video_source_op.par.resolutionh = 24
    
    return True

def optimize_performance_settings(toptochop_node):
    """
    Apply performance optimizations for real-time output
    """
    # TOP to CHOP optimization
    toptochop_node.par.stretch = 0  # 'fit' mode
    toptochop_node.par.dataformat = 'rgb'
    toptochop_node.par.interleave = 'pixel'
    
    # Enable GPU acceleration if available
    if hasattr(toptochop_node.par, 'gpumem'):
        toptochop_node.par.gpumem = True
    
    return toptochop_node

def create_universe_splitter(comp, source_chop, num_universes=60):
    """
    Create individual DMX Out CHOPs for each universe
    """
    dmx_outputs = []
    
    for universe_id in range(num_universes):
        # Create select CHOP for this universe's channels
        select_chop = comp.create(selectCHOP, f'universe_{universe_id}_select')
        
        # Calculate channel range for this universe
        start_chan = universe_id * 512
        end_chan = min(start_chan + 511, 30239)
        
        # Set channel names
        select_chop.par.channames = f'{start_chan}-{end_chan}'
        select_chop.par.renameto = 'chan[0-511]'
        
        # Connect source to select
        source_chop.outputConnectors[0].connect(select_chop)
        
        # Create DMX Out for this specific universe
        dmx_out = comp.create(dmxoutCHOP, f'artnet_universe_{universe_id}')
        dmx_out.par.protocol = 'artnet'
        dmx_out.par.artnetsubnet = 0
        dmx_out.par.artnetuniverse = universe_id
        dmx_out.par.artnetbroadcast = True
        dmx_out.par.artnetip = '192.168.1.255'
        dmx_out.par.active = True
        
        # Connect select to DMX out
        select_chop.outputConnectors[0].connect(dmx_out)
        
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
    info_chop.par.rate = True
    info_chop.par.timeslice = False
    
    # Create text TOP for status display
    status_text = comp.create(textTOP, 'artnet_status')
    status_text.par.text = f'ArtNet Output: {len(dmx_outputs)} universes'
    status_text.par.fontsize = 20
    
    return info_chop, status_text

def apply_pixel_mapping_420x24(toptochop_node):
    """
    Configure pixel mapping for 420x24 LED matrix layout
    """
    toptochop_node.par.resolutionw = 420
    toptochop_node.par.resolutionh = 24
    toptochop_node.par.dataformat = 'rgb'
    
    # Configure for sequential RGB channel output
    toptochop_node.par.interleave = 'pixel'  # R1G1B1R2G2B2...
    
    return toptochop_node

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

def full_automation_setup(comp, video_source_name):
    """
    Complete automation function to create entire ArtNet pipeline
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

# MCP Integration Commands
def execute_setup_command(video_source_name="resize_to_24"):
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
    dmx_nodes = [op for op in root.findChildren(type=dmxoutCHOP)]
    setup_network_configuration(dmx_nodes, new_ip)
    return f"Updated {len(dmx_nodes)} DMX outputs to IP: {new_ip}"

def toggle_artnet_output(enabled=True):
    """
    Enable/disable all ArtNet outputs
    """
    dmx_nodes = [op for op in root.findChildren(type=dmxoutCHOP)]
    for node in dmx_nodes:
        node.par.active = enabled
    return f"ArtNet output {'enabled' if enabled else 'disabled'} for {len(dmx_nodes)} universes"

# Validation functions
def check_artnet_status():
    """Check DMX output status"""
    dmx_nodes = [op for op in root.findChildren(type=dmxoutCHOP)]
    active_count = sum(1 for node in dmx_nodes if node.par.active.eval())
    return f"{active_count}/{len(dmx_nodes)} universes active"

def reset_artnet_pipeline():
    """Reset all ArtNet outputs"""
    dmx_nodes = [op for op in root.findChildren(type=dmxoutCHOP)]
    for node in dmx_nodes:
        node.par.active = False
        node.par.active = True
    return "ArtNet pipeline reset complete"