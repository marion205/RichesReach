#!/usr/bin/env python3
"""
Fix all remaining indentation errors by fixing excessive indentation patterns.
"""
import sys
import re

file_path = sys.argv[1] if len(sys.argv) > 1 else "backend/backend/final_complete_server.py"

with open(file_path, 'r') as f:
    lines = f.readlines()

fixed = 0
for i, line in enumerate(lines):
    if not line.strip() or line.strip().startswith('#'):
        continue
    
    spaces = len(line) - len(line.lstrip(' '))
    content = line.lstrip()
    
    # Fix lines with excessive indentation (>28 spaces) - reduce to proper level
    if spaces > 28:
        # Try to determine proper indent based on content
        if content.startswith('if ') or content.startswith('try:') or content.startswith('except'):
            new_indent = 16  # Inside handler try block
        elif content.startswith('return ') or content.startswith('raise '):
            new_indent = 16  # Inside handler
        elif '=' in content and not content.strip().startswith('#'):
            new_indent = 16  # Assignment
        else:
            new_indent = 12  # Default inside handler
        
        lines[i] = ' ' * new_indent + content + ('' if line.endswith('\n') else '\n')
        fixed += 1
        continue
    
    # Fix lines that appear to be at wrong level (between 20-28 spaces)
    # These might need to be at handler level (12-16 spaces)
    if 20 <= spaces <= 28:
        # Check if it's a statement that should be at handler level
        if (content.startswith('if ') or content.startswith('return ') or 
            content.startswith('raise ') or '=' in content[:20]):
            # Check previous line to determine proper indent
            if i > 0:
                prev_line = lines[i-1]
                prev_spaces = len(prev_line) - len(prev_line.lstrip(' '))
                # If previous line is at 12-16, use that level
                if 12 <= prev_spaces <= 16:
                    lines[i] = ' ' * prev_spaces + content + ('' if line.endswith('\n') else '\n')
                    fixed += 1

if fixed > 0:
    with open(file_path, 'w') as f:
        f.writelines(lines)
    print(f"Fixed {fixed} lines with excessive/wrong indentation")
else:
    print("No excessive indentation found")

