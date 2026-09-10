#!/usr/bin/env python3
"""Fix sampleOutput YAML parse errors by converting quoted strings with newlines to block scalars."""
import re
import os

base = "/Users/maverick/.hermes/profiles/swe/workspace/msql-studio/m_sql_studio_problems/problems"

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Find sampleOutput: "..." patterns that span multiple lines
    # We need to convert:
    #   sampleOutput: "field1 | field2\n---|---\nval1 | val2"
    # to:
    #   sampleOutput: |
    #     field1 | field2
    #     |---|---|
    #     val1 | val2
    
    lines = content.split('\n')
    new_lines = []
    i = 0
    fixed = False
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line has a sampleOutput: "..." with unclosed quote
        if re.match(r'^sampleOutput:\s*"', line):
            # Extract the content after sampleOutput: "
            quote_start = line.index('"', line.index('sampleOutput:') + len('sampleOutput:'))
            rest = line[quote_start+1:]
            
            # Check if the quote closes on the same line
            if rest.endswith('"') and not rest.endswith('\\"'):
                # Single line quoted string - leave as is (should be fine)
                new_lines.append(line)
                i += 1
                continue
            
            # Multi-line quoted string - convert to block scalar
            # Collect all lines until we find the closing quote
            quote_content_lines = [rest]
            j = i + 1
            found_close = False
            
            while j < len(lines):
                next_line = lines[j]
                if next_line.endswith('"') and not next_line.endswith('\\"'):
                    quote_content_lines.append(next_line[:-1])  # Remove closing quote
                    found_close = True
                    j += 1
                    break
                else:
                    quote_content_lines.append(next_line)
                    j += 1
            
            if found_close:
                # Convert to block scalar
                new_lines.append('sampleOutput: |')
                for ql in quote_content_lines:
                    new_lines.append('  ' + ql)
                fixed = True
                i = j
                continue
            else:
                # Couldn't find close - just append original
                new_lines.append(line)
                i += 1
                continue
        else:
            new_lines.append(line)
            i += 1
    
    if fixed:
        with open(filepath, 'w') as f:
            f.write('\n'.join(new_lines))
        return True
    return False

# Find all problem YAML files
fixed_count = 0
for root, dirs, files in os.walk(base):
    for fname in files:
        if fname.endswith('.yaml'):
            fpath = os.path.join(root, fname)
            if fix_file(fpath):
                print(f"Fixed: {fpath}")
                fixed_count += 1

print(f"\nTotal files fixed: {fixed_count}")
