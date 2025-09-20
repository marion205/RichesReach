#!/usr/bin/env python3
"""
Quick deployment script for RichesReach - faster approach
"""
import boto3
import subprocess
import time
import os
from pathlib import Path
def quick_deploy():
print(" Starting Quick Deployment to AWS...")
# Initialize AWS client
ec2 = boto3.client('ec2', region_name='us-east-2')
try:
# Get the existing instance
response = ec2.describe_instances(
InstanceIds=['i-0cf93dd9f7f54ce93']
)
instance = response['Reservations'][0]['Instances'][0]
public_ip = instance['PublicIpAddress']
state = instance['State']['Name']
print(f" Instance Status: {state}")
print(f" Public IP: {public_ip}")
if state != 'running':
print(" Instance is not running")
return False
# Use the most recent deployment package
deployment_package = "deployment/richesreach-production-fresh.tar.gz"
if not os.path.exists(deployment_package):
print(f" Deployment package not found: {deployment_package}")
return False
print(f" Using deployment package: {deployment_package}")
# Create a simple deployment script
deploy_script = f"""#!/bin/bash
set -e
echo " Starting quick deployment..."
# Update system
sudo apt update -y
# Install Docker if not present
if ! command -v docker &> /dev/null; then
echo " Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
fi
# Install Docker Compose if not present
if ! command -v docker-compose &> /dev/null; then
echo " Installing Docker Compose..."
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
fi
# Create app directory
sudo mkdir -p /opt/richesreach
cd /opt/richesreach
# Stop any existing containers
sudo docker-compose down 2>/dev/null || true
# Remove old files
sudo rm -rf richesreach-production 2>/dev/null || true
echo " System ready for deployment"
echo " Next steps:"
echo "1. Upload deployment package to /opt/richesreach/"
echo "2. Extract and configure"
echo "3. Start services"
# Create a simple health check endpoint
echo "#!/bin/bash" > /tmp/health-check.sh
echo "curl -f http://localhost:8000/health || exit 1" >> /tmp/health-check.sh
chmod +x /tmp/health-check.sh
echo " Quick setup completed!"
"""
# Save the script
with open('/tmp/quick_setup.sh', 'w') as f:
f.write(deploy_script)
print(" Quick deployment script created")
print(f" Your server is ready at: {public_ip}")
print("\n Next steps:")
print("1. Upload the deployment package to your server")
print("2. SSH into the server and run the setup")
print("3. Extract and start the application")
print(f"\n SSH command:")
print(f"ssh ubuntu@{public_ip}")
print(f"\n Upload command (from your local machine):")
print(f"scp {deployment_package} ubuntu@{public_ip}:/opt/richesreach/")
return True
except Exception as e:
print(f" Quick deployment failed: {e}")
return False
if __name__ == "__main__":
quick_deploy()
