# RichesReach Production Deployment Guide
This guide provides step-by-step instructions for deploying RichesReach to production.
## Prerequisites
### System Requirements
- **Server**: Ubuntu 20.04+ or CentOS 8+ (recommended: 4+ CPU cores, 8GB+ RAM, 100GB+ storage)
- **Docker**: Version 20.10+
- **Docker Compose**: Version 2.0+
- **Domain**: Registered domain name with SSL certificate
- **DNS**: Configured to point to your server
### Required Services
- **PostgreSQL**: 13+ (included in Docker setup)
- **Redis**: 6+ (included in Docker setup)
- **Nginx**: Latest (included in Docker setup)
## Pre-Deployment Setup
### 1. Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
# Install additional tools
sudo apt install -y git curl wget unzip
```
### 2. SSL Certificate Setup
```bash
# Install Certbot
sudo apt install -y certbot
# Generate SSL certificate
sudo certbot certonly --standalone -d yourdomain.com -d api.yourdomain.com
# Copy certificates to project directory
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./nginx/ssl/key.pem
sudo chown $USER:$USER ./nginx/ssl/*
```
### 3. Environment Configuration
```bash
# Run the production environment setup script
python scripts/setup_production_env.py
# Fill in the required values:
# - Database credentials
# - API keys (Alpha Vantage, News API, OpenAI)
# - Email configuration
# - AWS credentials (if using S3)
# - Sentry DSN (for error tracking)
```
## Deployment Process
### 1. Build Production Package
```bash
# Run the production build script
./scripts/build_production.sh
```
This script will:
- Clean previous builds
- Install dependencies
- Run tests
- Build backend and mobile app
- Create deployment package
### 2. Deploy to Server
```bash
# Copy deployment package to server
scp deployment/richesreach-production-*.tar.gz user@your-server:/home/user/
# SSH into server
ssh user@your-server
# Extract deployment package
tar -xzf richesreach-production-*.tar.gz
cd richesreach-production
```
### 3. Configure Production Environment
```bash
# Copy environment files
cp backend/.env.example backend/.env
cp mobile/.env.production.template mobile/.env.production
# Edit environment files with production values
nano backend/.env
nano mobile/.env.production
```
### 4. Start Services
```bash
# Start all services
docker-compose -f docker-compose.production.yml up -d
# Check service status
docker-compose -f docker-compose.production.yml ps
# View logs
docker-compose -f docker-compose.production.yml logs -f
```
### 5. Initialize Database
```bash
# Run database migrations
docker-compose -f docker-compose.production.yml exec backend python manage.py migrate
# Create superuser
docker-compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
# Collect static files
docker-compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput
```
## Post-Deployment Configuration
### 1. Configure Monitoring
```bash
# Access Grafana dashboard
open https://yourdomain.com:3000
# Default credentials: admin / (password from GRAFANA_PASSWORD env var)
# Import dashboards from monitoring/grafana/dashboards/
```
### 2. Set Up Log Rotation
```bash
# Create logrotate configuration
sudo nano /etc/logrotate.d/richesreach
# Add the following content:
/var/lib/docker/containers/*/*.log {
daily
rotate 7
compress
delaycompress
missingok
notifempty
create 0644 root root
}
```
### 3. Configure Firewall
```bash
# Configure UFW firewall
sudo ufw allow 22/tcp # SSH
sudo ufw allow 80/tcp # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```
### 4. Set Up Backup
```bash
# Create backup script
nano scripts/backup.sh
# Add the following content:
#!/bin/bash
BACKUP_DIR="/backups/richesreach"
DATE=$(date +%Y%m%d_%H%M%S)
# Create backup directory
mkdir -p $BACKUP_DIR
# Backup database
docker-compose -f docker-compose.production.yml exec -T postgres pg_dump -U $DB_USER $DB_NAME > $BACKUP_DIR/db_$DATE.sql
# Backup media files
tar -czf $BACKUP_DIR/media_$DATE.tar.gz media/
# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
# Make script executable
chmod +x scripts/backup.sh
# Add to crontab for daily backups
crontab -e
# Add: 0 2 * * * /path/to/scripts/backup.sh
```
## Monitoring and Maintenance
### 1. Health Checks
```bash
# Check application health
curl https://yourdomain.com/health/
# Check database connection
docker-compose -f docker-compose.production.yml exec backend python manage.py check --database default
# Check Redis connection
docker-compose -f docker-compose.production.yml exec redis redis-cli ping
```
### 2. Performance Monitoring
- **Grafana Dashboard**: https://yourdomain.com:3000
- **Prometheus Metrics**: https://yourdomain.com:9090
- **Application Logs**: `docker-compose logs -f backend`
### 3. Regular Maintenance
```bash
# Update application
git pull origin main
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d
# Clean up old Docker images
docker system prune -f
# Update SSL certificates
sudo certbot renew
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./nginx/ssl/key.pem
docker-compose -f docker-compose.production.yml restart nginx
```
## Troubleshooting
### Common Issues
1. **Database Connection Errors**
```bash
# Check database status
docker-compose -f docker-compose.production.yml exec postgres pg_isready -U $DB_USER
# Check database logs
docker-compose -f docker-compose.production.yml logs postgres
```
2. **SSL Certificate Issues**
```bash
# Test SSL configuration
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com
# Renew certificate
sudo certbot renew --dry-run
```
3. **Memory Issues**
```bash
# Check memory usage
docker stats
# Increase swap if needed
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```
### Log Locations
- **Application Logs**: `docker-compose logs backend`
- **Nginx Logs**: `docker-compose logs nginx`
- **Database Logs**: `docker-compose logs postgres`
- **Redis Logs**: `docker-compose logs redis`
## Security Considerations
1. **Regular Updates**: Keep all dependencies and system packages updated
2. **Firewall**: Use UFW or iptables to restrict access
3. **SSL/TLS**: Use strong SSL configuration with HSTS
4. **Backups**: Implement regular automated backups
5. **Monitoring**: Set up alerts for critical issues
6. **Access Control**: Use strong passwords and SSH keys
## Support
For deployment support:
- Check the logs first: `docker-compose logs -f`
- Review the monitoring dashboards
- Contact the development team with specific error messages
## Performance Optimization
### Database Optimization
```sql
-- Add indexes for better performance
CREATE INDEX CONCURRENTLY idx_user_portfolio_user_id ON user_portfolio(user_id);
CREATE INDEX CONCURRENTLY idx_stock_price_symbol_timestamp ON stock_price(symbol, timestamp);
```
### Redis Optimization
```bash
# Configure Redis for production
echo "maxmemory 512mb" >> redis.conf
echo "maxmemory-policy allkeys-lru" >> redis.conf
```
### Nginx Optimization
```nginx
# Add to nginx.conf for better performance
worker_processes auto;
worker_connections 1024;
keepalive_timeout 65;
gzip on;
gzip_comp_level 6;
```
This completes the production deployment guide. Follow these steps carefully to ensure a successful deployment.