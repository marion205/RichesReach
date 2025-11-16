#!/usr/bin/env python3
"""Comprehensive indentation fix for types.py"""
import re

def fix_indentation(content):
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    current_class_indent = 0
    current_method_indent = 0
    
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Detect class definitions
        if re.match(r'^class \w+.*:', stripped):
            fixed_lines.append(line)
            current_class_indent = 4
            i += 1
            # Skip blank lines after class
            while i < len(lines) and lines[i].strip() == '':
                fixed_lines.append(lines[i])
                i += 1
            continue
        
        # Detect method definitions (def resolve_ or def get_)
        if re.match(r'^def (resolve_|get_|set_)', stripped):
            # Check if we're in a class context
            if current_class_indent > 0:
                # Should be indented at class level
                if not line.startswith('    '):
                    fixed_lines.append('    ' + stripped)
                else:
                    fixed_lines.append(line)
                current_method_indent = 8
            else:
                fixed_lines.append(line)
            i += 1
            # Fix method body
            while i < len(lines):
                next_line = lines[i]
                next_stripped = next_line.strip()
                
                # Stop at next class or method definition
                if (re.match(r'^(class |def )', next_stripped) and 
                    not next_line.startswith('        ')):
                    break
                
                # Stop at end of class (blank line followed by class)
                if (next_stripped == '' and i + 1 < len(lines) and
                    re.match(r'^class ', lines[i + 1].strip())):
                    break
                
                # Fix indentation of method body
                if next_stripped and not next_stripped.startswith('#'):
                    if not next_line.startswith('        '):
                        # Should be indented 8 spaces (method body)
                        fixed_lines.append('        ' + next_stripped)
                    else:
                        fixed_lines.append(next_line)
                else:
                    fixed_lines.append(next_line)
                i += 1
            continue
        
        # Detect class Meta: definitions
        if stripped == 'class Meta:':
            if current_class_indent > 0:
                # Should be indented 4 spaces (inside class)
                fixed_lines.append('    class Meta:')
                i += 1
                # Fix Meta body
                while i < len(lines):
                    meta_line = lines[i]
                    meta_stripped = meta_line.strip()
                    
                    # Stop at end of Meta class
                    if (meta_stripped and not meta_stripped.startswith('#') and
                        not meta_line.startswith('        ')):
                        break
                    
                    # Fix Meta class body (should be 8 spaces)
                    if meta_stripped and not meta_stripped.startswith('#'):
                        if not meta_line.startswith('        '):
                            fixed_lines.append('        ' + meta_stripped)
                        else:
                            fixed_lines.append(meta_line)
                    else:
                        fixed_lines.append(meta_line)
                    i += 1
                continue
        
        # Detect class attributes (graphene fields)
        if (current_class_indent > 0 and stripped and 
            not stripped.startswith('#') and
            not stripped.startswith('def ') and
            not stripped.startswith('class ')):
            # Check if it's a class attribute
            if ('= graphene.' in stripped or 
                '= graphene.Field' in stripped or
                '= graphene.List' in stripped):
                # Should be indented 4 spaces
                if not line.startswith('    '):
                    fixed_lines.append('    ' + stripped)
                else:
                    fixed_lines.append(line)
                i += 1
                continue
        
        # Default: keep line as is
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)

# Read file
with open('deployment_package/backend/core/types.py', 'r') as f:
    content = f.read()

# Apply fixes
fixed_content = fix_indentation(content)

# Additional pattern-based fixes
# Fix: class Meta: followed by blank then model/fields
fixed_content = re.sub(
    r'(    class Meta:\s*\n\s*\n)(\s+)(model = \w+)',
    r'\1        \3',
    fixed_content
)
fixed_content = re.sub(
    r'(    class Meta:\s*\n\s*\n\s+model = \w+\s*\n)(\s+)(fields = )',
    r'\1        \3',
    fixed_content
)

# Fix: resolver methods with unindented return statements
fixed_content = re.sub(
    r'(    def resolve_\w+\(self, info\):\s*\n\s*\n)(return )',
    r'\1        \2',
    fixed_content
)

# Fix: if/for/while statements in method bodies
fixed_content = re.sub(
    r'(        return [^\n]+\n)(if |for |while |try:|\s+return )',
    r'\1        \2',
    fixed_content
)

# Write fixed file
with open('deployment_package/backend/core/types.py', 'w') as f:
    f.write(fixed_content)

print("✅ Comprehensive indentation fix applied")

