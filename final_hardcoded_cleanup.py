#!/usr/bin/env python3
"""
Final Hardcoded Values Cleanup Script
This script identifies and fixes only problematic hardcoded values while preserving
legitimate fallback values and development configurations.
"""

import os
import re
from pathlib import Path

def is_legitimate_hardcoded(line, file_path):
    """
    Determine if a hardcoded value is legitimate and should be preserved.
    Returns True if the hardcoded value should be kept.
    """
    line_lower = line.lower()
    file_str = str(file_path)
    
    # Skip test files and temporary scripts
    if any(skip in file_str for skip in ['test', 'temp', 'debug', 'mock', 'example', 'template']):
        return True
    
    # Skip documentation files
    if file_path.suffix in ['.md', '.txt', '.json', '.yml', '.yaml']:
        return True
    
    # Skip configuration files that legitimately contain localhost
    if any(config in file_str for config in ['settings_local', 'docker-compose', 'nginx', 'prometheus']):
        return True
    
    # Skip files that are meant to contain hardcoded values
    if any(skip in file_str for skip in ['env.localhost', 'env.local', 'localhost']):
        return True
    
    # Skip legitimate fallback values in environment variable defaults
    if 'os.getenv(' in line and 'localhost' in line:
        return True
    
    # Skip legitimate fallback values in process.env
    if 'process.env.' in line and '||' in line and 'localhost' in line:
        return True
    
    # Skip print statements and comments
    if line.strip().startswith('#') or line.strip().startswith('//') or 'print(' in line:
        return True
    
    # Skip legitimate development URLs in CORS settings
    if 'CORS_ALLOWED_ORIGINS' in line or 'CSRF_TRUSTED_ORIGINS' in line:
        return True
    
    return False

def fix_problematic_hardcoded_values(file_path):
    """Fix only problematic hardcoded values in a file"""
    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        lines = content.split('\n')
        changes_made = False
        
        for i, line in enumerate(lines):
            # Check if line contains hardcoded values
            if re.search(r'192\.168\.1\.236|127\.0\.0\.1|localhost|54\.160\.139\.56', line):
                # Skip if this is a legitimate hardcoded value
                if is_legitimate_hardcoded(line, file_path):
                    continue
                
                # Fix problematic patterns
                original_line = line
                
                # Fix malformed environment variable references
                if 'process.env.API_BASE_URL || "http://localhost:8000"' in line:
                    line = line.replace('process.env.API_BASE_URL || "http://localhost:8000"', 'process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:8000"')
                
                if 'process.env.API_HOST || "localhost"' in line:
                    line = line.replace('process.env.API_HOST || "localhost"', 'process.env.EXPO_PUBLIC_API_HOST || "localhost"')
                
                if 'process.env.WHISPER_API_URL || "http://localhost:3001"' in line:
                    line = line.replace('process.env.WHISPER_API_URL || "http://localhost:3001"', 'process.env.EXPO_PUBLIC_WHISPER_API_URL || "http://localhost:3001"')
                
                # Fix hardcoded IP addresses that should use environment variables
                if '192.168.1.236' in line and 'process.env' not in line:
                    line = line.replace('192.168.1.236', 'process.env.EXPO_PUBLIC_API_HOST || "192.168.1.236"')
                
                if '127.0.0.1' in line and 'process.env' not in line and not is_legitimate_hardcoded(line, file_path):
                    line = line.replace('127.0.0.1', 'process.env.API_HOST || "127.0.0.1"')
                
                if line != original_line:
                    lines[i] = line
                    changes_made = True
        
        # Write back if changes were made
        if changes_made:
            new_content = '\n'.join(lines)
            file_path.write_text(new_content, encoding='utf-8')
            return True
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False
    
    return False

def scan_and_fix_hardcoded_values():
    """Scan and fix problematic hardcoded values"""
    print("🔍 Final Hardcoded Values Cleanup Scan")
    print("=" * 50)
    
    # Directories to scan
    directories = [
        "mobile/src",
        "backend/backend"
    ]
    
    total_files_scanned = 0
    files_changed = 0
    
    for directory in directories:
        directory_path = Path(directory)
        if not directory_path.exists():
            print(f"⚠️  Directory {directory} not found, skipping...")
            continue
        
        print(f"\n📁 Scanning {directory}...")
        
        for file_path in directory_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in ['.ts', '.tsx', '.js', '.jsx', '.py']:
                total_files_scanned += 1
                
                # Check if file contains hardcoded values
                try:
                    content = file_path.read_text(encoding='utf-8')
                    if re.search(r'192\.168\.1\.236|127\.0\.0\.1|localhost|54\.160\.139\.56', content):
                        if fix_problematic_hardcoded_values(file_path):
                            files_changed += 1
                            print(f"✅ Fixed: {file_path}")
                except Exception as e:
                    print(f"⚠️  Error scanning {file_path}: {e}")
    
    print(f"\n📊 Scan Complete!")
    print(f"   Files scanned: {total_files_scanned}")
    print(f"   Files changed: {files_changed}")
    
    return files_changed

def verify_no_problematic_hardcoded_values():
    """Verify that no problematic hardcoded values remain"""
    print(f"\n🔍 Verifying no problematic hardcoded values remain...")
    
    problematic_patterns = [
        r'192\.168\.1\.236(?!.*process\.env)',
        r'127\.0\.0\.1(?!.*process\.env)',
        r'localhost(?!.*process\.env)(?!.*os\.getenv)(?!.*print)(?!.*#)(?!.*//)',
        r'54\.160\.139\.56(?!.*process\.env)'
    ]
    
    directories = ["mobile/src", "backend/backend"]
    problematic_files = []
    
    for directory in directories:
        directory_path = Path(directory)
        if not directory_path.exists():
            continue
        
        for file_path in directory_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in ['.ts', '.tsx', '.js', '.jsx', '.py']:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    for pattern in problematic_patterns:
                        if re.search(pattern, content):
                            # Check if this is a legitimate hardcoded value
                            lines = content.split('\n')
                            for line in lines:
                                if re.search(pattern, line) and not is_legitimate_hardcoded(line, file_path):
                                    problematic_files.append((file_path, line.strip()))
                                    break
                except Exception:
                    continue
    
    if problematic_files:
        print(f"⚠️  Found {len(problematic_files)} potentially problematic hardcoded values:")
        for file_path, line in problematic_files[:10]:  # Show first 10
            print(f"   {file_path}: {line}")
        if len(problematic_files) > 10:
            print(f"   ... and {len(problematic_files) - 10} more")
        return False
    else:
        print(f"✅ No problematic hardcoded values found!")
        return True

def main():
    """Main function"""
    print("🚀 Final Hardcoded Values Cleanup")
    print("=" * 60)
    
    # Scan and fix problematic hardcoded values
    files_changed = scan_and_fix_hardcoded_values()
    
    # Verify no problematic values remain
    is_clean = verify_no_problematic_hardcoded_values()
    
    print(f"\n🎯 Cleanup Complete!")
    if is_clean:
        print(f"✅ All problematic hardcoded values have been removed!")
        print(f"✅ Legitimate fallback values and development configs preserved!")
    else:
        print(f"⚠️  Some potentially problematic values may remain.")
        print(f"   Review the output above for any issues.")
    
    print(f"\n📋 Summary:")
    print(f"   Files changed: {files_changed}")
    print(f"   Status: {'CLEAN' if is_clean else 'NEEDS REVIEW'}")

if __name__ == "__main__":
    main()
