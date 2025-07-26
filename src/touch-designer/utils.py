# === Core Helpers ===

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

def rm(pattern):
    """Delete operators matching pattern"""
    import re
    matches = [op for op in op('/project1').children if re.search(pattern, op.name, re.IGNORECASE)]
    for op_obj in matches:
        op_obj.destroy()
    print(f"Deleted {len(matches)} operators")

def explore_tree(comp, depth=0):
    """Show detailed tree structure with CHOP values"""
    indent = "  " * depth
    print(f"{indent}{comp.name} ({comp.type})")
    if comp.family == 'CHOP' and comp.numChans > 0:
        for i in range(comp.numChans):