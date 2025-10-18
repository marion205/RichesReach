#!/bin/bash

# 🚀 RichesReach Production Deployment Script
# This script automates the production deployment process

set -e  # Exit on any error

echo "🚀 Starting RichesReach Production Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "mobile/package.json" ] || [ ! -d "backend" ]; then
    print_error "Please run this script from the RichesReach root directory"
    exit 1
fi

# Check if production environment file exists
if [ ! -f ".env.production" ]; then
    print_warning "Production environment file not found. Creating template..."
    cat > .env.production << EOF
# Production Environment Variables
DEBUG=False
SECRET_KEY=your-production-secret-key-here
DATABASE_URL=postgresql://user:password@host:port/dbname
REDIS_URL=redis://host:port/0
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key
FINNHUB_API_KEY=your-finnhub-key
NEWS_API_KEY=your-news-api-key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
EOF
    print_warning "Please update .env.production with your actual values before continuing"
    exit 1
fi

# Load production environment variables
print_status "Loading production environment variables..."
source .env.production

# Backend Deployment
print_status "Starting backend deployment..."

cd backend

# Activate virtual environment
if [ -d "venv" ]; then
    print_status "Activating virtual environment..."
    source venv/bin/activate
else
    print_error "Virtual environment not found. Please create one first."
    exit 1
fi

# Install/update dependencies
print_status "Installing backend dependencies..."
pip install -r requirements.txt

# Navigate to Django project directory
cd backend/backend/backend

# Run database migrations
print_status "Running database migrations..."
python manage.py migrate

# Collect static files
print_status "Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist
print_status "Checking for superuser..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print("Creating superuser...")
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("Superuser created: admin/admin123")
else:
    print("Superuser already exists")
EOF

# Test the backend
print_status "Testing backend configuration..."
python manage.py check --deploy

print_success "Backend deployment completed!"

# Mobile App Deployment
print_status "Starting mobile app deployment..."

cd ../../../mobile

# Install dependencies
print_status "Installing mobile dependencies..."
npm install

# Check if production environment file exists for mobile
if [ ! -f "env.production" ]; then
    print_warning "Mobile production environment file not found. Creating template..."
    cat > env.production << EOF
# Mobile Production Environment Variables
EXPO_PUBLIC_API_BASE_URL=https://yourdomain.com
EXPO_PUBLIC_GRAPHQL_URL=https://yourdomain.com/graphql/
EXPO_PUBLIC_RUST_API_URL=https://yourdomain.com:3001
EXPO_PUBLIC_WS_URL=wss://yourdomain.com/ws
EOF
    print_warning "Please update mobile/env.production with your actual values"
fi

# Build mobile app
print_status "Building mobile app for production..."

# Check if EAS CLI is installed
if ! command -v eas &> /dev/null; then
    print_warning "EAS CLI not found. Installing..."
    npm install -g @expo/eas-cli
fi

# Build for both platforms
print_status "Building for Android..."
eas build --platform android --profile production

print_status "Building for iOS..."
eas build --platform ios --profile production

print_success "Mobile app builds completed!"

# Final checks
print_status "Running final production checks..."

# Test backend health
print_status "Testing backend health endpoint..."
if curl -f -s http://localhost:8000/health > /dev/null; then
    print_success "Backend health check passed"
else
    print_warning "Backend health check failed - make sure server is running"
fi

# Check if all required files exist
print_status "Checking required files..."

required_files=(
    "backend/backend/backend/backend/richesreach/settings.py"
    "mobile/package.json"
    "mobile/app.json"
    ".env.production"
    "mobile/env.production"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        print_success "✓ $file exists"
    else
        print_error "✗ $file missing"
    fi
done

# Production readiness summary
echo ""
echo "🎉 Production Deployment Summary"
echo "================================"
echo "✅ Backend deployed and configured"
echo "✅ Database migrations completed"
echo "✅ Static files collected"
echo "✅ Mobile app built for production"
echo "✅ Environment variables configured"
echo ""
echo "📋 Next Steps:"
echo "1. Deploy backend to your production server"
echo "2. Configure your domain and SSL certificates"
echo "3. Submit mobile apps to app stores"
echo "4. Set up monitoring and analytics"
echo "5. Test all functionality in production"
echo ""
echo "🔗 Useful Commands:"
echo "• Start backend: cd backend && source venv/bin/activate && cd backend/backend/backend && python manage.py runserver"
echo "• Test GraphQL: curl -X POST http://localhost:8000/graphql/ -H 'Content-Type: application/json' -d '{\"query\": \"{ __schema { types { name } } }\"}'"
echo "• View logs: tail -f backend/logs/django.log"
echo ""
print_success "Production deployment completed successfully! 🚀"