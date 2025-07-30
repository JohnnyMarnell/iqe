"""
TouchDesigner Audio-Reactive Jelly Beans System
Created through Claude + TouchDesigner MCP integration

This file contains all the Python code developed for the audio-reactive
jelly bean displacement and static overlay effects.

Usage in TouchDesigner:
    exec(open('/Users/jmarnell/src/iqe/src/touch-designer/audio_reactive_jellybeans.py').read())
"""

import time

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def nop(name):
    """Find operator by name anywhere in the project"""
    results = op('/').findChildren(name=f'*{name}*')
    if len(results) == 1:
        return results[0]
    elif len(results) == 0:
        print(f"No operators found with '{name}' in the name")
        return None
    else:
        print(f"Multiple operators found with '{name}':")
        for i, op_obj in enumerate(results):
            print(f"  {i}: {op_obj.path}")
        return results

def rm(pattern):
    """Delete operators matching regex pattern"""
    import re
    matches = [op_obj for op_obj in op('/project1').children if re.search(pattern, op_obj.name, re.IGNORECASE)]
    for op_obj in matches:
        op_obj.destroy()
    print(f"Deleted {len(matches)} operators")

def explore_tree(comp, depth=0, max_depth=3):
    """Show detailed tree structure with CHOP values"""
    if depth > max_depth:
        return
    indent = "  " * depth
    print(f"{indent}{comp.name} ({comp.type})")
    if comp.family == 'CHOP' and comp.numChans > 0:
        for i in range(min(3, comp.numChans)):
            chan = comp.chan(i)
            print(f"{indent}  📊 {chan.name}: {chan.eval():.4f}")
    if hasattr(comp, 'children'):
        for child in comp.children:
            explore_tree(child, depth + 1, max_depth)

def check_params(op_obj, filter_text=''):
    """Check parameter names for an operator"""
    print(f"Parameters for {op_obj.path}:")
    for p in op_obj.pars():
        if filter_text.lower() in p.name.lower():
            print(f"  {p.name} = {p.eval()}")

def count_nodes(comp=None):
    """Count all nodes starting from comp (default: root)"""
    if comp is None:
        comp = op('/')
    count = 1
    if hasattr(comp, 'children'):
        for child in comp.children:
            count += count_nodes(child)
    return count

# ============================================================================
# AUDIO SIGNAL TRACING
# ============================================================================

def trace_audio_signal():
    """Debug audio signal through the chain"""
    chain = [
        ('audiodevin1', 0, 'Input'),
        ('audioAnalysis/out1', 'low', 'Analysis'),
        ('audio_amp', 0, 'Amplified'),
        ('audio_low', 0, 'Selected'),
        ('audio_lag', 0, 'Smoothed'),
        ('math1', 0, 'Output')
    ]
    
    print("📊 Audio Signal Trace:")
    for path, chan, label in chain:
        node = op(f'/project1/{path}')
        if node and node.numChans > 0:
            if isinstance(chan, str):
                val = next((node[i].eval() for i in range(node.numChans) 
                           if node[i].name == chan), 0)
            else:
                val = node[chan].eval()
            print(f"  {label:12} {val:8.3f}")

def monitor_displacement():
    """Monitor displacement values in real-time"""
    for _ in range(10):
        n = op('/project1/noise1')[0].eval() if op('/project1/noise1') else 0
        a = op('/project1/audio_lag')[0].eval() if op('/project1/audio_lag') else 0
        m = op('/project1/math1')[0].eval() if op('/project1/math1') else 0
        print(f"Noise: {n:.2f} | Audio: {a:.2f} | Output: {m:.2f}")
        time.sleep(0.5)

# ============================================================================
# EFFECT CONTROLS
# ============================================================================

def toggle_noise_modulation(enable=True):
    """Toggle between pure audio and noise-modulated displacement"""
    noise1 = op('/project1/noise1')
    chopto1 = op('/project1/chopto1')
    
    if noise1:
        noise1.bypass = not enable
        
    if chopto1:
        if enable:
            chopto1.par.chop = '/project1/math1'  # Noise × Audio
        else:
            chopto1.par.chop = '/project1/audio_lag'  # Pure audio
    
    print(f"✅ Noise modulation: {'ON' if enable else 'OFF'}")

def adjust_displacement_scale(scale=0.1):
    """Adjust displacement intensity"""
    displace1 = op('/project1/displace1')
    if displace1:
        displace1.par.displaceweighty = scale
        print(f"✅ Displacement scale set to {scale}")

def adjust_audio_sensitivity(gain=100):
    """Adjust audio amplification"""
    audio_amp = op('/project1/audio_amp')
    if audio_amp:
        audio_amp.par.gain = gain
        print(f"✅ Audio amplification set to {gain}x")

def adjust_static_intensity(opacity=0.5, brightness=0.5):
    """Adjust static overlay intensity"""
    static_level = op('/project1/static_level')
    if static_level:
        static_level.par.opacity = opacity
        static_level.par.brightness1 = brightness
        print(f"✅ Static: opacity={opacity}, brightness={brightness}")

# ============================================================================
# NODE LAYOUT FUNCTIONS
# ============================================================================

def reflow(parent_path='/project1', spacing=150, columns=6):
    """Arrange nodes in a grid layout"""
    parent = op(parent_path)
    if not parent:
        print(f"Parent {parent_path} not found")
        return
    
    nodes = [n for n in parent.children if n.expose]
    nodes.sort(key=lambda n: n.id)
    
    x_start = 100
    y_start = 500
    
    for i, node in enumerate(nodes):
        col = i % columns
        row = i // columns
        node.nodeX = x_start + (col * spacing)
        node.nodeY = y_start - (row * spacing)
    
    print(f"✅ Reflowed {len(nodes)} nodes in {columns} columns")

def reflow_audio_chain():
    """Layout the audio-reactive chain in a clear left-to-right flow"""
    layout = {
        # Audio input column
        'audiodevin1': (100, 400),
        'audioAnalysis': (100, 250),
        # Audio processing column
        'audio_amp': (300, 400),
        'audio_low': (300, 250),
        'audio_lag': (300, 100),
        # Modulation column
        'noise1': (500, 400),
        'math1': (500, 250),
        'time_driver': (500, 550),
        # Conversion column
        'chopto1': (700, 250),
        'chopto_static': (700, 100),
        # Visual source
        'moviefilein1': (100, 600),
        # Visual processing column
        'displace1': (900, 400),
        'static_noise': (900, 250),
        'static_level': (900, 100),
        # Final output column
        'audio_composite': (1100, 250),
        'out1': (1100, 100),
        # Utilities at bottom
        'claude_utils': (100, -100),
        'mcp_webserver_base': (300, -100),
    }
    
    for name, (x, y) in layout.items():
        node = op(f'/project1/{name}')
        if node:
            node.nodeX = x
            node.nodeY = y
    
    print("✅ Audio chain reflowed in logical columns")

def move_node(name, x, y):
    """Quickly position a specific node"""
    node = nop(name)
    if node:
        node.nodeX = x
        node.nodeY = y
        print(f"✅ Moved {name} to ({x}, {y})")

# ============================================================================
# SYSTEM SETUP & RESTORATION
# ============================================================================

def setup_audio_reactive_jellybeans():
    """Restore audio-reactive jelly bean setup after restart"""
    
    print("🔧 Setting up audio-reactive jelly bean system...\n")
    
    # 1. Ensure audio device is active
    audio_in = op('/project1/audiodevin1')
    if audio_in:
        audio_in.par.active = 1
        print(f"✅ Audio device: {audio_in.par.device}")
    
    # 2. Create/verify audio amplification
    audio_out = op('/project1/audioAnalysis/out1')
    audio_amp = op('/project1/audio_amp')
    if not audio_amp:
        audio_amp = op('/project1').create(mathCHOP, 'audio_amp')
    
    if audio_amp:
        audio_amp.par.chopop = 'mul'
        audio_amp.par.gain = 100
        # Connect: audioAnalysis → amp → audio_low
        if audio_out:
            audio_out.outputConnectors[0].connect(audio_amp)
    
    # 3. Create audio_lag if missing
    audio_lag = op('/project1/audio_lag')
    if not audio_lag:
        audio_lag = op('/project1').create(lagCHOP, 'audio_lag')
    
    if audio_lag:
        audio_lag.par.lag1 = 0.1
    
    # 4. Create time_driver (LFO) if missing
    time_driver = op('/project1/time_driver')
    if not time_driver:
        time_driver = op('/project1').create(lfoCHOP, 'time_driver')
    
    if time_driver:
        time_driver.par.wavetype = 'ramp'
        time_driver.par.frequency = 0.05
        time_driver.par.amp = 10
    
    # 5. Configure noise
    noise1 = op('/project1/noise1')
    if noise1 and time_driver:
        noise1.par.type = 'sparse'
        noise1.par.period = 1.0
        noise1.par.amp = 1.0
        noise1.bypass = False
        # Animate with LFO
        noise1.par.tx.expr = 'op("/project1/time_driver")[0] * 2'
    
    # 6. Verify connections
    nodes_to_connect = [
        ('audio_amp', 'audio_low'),
        ('audio_low', 'audio_lag'),
        ('noise1', 'math1', 0),
        ('audio_lag', 'math1', 1)
    ]
    
    for src_name, dst_name, *input_idx in nodes_to_connect:
        src = op(f'/project1/{src_name}')
        dst = op(f'/project1/{dst_name}')
        if src and dst:
            idx = input_idx[0] if input_idx else 0
            # Clear existing connection
            if idx < len(dst.inputConnectors):
                dst.inputConnectors[idx].disconnect()
            # Make new connection
            src.outputConnectors[0].connect(dst.inputConnectors[idx])
    
    # 7. Set critical parameters
    math1 = op('/project1/math1')
    if math1:
        math1.par.chopop = 'mul'  # CRITICAL: Not 'off'!
        math1.par.gain = 3.0
    
    chopto1 = op('/project1/chopto1')
    if chopto1:
        chopto1.par.chop = '/project1/math1'
    
    # 8. Configure displacement
    displace1 = op('/project1/displace1')
    if displace1:
        displace1.par.displaceweighty = 0.1
        displace1.par.vertsource = 'red'
    
    # 9. Configure static overlay
    static_level = op('/project1/static_level')
    chopto_static = op('/project1/chopto_static')
    
    if static_level and chopto_static:
        static_level.par.opacity.expr = 'op("/project1/chopto_static")[0]'
        static_level.par.brightness1 = 0.5
        chopto_static.par.chop = '/project1/audio_lag'
    
    # 10. Connect final composite
    audio_composite = op('/project1/audio_composite')
    if audio_composite and displace1 and static_level:
        # Clear connections
        for conn in audio_composite.inputConnectors:
            conn.disconnect()
        # Connect displaced video and static
        displace1.outputConnectors[0].connect(audio_composite.inputConnectors[0])
        static_level.outputConnectors[0].connect(audio_composite.inputConnectors[1])
        audio_composite.par.operand = 'over'
    
    # 11. Connect to output
    out1 = op('/project1/out1')
    if out1 and audio_composite:
        out1.inputConnectors[0].disconnect()
        audio_composite.outputConnectors[0].connect(out1)
    
    # 12. Force cook the chain
    for node_name in ['audioAnalysis', 'audio_amp', 'audio_low', 'audio_lag', 
                      'noise1', 'time_driver', 'math1', 'chopto1', 'displace1']:
        node = op(f'/project1/{node_name}')
        if node:
            node.cook(force=True)
    
    print("\n✅ Audio-reactive system restored!")
    reflow_audio_chain()
    trace_audio_signal()

# ============================================================================
# QUICK FIXES
# ============================================================================

def fix_math_multiply():
    """Quick fix when math1 gets set to 'off' again"""
    math1 = op('/project1/math1')
    if math1:
        math1.par.chopop = 'mul'
        math1.par.gain = 3.0
        print("✅ Fixed math1 multiply operation")

def fix_audio_connections():
    """Fix common audio connection issues"""
    # Ensure audio amp exists and is connected
    audio_out = op('/project1/audioAnalysis/out1')
    audio_amp = op('/project1/audio_amp')
    audio_low = op('/project1/audio_low')
    audio_lag = op('/project1/audio_lag')
    
    if audio_out and audio_amp and audio_low and audio_lag:
        # Clear and reconnect
        audio_amp.inputConnectors[0].disconnect()
        audio_low.inputConnectors[0].disconnect()
        audio_lag.inputConnectors[0].disconnect()
        
        audio_out.outputConnectors[0].connect(audio_amp)
        audio_amp.outputConnectors[0].connect(audio_low)
        audio_low.outputConnectors[0].connect(audio_lag)
        
        print("✅ Fixed audio chain connections")

# ============================================================================
# FINAL WORKING CONFIGURATION
# ============================================================================

def restore_final_config():
    """Restore the final working configuration that uses LFO-driven noise"""
    print("🔧 Restoring final working configuration...\n")
    
    # 1. LFO settings (drives the noise animation)
    lfo = op('/project1/time_driver')
    if lfo:
        lfo.par.wavetype = 'sin'      # Smooth sine wave
        lfo.par.frequency = 0.1        # Gentle speed
        lfo.par.amp = 10              # Good range
        lfo.bypass = False             # Make sure it's active
        print("✅ LFO configured")
    
    # 2. Noise settings (hermite for smooth movement)
    noise1 = op('/project1/noise1')
    if noise1:
        noise1.par.type = 'hermite'    # Smooth interpolated noise
        noise1.par.period = 1.0
        noise1.par.amp = 1.0
        noise1.par.rough = 0.25
        # LFO drives the transform
        noise1.par.tx.expr = 'op("/project1/time_driver")[0] * 2'
        print("✅ Noise configured with LFO animation")
    
    # 3. Math multiply settings
    math1 = op('/project1/math1')
    if math1:
        math1.par.chopop = 'mul'       # Multiply noise × audio
        math1.par.gain = 1.0
        print("✅ Math set to multiply")
    
    # 4. Displacement settings
    displace1 = op('/project1/displace1')
    if displace1:
        displace1.par.displaceweighty = 0.02  # Subtle displacement
        displace1.par.vertsource = 'red'
        print("✅ Displacement configured")
    
    # 5. Audio amplification
    audio_amp = op('/project1/audio_amp')
    if audio_amp:
        audio_amp.par.gain = 100       # 100x amplification
        print("✅ Audio amplification set")
    
    print("\n✅ Final configuration restored!")
    print("\nSignal flow:")
    print("  LFO → animates → noise1 × audio → displacement")
    print("  Creates smooth, continuous warping modulated by sound")

# ============================================================================
# QUICK ADJUSTMENT FUNCTION
# ============================================================================

def quick_adjust(speed=None, displacement=None, movement_range=None):
    """Quickly adjust the main parameters"""
    if speed is not None:
        lfo = op('/project1/time_driver')
        if lfo:
            lfo.par.frequency = speed
            print(f"✅ LFO speed: {speed} Hz")
    
    if displacement is not None:
        displace1 = op('/project1/displace1')
        if displace1:
            displace1.par.displaceweighty = displacement
            print(f"✅ Displacement: {displacement}")
    
    if movement_range is not None:
        noise1 = op('/project1/noise1')
        if noise1:
            noise1.par.tx.expr = f'op("/project1/time_driver")[0] * {movement_range}'
            print(f"✅ Movement range: ×{movement_range}")

# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__" or True:  # Always run in TouchDesigner
    # Load all functions into global namespace
    for name, obj in list(locals().items()):
        if callable(obj) and not name.startswith('_'):
            globals()[name] = obj
    
    print("✅ Audio-reactive jelly beans utilities loaded!")
    print("\nAvailable functions:")
    print("  Setup: setup_audio_reactive_jellybeans()")
    print("  Restore: restore_final_config()")
    print("  Layout: reflow_audio_chain(), reflow()")
    print("  Debug: trace_audio_signal(), monitor_displacement()")
    print("  Adjust: quick_adjust(speed, displacement, movement_range)")
    print("  Fix: fix_math_multiply(), fix_audio_connections()")
    print("\nRun restore_final_config() to restore the working setup")