# 🚀 RichesReach Production Setup Guide

## Overview
This guide will help you deploy RichesReach to a production server with PostgreSQL, Redis, Celery, and Nginx.

## Prerequisites
- Ubuntu 20.04+ or CentOS 8+ server
- Root or sudo access
- Domain name pointing to your server
- Basic knowledge of Linux server administration

## Step 1: Server Preparation

### Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### Install Required Packages
```bash
# Install Python 3.10+
sudo apt install python3.10 python3.10-venv python3-pip -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Install Redis
sudo apt install redis-server -y

# Install Nginx
sudo apt install nginx -y

# Install Git
sudo apt install git -y
```

## Step 2: Database Setup

### Configure PostgreSQL
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE richesreach_prod;
CREATE USER richesreach_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE richesreach_prod TO richesreach_user;
\q
```

### Configure Redis
```bash
# Edit Redis config
sudo nano /etc/redis/redis.conf

# Set these values:
bind 127.0.0.1
port 6379
save 900 1
save 300 10
save 60 10000

# Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

## Step 3: Application Deployment

### Clone Repository
```bash
cd /opt
sudo git clone https://github.com/yourusername/RichesReach.git
sudo chown -R $USER:$USER /opt/RichesReach
cd /opt/RichesReach/backend/backend
```

### Create Virtual Environment
```bash
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

### Install Dependencies
```bash
pip install -r requirements_production.txt
```

### Configure Environment
```bash
# Copy environment template
cp env_production_template.txt .env.production

# Edit with your values
nano .env.production
```

### Run Deployment Script
```bash
chmod +x deploy_production.sh
./deploy_production.sh
```

## Step 4: SSL Certificate Setup

### Install Certbot
```bash
sudo apt install certbot python3-certbot-nginx -y
```

### Obtain SSL Certificate
```bash
sudo certbot --nginx -d api.richesreach.com -d www.richesreach.com
```

### Auto-renewal
```bash
sudo crontab -e
# Add this line:
0 12 * * * /usr/bin/certbot renew --quiet
```

## Step 5: Nginx Configuration

### Copy Nginx Config
```bash
sudo cp nginx_richesreach.conf /etc/nginx/sites-available/richesreach
sudo ln -s /etc/nginx/sites-available/richesreach /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
```

### Test and Reload Nginx
```bash
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl enable nginx
```

## Step 6: Firewall Configuration

### Configure UFW
```bash
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## Step 7: Monitoring and Maintenance

### Check Service Status
```bash
sudo systemctl status richesreach-django
sudo systemctl status richesreach-celery
sudo systemctl status richesreach-celery-beat
sudo systemctl status redis-server
sudo systemctl status postgresql
sudo systemctl status nginx
```

### View Logs
```bash
# Application logs
sudo journalctl -u richesreach-django -f
sudo journalctl -u richesreach-celery -f

# Nginx logs
sudo tail -f /var/log/nginx/richesreach_access.log
sudo tail -f /var/log/nginx/richesreach_error.log

# Django logs
tail -f /var/log/richesreach/django.log
```

### Update Stock Data
```bash
cd /opt/RichesReach/backend/backend
source venv/bin/activate
python3 update_stocks_manual.py --priority
```

## Step 8: Backup Strategy

### Database Backup
```bash
# Create backup script
sudo nano /opt/backup_database.sh

#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U richesreach_user richesreach_prod > /opt/backups/richesreach_$DATE.sql
find /opt/backups -name "*.sql" -mtime +7 -delete

# Make executable
sudo chmod +x /opt/backup_database.sh

# Add to crontab
sudo crontab -e
# Add: 0 2 * * * /opt/backup_database.sh
```

## Step 9: Performance Optimization

### PostgreSQL Tuning
```bash
sudo nano /etc/postgresql/14/main/postgresql.conf

# Add these settings:
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100

sudo systemctl restart postgresql
```

### Redis Tuning
```bash
sudo nano /etc/redis/redis.conf

# Add these settings:
maxmemory 256mb
maxmemory-policy allkeys-lru
tcp-keepalive 60

sudo systemctl restart redis-server
```

## Step 10: Security Hardening

### Fail2Ban Setup
```bash
sudo apt install fail2ban -y

sudo nano /etc/fail2ban/jail.local
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true

sudo systemctl restart fail2ban
```

### Regular Security Updates
```bash
# Add to crontab
sudo crontab -e
# Add: 0 3 * * 0 apt update && apt upgrade -y
```

## Troubleshooting

### Common Issues

1. **Service won't start**
   ```bash
   sudo journalctl -u richesreach-django -n 50
   ```

2. **Database connection issues**
   ```bash
   sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
   ```

3. **Redis connection issues**
   ```bash
   redis-cli ping
   ```

4. **Nginx configuration errors**
   ```bash
   sudo nginx -t
   ```

### Performance Monitoring
```bash
# Install monitoring tools
sudo apt install htop iotop nethogs -y

# Monitor system resources
htop
iotop
nethogs
```

## Production Checklist

- [ ] Server updated and secured
- [ ] PostgreSQL installed and configured
- [ ] Redis installed and running
- [ ] Application deployed and running
- [ ] SSL certificate installed
- [ ] Nginx configured and running
- [ ] Firewall configured
- [ ] Monitoring set up
- [ ] Backup strategy implemented
- [ ] Performance optimized
- [ ] Security hardened

## Support

For issues or questions:
1. Check the logs first
2. Verify all services are running
3. Test the API endpoints
4. Check system resources

## API Endpoints

- **GraphQL**: `https://api.richesreach.com/graphql/`
- **Health Check**: `https://api.richesreach.com/health/`
- **Admin**: `https://api.richesreach.com/admin/`

Your RichesReach production server is now ready! 🎉
