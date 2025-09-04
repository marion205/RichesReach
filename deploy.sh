#!/bin/bash

# RichesReach Deployment Script
# This script helps deploy the app to production

set -e  # Exit on any error

echo "🚀 RichesReach Deployment Script"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
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
if [ ! -f "backend/manage.py" ]; then
    print_error "Please run this script from the RichesReach root directory"
    exit 1
fi

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    print_warning "No .env file found. Please create one from env.example"
    echo "cp backend/env.example backend/.env"
    echo "Then edit backend/.env with your production values"
    exit 1
fi

print_status "Starting deployment process..."

# 1. Install production dependencies
print_status "Installing production dependencies..."
cd backend
source ../.venv/bin/activate
pip install -r requirements-production.txt

# 2. Run database migrations
print_status "Running database migrations..."
python manage.py migrate

# 3. Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput

# 4. Create superuser (if needed)
print_warning "Do you want to create a superuser? (y/n)"
read -r create_superuser
if [ "$create_superuser" = "y" ]; then
    python manage.py createsuperuser
fi

# 5. Test the application
print_status "Testing the application..."
python manage.py check --deploy

# 6. Start the production server
print_status "Starting production server..."
print_warning "Make sure to use a proper WSGI server like Gunicorn in production!"
echo "Example: gunicorn --bind 0.0.0.0:8000 richesreach.wsgi:application"

cd ..

print_status "Deployment preparation complete!"
echo ""
echo "Next steps:"
echo "1. Set up your production server (AWS, DigitalOcean, etc.)"
echo "2. Configure your domain name and SSL"
echo "3. Set up monitoring (Sentry, etc.)"
echo "4. Build and submit your mobile app"
echo ""
echo "See DEPLOYMENT_GUIDE.md for detailed instructions"
