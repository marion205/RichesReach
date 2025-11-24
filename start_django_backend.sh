#!/usr/bin/env bash
# Start Django backend server with auto-bootstrap if needed

set -e

REPO_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$REPO_ROOT/deployment_package/backend"
VENV_DIR="$REPO_ROOT/venv"

echo "🚀 Starting RichesReach Django Backend..."

# Check if bootstrap is needed
if [ ! -d "$VENV_DIR" ] || ! "$VENV_DIR/bin/python" -c "import django" 2>/dev/null; then
  echo "⚠️  Backend not bootstrapped. Running bootstrap first..."
  "$REPO_ROOT/bootstrap_backend.sh" --no-start
  echo ""
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Go to backend directory
cd "$BACKEND_DIR"

# Check if migrations are up to date
echo "🔍 Checking migrations..."
python manage.py makemigrations --check --dry-run core > /dev/null 2>&1 || {
  echo "⚠️  Pending migrations detected. Running migrations..."
  python manage.py makemigrations core
  python manage.py migrate
}

echo ""
echo "📡 Starting Django server on http://0.0.0.0:8000 (accessible from iOS Simulator)"
echo "📡 GraphQL Playground: http://localhost:8000/graphql"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the server bound to 0.0.0.0 so iOS Simulator can access it
python manage.py runserver 0.0.0.0:8000

