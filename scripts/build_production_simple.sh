#!/bin/bash

# Simplified Production Build Script for RichesReach
# This script builds the app for production deployment without ML dependencies

set -e  # Exit on any error

echo "🚀 Starting RichesReach Production Build (Simplified)..."

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
if [ ! -d "mobile" ] || [ ! -d "backend" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Check if required tools are installed
check_dependencies() {
    print_status "Checking dependencies..."
    
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed"
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    print_success "All dependencies are installed"
}

# Clean previous builds
clean_builds() {
    print_status "Cleaning previous builds..."
    
    # Clean mobile build artifacts
    if [ -d "mobile/.expo" ]; then
        rm -rf mobile/.expo
    fi
    
    if [ -d "mobile/dist" ]; then
        rm -rf mobile/dist
    fi
    
    if [ -d "mobile/build" ]; then
        rm -rf mobile/build
    fi
    
    # Clean backend build artifacts
    if [ -d "backend/__pycache__" ]; then
        find backend -name "__pycache__" -type d -exec rm -rf {} +
    fi
    
    if [ -d "backend/*.pyc" ]; then
        find backend -name "*.pyc" -delete
    fi
    
    print_success "Build artifacts cleaned"
}

# Install mobile dependencies
install_mobile_dependencies() {
    print_status "Installing mobile dependencies..."
    
    cd mobile
    npm ci --production=false
    cd ..
    
    print_success "Mobile dependencies installed"
}

# Install backend dependencies (core only)
install_backend_dependencies() {
    print_status "Installing backend dependencies (core only)..."
    
    cd backend
    
    # Install core Django dependencies only
    pip install Django>=4.2.0
    pip install graphene-django>=3.1.0
    pip install django-cors-headers>=4.0.0
    pip install psycopg2-binary==2.9.7
    pip install redis==4.6.0
    pip install requests>=2.31.0
    pip install python-dotenv==1.0.0
    pip install gunicorn
    pip install whitenoise
    
    cd ..
    
    print_success "Backend dependencies installed"
}

# Validate environment configuration
validate_environment() {
    print_status "Validating environment configuration..."
    
    # Check if production environment files exist
    if [ ! -f "backend/.env" ]; then
        print_warning "Backend .env file not found. Creating template..."
        cp backend/production.env.template backend/.env
        print_warning "Please edit backend/.env with your production values"
    fi
    
    if [ ! -f "mobile/.env.production" ]; then
        print_warning "Mobile .env.production file not found. Creating template..."
        cp mobile/env.production.template mobile/.env.production
        print_warning "Please edit mobile/.env.production with your production values"
    fi
    
    print_success "Environment configuration validated"
}

# Build mobile app
build_mobile() {
    print_status "Building mobile app..."
    
    cd mobile
    
    # Set production environment
    export EXPO_PUBLIC_ENVIRONMENT=production
    
    # Build for production (Expo managed workflow)
    npx expo export --platform all --output-dir dist
    
    cd ..
    
    print_success "Mobile app built successfully"
}

# Build backend
build_backend() {
    print_status "Building backend..."
    
    cd backend
    
    # Run database migrations (if database is available)
    if python3 manage.py check --database default 2>/dev/null; then
        python3 manage.py makemigrations
        python3 manage.py migrate
    else
        print_warning "Database not available, skipping migrations"
    fi
    
    # Collect static files
    python3 manage.py collectstatic --noinput
    
    # Validate Django configuration
    python3 manage.py check --deploy
    
    cd ..
    
    print_success "Backend built successfully"
}

# Create production deployment package
create_deployment_package() {
    print_status "Creating deployment package..."
    
    # Create deployment directory
    mkdir -p deployment/richesreach-production
    
    # Copy backend files
    cp -r backend deployment/richesreach-production/
    cp -r scripts deployment/richesreach-production/
    cp -r docs deployment/richesreach-production/
    
    # Copy mobile build artifacts
    if [ -d "mobile/dist" ]; then
        cp -r mobile/dist deployment/richesreach-production/mobile-dist
    fi
    
    # Copy mobile app configuration
    if [ -f "mobile/app.json" ]; then
        cp mobile/app.json deployment/richesreach-production/
    fi
    
    if [ -f "mobile/package.json" ]; then
        cp mobile/package.json deployment/richesreach-production/mobile-package.json
    fi
    
    # Copy configuration files
    cp docker-compose.production.yml deployment/richesreach-production/
    cp Dockerfile deployment/richesreach-production/
    cp .gitignore deployment/richesreach-production/
    
    # Create deployment README
    cat > deployment/richesreach-production/README.md << EOF
# RichesReach Production Deployment

This package contains the production-ready RichesReach application.

## Contents
- backend/: Django backend application
- scripts/: Deployment and setup scripts
- docs/: Documentation
- mobile-dist/: Mobile app build artifacts
- docker-compose.production.yml: Production Docker configuration
- Dockerfile: Docker configuration

## Deployment Instructions
1. Copy this package to your production server
2. Run the setup scripts in the scripts/ directory
3. Configure environment variables
4. Start the application using Docker Compose

## Support
For deployment support, contact the development team.
EOF
    
    # Create deployment archive
    cd deployment
    tar -czf richesreach-production-$(date +%Y%m%d-%H%M%S).tar.gz richesreach-production/
    cd ..
    
    print_success "Deployment package created: deployment/richesreach-production-$(date +%Y%m%d-%H%M%S).tar.gz"
}

# Main build process
main() {
    print_status "Starting production build process..."
    
    check_dependencies
    clean_builds
    install_mobile_dependencies
    install_backend_dependencies
    validate_environment
    build_mobile
    build_backend
    create_deployment_package
    
    print_success "🎉 Production build completed successfully!"
    print_status "Deployment package is ready in the deployment/ directory"
    print_status "Next steps:"
    print_status "1. Deploy the package to your production server"
    print_status "2. Configure production environment variables"
    print_status "3. Start the application using Docker Compose"
    print_status "4. Monitor the application using the provided monitoring tools"
}

# Run main function
main "$@"
