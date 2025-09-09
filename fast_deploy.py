#!/usr/bin/env python3
"""
Fast deployment script - uploads and deploys in one go
"""
import subprocess
import time
import os

def fast_deploy():
    print("🚀 Starting Fast Deployment...")
    
    server_ip = "18.217.92.158"
    deployment_package = "deployment/richesreach-production-fresh.tar.gz"
    
    if not os.path.exists(deployment_package):
        print(f"❌ Deployment package not found: {deployment_package}")
        return False
    
    print(f"📦 Uploading {deployment_package} to server...")
    
    try:
        # Upload the package
        upload_cmd = [
            "scp", 
            "-o", "StrictHostKeyChecking=no",
            deployment_package, 
            f"ubuntu@{server_ip}:/tmp/"
        ]
        
        result = subprocess.run(upload_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Upload failed: {result.stderr}")
            return False
        
        print("✅ Package uploaded successfully")
        
        # Create deployment commands
        deploy_commands = f"""
# Update system
sudo apt update -y

# Install Docker
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker ubuntu
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Create app directory
sudo mkdir -p /opt/richesreach
cd /opt/richesreach

# Stop any existing containers
sudo docker-compose down 2>/dev/null || true

# Extract the package
sudo tar -xzf /tmp/richesreach-production-fresh.tar.gz

# Find the extracted directory
EXTRACTED_DIR=$(find . -name "richesreach-production*" -type d | head -1)
if [ -n "$EXTRACTED_DIR" ]; then
    sudo mv "$EXTRACTED_DIR"/* .
    sudo rmdir "$EXTRACTED_DIR"
fi

# Set permissions
sudo chown -R ubuntu:ubuntu .

# Create basic environment file
cat > backend/.env << 'EOF'
SECRET_KEY=your-super-secret-production-key-here
DEBUG=False
DOMAIN_NAME=18.217.92.158

# Database Configuration
DB_NAME=richesreach
DB_USER=postgres
DB_PASSWORD=securepassword123
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
DEFAULT_FROM_EMAIL=noreply@18.217.92.158

# API Keys (you'll need to add these)
OPENAI_API_KEY=your-openai-api-key
ALPHA_VANTAGE_API_KEY=your-alphavantage-api-key
NEWS_API_KEY=your-news-api-key

# Security
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
EOF

# Start services
sudo docker-compose -f docker-compose.production.yml up -d

# Wait a moment for services to start
sleep 10

# Check if services are running
sudo docker-compose -f docker-compose.production.yml ps

echo "🎉 Deployment completed!"
echo "🌐 Your app should be available at: http://{server_ip}"
"""
        
        # Execute deployment commands
        print("🔧 Deploying application...")
        
        ssh_cmd = [
            "ssh", 
            "-o", "StrictHostKeyChecking=no",
            f"ubuntu@{server_ip}",
            deploy_commands
        ]
        
        result = subprocess.run(ssh_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Deployment failed: {result.stderr}")
            return False
        
        print("✅ Deployment completed!")
        print(f"🌐 Your app should be available at: http://{server_ip}")
        print(f"🏥 Health check: http://{server_ip}/health/")
        
        return True
        
    except Exception as e:
        print(f"❌ Fast deployment failed: {e}")
        return False

if __name__ == "__main__":
    fast_deploy()
