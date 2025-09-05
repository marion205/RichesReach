#!/usr/bin/env python3
"""
Fix RateLimiter usage in mutations.py
"""
import re

def fix_rate_limiter_usage():
    """Fix all RateLimiter instantiations in mutations.py"""
    
    file_path = '/Users/marioncollins/RichesReach/backend/core/mutations.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix CreateUser mutation
    content = re.sub(
        r'# Check rate limiting for user creation\n        is_limited, attempts_remaining, reset_time = RateLimiter\.is_rate_limited\(\n            info\.context, action=\'user_creation\', max_attempts=5, window_minutes=60\n        \)\n        if not rate_limiter\.allow_request\(info\.context\.META\.get\(\'REMOTE_ADDR\', \'unknown\'\)\):\n            raise GraphQLError\("Too many user creation attempts\. Please try again later\."\)',
        '''# Check rate limiting for user creation
        is_limited, attempts_remaining, reset_time = RateLimiter.is_rate_limited(
            info.context, action='user_creation', max_attempts=5, window_minutes=60
        )
        if is_limited:
            raise GraphQLError(f"Too many user creation attempts. Please try again after {reset_time}.")''',
        content
    )
    
    # Fix ForgotPassword mutation
    content = re.sub(
        r'rate_limiter = RateLimiter\(\'password_reset\', max_attempts=3, window_minutes=60\)',
        '''# Check rate limiting for password reset
        is_limited, attempts_remaining, reset_time = RateLimiter.is_rate_limited(
            info.context, action='password_reset', max_attempts=3, window_minutes=60
        )
        if is_limited:
            raise GraphQLError(f"Too many password reset attempts. Please try again after {reset_time}.")''',
        content
    )
    
    # Fix ResetPassword mutation
    content = re.sub(
        r'rate_limiter = RateLimiter\(\'password_reset_confirm\', max_attempts=5, window_minutes=60\)',
        '''# Check rate limiting for password reset confirmation
        is_limited, attempts_remaining, reset_time = RateLimiter.is_rate_limited(
            info.context, action='password_reset_confirm', max_attempts=5, window_minutes=60
        )
        if is_limited:
            raise GraphQLError(f"Too many password reset attempts. Please try again after {reset_time}.")''',
        content
    )
    
    # Fix ChangePassword mutation
    content = re.sub(
        r'rate_limiter = RateLimiter\(\'password_change\', max_attempts=5, window_minutes=60\)',
        '''# Check rate limiting for password change
        is_limited, attempts_remaining, reset_time = RateLimiter.is_rate_limited(
            info.context, action='password_change', max_attempts=5, window_minutes=60
        )
        if is_limited:
            raise GraphQLError(f"Too many password change attempts. Please try again after {reset_time}.")''',
        content
    )
    
    # Fix ResendVerificationEmail mutation
    content = re.sub(
        r'rate_limiter = RateLimiter\(\'resend_verification\', max_attempts=3, window_minutes=60\)',
        '''# Check rate limiting for resend verification
        is_limited, attempts_remaining, reset_time = RateLimiter.is_rate_limited(
            info.context, action='resend_verification', max_attempts=3, window_minutes=60
        )
        if is_limited:
            raise GraphQLError(f"Too many verification email requests. Please try again after {reset_time}.")''',
        content
    )
    
    # Fix EnhancedTokenAuth mutation
    content = re.sub(
        r'rate_limiter = RateLimiter\(\'login\', max_attempts=5, window_minutes=15\)',
        '''# Check rate limiting for login
        is_limited, attempts_remaining, reset_time = RateLimiter.is_rate_limited(
            info.context, action='login', max_attempts=5, window_minutes=15
        )
        if is_limited:
            raise GraphQLError(f"Too many login attempts. Please try again after {reset_time}.")''',
        content
    )
    
    # Write the fixed content back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("✅ Fixed RateLimiter usage in mutations.py")

if __name__ == "__main__":
    fix_rate_limiter_usage()
