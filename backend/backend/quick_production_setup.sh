#!/bin/bash

# Quick Production Setup Script for RichesReach
# This script will help you set up a production environment quickly

set -e

echo "🚀 RichesReach Quick Production Setup"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please don't run this script as root. Run as a regular user with sudo privileges."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    print_error "Please run this script from the Django project root directory"
    exit 1
fi

print_info "Starting production setup..."

# Step 1: Update system
print_info "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Step 2: Install required packages
print_info "Installing required packages..."
sudo apt install -y python3.10 python3.10-venv python3-pip postgresql postgresql-contrib redis-server nginx git

# Step 3: Start and enable services
print_info "Starting and enabling services..."
sudo systemctl start postgresql redis-server nginx
sudo systemctl enable postgresql redis-server nginx

# Step 4: Configure PostgreSQL
print_info "Configuring PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE richesreach_prod;" || true
sudo -u postgres psql -c "CREATE USER richesreach_user WITH PASSWORD 'secure_password_123';" || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE richesreach_prod TO richesreach_user;" || true

# Step 5: Configure Redis
print_info "Configuring Redis..."
sudo sed -i 's/^# bind localhost/bind localhost/' /etc/redis/redis.conf
sudo systemctl restart redis-server

# Step 6: Create virtual environment
print_info "Creating virtual environment..."
python3.10 -m venv venv
source venv/bin/activate

# Step 7: Install dependencies
print_info "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements_production.txt

# Step 8: Create production environment file
print_info "Creating production environment file..."
if [ ! -f ".env.production" ]; then
    cp env_production_template.txt .env.production
    print_warning "Please edit .env.production with your actual values:"
    print_warning "- SECRET_KEY: Generate a new secret key"
    print_warning "- DB_PASSWORD: Use the password you set for richesreach_user"
    print_warning "- API keys: Update with your actual API keys"
    print_warning "- ALLOWED_HOSTS: Update with your domain"
fi

# Step 9: Set up Django
print_info "Setting up Django..."
export DJANGO_SETTINGS_MODULE=richesreach.production_settings
python3 manage.py migrate
python3 manage.py collectstatic --noinput

# Step 10: Populate initial data
print_info "Populating initial data..."
python3 simple_populate_stocks.py

# Step 11: Test the system
print_info "Running system tests..."
python3 comprehensive_system_test.py

# Step 12: Create systemd services
print_info "Creating systemd services..."

# Django service
sudo tee /etc/systemd/system/richesreach-django.service > /dev/null <<EOF
[Unit]
Description=RichesReach Django Application
After=network.target

[Service]
Type=exec
User=$USER
Group=$USER
WorkingDirectory=$PWD
Environment=DJANGO_SETTINGS_MODULE=richesreach.production_settings
Environment=PYTHONPATH=$PWD
ExecStart=$PWD/venv/bin/python manage.py runserver 0.0.0.0:8001
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Celery worker service
sudo tee /etc/systemd/system/richesreach-celery.service > /dev/null <<EOF
[Unit]
Description=RichesReach Celery Worker
After=network.target redis.service

[Service]
Type=exec
User=$USER
Group=$USER
WorkingDirectory=$PWD
Environment=DJANGO_SETTINGS_MODULE=richesreach.production_settings
Environment=PYTHONPATH=$PWD
ExecStart=$PWD/venv/bin/python start_celery_worker.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Step 13: Configure Nginx
print_info "Configuring Nginx..."
sudo cp nginx_richesreach.conf /etc/nginx/sites-available/richesreach
sudo ln -sf /etc/nginx/sites-available/richesreach /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Step 14: Enable and start services
print_info "Enabling and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable richesreach-django richesreach-celery
sudo systemctl start richesreach-django richesreach-celery

# Step 15: Configure firewall
print_info "Configuring firewall..."
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Step 16: Test services
print_info "Testing services..."
sleep 5

# Test Django
if curl -s http://process.env.MARKET_DATA_URL || "localhost:8001"/graphql/ -d '{"query":"{ ping }"}' | grep -q "pong"; then
    print_status "Django service is running correctly"
else
    print_warning "Django service may not be running correctly"
fi

# Test Redis
if redis-cli ping | grep -q "PONG"; then
    print_status "Redis is running correctly"
else
    print_warning "Redis may not be running correctly"
fi

# Test PostgreSQL
if sudo -u postgres psql -c "SELECT 1;" > /dev/null 2>&1; then
    print_status "PostgreSQL is running correctly"
else
    print_warning "PostgreSQL may not be running correctly"
fi

# Test Nginx
if sudo nginx -t; then
    print_status "Nginx configuration is valid"
    sudo systemctl reload nginx
else
    print_warning "Nginx configuration has issues"
fi

# Final status
print_status "Production setup completed!"
echo ""
print_info "Your RichesReach API is now running at:"
print_info "http://$(hostname -I | awk '{print $1}'):8001/graphql/"
echo ""
print_warning "Next steps:"
print_warning "1. Edit .env.production with your actual values"
print_warning "2. Set up your domain DNS to point to this server"
print_warning "3. Install SSL certificate: sudo certbot --nginx -d yourdomain.com"
print_warning "4. Update ALLOWED_HOSTS in .env.production with your domain"
print_warning "5. Restart services: sudo systemctl restart richesreach-django"
echo ""
print_info "To check service status:"
print_info "sudo systemctl status richesreach-django"
print_info "sudo systemctl status richesreach-celery"
print_info "sudo systemctl status nginx"
echo ""
print_info "To view logs:"
print_info "sudo journalctl -u richesreach-django -f"
print_info "sudo journalctl -u richesreach-celery -f"
echo ""
print_status "Production setup complete! 🎉"
