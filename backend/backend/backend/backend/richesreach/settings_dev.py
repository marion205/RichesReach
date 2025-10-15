from .settings import *

DEBUG = True
ALLOWED_HOSTS = ["*"]

# make these additions safe to import repeatedly
if "corsheaders" not in INSTALLED_APPS:
    INSTALLED_APPS += ["corsheaders"]

if "corsheaders.middleware.CorsMiddleware" not in MIDDLEWARE:
    MIDDLEWARE = ["corsheaders.middleware.CorsMiddleware"] + list(MIDDLEWARE)

CORS_ALLOW_ALL_ORIGINS = True  # dev only

# dev-friendly security
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
