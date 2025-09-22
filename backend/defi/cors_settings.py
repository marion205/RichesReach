# CORS and rate limiting configuration
# Add these to your main settings.py

# CORS Configuration
CORS_ALLOWED_ORIGINS = [
    "https://yourapp.com",
    "exp://127.0.0.1:19000",   # Expo dev
    "http://localhost:19006"   # RN web if used
]

# For development only - remove in production
# CORS_ALLOW_ALL_ORIGINS = True

# Optional: tighten common headers
CORS_ALLOW_HEADERS = ["content-type", "authorization"]

# Rate limiting configuration
RATELIMIT_USE_CACHE = 'default'  # Use your default cache
RATELIMIT_ENABLE = True

# Additional security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
