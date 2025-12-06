#!/usr/bin/env python3
"""
Manually fix shellScript array issue in Xcode project.pbxproj
This fixes the issue before xcodeproj gem tries to parse it
"""

import re
import sys

def fix_shellscript_arrays(content):
    """Convert shellScript arrays to strings"""
    
    # Pattern to match: shellScript = ( "line1", "line2", ... );
    # Replace with: shellScript = "line1\nline2\n...";
    
    pattern = r'shellScript\s*=\s*\(\s*((?:"[^"]*"(?:\s*,\s*"[^"]*")*)\s*)\);'
    
    def replace_func(match):
        array_content = match.group(1)
        # Extract all quoted strings
        strings = re.findall(r'"([^"]*)"', array_content)
        # Join with newlines
        joined = '\\n'.join(strings)
        return f'shellScript = "{joined}";'
    
    fixed = re.sub(pattern, replace_func, content)
    return fixed

if __name__ == '__main__':
    project_file = 'ios/RichesReach.xcodeproj/project.pbxproj'
    
    try:
        with open(project_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        fixed = fix_shellscript_arrays(content)
        
        if fixed != original:
            with open(project_file, 'w', encoding='utf-8') as f:
                f.write(fixed)
            print("✅ Fixed shellScript arrays in project.pbxproj")
            sys.exit(0)
        else:
            print("ℹ️  No shellScript arrays found (already correct or different format)")
            sys.exit(0)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)






