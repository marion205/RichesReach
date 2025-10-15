#!/bin/bash
# RichesReach Production Deployment Script

set -e

echo "🚀 Starting RichesReach Production Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "backend/backend/manage.py" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Load environment variables
if [ -f ".env.production" ]; then
    export $(cat .env.production | grep -v '^#' | xargs)
    print_status "Environment variables loaded"
else
    print_warning "No .env.production file found. Using system environment variables."
fi

# Navigate to backend
cd backend/backend

# Install dependencies
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Run database migrations
print_status "Running database migrations..."
python3 manage.py migrate

# Collect static files
print_status "Collecting static files..."
python3 manage.py collectstatic --noinput

# Create superuser if needed
print_status "Checking for superuser..."
python3 manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser('admin', 'admin@richesreach.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

# Start the server
print_status "Starting production server..."
python3 final_complete_server.py

print_status "Deployment completed successfully!"
