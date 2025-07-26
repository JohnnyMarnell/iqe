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

### Next Steps & Advanced Patterns

- **Component creation with Python** - build entire networks programmatically
- **MCP integration** - live project state queries
- **Claude Code integration** - iterative development with full context
- **Custom operator development** - extend TouchDesigner capabilities

### Resources for Deep Dive

- Official TouchDesigner Python documentation
- Connector Class documentation (for operator connections)
- OP Class documentation (for operator manipulation)
- CHOP Class documentation (for channel operations)

---

*This guide represents lessons learned from hands-on TouchDesigner + Claude experimentation. The key insight: TouchDesigner's Python API is powerful but requires discovery-driven development rather than assumption-based coding.*