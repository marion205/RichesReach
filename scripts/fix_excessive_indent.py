#!/usr/bin/env python3
"""
Fix lines with excessive indentation (>24 spaces) by reducing to proper level.
"""
import sys
import re

file_path = sys.argv[1] if len(sys.argv) > 1 else "backend/backend/final_complete_server.py"

with open(file_path, 'r') as f:
    lines = f.readlines()

fixed = 0
for i, line in enumerate(lines):
    if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('"""'):
        spaces = len(line) - len(line.lstrip(' '))
        # If more than 24 spaces, reduce to 16 (4 levels)
        if spaces > 24:
            content = line.lstrip()
            # Try to determine proper indentation based on context
            # Most handlers should be at 8 spaces (inside main try block)
            # Code inside handlers should be at 12-16 spaces
            if 'if ' in content[:10] or 'return ' in content[:10] or content.strip().startswith('#'):
                # Likely should be at 12 spaces (3 levels inside try -> handler -> if)
                new_line = '            ' + content
            else:
                # Default: reduce to 16 spaces
                new_line = '                ' + content
            lines[i] = new_line
            fixed += 1

if fixed > 0:
    with open(file_path, 'w') as f:
        f.writelines(lines)
    print(f"Fixed {fixed} lines with excessive indentation")
else:
    print("No excessive indentation found")

