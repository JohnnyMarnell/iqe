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
            chan = comp.chan(i)
            print(f"{indent}  📊 {chan.name}: {chan.eval()}")
    if hasattr(comp, 'children'):
        for child in comp.children:
            explore_tree(child, depth + 1)

def check_warnings(*node_paths):
    """
    Check nodes for warnings and errors.
    
    Usage:
        check_warnings()  # Check all nodes in /project1
        check_warnings('render1', 'resize_to_24')  # Check specific nodes
        check_warnings('/project1/render1', '/project1/out')  # Full paths
    
    Returns:
        dict: Dictionary with 'errors' and 'warnings' lists
    """
    results = {'errors': [], 'warnings': []}
    
    # If no paths provided, check all nodes in project1
    if not node_paths:
        nodes_to_check = op('/project1').children
    else:
        nodes_to_check = []
        for path in node_paths:
            # Handle both relative names and full paths
            if '/' in path:
                node = op(path)
            else:
                node = op(f'/project1/{path}')
            if node:
                nodes_to_check.append(node)
            else:
                print(f"⚠️  Node not found: {path}")
    
    # Check each node
    for node in nodes_to_check:
        errors = node.errors()
        warnings = node.warnings()
        
        if errors:
            print(f"❌ ERROR in {node.path}: {errors}")
            results['errors'].append({'node': node.path, 'message': errors})
            
        if warnings:
            print(f"⚠️  WARNING in {node.path}: {warnings}")
            results['warnings'].append({'node': node.path, 'message': warnings})
    
    # Summary
    if not results['errors'] and not results['warnings']:
        print("✅ No warnings or errors found!")
    else:
        print(f"\nSummary: {len(results['errors'])} errors, {len(results['warnings'])} warnings")
    
    return results