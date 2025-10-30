#!/bin/bash
# Production Deployment Script for RichesReach
# This script deploys the app to a production server
set -e # Exit on any error
echo " Starting RichesReach Production Deployment..."
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
# Configuration
SERVER_USER="ubuntu" # Change this to your server user
SERVER_HOST="your-server.com" # Change this to your server hostname/IP
SERVER_PATH="/home/ubuntu/richesreach" # Change this to your deployment path
DEPLOYMENT_PACKAGE="deployment/richesreach-production-20250908-113441.tar.gz"
# Check if deployment package exists
if [ ! -f "$DEPLOYMENT_PACKAGE" ]; then
print_error "Deployment package not found: $DEPLOYMENT_PACKAGE"
print_status "Please run the build script first: ./scripts/build_production_simple.sh"
exit 1
fi
# Function to execute commands on remote server
execute_remote() {
ssh $SERVER_USER@$SERVER_HOST "$1"
}
# Function to copy files to remote server
copy_to_server() {
scp "$1" $SERVER_USER@$SERVER_HOST:"$2"
}
# Function to copy directory to remote server
copy_dir_to_server() {
scp -r "$1" $SERVER_USER@$SERVER_HOST:"$2"
}
# Step 1: Copy deployment package to server
deploy_package() {
print_status "Step 1: Copying deployment package to server..."
# Create deployment directory on server
execute_remote "mkdir -p $SERVER_PATH"
# Copy deployment package
copy_to_server "$DEPLOYMENT_PACKAGE" "$SERVER_PATH/"
# Extract package on server
execute_remote "cd $SERVER_PATH && tar -xzf $(basename $DEPLOYMENT_PACKAGE)"
print_success "Deployment package copied and extracted"
}
# Step 2: Install server dependencies
install_server_dependencies() {
print_status "Step 2: Installing server dependencies..."
# Update system packages
execute_remote "sudo apt update && sudo apt upgrade -y"
# Install Docker
execute_remote "curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh"
execute_remote "sudo usermod -aG docker $SERVER_USER"
# Install Docker Compose
execute_remote "sudo curl -L \"https://github.com/docker/compose/releases/latest/download/docker-compose-\$(uname -s)-\$(uname -m)\" -o /usr/local/bin/docker-compose"
execute_remote "sudo chmod +x /usr/local/bin/docker-compose"
# Install additional tools
execute_remote "sudo apt install -y git curl wget unzip nginx certbot python3-certbot-nginx"
print_success "Server dependencies installed"
}
# Step 3: Configure SSL certificates
configure_ssl() {
print_status "Step 3: Configuring SSL certificates..."
# Get domain name from user
read -p "Enter your domain name (e.g., yourdomain.com): " DOMAIN_NAME
if [ -z "$DOMAIN_NAME" ]; then
print_warning "No domain provided, skipping SSL configuration"
return
fi
# Generate SSL certificate
execute_remote "sudo certbot certonly --standalone -d $DOMAIN_NAME -d api.$DOMAIN_NAME --non-interactive --agree-tos --email admin@$DOMAIN_NAME"
# Copy certificates to project directory
execute_remote "sudo mkdir -p $SERVER_PATH/nginx/ssl"
execute_remote "sudo cp /etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem $SERVER_PATH/nginx/ssl/cert.pem"
execute_remote "sudo cp /etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem $SERVER_PATH/nginx/ssl/key.pem"
execute_remote "sudo chown $SERVER_USER:$SERVER_USER $SERVER_PATH/nginx/ssl/*"
print_success "SSL certificates configured"
}
# Step 4: Configure environment variables
configure_environment() {
print_status "Step 4: Configuring environment variables..."
# Copy environment templates
execute_remote "cd $SERVER_PATH/richesreach-production && cp backend/production.env.template backend/.env"
execute_remote "cd $SERVER_PATH/richesreach-production && cp mobile/env.production.template mobile/.env.production"
print_warning "Please edit the environment files on the server:"
print_warning "1. Edit backend/.env with your production values"
print_warning "2. Edit mobile/.env.production with your production values"
print_warning "3. Run: nano backend/.env"
print_warning "4. Run: nano mobile/.env.production"
read -p "Press Enter when you've configured the environment variables..."
}
# Step 5: Start production services
start_services() {
print_status "Step 5: Starting production services..."
# Start Docker services
execute_remote "cd $SERVER_PATH/richesreach-production && docker-compose -f docker-compose.production.yml up -d"
# Wait for services to start
print_status "Waiting for services to start..."
sleep 30
# Check service status
execute_remote "cd $SERVER_PATH/richesreach-production && docker-compose -f docker-compose.production.yml ps"
print_success "Production services started"
}
# Step 6: Initialize database
initialize_database() {
print_status "Step 6: Initializing database..."
# Run database migrations
execute_remote "cd $SERVER_PATH/richesreach-production && docker-compose -f docker-compose.production.yml exec backend python manage.py migrate"
# Create superuser
print_warning "Creating superuser account..."
execute_remote "cd $SERVER_PATH/richesreach-production && docker-compose -f docker-compose.production.yml exec backend python manage.py createsuperuser"
# Collect static files
execute_remote "cd $SERVER_PATH/richesreach-production && docker-compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput"
print_success "Database initialized"
}
# Step 7: Configure Nginx
configure_nginx() {
print_status "Step 7: Configuring Nginx..."
# Copy Nginx configuration
execute_remote "sudo cp $SERVER_PATH/richesreach-production/nginx/nginx.production.conf /etc/nginx/nginx.conf"
# Test Nginx configuration
execute_remote "sudo nginx -t"
# Restart Nginx
execute_remote "sudo systemctl restart nginx"
execute_remote "sudo systemctl enable nginx"
print_success "Nginx configured"
}
# Step 8: Verify deployment
verify_deployment() {
print_status "Step 8: Verifying deployment..."
# Check service health
execute_remote "cd $SERVER_PATH/richesreach-production && docker-compose -f docker-compose.production.yml ps"
# Check application health
execute_remote "curl -f process.env.API_BASE_URL || "http://localhost"/health/ || echo 'Health check failed'"
# Check logs
execute_remote "cd $SERVER_PATH/richesreach-production && docker-compose -f docker-compose.production.yml logs --tail=50"
print_success "Deployment verification completed"
}
# Main deployment process
main() {
print_status "Starting production deployment process..."
# Get server details from user
read -p "Enter server hostname/IP: " SERVER_HOST
read -p "Enter server username (default: ubuntu): " SERVER_USER
SERVER_USER=${SERVER_USER:-ubuntu}
if [ -z "$SERVER_HOST" ]; then
print_error "Server hostname/IP is required"
exit 1
fi
print_status "Deploying to: $SERVER_USER@$SERVER_HOST"
# Test SSH connection
print_status "Testing SSH connection..."
if ! execute_remote "echo 'SSH connection successful'"; then
print_error "SSH connection failed. Please check your server details and SSH keys."
exit 1
fi
# Run deployment steps
deploy_package
install_server_dependencies
configure_ssl
configure_environment
start_services
initialize_database
configure_nginx
verify_deployment
print_success " Production deployment completed successfully!"
print_status "Your RichesReach app is now live at: https://$DOMAIN_NAME"
print_status "Next steps:"
print_status "1. Configure your domain DNS to point to this server"
print_status "2. Set up monitoring and alerts"
print_status "3. Configure backup procedures"
print_status "4. Test all features thoroughly"
}
# Run main function
main "$@"
