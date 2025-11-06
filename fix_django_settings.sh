#!/bin/bash
# Fix Django Settings Configuration

echo "🔧 Fixing Django Settings Configuration"
echo "======================================="
echo ""

BACKEND_DIR="deployment_package/backend"
SETTINGS_SOURCE="deployment/richesreach-production/backend/richesreach/settings.py"
SETTINGS_TARGET="$BACKEND_DIR/richesreach/settings.py"

# Step 1: Create richesreach directory
echo "1️⃣ Creating richesreach directory..."
mkdir -p "$BACKEND_DIR/richesreach"
touch "$BACKEND_DIR/richesreach/__init__.py"
echo "✅ Created: $BACKEND_DIR/richesreach/"
echo ""

# Step 2: Copy or create settings file
echo "2️⃣ Setting up settings.py..."
if [ -f "$SETTINGS_SOURCE" ]; then
    echo "📋 Found existing settings file, copying..."
    cp "$SETTINGS_SOURCE" "$SETTINGS_TARGET"
    echo "✅ Copied from: $SETTINGS_SOURCE"
else
    echo "📝 Creating minimal settings file..."
    cat > "$SETTINGS_TARGET" << 'EOF'
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-change-me-in-production')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'graphene_django',
    'corsheaders',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'richesreach.urls'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'richesreach'),
        'USER': os.getenv('DB_USER', os.getenv('USER', 'postgres')),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

GRAPHENE = {
    'SCHEMA': 'core.schema.schema',
}

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8081",
    "http://localhost:19006",
]

CORS_ALLOW_CREDENTIALS = True
EOF
    echo "✅ Created minimal settings file"
fi
echo ""

# Step 3: Verify settings file
echo "3️⃣ Verifying settings file..."
if [ -f "$SETTINGS_TARGET" ]; then
    echo "✅ Settings file exists: $SETTINGS_TARGET"
    echo "   File size: $(wc -l < "$SETTINGS_TARGET") lines"
else
    echo "❌ Settings file not found!"
    exit 1
fi
echo ""

# Step 4: Test Django settings
echo "4️⃣ Testing Django settings..."
cd "$BACKEND_DIR"
source venv/bin/activate 2>/dev/null || echo "⚠️  Virtual environment not found, skipping activation"
python manage.py check --settings=richesreach.settings 2>&1 | head -10 || echo "⚠️  Django check failed (may need database connection)"
echo ""

# Summary
echo "======================================="
echo "✅ Django Settings Configuration Fix Complete!"
echo ""
echo "📁 Settings file location:"
echo "   $SETTINGS_TARGET"
echo ""
echo "📝 Next steps:"
echo "1. Review settings file: cat $SETTINGS_TARGET"
echo "2. Update database credentials if needed"
echo "3. Restart server: python3 main_server.py"
echo "4. Test endpoints: ./test_yodlee_comprehensive.sh"

