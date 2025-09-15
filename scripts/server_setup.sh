#!/bin/bash
# Server Setup Script for RichesReach
# Run this script on your production server
set -e
echo " Setting up RichesReach on production server..."
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
# Update system
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y
# Install Docker
print_status "Installing Docker..."
if ! command -v docker &> /dev/null; then
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
print_success "Docker installed"
else
print_success "Docker already installed"
fi
# Install Docker Compose
print_status "Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
print_success "Docker Compose installed"
else
print_success "Docker Compose already installed"
fi
# Install additional tools
print_status "Installing additional tools..."
sudo apt install -y git curl wget unzip nginx certbot python3-certbot-nginx
# Create app directory
print_status "Creating application directory..."
mkdir -p /home/ubuntu/richesreach
cd /home/ubuntu/richesreach
print_success "Server setup completed!"
print_warning "Next steps:"
print_warning "1. Upload your deployment package to this server"
print_warning "2. Extract the package: tar -xzf richesreach-production-*.tar.gz"
print_warning "3. Configure environment variables"
print_warning "4. Start services with docker-compose"
echo ""
echo " Your server is ready for RichesReach deployment!"
echo " Current directory: $(pwd)"
echo " Docker version: $(docker --version)"
echo " Docker Compose version: $(docker-compose --version)"
