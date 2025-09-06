# 🚀 AWS PostgreSQL Deployment Guide

## Overview
This guide will help you deploy RichesReach to AWS with PostgreSQL database.

## Prerequisites
- AWS Account
- AWS CLI installed and configured
- Domain name (optional but recommended)

## Step 1: Set Up AWS RDS PostgreSQL

### 1.1 Create RDS Instance
```bash
# Using AWS CLI
aws rds create-db-instance \
    --db-instance-identifier richesreach-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --engine-version 15.4 \
    --master-username postgres \
    --master-user-password YourSecurePassword123! \
    --allocated-storage 20 \
    --storage-type gp2 \
    --vpc-security-group-ids sg-xxxxxxxxx \
    --db-subnet-group-name default \
    --backup-retention-period 7 \
    --multi-az \
    --storage-encrypted \
    --enable-performance-insights
```

### 1.2 Configure Security Group
- **Inbound Rules:**
  - Type: PostgreSQL, Port: 5432, Source: Your EC2 Security Group
  - Type: PostgreSQL, Port: 5432, Source: Your IP (for initial setup)

### 1.3 Get Connection Details
```bash
aws rds describe-db-instances --db-instance-identifier richesreach-db
```

## Step 2: Set Up AWS ElastiCache Redis

### 2.1 Create Redis Cluster
```bash
aws elasticache create-cache-cluster \
    --cache-cluster-id richesreach-redis \
    --cache-node-type cache.t3.micro \
    --engine redis \
    --num-cache-nodes 1 \
    --port 6379 \
    --cache-subnet-group-name default \
    --security-group-ids sg-xxxxxxxxx
```

## Step 3: Configure Environment Variables

### 3.1 Create Production Environment File
```bash
cp production.env.template .env
```

### 3.2 Update .env with Your Values
```bash
# Database Configuration
DB_NAME=richesreach
DB_USER=postgres
DB_PASSWORD=YourSecurePassword123!
DB_HOST=richesreach-db.xxxxxxxxx.us-east-1.rds.amazonaws.com
DB_PORT=5432

# Redis Configuration
REDIS_HOST=richesreach-redis.xxxxxxxxx.cache.amazonaws.com
REDIS_PORT=6379

# Other settings...
```

## Step 4: Deploy to AWS EC2

### 4.1 Launch EC2 Instance
- **Instance Type:** t3.small or t3.medium
- **AMI:** Ubuntu Server 22.04 LTS
- **Security Group:** Allow HTTP (80), HTTPS (443), SSH (22)

### 4.2 Install Dependencies
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev -y

# Install PostgreSQL client
sudo apt install postgresql-client -y

# Install Redis client
sudo apt install redis-tools -y

# Install Node.js (for frontend)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y
```

### 4.3 Deploy Application
```bash
# Clone repository
git clone https://github.com/yourusername/RichesReach.git
cd RichesReach

# Set up Python environment
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Set up environment
cd backend
cp production.env.template .env
# Edit .env with your values

# Run migration
python migrate_to_postgres.py

# Test the application
python manage.py runserver 0.0.0.0:8000
```

## Step 5: Set Up Production Server

### 5.1 Install Gunicorn
```bash
pip install gunicorn
```

### 5.2 Create Gunicorn Service
```bash
sudo nano /etc/systemd/system/richesreach.service
```

```ini
[Unit]
Description=RichesReach Django App
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/RichesReach/backend
Environment="PATH=/home/ubuntu/RichesReach/.venv/bin"
ExecStart=/home/ubuntu/RichesReach/.venv/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 richesreach.wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

### 5.3 Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl start richesreach
sudo systemctl enable richesreach
```

## Step 6: Set Up Nginx

### 6.1 Install Nginx
```bash
sudo apt install nginx -y
```

### 6.2 Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/richesreach
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/ubuntu/RichesReach/backend/staticfiles/;
    }

    location /media/ {
        alias /home/ubuntu/RichesReach/backend/media/;
    }
}
```

### 6.3 Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/richesreach /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Step 7: Set Up SSL with Let's Encrypt

### 7.1 Install Certbot
```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 7.2 Get SSL Certificate
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

## Step 8: Set Up Monitoring

### 8.1 Install CloudWatch Agent
```bash
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb
```

### 8.2 Configure Logging
```bash
sudo nano /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
```

## Step 9: Set Up Backups

### 9.1 Database Backups
```bash
# Create backup script
sudo nano /home/ubuntu/backup_db.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h your-rds-endpoint -U postgres -d richesreach > /home/ubuntu/backups/db_backup_$DATE.sql
aws s3 cp /home/ubuntu/backups/db_backup_$DATE.sql s3://your-backup-bucket/
```

### 9.2 Set Up Cron Job
```bash
crontab -e
# Add: 0 2 * * * /home/ubuntu/backup_db.sh
```

## Step 10: Deploy Mobile App

### 10.1 Build for Production
```bash
cd mobile
npm install
npx expo build:android
npx expo build:ios
```

### 10.2 Update API Endpoints
Update your mobile app to use your production domain:
```typescript
const API_URL = 'https://yourdomain.com/graphql/';
```

## Cost Estimation

### Monthly AWS Costs (Estimated)
- **RDS PostgreSQL (db.t3.micro):** ~$15/month
- **ElastiCache Redis (cache.t3.micro):** ~$15/month
- **EC2 (t3.small):** ~$17/month
- **Data Transfer:** ~$5/month
- **Total:** ~$52/month

## Security Checklist

- ✅ RDS in private subnet
- ✅ Security groups configured
- ✅ SSL certificate installed
- ✅ Environment variables secured
- ✅ Database backups enabled
- ✅ Monitoring configured
- ✅ Firewall rules applied

## Troubleshooting

### Common Issues
1. **Database Connection Failed**
   - Check security group rules
   - Verify connection string
   - Check RDS status

2. **Redis Connection Failed**
   - Check ElastiCache security group
   - Verify Redis endpoint

3. **Static Files Not Loading**
   - Check Nginx configuration
   - Run `python manage.py collectstatic`

## Support

For issues or questions:
1. Check AWS CloudWatch logs
2. Check Django logs: `/home/ubuntu/RichesReach/backend/logs/`
3. Check Nginx logs: `/var/log/nginx/`

---

**🎉 Congratulations! Your RichesReach app is now running on AWS with PostgreSQL!**
