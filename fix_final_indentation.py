#!/usr/bin/env python3
"""Final comprehensive fix for all indentation issues"""
import re

with open('deployment_package/backend/core/types.py', 'r') as f:
    content = f.read()

# Fix: Extra indented return statements after if statements
content = re.sub(
    r'(\s+if [^\n]+:\s*\n\s+return [^\n]+\n)\s{12,16}(return )',
    r'\1        \2',
    content,
    flags=re.MULTILINE
)

# Fix: Methods with blank lines and then return
content = re.sub(
    r'(    def resolve_\w+\(self, info\):\s*\n\s*\n\s+)(return )',
    r'\1        \2',
    content
)

# Fix: Methods with blank lines and then if/for/while
content = re.sub(
    r'(    def resolve_\w+\(self, info\):\s*\n\s*\n\s+)(if |for |while |try:)',
    r'\1        \2',
    content
)

# Fix: Unindented return statements in method bodies
content = re.sub(
    r'(\n        if [^\n]+:\s*\n)(\s+return [^\n]+\s*\n)(\s{12,16}return )',
    r'\1        \2        \3',
    content
)

# Fix: Methods that should have proper indentation
lines = content.split('\n')
fixed_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    
    # Fix pattern: if statement followed by over-indented return
    if (i > 0 and 
        re.match(r'\s+if .+:', lines[i-1]) and
        re.match(r'\s{12,16}return ', line)):
        # Fix to proper indentation (8 spaces for method body)
        fixed_lines.append('        ' + line.lstrip())
        i += 1
        continue
    
    # Fix pattern: method definition with blank lines then return
    if (i > 0 and
        re.match(r'    def resolve_\w+\(self, info\):', lines[i-1]) and
        line.strip() == '' and
        i + 1 < len(lines) and
        re.match(r'\s+return ', lines[i+1])):
        fixed_lines.append(line)
        i += 1
        # Fix the return statement
        if i < len(lines):
            fixed_lines.append('        ' + lines[i].lstrip())
            i += 1
        continue
    
    fixed_lines.append(line)
    i += 1

content = '\n'.join(fixed_lines)

# Write fixed content
with open('deployment_package/backend/core/types.py', 'w') as f:
    f.write(content)

print("✅ Final indentation fixes applied")

