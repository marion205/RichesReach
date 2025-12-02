#!/usr/bin/env bash

set -e

echo "🚀 RichesReach Backend Bootstrap"

# Resolve repo root (directory where this script lives)
REPO_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BACKEND_DIR="$REPO_ROOT/deployment_package/backend"
VENV_DIR="$REPO_ROOT/venv"

echo "📁 Repo root:        $REPO_ROOT"
echo "📁 Backend dir:      $BACKEND_DIR"
echo "📁 Virtualenv dir:   $VENV_DIR"
echo

# 1. Create venv if missing
if [ ! -d "$VENV_DIR" ]; then
  echo "🐍 No virtualenv found. Creating one..."
  python3 -m venv "$VENV_DIR"
  echo "✅ Virtualenv created."
else
  echo "✅ Virtualenv already exists."
fi

# 2. Activate venv
# shellcheck disable=SC1090
source "$VENV_DIR/bin/activate"
echo "✅ Virtualenv activated: $(which python)"

# 3. Ensure we're in backend dir
cd "$BACKEND_DIR"

# 4. Install dependencies *if Django is missing*
echo
echo "🔍 Checking for Django..."
if python -c "import django" 2>/dev/null; then
  echo "✅ Django is installed. Skipping full requirements install."
else
  echo "⚠️ Django not found. Installing requirements..."
  if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found in $BACKEND_DIR"
    echo "   Make sure you're in the right directory."
    exit 1
  fi
  
  # Try to install requirements, but continue if graphql-jwt fails (it's optional)
  pip install -r requirements.txt || {
    echo "⚠️  Some packages failed to install. Trying without graphql-jwt (optional)..."
    # Install without graphql-jwt if it fails
    grep -v "graphql-jwt" requirements.txt > /tmp/requirements_no_jwt.txt || true
    pip install -r /tmp/requirements_no_jwt.txt || pip install -r requirements.txt --ignore-installed graphql-jwt 2>/dev/null || true
    echo "✅ Requirements installed (graphql-jwt may be missing but is optional)."
  }
  
  # Verify Django is now installed
  if python -c "import django" 2>/dev/null; then
    echo "✅ Django is now installed."
  else
    echo "❌ Django installation failed. Please check requirements.txt"
    exit 1
  fi
fi

# 5. Check for ML dependencies (optional but helpful)
echo
echo "🔍 Checking for ML dependencies..."
MISSING_ML_DEPS=()
if ! python -c "import sklearn" 2>/dev/null; then
  MISSING_ML_DEPS+=("scikit-learn")
fi
if ! python -c "import statsmodels" 2>/dev/null; then
  MISSING_ML_DEPS+=("statsmodels")
fi
if ! python -c "import pandas" 2>/dev/null; then
  MISSING_ML_DEPS+=("pandas")
fi
if ! python -c "import numpy" 2>/dev/null; then
  MISSING_ML_DEPS+=("numpy")
fi

if [ ${#MISSING_ML_DEPS[@]} -gt 0 ]; then
  echo "⚠️  Missing ML dependencies: ${MISSING_ML_DEPS[*]}"
  echo "   These are optional but recommended for advanced ML features."
  read -r -p "   Install them now? [y/N] " answer
  case "$answer" in
    [yY][eE][sS]|[yY])
      pip install "${MISSING_ML_DEPS[@]}"
      echo "✅ ML dependencies installed."
      ;;
    *)
      echo "⏭️  Skipping ML dependencies. You can install them later if needed."
      ;;
  esac
else
  echo "✅ All ML dependencies are installed."
fi

# 6. Run migrations
echo
echo "⚙️ Running migrations..."
python manage.py makemigrations core
python manage.py migrate
echo "✅ Migrations complete."

# 7. Optional: start backend server (skip if --no-start flag)
if [ "$1" = "--no-start" ]; then
  echo "✅ Bootstrap complete (--no-start flag)."
  echo "   Start the server with: ./start_django_backend.sh"
else
  echo
  read -r -p "▶️  Start backend server now with 'python manage.py runserver'? [y/N] " answer
  case "$answer" in
    [yY][eE][sS]|[yY])
      echo "🚀 Starting Django server on http://127.0.0.1:8000 ..."
      echo "   GraphQL Playground: http://127.0.0.1:8000/graphql"
      python manage.py runserver
      ;;
    *)
      echo "✅ Bootstrap complete. You can start the server later with:"
      echo "   ./start_django_backend.sh"
      echo "   or"
      echo "   cd \"$BACKEND_DIR\""
      echo "   source \"$VENV_DIR/bin/activate\""
      echo "   python manage.py runserver"
      ;;
  esac
fi

