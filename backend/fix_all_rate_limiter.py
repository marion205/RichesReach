#!/usr/bin/env python3
"""
Fix all remaining RateLimiter usage in mutations.py
"""
import re

def fix_all_rate_limiter():
    """Fix all remaining rate_limiter references in mutations.py"""
    
    file_path = '/Users/marioncollins/RichesReach/backend/core/mutations.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix all remaining rate_limiter.allow_request calls
    content = re.sub(
        r'if not rate_limiter\.allow_request\(info\.context\.META\.get\(\'REMOTE_ADDR\', \'unknown\'\)\):\n\s+raise GraphQLError\("Too many .* attempts\. Please try again later\."\)',
        'if is_limited:\n            raise GraphQLError(f"Too many attempts. Please try again after {reset_time}.")',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # Fix the enhanced token auth rate limiter
    content = re.sub(
        r'if not rate_limiter\.allow_request\(client_ip\):\n\s+raise GraphQLError\("Too many login attempts\. Please try again later\."\)',
        'if is_limited:\n            raise GraphQLError(f"Too many login attempts. Please try again after {reset_time}.")',
        content,
        flags=re.MULTILINE | re.DOTALL
    )
    
    # Write the fixed content back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Fixed all remaining RateLimiter usage in mutations.py")

if __name__ == "__main__":
    fix_all_rate_limiter()
