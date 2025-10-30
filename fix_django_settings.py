#!/usr/bin/env python3
"""
Fix All Malformed Environment Variables in Django Settings
This script fixes all malformed environment variable references in Django settings files.
"""

import re
from pathlib import Path

def fix_settings_file(file_path):
    """Fix malformed environment variables in a Django settings file"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Fix malformed patterns
        fixes = [
            # Fix os.getenv with malformed defaults
            (r'os\.getenv\(\'([A-Z_]+)\', \'process\.env\.([A-Z_]+) \|\| "([^"]+)"\'\)', 
             r'os.getenv(\'\1\', \'\3\')'),
            
            # Fix malformed URLs in lists
            (r'"process\.env\.([A-Z_]+) \|\| "([^"]+)""', 
             r'"\2"'),
            
            # Fix malformed URLs with colons
            (r'http://process\.env\.([A-Z_]+) \|\| "localhost":(\d+)', 
             r'http://localhost:\2'),
            
            # Fix redis URLs
            (r'redis://process\.env\.([A-Z_]+) \|\| "localhost":(\d+)/', 
             r'redis://localhost:\2/'),
            
            # Fix other malformed patterns
            (r'process\.env\.([A-Z_]+) \|\| "([^"]+)"/', 
             r'\2/'),
        ]
        
        changes_made = False
        for pattern, replacement in fixes:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made = True
        
        # Write back if changes were made
        if changes_made and content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return True
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False
    
    return False

def main():
    """Main function to fix all Django settings files"""
    print("🔧 Fixing All Malformed Environment Variables in Django Settings")
    print("=" * 60)
    
    settings_files = [
        "backend/backend/richesreach/settings.py",
        "backend/backend/richesreach/settings_local.py",
        "backend/backend/richesreach/settings_production.py",
        "backend/backend/richesreach/settings_production_clean.py",
        "backend/backend/richesreach/settings_local_db.py",
        "backend/backend/richesreach/settings_production_real.py",
        "backend/backend/richesreach/settings_local_prod.py",
        "backend/backend/richesreach/settings_dev.py",
        "backend/backend/richesreach/settings_aws.py",
        "backend/backend/richesreach/settings_secure_production.py",
        "backend/backend/richesreach/settings_dev_real.py",
    ]
    
    files_changed = 0
    for settings_file in settings_files:
        file_path = Path(settings_file)
        if file_path.exists():
            if fix_settings_file(file_path):
                files_changed += 1
                print(f"✅ Fixed: {settings_file}")
        else:
            print(f"⚠️  File {settings_file} not found, skipping...")
    
    print(f"\n🎯 Fixed {files_changed} Django settings files!")
    print(f"\n🚀 All malformed environment variable references should now be fixed!")

if __name__ == "__main__":
    main()
