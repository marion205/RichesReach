#!/usr/bin/env python3
"""
Script to remove all emojis from code files in the RichesReach project.
This script will clean up emojis from code files while preserving functionality.
"""
import os
import re
import sys
from pathlib import Path

def remove_emojis_from_text(text):
    """Remove all emojis from text while preserving functionality."""
    # Comprehensive emoji regex pattern
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002600-\U000026FF"  # miscellaneous symbols
        "\U00002700-\U000027BF"  # dingbats
        "\U0000FE00-\U0000FE0F"  # variation selectors
        "\U0001F900-\U0001F9FF"  # supplemental symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
        "\U0001F018-\U0001F0FF"  # playing cards
        "\U0001F200-\U0001F2FF"  # enclosed CJK letters and months
        "\U0001F300-\U0001F5FF"  # miscellaneous symbols and pictographs
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F680-\U0001F6FF"  # transport and map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # geometric shapes extended
        "\U0001F800-\U0001F8FF"  # supplemental arrows-C
        "\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
        "\U0001FA00-\U0001FA6F"  # chess symbols
        "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
        "\U0001FB00-\U0001FBFF"  # symbols for legacy computing
        "\U0001FC00-\U0001FCFF"  # symbols for legacy computing
        "\U0001FD00-\U0001FDFF"  # symbols for legacy computing
        "\U0001FE00-\U0001FE0F"  # variation selectors
        "\U0001FF00-\U0001FFFF"  # symbols for legacy computing
        "]+", 
        flags=re.UNICODE
    )
    
    # Remove emojis and clean up extra spaces
    cleaned_text = emoji_pattern.sub('', text)
    
    # Clean up multiple spaces and newlines
    cleaned_text = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned_text)  # Multiple empty lines
    cleaned_text = re.sub(r'[ \t]+', ' ', cleaned_text)  # Multiple spaces/tabs
    cleaned_text = re.sub(r'^\s+', '', cleaned_text, flags=re.MULTILINE)  # Leading whitespace
    
    return cleaned_text

def should_process_file(file_path):
    """Determine if a file should be processed."""
    # Skip binary files and certain directories
    skip_dirs = {
        'node_modules', '.git', 'venv', '__pycache__', 
        '.expo', 'build', 'dist', '.next', 'coverage',
        '.venv', 'deployment_package'  # Skip deployment package and venv
    }
    skip_extensions = {
        '.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', 
        '.pdf', '.zip', '.tar', '.gz', '.dmg', '.exe',
        '.so', '.dylib', '.dll', '.pkl', '.h5', '.model'
    }
    
    # Check if file is in a skip directory
    for part in file_path.parts:
        if part in skip_dirs:
            return False
    
    # Check file extension
    if file_path.suffix.lower() in skip_extensions:
        return False
    
    # Only process text files
    return file_path.suffix.lower() in {
        '.py', '.js', '.ts', '.tsx', '.jsx', '.md', '.txt', 
        '.json', '.yml', '.yaml', '.sh', '.sql', '.rs', 
        '.html', '.css', '.scss', '.sass', '.less'
    }

def process_file(file_path):
    """Process a single file to remove emojis."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            original_content = f.read()
        
        cleaned_content = remove_emojis_from_text(original_content)
        
        # Only write if content changed
        if cleaned_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(cleaned_content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to process all files."""
    project_root = Path(__file__).parent.parent
    processed_files = 0
    modified_files = 0
    
    print("Starting emoji removal process...")
    print(f"Project root: {project_root}")
    
    # Process all files in the project, excluding venv and deployment_package
    for file_path in project_root.rglob('*'):
        if file_path.is_file() and should_process_file(file_path):
            processed_files += 1
            if process_file(file_path):
                modified_files += 1
                print(f"Modified: {file_path.relative_to(project_root)}")
    
    print(f"\nEmoji removal complete!")
    print(f"Files processed: {processed_files}")
    print(f"Files modified: {modified_files}")

if __name__ == "__main__":
    main()