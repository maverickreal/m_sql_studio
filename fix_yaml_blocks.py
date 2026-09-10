#!/usr/bin/env python3
"""Fix YAML files with broken SQL blocks by writing proper block scalars."""
import re
import os

base = "/Users/maverick/.hermes/profiles/swe/workspace/msql-studio/m_sql_studio_problems/problems"

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Parse the YAML manually to find broken SQL blocks
    lines = content.split('\n')
    new_lines = []
    i = 0
    fixed = False
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line starts a block scalar (key: | or key: |-)
        m = re.match(r'^(\w+):\s*\|-?$', line)
        if m:
            key = m.group(1)
            new_lines.append(line)
            i += 1
            
            # Collect all subsequent lines that are part of this block
            block_lines = []
            while i < len(lines):
                next_line = lines[i]
                # Stop if we hit a new key at column 0
                if re.match(r'^[a-zA-Z_][\w]*:', next_line):
                    break
                block_lines.append(next_line)
                i += 1
            
            # Re-indent all block lines to have 2-space indent
            # Strip any existing leading whitespace, then add 2 spaces
            for bl in block_lines:
                stripped = bl.strip()
                new_lines.append('  ' + stripped if stripped else '')
            
            fixed = True
            continue
        
        new_lines.append(line)
        i += 1
    
    if fixed:
        with open(filepath, 'w') as f:
            f.write('\n'.join(new_lines))
        return True
    return False

fixed_count = 0
for root, dirs, files in os.walk(base):
    for fname in files:
        if fname.endswith('.yaml'):
            fpath = os.path.join(root, fname)
            if fix_file(fpath):
                print(f"Fixed: {fpath}")
                fixed_count += 1

print(f"\nTotal files fixed: {fixed_count}")
