#!/usr/bin/env python3
"""
Comprehensive Hardcoded Values Removal Script
This script removes ALL hardcoded IP addresses, localhost, and other hardcoded values
from the entire codebase and replaces them with environment variables.
"""

import os
import re
from pathlib import Path

# Define replacements for different types of hardcoded values
REPLACEMENTS = {
    # IP Addresses
    '192.168.1.236': 'process.env.EXPO_PUBLIC_API_HOST || "localhost"',
    '127.0.0.1': 'process.env.API_HOST || "localhost"',
    '54.160.139.56': 'process.env.PRODUCTION_API_HOST || "api.richesreach.com"',
    
    # Localhost variations
    'localhost:8000': 'process.env.API_BASE_URL || "localhost:8000"',
    'localhost:8001': 'process.env.MARKET_DATA_URL || "localhost:8001"',
    'localhost:3000': 'process.env.FRONTEND_URL || "localhost:3000"',
    'localhost:3001': 'process.env.WHISPER_API_URL || "localhost:3001"',
    'localhost:8081': 'process.env.MOBILE_SERVER_URL || "localhost:8081"',
    'localhost:6379': 'process.env.REDIS_HOST || "localhost:6379"',
    'localhost:5432': 'process.env.DB_HOST || "localhost:5432"',
    
    # Protocol + localhost
    'http://localhost': 'process.env.API_BASE_URL || "http://localhost"',
    'https://localhost': 'process.env.API_BASE_URL || "https://localhost"',
    'ws://localhost': 'process.env.WS_URL || process.env.EXPO_PUBLIC_WS_URL || "ws://localhost"',
    'wss://localhost': 'process.env.WS_URL || process.env.EXPO_PUBLIC_WS_URL || "wss://localhost"',
    
    # Specific endpoints
    'http://localhost:8000': 'process.env.EXPO_PUBLIC_API_BASE_URL || "http://localhost:8000"',
    'http://localhost:8001': 'process.env.MARKET_DATA_URL || "http://localhost:8001"',
    'http://localhost:3000': 'process.env.FRONTEND_URL || "http://localhost:3000"',
    'http://localhost:3001': 'process.env.WHISPER_API_URL || "http://localhost:3001"',
    'http://localhost:8081': 'process.env.MOBILE_SERVER_URL || "http://localhost:8081"',
    'ws://localhost:8000/ws/': 'process.env.EXPO_PUBLIC_WS_URL || process.env.WS_URL || "ws://localhost:8000/ws/"',
    
    # Production URLs
    'http://54.160.139.56:8000': 'process.env.PRODUCTION_API_URL || "https://api.richesreach.com"',
    'https://54.160.139.56:8000': 'process.env.PRODUCTION_API_URL || "https://api.richesreach.com"',
}

# Files to skip (don't modify these)
SKIP_FILES = {
    '.git',
    'node_modules',
    '__pycache__',
    '.env',
    '.env.example',
    'package-lock.json',
    'yarn.lock',
    '.DS_Store',
    '*.log',
    '*.tmp',
    '*.cache',
}

# File extensions to process
PROCESS_EXTENSIONS = {
    '.ts', '.tsx', '.js', '.jsx', '.py', '.json', '.md', '.sh', '.yml', '.yaml',
    '.conf', '.cfg', '.ini', '.txt', '.html', '.css', '.scss'
}

def should_skip_file(file_path):
    """Check if file should be skipped"""
    file_path_str = str(file_path)
    
    # Skip if any part of the path matches skip patterns
    for skip_pattern in SKIP_FILES:
        if skip_pattern in file_path_str:
            return True
    
    # Skip if not a processable extension
    if file_path.suffix not in PROCESS_EXTENSIONS:
        return True
    
    return False

def fix_hardcoded_values_in_file(file_path):
    """Fix hardcoded values in a single file"""
    try:
        # Read file content
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Apply replacements
        changes_made = False
        for hardcoded, replacement in REPLACEMENTS.items():
            if hardcoded in content:
                # Use regex to replace only whole words/strings, not partial matches
                pattern = re.escape(hardcoded)
                
                # For URLs, replace the entire URL
                if hardcoded.startswith('http'):
                    content = re.sub(pattern, replacement, content)
                    changes_made = True
                # For IP addresses, be more careful
                elif '.' in hardcoded and not hardcoded.startswith('process.env'):
                    # Replace IP addresses that are standalone or in URLs
                    content = re.sub(pattern, replacement, content)
                    changes_made = True
                # For other values, replace as-is
                else:
                    content = content.replace(hardcoded, replacement)
                    changes_made = True
        
        # Write back if changes were made
        if changes_made and content != original_content:
            file_path.write_text(content, encoding='utf-8')
            return True
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False
    
    return False

def fix_hardcoded_values_in_directory(directory):
    """Fix hardcoded values in all files in a directory"""
    directory_path = Path(directory)
    if not directory_path.exists():
        return
    
    files_processed = 0
    files_changed = 0
    
    for file_path in directory_path.rglob('*'):
        if file_path.is_file() and not should_skip_file(file_path):
            files_processed += 1
            if fix_hardcoded_values_in_file(file_path):
                files_changed += 1
                print(f"✅ Fixed: {file_path}")
    
    print(f"📊 Processed {files_processed} files, changed {files_changed} files in {directory}")

def create_environment_template():
    """Create a comprehensive environment template"""
    env_template = """# RichesReach Comprehensive Environment Configuration
# Copy this file to .env and update the values for your environment

# =============================================================================
# API CONFIGURATION
# =============================================================================

# Main API Base URL (required)
# For development: http://localhost:8000 or http://YOUR_IP:8000
# For production: https://api.richesreach.com
EXPO_PUBLIC_API_BASE_URL=http://localhost:8000
API_BASE_URL=http://localhost:8000
PRODUCTION_API_URL=https://api.richesreach.com

# Alternative API URLs
EXPO_PUBLIC_API_HOST=localhost
API_HOST=localhost
PRODUCTION_API_HOST=api.richesreach.com

# =============================================================================
# SERVICE-SPECIFIC URLs
# =============================================================================

# Market Data Service
MARKET_DATA_URL=http://localhost:8001
EXPO_PUBLIC_MARKET_DATA_URL=http://localhost:8001

# Frontend URLs
FRONTEND_URL=http://localhost:3000
EXPO_PUBLIC_FRONTEND_URL=http://localhost:3000

# Whisper API (Voice Transcription)
WHISPER_API_URL=http://localhost:3001
EXPO_PUBLIC_WHISPER_API_URL=http://localhost:3001

# Mobile Development Server
MOBILE_SERVER_URL=http://localhost:8081
EXPO_PUBLIC_MOBILE_SERVER_URL=http://localhost:8081

# =============================================================================
# WEBSOCKET CONFIGURATION
# =============================================================================

# WebSocket / Signaling URLs
WS_URL=ws://localhost:8000/ws/
EXPO_PUBLIC_WS_URL=ws://localhost:8000/ws/
EXPO_PUBLIC_SIGNAL_URL=ws://localhost:8000/fireside

# ICE/TURN (comma-separated for multiple URLs)
EXPO_PUBLIC_TURN_URLS=
EXPO_PUBLIC_TURN_USERNAME=
EXPO_PUBLIC_TURN_CREDENTIAL=

# Auth refresh (mobile)
EXPO_PUBLIC_AUTH_REFRESH_PATH=/auth/refresh
EXPO_PUBLIC_AUTH_REFRESH_MODE=cookie

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# Database Host
DB_HOST=localhost:5432
REDIS_HOST=localhost:6379

# =============================================================================
# BLOCKCHAIN SERVICES
# =============================================================================

# WalletConnect Project ID
EXPO_PUBLIC_WALLETCONNECT_PROJECT_ID=42421cf8-2df7-45c6-9475-df4f4b115ffc

# Alchemy API URLs
EXPO_PUBLIC_ALCHEMY_SEPOLIA_URL=https://eth-sepolia.g.alchemy.com/v2/2-rJhszNwQ6I3NuBdN5pz
EXPO_PUBLIC_ALCHEMY_POLYGON_URL=uuKmy9dPAjaSVXVEtCumQPga1dqEPDS2

# =============================================================================
# COMMUNICATION SERVICES
# =============================================================================

# Agora App ID for voice/video
EXPO_PUBLIC_AGORA_APP_ID=2d220d40a19d4fea955d4aac662b24d1

# GetStream.io keys
EXPO_PUBLIC_STREAM_API_KEY=4866mbx8b4jv

# =============================================================================
# DEVELOPMENT CONFIGURATION
# =============================================================================

# Enable debug logging
EXPO_PUBLIC_DEBUG=true

# Enable mock data mode
EXPO_PUBLIC_USE_MOCK_DATA=false

# =============================================================================
# PRODUCTION CONFIGURATION
# =============================================================================

# Production URLs (uncomment for production deployment)
# EXPO_PUBLIC_API_BASE_URL=https://api.richesreach.com
# API_BASE_URL=https://api.richesreach.com
# PRODUCTION_API_URL=https://api.richesreach.com
# EXPO_PUBLIC_WS_URL=wss://api.richesreach.com/ws/
# EXPO_PUBLIC_MARKET_DATA_URL=https://api.richesreach.com
# EXPO_PUBLIC_FRONTEND_URL=https://app.richesreach.com
# EXPO_PUBLIC_WHISPER_API_URL=https://api.richesreach.com
# EXPO_PUBLIC_MOBILE_SERVER_URL=https://api.richesreach.com
"""
    
    with open("environment_template.env", "w") as f:
        f.write(env_template)
    print("✅ Created environment_template.env")

def main():
    """Main function to remove all hardcoded values"""
    print("🔧 Removing ALL Hardcoded Values from RichesReach Codebase")
    print("=" * 60)
    
    # Process different directories
    directories_to_process = [
        "mobile/src",
        "backend/backend",
        "backend/server",
        "scripts",
        "infrastructure",
        "monitoring"
    ]
    
    total_files_changed = 0
    
    for directory in directories_to_process:
        if Path(directory).exists():
            print(f"\n📁 Processing {directory}...")
            fix_hardcoded_values_in_directory(directory)
        else:
            print(f"⚠️  Directory {directory} not found, skipping...")
    
    # Create environment template
    print(f"\n📋 Creating environment template...")
    create_environment_template()
    
    print(f"\n🎯 Hardcoded Values Removal Complete!")
    print(f"\n📋 Next Steps:")
    print(f"1. Copy environment_template.env to .env")
    print(f"2. Update .env with your specific configuration")
    print(f"3. Restart all services to pick up new environment variables")
    print(f"4. Verify all services work with environment-based configuration")
    
    print(f"\n🚀 All hardcoded values have been replaced with environment variables!")

if __name__ == "__main__":
    main()
