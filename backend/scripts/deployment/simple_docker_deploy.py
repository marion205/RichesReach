#!/usr/bin/env python3
"""
Simple Docker deployment - embed everything in user data
"""
import boto3
import time
def simple_docker_deploy():
print(" Starting Simple Docker Deployment...")
# Initialize AWS client
ec2 = boto3.client('ec2', region_name='us-east-2')
try:
# Create user data script with embedded Docker setup
user_data = '''#!/bin/bash
# Update system and install Docker
apt-get update
apt-get install -y docker.io curl
# Start Docker service
systemctl start docker
systemctl enable docker
# Create application directory
mkdir -p /app
cd /app
# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
CMD curl -f http://localhost:8000/health || exit 1
CMD ["python", "app.py"]
EOF
# Create requirements.txt
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
pydantic==2.5.0
EOF
# Create app.py
cat > app.py << 'EOF'
#!/usr/bin/env python3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from datetime import datetime
app = FastAPI(title="RichesReach AI", version="1.0.0")
app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
)
@app.on_event("startup")
async def startup_event():
print(f" RichesReach AI starting up at {datetime.now()}")
@app.get("/")
async def root():
return {
"message": "Welcome to RichesReach AI!",
"status": "healthy",
"version": "1.0.0",
"timestamp": datetime.now().isoformat()
}
@app.get("/health")
async def health():
return {
"status": "healthy",
"service": "RichesReach AI",
"timestamp": datetime.now().isoformat(),
"uptime": "running"
}
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
if __name__ == "__main__":
port = int(os.environ.get("PORT", 8000))
host = os.environ.get("HOST", "0.0.0.0")
print(f" Starting server on {host}:{port}")
uvicorn.run(app, host=host, port=port, log_level="info")
EOF
# Build and run the Docker container
echo " Building Docker image..."
docker build -t richesreach-ai .
echo " Starting Docker container..."
docker run -d --name richesreach-app -p 8000:8000 --restart unless-stopped richesreach-ai
# Wait for the application to start
echo "⏳ Waiting for application to start..."
sleep 30
# Check container status
echo " Container status:"
docker ps
echo " Container logs:"
docker logs richesreach-app
# Test the application
echo " Testing application..."
curl -f http://localhost:8000/health && echo " Health check passed" || echo " Health check failed"
# Set up auto-restart on boot
echo "@reboot cd /app && docker start richesreach-app" | crontab -
'''
# Launch new instance
print(" Launching new Docker instance...")
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
{'Key': 'Name', 'Value': 'RichesReach-Docker-Simple'},
{'Key': 'Project', 'Value': 'RichesReach-AI'},
{'Key': 'Deployment', 'Value': 'Docker-Simple'}
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
simple_docker_deploy()
