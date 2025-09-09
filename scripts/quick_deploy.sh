#!/bin/bash

# Quick Production Deployment Script for RichesReach
# Simplified version for immediate deployment

set -e

echo "🚀 Quick Production Deployment for RichesReach"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Get server details
echo "Enter your production server details:"
read -p "Server IP/Hostname: " SERVER_HOST
read -p "Username (default: ubuntu): " SERVER_USER
SERVER_USER=${SERVER_USER:-ubuntu}
read -p "Domain name (optional): " DOMAIN_NAME

# Deployment package
DEPLOYMENT_PACKAGE="deployment/richesreach-production-20250908-113441.tar.gz"

if [ ! -f "$DEPLOYMENT_PACKAGE" ]; then
    echo "❌ Deployment package not found. Please run the build script first."
    exit 1
fi

print_status "Deploying to $SERVER_USER@$SERVER_HOST..."

# Step 1: Copy package to server
print_status "Copying deployment package..."
scp "$DEPLOYMENT_PACKAGE" $SERVER_USER@$SERVER_HOST:/home/$SERVER_USER/

# Step 2: Extract and setup on server
print_status "Setting up on server..."
ssh $SERVER_USER@$SERVER_HOST << EOF
    # Extract package
    tar -xzf $(basename $DEPLOYMENT_PACKAGE)
    cd richesreach-production
    
    # Install Docker if not present
    if ! command -v docker &> /dev/null; then
        curl -fsSL https://get.docker.com -o get-docker.sh
        sudo sh get-docker.sh
        sudo usermod -aG docker $USER
    fi
    
    # Install Docker Compose if not present
    if ! command -v docker-compose &> /dev/null; then
        sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)" -o /usr/local/bin/docker-compose
        sudo chmod +x /usr/local/bin/docker-compose
    fi
    
    # Create environment files
    cp backend/production.env.template backend/.env
    cp mobile/env.production.template mobile/.env.production
    
    echo "✅ Setup complete on server"
    echo "📝 Next steps:"
    echo "1. Edit backend/.env with your production values"
    echo "2. Edit mobile/.env.production with your production values"
    echo "3. Run: docker-compose -f docker-compose.production.yml up -d"
    echo "4. Run: docker-compose exec backend python manage.py migrate"
    echo "5. Run: docker-compose exec backend python manage.py createsuperuser"
EOF

print_success "🎉 Quick deployment completed!"
print_warning "Please SSH into your server and complete the configuration:"
print_warning "ssh $SERVER_USER@$SERVER_HOST"
print_warning "cd richesreach-production"
print_warning "nano backend/.env  # Configure your environment variables"
print_warning "docker-compose -f docker-compose.production.yml up -d"
