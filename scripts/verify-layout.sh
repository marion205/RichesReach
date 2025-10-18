#!/bin/bash
set -euo pipefail

# Default to the current nested structure, but allow override
APP_DIR="${APP_DIR:-backend/backend/backend/backend}"

echo "🔍 Verifying project layout in: $APP_DIR"

# Check for essential Django files
test -f "$APP_DIR/manage.py" || { echo "❌ manage.py missing in $APP_DIR"; exit 1; }
test -d "$APP_DIR/richesreach" || { echo "❌ richesreach/ directory missing in $APP_DIR"; exit 1; }
test -f "$APP_DIR/richesreach/settings.py" || { echo "❌ richesreach/settings.py missing in $APP_DIR"; exit 1; }
# Note: requirements.txt is now in backend/ (main directory), not in Django app directory

# Check for Dockerfile at root
test -f "Dockerfile" || { echo "❌ Dockerfile missing at repo root"; exit 1; }

echo "✅ Layout looks good! All essential files found."
echo "📁 App directory: $APP_DIR"
echo "🐳 Dockerfile: $(pwd)/Dockerfile"
