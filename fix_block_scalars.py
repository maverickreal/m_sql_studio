#!/usr/bin/env python3
"""Fix SQL block scalars that got their indentation stripped."""
import re
import os

base = "/Users/maverick/.hermes/profiles/swe/workspace/msql-studio/m_sql_studio_problems/problems"

def fix_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    i = 0
    fixed = False
    
    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip('\n')
        
        # Check if this line starts a block scalar (| or |-)
        # and the next line is at column 0 (should be indented)
        if re.match(r'^\w+:\s*\|-?$', stripped):
            new_lines.append(line)
            i += 1
            
            # Collect all subsequent lines that should be part of this block scalar
            block_lines = []
            while i < len(lines):
                next_line = lines[i].rstrip('\n')
                # If it's empty, indented, or starts with whitespace, it's part of the block
                if next_line == '' or next_line.startswith('  ') or next_line.startswith('\t'):
                    block_lines.append('  ' + next_line.lstrip() if not next_line.startswith('  ') else next_line)
                    i += 1
                else:
                    break
            
            if block_lines:
                new_lines.extend([bl + '\n' for bl in block_lines])
                fixed = True
            continue
        
        new_lines.append(line)
        i += 1
    
    if fixed:
        with open(filepath, 'w') as f:
            f.writelines(new_lines)
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
