#!/usr/bin/env python3
"""
Fix ALL indentation errors where lines following : are not properly indented.
"""
import sys

file_path = sys.argv[1] if len(sys.argv) > 1 else "backend/backend/final_complete_server.py"

with open(file_path, 'r') as f:
    lines = f.readlines()

fixed = 0
i = 0
while i < len(lines) - 1:
    line = lines[i]
    
    # If line ends with :, the next non-empty line should be indented
    if line.rstrip().endswith(':') and not line.strip().startswith('#'):
        my_indent = len(line) - len(line.lstrip())
        
        # Find next non-empty line
        for j in range(i + 1, min(i + 10, len(lines))):
            next_line = lines[j]
            if not next_line.strip() or next_line.strip().startswith('#'):
                continue
            
            stripped = next_line.lstrip()
            curr_indent = len(next_line) - len(stripped)
            
            # If it starts with a statement keyword and isn't indented enough
            keywords = ['if ', 'for ', 'while ', 'elif ', 'else:', 'return ', 'raise ', 'try:', 'except', 'break', 'continue', 'pass']
            if any(stripped.startswith(kw) for kw in keywords):
                if curr_indent <= my_indent:
                    expected = my_indent + 4
                    lines[j] = ' ' * expected + stripped + ('' if next_line.endswith('\n') else '\n')
                    fixed += 1
                    # Also fix the block that follows
                    block_indent = expected
                    k = j + 1
                    while k < len(lines):
                        bline = lines[k]
                        if not bline.strip():
                            k += 1
                            continue
                        bline_indent = len(bline) - len(bline.lstrip())
                        # Stop if we hit same or less indent (sibling or outer)
                        if bline_indent <= my_indent:
                            break
                        # If line is part of this block but not indented enough
                        if bline_indent <= block_indent and not any(bline.lstrip().startswith(kw) for kw in ['elif ', 'else:', 'except', 'finally']):
                            if bline_indent < expected + 4:
                                lines[k] = ' ' * (expected + 4) + bline.lstrip()
                                fixed += 1
                        k += 1
                    break
            # Also check for variable assignments
            elif '=' in stripped and not stripped.startswith('=') and curr_indent <= my_indent:
                expected = my_indent + 4
                lines[j] = ' ' * expected + stripped + ('' if next_line.endswith('\n') else '\n')
                fixed += 1
                break
            else:
                break
    i += 1

if fixed > 0:
    with open(file_path, 'w') as f:
        f.writelines(lines)
    print(f"Fixed {fixed} indentation issues")
else:
    print("No indentation issues found")

