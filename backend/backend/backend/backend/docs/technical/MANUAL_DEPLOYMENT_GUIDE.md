# Manual Deployment Guide for RichesReach
## **Your Server Details:**
- **Server IP**: 18.217.92.158
- **Username**: ubuntu
- **Deployment Package**: `richesreach-production-20250908-113441.tar.gz` (672MB)
## **Step 1: Access Your Server**
### **Option A: AWS EC2 Console (Recommended)**
1. Go to your AWS EC2 console
2. Find your instance (IP: 18.217.92.158)
3. Click "Connect" → "EC2 Instance Connect" or "Session Manager"
4. This will open a browser-based terminal
### **Option B: Download EC2 Key Pair**
1. If you have the .pem key file, use it:
```bash
ssh -i your-key.pem ubuntu@18.217.92.158
```
### **Option C: Server Console Access**
1. Use your cloud provider's console (AWS, DigitalOcean, etc.)
2. Access the server directly through their web interface
## **Step 2: Upload Deployment Package**
### **Method 1: Direct Upload via Console**
1. In your server console, run:
```bash
# Create a directory for the app
mkdir -p /home/ubuntu/richesreach
cd /home/ubuntu/richesreach
```
2. Download the deployment package directly:
```bash
# You'll need to upload the file to a temporary location first
# Or use a file transfer service like WeTransfer, Google Drive, etc.
```
### **Method 2: Use SCP with Password (if enabled)**
```bash
# From your local machine, if password auth is enabled:
scp deployment/richesreach-production-20250908-113441.tar.gz ubuntu@18.217.92.158:/home/ubuntu/
```
### **Method 3: Use AWS S3 (Recommended)**
1. Upload your deployment package to S3:
```bash
# From your local machine:
aws s3 cp deployment/richesreach-production-20250908-113441.tar.gz s3://your-bucket/
```
2. Download from S3 on the server:
```bash
# On the server:
aws s3 cp s3://your-bucket/richesreach-production-20250908-113441.tar.gz /home/ubuntu/
```
## **Step 3: Extract and Setup**
Once you have the package on your server:
```bash
# Extract the package
cd /home/ubuntu
tar -xzf richesreach-production-20250908-113441.tar.gz
cd richesreach-production
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
# Install additional tools
sudo apt update
sudo apt install -y git curl wget unzip nginx certbot python3-certbot-nginx
```
## **Step 4: Configure Environment**
```bash
# Create environment files
cp backend/production.env.template backend/.env
cp mobile/env.production.template mobile/.env.production
# Edit the environment files
nano backend/.env
nano mobile/.env.production
```
### **Required Environment Variables:**
#### **Backend (.env):**
```bash
# Django Settings
SECRET_KEY=your-super-secret-production-key-here
DEBUG=False
DOMAIN_NAME=yourdomain.com
# Database Configuration
DB_NAME=richesreach
DB_USER=postgres
DB_PASSWORD=your-secure-database-password
DB_HOST=postgres
DB_PORT=5432
# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
# API Keys
OPENAI_API_KEY=your-openai-api-key
ALPHA_VANTAGE_API_KEY=your-alphavantage-api-key
NEWS_API_KEY=your-news-api-key
# Security
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```
#### **Mobile (.env.production):**
```bash
EXPO_PUBLIC_API_URL=https://yourdomain.com
EXPO_PUBLIC_GRAPHQL_URL=https://yourdomain.com/graphql
EXPO_PUBLIC_WS_URL=wss://yourdomain.com/ws
EXPO_PUBLIC_ENVIRONMENT=production
EXPO_PUBLIC_APP_VERSION=1.0.0
EXPO_PUBLIC_BUILD_NUMBER=1
# API Keys
EXPO_PUBLIC_ALPHA_VANTAGE_API_KEY=your-alpha-vantage-api-key
EXPO_PUBLIC_NEWS_API_KEY=your-news-api-key
```
## **Step 5: Start Services**
```bash
# Start all services
docker-compose -f docker-compose.production.yml up -d
# Check service status
docker-compose -f docker-compose.production.yml ps
# View logs
docker-compose -f docker-compose.production.yml logs -f
```
## **Step 6: Initialize Database**
```bash
# Run database migrations
docker-compose -f docker-compose.production.yml exec backend python manage.py migrate
# Create superuser
docker-compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
# Collect static files
docker-compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput
```
## **Step 7: Configure SSL (Optional)**
```bash
# Install SSL certificate
sudo certbot certonly --standalone -d yourdomain.com
# Copy certificates
sudo mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem nginx/ssl/key.pem
sudo chown ubuntu:ubuntu nginx/ssl/*
# Restart services
docker-compose -f docker-compose.production.yml restart
```
## **Step 8: Verify Deployment**
```bash
# Check application health
curl http://localhost/health/
# Check service status
docker-compose -f docker-compose.production.yml ps
# View logs
docker-compose -f docker-compose.production.yml logs --tail=50
```
## **Step 9: Configure Firewall**
```bash
# Configure UFW firewall
sudo ufw allow 22/tcp # SSH
sudo ufw allow 80/tcp # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```
## ** Success!**
Your RichesReach app should now be running at:
- **HTTP**: http://18.217.92.158
- **HTTPS**: https://yourdomain.com (if SSL configured)
## ** Monitoring**
Access your monitoring dashboards:
- **Grafana**: http://18.217.92.158:3000
- **Prometheus**: http://18.217.92.158:9090
## ** Troubleshooting**
### **Common Issues:**
1. **Services not starting:**
```bash
docker-compose -f docker-compose.production.yml logs
```
2. **Database connection errors:**
```bash
docker-compose -f docker-compose.production.yml exec postgres pg_isready
```
3. **Port conflicts:**
```bash
sudo netstat -tulpn | grep :80
```
### **Useful Commands:**
```bash
# Restart all services
docker-compose -f docker-compose.production.yml restart
# View service logs
docker-compose -f docker-compose.production.yml logs -f backend
# Check resource usage
docker stats
# Update application
git pull origin main
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d
```
## ** Support**
If you need help:
1. Check the logs: `docker-compose logs -f`
2. Review the monitoring dashboards
3. Contact the development team with specific error messages
**Your RichesReach app is now live and ready to serve users!** 
