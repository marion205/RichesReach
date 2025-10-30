#!/usr/bin/env python3
"""
Docker-based deployment to AWS EC2
"""
import boto3
import time
import zipfile
import tempfile
from pathlib import Path
def docker_deploy():
print(" Starting Docker-based Deployment...")
# Initialize AWS client
ec2 = boto3.client('ec2', region_name='us-east-2')
try:
# Create deployment package with Docker files
print(" Creating Docker deployment package...")
with tempfile.TemporaryDirectory() as temp_dir:
package_path = Path(temp_dir) / "docker-app.zip"
# Create the zip file with all necessary files
with zipfile.ZipFile(package_path, 'w') as zipf:
# Add Dockerfile
zipf.writestr("Dockerfile", '''# Use Python 3.11 slim image
FROM python:3.11-slim
# Set working directory
WORKDIR /app
# Install system dependencies
RUN apt-get update && apt-get install -y \\
curl \\
&& rm -rf /var/lib/apt/lists/*
# Copy requirements first for better caching
COPY requirements.txt .
# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Copy application code
COPY app.py .
# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
# Expose port
EXPOSE 8000
# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
CMD curl -f http://process.env.API_BASE_URL || "localhost:8000"/health || exit 1
# Run the application
CMD ["python", "app.py"]
''')
# Add requirements.txt
zipf.writestr("requirements.txt", '''fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
''')
# Add app.py
zipf.writestr("app.py", '''#!/usr/bin/env python3
"""
RichesReach AI - FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import time
from datetime import datetime
# Create FastAPI app
app = FastAPI(
title="RichesReach AI",
description="AI-powered financial platform",
version="1.0.0",
docs_url="/docs",
redoc_url="/redoc"
)
# Add CORS middleware
app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
)
# Startup event
@app.on_event("startup")
async def startup_event():
print(f" RichesReach AI starting up at {datetime.now()}")
print(" Application is ready!")
# Root endpoint
@app.get("/")
async def root():
return {
"message": "Welcome to RichesReach AI!",
"status": "healthy",
"version": "1.0.0",
"timestamp": datetime.now().isoformat()
}
# Health check endpoint
@app.get("/health")
async def health():
return {
"status": "healthy",
"service": "RichesReach AI",
"timestamp": datetime.now().isoformat(),
"uptime": "running"
}
# API test endpoint
@app.get("/api/test")
async def test():
return {
"message": "API is working perfectly!",
"timestamp": datetime.now().isoformat(),
"features": [
"AI-powered recommendations",
"Real-time portfolio tracking",
"Financial insights",
"Risk assessment"
]
}
# Status endpoint
@app.get("/api/status")
async def status():
return {
"service": "RichesReach AI",
"status": "operational",
"version": "1.0.0",
"environment": os.environ.get("ENVIRONMENT", "production"),
"timestamp": datetime.now().isoformat()
}
if __name__ == "__main__":
port = int(os.environ.get("PORT", 8000))
host = os.environ.get("HOST", "0.0.0.0")
print(f" Starting server on {host}:{port}")
uvicorn.run(
app, 
host=host, 
port=port,
log_level="info",
access_log=True
)
''')
# Add docker-compose.yml
zipf.writestr("docker-compose.yml", '''version: '3.8'
services:
richesreach-ai:
build: .
ports:
- "8000:8000"
environment:
- ENVIRONMENT=production
- PORT=8000
- HOST=0.0.0.0
restart: unless-stopped
healthcheck:
test: ["CMD", "curl", "-f", "http://process.env.API_BASE_URL || "localhost:8000"/health"]
interval: 30s
timeout: 10s
retries: 3
start_period: 40s
''')
# Create user data script for Docker deployment
user_data = f'''#!/bin/bash
# Update system
apt-get update
apt-get install -y docker.io docker-compose curl
# Start Docker service
systemctl start docker
systemctl enable docker
# Add ubuntu user to docker group
usermod -aG docker ubuntu
# Download and extract the application
cd /home/ubuntu
curl -o app.zip https://github.com/your-repo/richesreach/archive/main.zip
unzip -o app.zip
cd richesreach-main
# Build and run the Docker container
docker-compose up -d --build
# Wait for the application to start
sleep 30
# Check if the container is running
docker ps
docker logs richesreach-ai_richesreach-ai_1
# Test the application
curl -f http://process.env.API_BASE_URL || "localhost:8000"/health || echo "Health check failed"
# Set up auto-restart on boot
echo "@reboot cd /home/ubuntu/richesreach-main && docker-compose up -d" | crontab -
'''
# Launch new instance
print(" Launching new Docker-based instance...")
response = ec2.run_instances(
ImageId='ami-019b9d054031a0268', # Ubuntu 20.04 LTS
MinCount=1,
MaxCount=1,
InstanceType='t2.micro',
SecurityGroupIds=['sg-015c977be8595f590'],
UserData=user_data,
TagSpecifications=[
{
'ResourceType': 'instance',
'Tags': [
{'Key': 'Name', 'Value': 'RichesReach-Docker'},
{'Key': 'Project', 'Value': 'RichesReach-AI'},
{'Key': 'Deployment', 'Value': 'Docker'}
]
}
]
)
instance_id = response['Instances'][0]['InstanceId']
print(f" Instance launched: {instance_id}")
# Wait for instance to be running
print("⏳ Waiting for instance to be running...")
waiter = ec2.get_waiter('instance_running')
waiter.wait(InstanceIds=[instance_id])
# Get public IP
response = ec2.describe_instances(InstanceIds=[instance_id])
public_ip = response['Reservations'][0]['Instances'][0]['PublicIpAddress']
print(f" Public IP: {public_ip}")
print(f" Test URL: http://{public_ip}:8000/health")
print("⏳ Docker container is building and starting...")
print(" Wait 3-5 minutes for the Docker container to fully start")
return public_ip
except Exception as e:
print(f" Error: {e}")
return None
if __name__ == "__main__":
docker_deploy()
