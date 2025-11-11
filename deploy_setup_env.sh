#!/bin/bash

# RichesReach Production Environment Setup Script
# This script copies the production environment file to .env

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${SCRIPT_DIR}/deployment_package/backend"
ENV_SOURCE="${BACKEND_DIR}/env.production.complete"
ENV_TARGET="${BACKEND_DIR}/.env"

echo "🚀 RichesReach Production Environment Setup"
echo "=========================================="
echo ""

# Check if source file exists
if [ ! -f "$ENV_SOURCE" ]; then
    echo "❌ Error: Source file not found: $ENV_SOURCE"
    exit 1
fi

# Backup existing .env if it exists
if [ -f "$ENV_TARGET" ]; then
    BACKUP_FILE="${ENV_TARGET}.backup.$(date +%Y%m%d_%H%M%S)"
    echo "📦 Backing up existing .env to: $BACKUP_FILE"
    cp "$ENV_TARGET" "$BACKUP_FILE"
    echo "✅ Backup created"
    echo ""
fi

# Copy production env file
echo "📋 Copying production environment file..."
cp "$ENV_SOURCE" "$ENV_TARGET"
echo "✅ Environment file copied to: $ENV_TARGET"
echo ""

# Verify critical variables
echo "🔍 Verifying critical configuration..."
if grep -q "SENTRY_DSN=" "$ENV_TARGET" && ! grep -q "SENTRY_DSN=$" "$ENV_TARGET"; then
    echo "✅ Sentry DSN configured"
else
    echo "⚠️  Warning: Sentry DSN not configured"
fi

if grep -q "DATABASE_URL=" "$ENV_TARGET" && ! grep -q "DATABASE_URL=$" "$ENV_TARGET"; then
    echo "✅ Database URL configured"
else
    echo "⚠️  Warning: Database URL not configured"
fi

if grep -q "SECRET_KEY=" "$ENV_TARGET" && ! grep -q "SECRET_KEY=$" "$ENV_TARGET"; then
    echo "✅ Secret key configured"
else
    echo "⚠️  Warning: Secret key not configured"
fi

echo ""
echo "✅ Environment setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Review .env file for any missing values"
echo "   2. Ensure .env is in .gitignore (should not be committed)"
echo "   3. Deploy your application"
echo ""

