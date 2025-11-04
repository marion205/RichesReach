#!/usr/bin/env python3
"""
Fix all handler indentation issues after return statements and ensure proper structure.
"""
import re
import sys

file_path = sys.argv[1] if len(sys.argv) > 1 else "backend/backend/final_complete_server.py"

with open(file_path, 'r') as f:
    lines = f.readlines()

# Pattern to find handlers that appear after return statements
pattern_after_return = re.compile(r'^\s+return.*\n\s+if\s+["\'].*["\']\s+in\s+fields\s*:')

fixed = 0
i = 0

# Fix handlers that appear immediately after return statements
while i < len(lines) - 1:
    line = lines[i]
    next_line = lines[i + 1] if i + 1 < len(lines) else ""
    
    # If this is a return and next line is an if handler, fix it
    if 'return' in line and not line.strip().startswith('#'):
        if i + 1 < len(lines) and re.match(r'^\s+if\s+["\'].*["\']\s+in\s+fields\s*:', next_line):
            # Add blank line and fix indentation
            indent = len(lines[i]) - len(lines[i].lstrip(' '))
            handler_indent = len(next_line) - len(next_line.lstrip(' '))
            
            # Handler should be at same level as previous handler (8 spaces from function start typically)
            # If it's too indented, reduce it
            if handler_indent > indent and handler_indent > 12:
                # Reduce to proper level
                target_indent = 8  # Standard handler indent inside try block
                content = next_line.lstrip()
                lines[i + 1] = ' ' * target_indent + content + '\n'
                fixed += 1
    
    # Fix lines with excessive indentation (>30 spaces)
    spaces = len(line) - len(line.lstrip(' '))
    if spaces > 30 and line.strip() and not line.strip().startswith('#'):
        # Determine proper indent based on context
        # Check previous non-empty line
        prev_indent = 8
        for j in range(i - 1, max(0, i - 10), -1):
            if lines[j].strip():
                prev_indent = len(lines[j]) - len(lines[j].lstrip(' '))
                break
        
        # Fix this line
        content = line.lstrip()
        # Use previous indent + 4, but cap at 20
        new_indent = min(prev_indent + 4, 20)
        lines[i] = ' ' * new_indent + content + ('' if line.endswith('\n') else '\n')
        fixed += 1
    
    i += 1

if fixed > 0:
    with open(file_path, 'w') as f:
        f.writelines(lines)
    print(f"Fixed {fixed} lines")
else:
    print("No issues found")

