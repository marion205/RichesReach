# 🚀 RichesReach Deployment Commands

## **Copy-Paste Deployment Commands**

Once you have access to your server (18.217.92.158), copy and paste these commands:

### **Step 1: Server Setup**
```bash
# Update system and install dependencies
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install additional tools
sudo apt install -y git curl wget unzip nginx certbot python3-certbot-nginx

# Create app directory
mkdir -p /home/ubuntu/richesreach
cd /home/ubuntu/richesreach
```

### **Step 2: Upload Deployment Package**

**Option A: If you have the file on your local machine, upload it via:**
- AWS EC2 console file manager
- Cloud provider's file upload feature
- Or use a file transfer service

**Option B: Download directly (if you upload to a public location):**
```bash
# Example: Download from a public URL
wget https://your-url.com/richesreach-production-20250908-113441.tar.gz
```

### **Step 3: Extract and Configure**
```bash
# Extract the deployment package
tar -xzf richesreach-production-20250908-113441.tar.gz
cd richesreach-production

# Create environment files
cp backend/production.env.template backend/.env
cp mobile/env.production.template mobile/.env.production

# Edit environment variables (you'll need to fill in your values)
nano backend/.env
```

### **Step 4: Configure Environment Variables**

**Edit backend/.env with your values:**
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

### **Step 5: Start Services**
```bash
# Start all services
docker-compose -f docker-compose.production.yml up -d

# Check service status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f
```

### **Step 6: Initialize Database**
```bash
# Run database migrations
docker-compose -f docker-compose.production.yml exec backend python manage.py migrate

# Create superuser
docker-compose -f docker-compose.production.yml exec backend python manage.py createsuperuser

# Collect static files
docker-compose -f docker-compose.production.yml exec backend python manage.py collectstatic --noinput
```

### **Step 7: Configure Firewall**
```bash
# Configure UFW firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### **Step 8: Verify Deployment**
```bash
# Check application health
curl http://localhost/health/

# Check service status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs --tail=50
```

## **🎉 Success!**

Your RichesReach app should now be running at:
- **HTTP**: http://18.217.92.158
- **HTTPS**: https://yourdomain.com (if SSL configured)

## **📊 Monitoring**

Access your monitoring dashboards:
- **Grafana**: http://18.217.92.158:3000
- **Prometheus**: http://18.217.92.158:9090

## **🔧 Troubleshooting**

### **Common Commands:**
```bash
# Restart all services
docker-compose -f docker-compose.production.yml restart

# View service logs
docker-compose -f docker-compose.production.yml logs -f backend

# Check resource usage
docker stats

# Check if services are running
docker-compose -f docker-compose.production.yml ps
```

### **If something goes wrong:**
```bash
# Stop all services
docker-compose -f docker-compose.production.yml down

# Remove all containers and start fresh
docker-compose -f docker-compose.production.yml down -v
docker-compose -f docker-compose.production.yml up -d
```

## **📱 Mobile App**

Your mobile app is built and ready in:
- `mobile-dist/_expo/static/js/ios/` - iOS bundle
- `mobile-dist/_expo/static/js/android/` - Android bundle

You can submit these to the App Store and Google Play Store.

---

**Your RichesReach app is now live and ready to serve users!** 🚀
