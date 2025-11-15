#!/usr/bin/env python3
"""
Comprehensive script to fix ALL indentation errors in queries.py
"""
import re

with open('core/queries.py', 'r') as f:
    lines = f.readlines()

fixed = []
i = 0

while i < len(lines):
    line = lines[i]
    indent = len(line) - len(line.lstrip())
    
    # Check for control structures
    control_match = re.match(r'^(\s+)(if|try|except|for|while|with|elif|else|def|class)\s+.*:\s*$', line)
    
    if control_match:
        fixed.append(line)
        i += 1
        
        # Skip blank lines
        while i < len(lines) and lines[i].strip() == '':
            fixed.append(lines[i])
            i += 1
        
        # Check if next line needs indentation
        if i < len(lines):
            next_line = lines[i]
            next_indent = len(next_line) - len(next_line.lstrip())
            
            # If next line is at same or less indent and not a comment/blank, we need a body
            if (next_line.strip() and 
                not next_line.strip().startswith('#') and
                next_indent <= indent):
                
                # Check if it's another control structure at same level
                next_control = re.match(r'^\s+(elif|else|except|def|class)\s+.*:\s*$', next_line)
                if next_control and next_indent == indent:
                    # This is fine, it's an elif/else/except at same level
                    continue
                else:
                    # Need to add a body
                    if 'if user.is_anonymous' in line:
                        fixed.append(' ' * (indent + 4) + 'return []\n')
                    elif 'except' in line:
                        fixed.append(' ' * (indent + 4) + 'return None\n')
                    elif 'try' in line:
                        # Don't add anything yet, wait for except
                        continue
                    elif 'def' in line or 'class' in line:
                        fixed.append(' ' * (indent + 4) + 'pass\n')
                    else:
                        fixed.append(' ' * (indent + 4) + 'pass\n')
                    continue
    
    # Fix duplicate control structures
    if i + 1 < len(lines):
        next_line = lines[i + 1]
        if (re.match(r'^\s+(if|try|except|for|while|with|elif|else)\s+.*:\s*$', line) and
            re.match(r'^\s+(if|try|except|for|while|with|elif|else)\s+.*:\s*$', next_line) and
            len(line) - len(line.lstrip()) == len(next_line) - len(next_line.lstrip())):
            # Skip duplicate
            fixed.append(line)
            i += 2
            continue
    
    # Fix lines that should be indented inside try/if blocks
    if i > 0:
        prev_line = lines[i - 1]
        prev_indent = len(prev_line) - len(prev_line.lstrip())
        
        # If previous line is a control structure and this line is at same indent, indent it
        if (re.match(r'^\s+(if|try|for|while|with|elif|else)\s+.*:\s*$', prev_line) and
            next_indent == prev_indent and
            line.strip() and
            not line.strip().startswith('#') and
            not re.match(r'^\s+(elif|else|except|def|class)\s+.*:\s*$', line)):
            # Indent this line
            fixed.append(' ' * (prev_indent + 4) + line.lstrip())
            i += 1
            continue
    
    fixed.append(line)
    i += 1

# Remove duplicate except/elif statements
final = []
i = 0
while i < len(fixed):
    line = fixed[i]
    
    # Check for duplicate consecutive control structures
    if i + 1 < len(fixed):
        next_line = fixed[i + 1]
        if (re.match(r'^\s+(except|elif)\s+.*:\s*$', line) and 
            re.match(r'^\s+(except|elif)\s+.*:\s*$', next_line) and
            len(line) - len(line.lstrip()) == len(next_line) - len(next_line.lstrip())):
            # Skip duplicate
            final.append(line)
            i += 2
            continue
    
    final.append(line)
    i += 1

with open('core/queries.py', 'w') as f:
    f.writelines(final)

print("✅ Fixed indentation issues")

