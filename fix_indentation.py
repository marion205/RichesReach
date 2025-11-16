#!/usr/bin/env python3
"""Fix indentation issues in types.py"""
import re

with open('deployment_package/backend/core/types.py', 'r') as f:
    lines = f.readlines()

fixed_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Fix class definitions - ensure docstrings and attributes are indented
    if re.match(r'^class \w+.*:', line):
        fixed_lines.append(line)
        i += 1
        # Skip blank lines
        while i < len(lines) and lines[i].strip() == '':
            fixed_lines.append(lines[i])
            i += 1
        # Fix docstring
        if i < len(lines) and lines[i].strip().startswith('"""'):
            fixed_lines.append('    ' + lines[i].lstrip())
            i += 1
        # Fix attributes - they should be indented
        while i < len(lines):
            next_line = lines[i]
            # Stop at next class or function definition at module level
            if (re.match(r'^(class |def )', next_line) and 
                not next_line.startswith('    ')):
                break
            # If it's an attribute or method, ensure proper indentation
            if next_line.strip() and not next_line.startswith('    '):
                if not re.match(r'^(class |def |#)', next_line):
                    fixed_lines.append('    ' + next_line.lstrip())
                else:
                    fixed_lines.append(next_line)
            else:
                fixed_lines.append(next_line)
            i += 1
    else:
        fixed_lines.append(line)
        i += 1

with open('deployment_package/backend/core/types.py', 'w') as f:
    f.writelines(fixed_lines)

print("✅ Fixed indentation in types.py")

