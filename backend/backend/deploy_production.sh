#!/bin/bash

# Production deployment script for RichesReach
set -e

echo "🚀 Starting RichesReach Production Deployment..."

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
if [ ! -f "manage.py" ]; then
    print_error "Please run this script from the Django project root directory"
    exit 1
fi

# Set production environment
export DJANGO_SETTINGS_MODULE=richesreach.production_settings
export PYTHONPATH=$PWD:$PYTHONPATH

print_status "Environment configured for production"

# Install production requirements
print_status "Installing production requirements..."
pip install -r requirements_production.txt

# Create log directory
sudo mkdir -p /var/log/richesreach
sudo chown $USER:$USER /var/log/richesreach

# Run database migrations
print_status "Running database migrations..."
python3 manage.py migrate

# Collect static files
print_status "Collecting static files..."
python3 manage.py collectstatic --noinput

# Populate initial data
print_status "Populating initial stock data..."
python3 simple_populate_stocks.py

# Update stock prices
print_status "Updating stock prices with real-time data..."
python3 update_stocks_manual.py --priority

# Test the system
print_status "Running system tests..."
python3 comprehensive_system_test.py

# Create systemd service files
print_status "Creating systemd service files..."

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
ExecStart=/usr/bin/python3 manage.py runserver 0.0.0.0:8001
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
ExecStart=/usr/bin/python3 start_celery_worker.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Celery beat service
sudo tee /etc/systemd/system/richesreach-celery-beat.service > /dev/null <<EOF
[Unit]
Description=RichesReach Celery Beat Scheduler
After=network.target redis.service

[Service]
Type=exec
User=$USER
Group=$USER
WorkingDirectory=$PWD
Environment=DJANGO_SETTINGS_MODULE=richesreach.production_settings
Environment=PYTHONPATH=$PWD
ExecStart=/usr/bin/python3 start_celery_worker.py beat
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable services
sudo systemctl daemon-reload
sudo systemctl enable richesreach-django
sudo systemctl enable richesreach-celery
sudo systemctl enable richesreach-celery-beat

print_status "Systemd services created and enabled"

# Start services
print_status "Starting services..."
sudo systemctl start richesreach-django
sudo systemctl start richesreach-celery
sudo systemctl start richesreach-celery-beat

# Check service status
print_status "Checking service status..."
sudo systemctl status richesreach-django --no-pager -l
sudo systemctl status richesreach-celery --no-pager -l
sudo systemctl status richesreach-celery-beat --no-pager -l

print_status "Production deployment completed successfully!"
print_warning "Don't forget to:"
print_warning "1. Configure your domain DNS to point to this server"
print_warning "2. Set up SSL certificates (Let's Encrypt recommended)"
print_warning "3. Configure your reverse proxy (nginx/Apache)"
print_warning "4. Set up monitoring and backups"
print_warning "5. Update environment variables in /etc/environment"

echo ""
print_status "Your RichesReach API is now running at:"
print_status "http://$(hostname -I | awk '{print $1}'):8001/graphql/"
print_status "Health check: curl http://$(hostname -I | awk '{print $1}'):8001/graphql/ -d '{\"query\":\"{ ping }\"}'"