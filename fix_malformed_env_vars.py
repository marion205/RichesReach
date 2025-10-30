#!/usr/bin/env python3
"""
Fix Malformed Environment Variable References
This script fixes the malformed environment variable references created by the previous script.
"""

import os
import re
from pathlib import Path

def fix_malformed_env_vars(file_path):
    """Fix malformed environment variable references in a file"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Fix malformed patterns
        fixes = [
            # Fix double environment variable references
            (r'process\.env\.EXPO_PUBLIC_API_BASE_URL \|\| [\'"]http://process\.env\.API_BASE_URL \|\| "localhost:8000"[\'"]', 
             'process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:8000"'),
            
            (r'process\.env\.EXPO_PUBLIC_API_BASE_URL \|\| [\'"]http://process\.env\.API_BASE_URL \|\| "localhost:8000"[\'"]', 
             'process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:8000"'),
            
            (r'process\.env\.API_BASE_URL \|\| [\'"]localhost:8000[\'"]', 
             'process.env.API_BASE_URL || "localhost:8000"'),
            
            (r'process\.env\.MARKET_DATA_URL \|\| [\'"]localhost:8001[\'"]', 
             'process.env.MARKET_DATA_URL || "localhost:8001"'),
            
            (r'process\.env\.WHISPER_API_URL \|\| [\'"]localhost:3001[\'"]', 
             'process.env.WHISPER_API_URL || "localhost:3001"'),
            
            # Fix URLs with malformed environment variables
            (r'http://process\.env\.([A-Z_]+) \|\| "localhost:(\d+)"', 
             r'process.env.\1 || "http://localhost:\2"'),
            
            # Fix other malformed patterns
            (r'process\.env\.API_BASE_URL \|\| [\'"]http://localhost[\'"]', 
             'process.env.API_BASE_URL || "http://localhost"'),
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

def fix_malformed_env_vars_in_directory(directory):
    """Fix malformed environment variables in all files in a directory"""
    directory_path = Path(directory)
    if not directory_path.exists():
        return
    
    files_processed = 0
    files_changed = 0
    
    for file_path in directory_path.rglob('*'):
        if file_path.is_file() and file_path.suffix in ['.ts', '.tsx', '.js', '.jsx', '.py']:
            files_processed += 1
            if fix_malformed_env_vars(file_path):
                files_changed += 1
                print(f"✅ Fixed: {file_path}")
    
    print(f"📊 Processed {files_processed} files, changed {files_changed} files in {directory}")

def main():
    """Main function to fix malformed environment variables"""
    print("🔧 Fixing Malformed Environment Variable References")
    print("=" * 50)
    
    # Process mobile and backend directories
    directories_to_process = [
        "mobile/src",
        "backend/backend"
    ]
    
    for directory in directories_to_process:
        if Path(directory).exists():
            print(f"\n📁 Processing {directory}...")
            fix_malformed_env_vars_in_directory(directory)
        else:
            print(f"⚠️  Directory {directory} not found, skipping...")
    
    print(f"\n🎯 Malformed Environment Variables Fixed!")
    print(f"\n🚀 All environment variable references should now be properly formatted!")

if __name__ == "__main__":
    main()
