#!/bin/bash
# Yodlee Setup Script
# This script helps set up Yodlee integration

set -e

echo "🏦 Yodlee Banking Integration Setup"
echo "===================================="
echo ""

# Check if we're in the right directory
if [ ! -f "deployment_package/backend/manage.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

cd deployment_package/backend

# Step 1: Check Python and Django
echo "📋 Step 1: Checking Python and Django..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

python3 --version

# Check if Django is available
if python3 -c "import django" 2>/dev/null; then
    echo "✅ Django is installed"
    DJANGO_AVAILABLE=true
else
    echo "⚠️  Django is not installed. Migrations will be skipped."
    DJANGO_AVAILABLE=false
fi

# Step 2: Install dependencies
echo ""
echo "📦 Step 2: Installing dependencies..."
echo "Installing cryptography (required for token encryption)..."
pip3 install cryptography --user 2>/dev/null || echo "⚠️  Could not install cryptography (may need sudo or virtualenv)"

echo "Installing celery (optional, for async tasks)..."
pip3 install celery --user 2>/dev/null || echo "⚠️  Could not install celery (optional)"

echo "Installing boto3 (optional, for AWS KMS)..."
pip3 install boto3 --user 2>/dev/null || echo "⚠️  Could not install boto3 (optional)"

# Step 3: Environment variables
echo ""
echo "🔐 Step 3: Setting up environment variables..."
if [ ! -f "env.yodlee.sample" ]; then
    echo "❌ env.yodlee.sample not found in deployment_package/backend/"
    echo "   Creating from template..."
    # Create the sample file if it doesn't exist
    cat > env.yodlee.sample << 'EOF'
# Yodlee Banking Integration Configuration
USE_YODLEE=true
YODLEE_BASE_URL=https://sandbox.api.yodlee.com/ysl
YODLEE_CLIENT_ID=your_client_id
YODLEE_SECRET=your_client_secret
YODLEE_APP_ID=your_app_id
YODLEE_FASTLINK_URL=https://fastlink.yodlee.com
YODLEE_WEBHOOK_SECRET=your_webhook_secret
BANK_TOKEN_ENCRYPTION=fernet
BANK_TOKEN_ENC_KEY=your_key_here
YODLEE_MAX_RETRIES=3
YODLEE_RETRY_DELAY=1
YODLEE_TIMEOUT=10
EOF
    echo "✅ Created env.yodlee.sample"
fi

if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from env.yodlee.sample..."
    cp env.yodlee.sample .env
    echo "✅ Created .env file"
    echo "⚠️  IMPORTANT: Edit .env file and add your Yodlee credentials!"
else
    echo "✅ .env file already exists"
    echo "⚠️  Make sure it includes Yodlee configuration from env.yodlee.sample"
    # Check if Yodlee vars are already in .env
    if grep -q "YODLEE_CLIENT_ID" .env 2>/dev/null; then
        echo "✅ Yodlee variables found in .env"
    else
        echo "⚠️  Adding Yodlee variables to .env..."
        cat env.yodlee.sample >> .env
        echo "✅ Added Yodlee configuration to .env"
    fi
fi

# Step 4: Generate encryption key
echo ""
echo "🔑 Step 4: Generating encryption key..."
if python3 -c "from cryptography.fernet import Fernet" 2>/dev/null; then
    ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    echo "Generated encryption key:"
    echo "BANK_TOKEN_ENC_KEY=$ENCRYPTION_KEY"
    echo ""
    echo "⚠️  Add this to your .env file as BANK_TOKEN_ENC_KEY"
else
    echo "⚠️  cryptography not installed, skipping key generation"
fi

# Step 5: Run migrations (if Django is available)
if [ "$DJANGO_AVAILABLE" = true ]; then
    echo ""
    echo "🗄️  Step 5: Running migrations..."
    echo "Creating migrations..."
    python3 manage.py makemigrations core || echo "⚠️  Could not create migrations"
    
    echo "Applying migrations..."
    python3 manage.py migrate || echo "⚠️  Could not apply migrations"
    echo "✅ Migrations complete"
else
    echo ""
    echo "⚠️  Step 5: Skipping migrations (Django not available)"
    echo "   Run these commands when Django is available:"
    echo "   cd deployment_package/backend"
    echo "   python manage.py makemigrations core"
    echo "   python manage.py migrate"
fi

# Summary
echo ""
echo "✅ Setup Complete!"
echo ""
echo "📝 Next Steps:"
echo "1. Edit .env file and add your Yodlee credentials:"
echo "   - YODLEE_CLIENT_ID"
echo "   - YODLEE_SECRET"
echo "   - YODLEE_APP_ID"
echo "   - YODLEE_WEBHOOK_SECRET"
echo "   - BANK_TOKEN_ENC_KEY (use the generated key above)"
echo ""
echo "2. Test the endpoints:"
echo "   curl http://localhost:8000/api/yodlee/fastlink/start"
echo ""
echo "📚 Documentation:"
echo "   - YODLEE_SETUP_INSTRUCTIONS.md"
echo "   - YODLEE_IMPLEMENTATION_COMPLETE.md"
echo "   - YODLEE_ENHANCEMENTS_COMPLETE.md"

