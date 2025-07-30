# CLAUDE.md - TouchDesigner Python Guide

## Core Concepts Learned

### The TouchDesigner Python Console (Textport)
- **Open with**: `Alt+Shift+T`
- **Essential for debugging** - much better than guessing UI locations
- **Always start here** for testing before writing DAT scripts
- **Persistent functions** - define once, use throughout session

### Key TouchDesigner Python Patterns

#### Finding Operators
```python
# Our custom search function - much better than op()
def nop(name):
    """Find operator by name anywhere in the project"""
    results = root.findChildren(name=f'*{name}*')
    if len(results) == 1:
        return results[0]
    elif len(results) == 0:
        print(f"No operators found with '{name}' in the name")
        return None
    else:
        print(f"Multiple operators found with '{name}':")
        for i, op in enumerate(results):
            print(f"  {i}: {op.path}")
        return results

# Usage
audio_chop = nop('audioAnalysis')  # Much better than guessing paths
```

#### Cleanup & Project Management
```python
def rm(pattern):
    """Delete operators matching regex pattern"""
    import re
    matches = [op for op in op('/project1').children if re.search(pattern, op.name, re.IGNORECASE)]
    for op_obj in matches:
        op_obj.destroy()
    print(f"Deleted {len(matches)} operators")

# Usage
rm("lag|math")  # Clean up test operators
```

#### Project Exploration
```python
def explore_tree(comp, depth=0):
    """Show detailed tree structure with CHOP values"""
    indent = "  " * depth
    print(f"{indent}{comp.name} ({comp.type})")
    if comp.family == 'CHOP' and comp.numChans > 0:
        for i in range(comp.numChans):
            chan = comp.chan(i)
            print(f"{indent}  📊 {chan.name}: {chan.eval()}")
    if hasattr(comp, 'children'):
        for child in comp.children:
            explore_tree(child, depth + 1)

# Usage - essential for understanding complex audio analysis setups
explore_tree(op('/project1/audioAnalysis'))
```

### TouchDesigner Python API Gotchas

#### CHOP Channel Access
```python
# ❌ WRONG - causes 'not subscriptable' errors
op('audioAnalysis')['low']

# ✅ CORRECT - full path to specific output CHOP
op('/project1/audioAnalysis/out1')['low']

# Always verify the actual CHOP structure first!
```

#### Operator Creation & Connection
```python
# Creating operators
lag = op('/project1').create(lagCHOP)  # Use type objects, not strings

# Connecting operators - use outputConnectors/inputConnectors
source.outputConnectors[0].connect(destination)
source.outputConnectors[0].connect(destination.inputConnectors[1])  # Specific input

# Setting parameters - check actual parameter names first!
def check_params(op_obj):
    for p in op_obj.pars():
        if 'target_word' in p.name.lower():
            print(f"  {p.name}")
```

#### Parameter Names Are Not Obvious
```python
# Common parameter name discoveries:
# Lag CHOP: .par.lag1, .par.lag2 (not .par.lag)
# Math CHOP: .par.chopop (not .par.combine)
# Always check first: [p.name for p in op.pars() if 'keyword' in p.name.lower()]
```

### Audio-Reactive Visual Patterns

#### Basic Audio → Visual Connection
```python
# Simple parameter driving
geometry.par.sx = 'op("/path/to/audio/out1")["low"]'
```

#### Complex Audio Processing Chain
```python
def create_audio_reactive_system():
    # Method 1: Additive (smooth movement + audio spikes)
    math_chop = op('/project1').create(mathCHOP)
    math_chop.par.chopop = 'add'
    noise_source.outputConnectors[0].connect(math_chop)
    audio_source.outputConnectors[0].connect(math_chop.inputConnectors[1])
    
    # Method 2: Multiplicative (modulate noise intensity)
    math_chop.par.chopop = 'mult'  # Audio modulates noise amplitude
    
    # Method 3: Selective channels
    select_chop = op('/project1').create(selectCHOP)
    select_chop.par.channames = 'low'  # or 'rythm', 'kick', etc.
```

#### A/B Testing Audio Systems
```python
# Quick switching for comparison
chopto.par.chop = '/project1/noise1'        # Raw noise
chopto.par.chop = '/project1/math1'         # Audio-reactive

# Or bypass toggle
math_chop.bypass = True   # Bypass the processing
math_chop.bypass = False  # Enable processing
```

### Development Workflow

#### Iterative Development Pattern
```python
# Clean slate approach for quick iteration
def act():
    # ... your experimental code here ...

# Usage
rm("test_operators") ; act()  # Clean + rebuild in one line
```

#### Parameter Discovery Workflow
1. Create operator in textport: `test_op = op('/project1').create(operatorType)`
2. Discover parameters: `[p.name for p in test_op.pars() if 'keyword' in p.name.lower()]`
3. Test connections: `source.outputConnectors[0].connect(test_op)`
4. Clean up: `test_op.destroy()`

### Common Mistakes & Solutions

#### Path Problems
- **Problem**: `AttributeError: 'NoneType'` - operator not found
- **Solution**: Use `nop()` function or `root.findChildren()` to locate actual paths
- **Always verify**: Audio analysis containers often have nested structures

#### Parameter Errors
- **Problem**: `AttributeError: 'ParCollection' object has no attribute 'parameter_name'`
- **Solution**: Check real parameter names first, don't assume
- **Tool**: Use parameter discovery functions

#### Connection Errors
- **Problem**: `IndexError: list assignment index out of range`
- **Solution**: Use `.connect()` method, not direct assignment to inputs
- **Pattern**: `source.outputConnectors[0].connect(destination.inputConnectors[N])`

#### Operator Explosion
- **Problem**: Multiple operators created when testing
- **Solution**: Always include cleanup in development functions
- **Pattern**: `rm("pattern") ; create_function()`

### Audio Analysis Deep Dive

From our exploration, typical audio analysis structure:
```
/project1/audioAnalysis/
├── out1 (CHOP) - Main output with all channels:
│   ├── low: bass frequencies
│   ├── mid: mid frequencies  
│   ├── high: high frequencies
│   ├── kick: kick drum detection
│   ├── snare: snare detection
│   ├── rythm: rhythm detection
│   └── ... other analysis channels
├── low/ (container) - Low frequency processing UI
├── mid/ (container) - Mid frequency processing UI
└── high/ (container) - High frequency processing UI
```

**Key insight**: The `out1` CHOP is usually what you want to reference, not the container itself.

### TouchDesigner + Python Philosophy

1. **Start with textport exploration** - don't guess, discover
2. **Build helper functions** - TouchDesigner's API is verbose
3. **Clean iteration cycles** - rm() + act() pattern for rapid development
4. **Parameter discovery first** - check real names before assuming
5. **Use Python for complex logic** - visual programming for data flow
6. **Use bypass, not disconnect** - Maintain connections, toggle processing

### MCP Integration Lessons Learned

#### Operator Type Names
```python
# ❌ WRONG - Python class names don't work in MCP
op('/project1').create(mathCHOP)  # NameError

# ✅ CORRECT - Use string type names for MCP
mcp__touchdesigner__create_td_node(nodeType='mathCHOP')
```

#### Common MCP Type Names
- `mathCHOP`, `selectCHOP`, `lagCHOP`, `noiseCHOP`, `levelCHOP`
- `noiseTOP`, `compositeTOP`, `levelTOP`, `choptoTOP`, `displaceTOP`
- `textDAT`, `executeDAT`

#### Parameter Setting Patterns
```python
# ❌ WRONG - Direct assignment for expressions
node.par.opacity = 'op("/project1/chopto")[0]'

# ✅ CORRECT - Use .expr for expression parameters
node.par.opacity.expr = 'op("/project1/chopto")[0]'

# ✅ For numeric values, direct assignment works
node.par.gain = 2.0
```

#### Audio Weak Signal Issues
```python
# Audio from microphone often needs massive amplification
# Create amplifier between audioAnalysis and processing:
amp = create_node('mathCHOP', 'audio_amp')
amp.par.chopop = 'mult'
amp.par.gain = 100  # 100x amplification often needed!
```

### Project Startup & Restoration

#### Essential Startup Script
```python
def setup_audio_reactive_jellybeans():
    """Restore audio-reactive jelly bean setup after restart"""
    
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
        audio_amp.par.chopop = 'mult'
        audio_amp.par.gain = 100
        # Connect: audioAnalysis → amp → audio_low
        audio_out.outputConnectors[0].connect(audio_amp)
    
    # 3. Verify connections
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
            src.outputConnectors[0].connect(dst.inputConnectors[idx])
    
    # 4. Set critical parameters
    math1 = op('/project1/math1')
    if math1:
        math1.par.chopop = 'mult'  # CRITICAL: Not 'off'!
        math1.par.gain = 5.0
    
    # 5. Configure displacement
    displace = op('/project1/displace1')
    if displace:
        displace.par.displaceweighty = 0.5
    
    print("✅ Audio-reactive system restored!")
```

### Enhanced Utility Functions

```python
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

def check_cooking():
    """Force cook critical nodes"""
    critical_nodes = [
        'audioAnalysis', 'audio_amp', 'audio_low', 
        'audio_lag', 'math1', 'chopto1', 'displace1'
    ]
    
    for node_name in critical_nodes:
        node = op(f'/project1/{node_name}')
        if node:
            node.cook(force=True)
    print("✅ Force cooked all critical nodes")
```

### Common Error Prevention

1. **Always check if node exists before accessing properties**
   ```python
   if node and node.numChans > 0:  # Safe access
       value = node[0].eval()
   ```

2. **Use MCP node creation with string types**
   ```python
   mcp__touchdesigner__create_td_node(nodeType='mathCHOP', nodeName='my_math')
   ```

3. **Set expression parameters with .expr**
   ```python
   param.expr = 'expression_string'  # Not param = 'expression_string'
   ```

4. **Bypass nodes instead of disconnecting**
   ```python
   node.bypass = True  # Maintains connections, stops processing
   ```

5. **Audio needs amplification**
   - Microphone input is often very weak (0.001 - 0.01 range)
   - Use 50x-200x amplification for visible effects

### Next Steps & Advanced Patterns

- **Component creation with Python** - build entire networks programmatically
- **MCP integration** - live project state queries with proper type names
- **Claude Code integration** - iterative development with full context
- **Custom operator development** - extend TouchDesigner capabilities
- **Persistent utility DATs** - Store functions in project for reuse

### Resources for Deep Dive

- Official TouchDesigner Python documentation
- Connector Class documentation (for operator connections)
- OP Class documentation (for operator manipulation)
- CHOP Class documentation (for channel operations)
- [MCP TouchDesigner Server](https://github.com/touchdesigner/td-mcp-server)

---

*This guide represents lessons learned from hands-on TouchDesigner + Claude experimentation. The key insight: TouchDesigner's Python API is powerful but requires discovery-driven development rather than assumption-based coding. MCP integration requires understanding the differences between Python API and MCP command syntax.*