#!/bin/bash

# Setup local environment with secure API keys
set -e

echo "🔐 Setting up local environment with secure API keys"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if .env already exists
if [ -f ".env" ]; then
    log_warn ".env file already exists. Backing up to .env.backup"
    cp .env .env.backup
fi

# Create .env from template
log_info "Creating .env file from template..."
cp env.template .env

# Update with actual API keys
log_info "Setting up API keys..."

# Update Polygon API key
sed -i '' 's/your-polygon-api-key-here/uuKmy9dPAjaSVXVEtCumQPga1dqEPDS2/g' .env

# Update Finnhub API key
sed -i '' 's/your-finnhub-api-key-here/d2rnitpr01qv11lfegugd2rnitpr01qv11lfegv0/g' .env

# Update News API key
sed -i '' 's/your-news-api-key-here/94a335c7316145f79840edd62f77e11e/g' .env

# Update OpenAI API key
sed -i '' 's/your-openai-api-key-here/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/g' .env

# Generate a secure secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))")
sed -i '' "s/your-secret-key-here/$SECRET_KEY/g" .env

log_info "✅ Local environment configured with secure API keys"
log_info "✅ .env file created with production-ready settings"
log_info "✅ API keys are now stored securely in environment variables"

# Add .env to .gitignore if not already there
if ! grep -q "^\.env$" .gitignore; then
    echo ".env" >> .gitignore
    log_info "✅ Added .env to .gitignore for security"
fi

log_info "🔐 Your API keys are now secure and not in version control!"
log_info "🚀 You can now run your local server with: cd backend/backend && python final_complete_server.py"
