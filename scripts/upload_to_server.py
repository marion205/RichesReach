#!/usr/bin/env python3
"""
Simple file upload script for RichesReach deployment
This script helps you upload your deployment package to the server
"""
import os
import sys
import subprocess
from pathlib import Path
def upload_via_s3():
"""Upload deployment package to S3 for easy download"""
print(" Uploading deployment package to S3...")
deployment_package = "deployment/richesreach-production-20250908-113441.tar.gz"
if not Path(deployment_package).exists():
print(" Deployment package not found!")
return False
try:
# Upload to S3 (you'll need to configure your bucket)
bucket_name = input("Enter your S3 bucket name: ").strip()
if not bucket_name:
print(" S3 bucket name is required")
return False
# Upload file
cmd = f"aws s3 cp {deployment_package} s3://{bucket_name}/"
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
if result.returncode == 0:
print(f" Uploaded to S3: s3://{bucket_name}/richesreach-production-20250908-113441.tar.gz")
print(f"\n To download on your server, run:")
print(f"aws s3 cp s3://{bucket_name}/richesreach-production-20250908-113441.tar.gz /home/ubuntu/")
return True
else:
print(f" Upload failed: {result.stderr}")
return False
except Exception as e:
print(f" Error: {e}")
return False
def upload_via_http():
"""Create a simple HTTP server for file download"""
print(" Starting HTTP server for file download...")
deployment_package = "deployment/richesreach-production-20250908-113441.tar.gz"
if not Path(deployment_package).exists():
print(" Deployment package not found!")
return False
try:
# Get local IP address
import socket
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
print(f" Starting HTTP server on {local_ip}:8000")
print(f" On your server, run:")
print(f"wget http://{local_ip}:8000/richesreach-production-20250908-113441.tar.gz")
print(f"\n⏹ Press Ctrl+C to stop the server")
# Start HTTP server
os.chdir("deployment")
subprocess.run(["python3", "-m", "http.server", "8000"])
except KeyboardInterrupt:
print("\n Server stopped")
return True
except Exception as e:
print(f" Error: {e}")
return False
def create_download_script():
"""Create a download script for the server"""
print(" Creating download script for server...")
script_content = """#!/bin/bash
# Download script for RichesReach deployment package
echo " Downloading RichesReach deployment package..."
# Method 1: Direct download (if you have a public URL)
# wget https://your-url.com/richesreach-production-20250908-113441.tar.gz
# Method 2: Download from S3
# aws s3 cp s3://your-bucket/richesreach-production-20250908-113441.tar.gz /home/ubuntu/
# Method 3: Download from HTTP server (run this on your local machine first)
# python3 -m http.server 8000
# Then run: wget http://YOUR_LOCAL_IP:8000/richesreach-production-20250908-113441.tar.gz
echo " Extracting package..."
tar -xzf richesreach-production-20250908-113441.tar.gz
cd richesreach-production
echo " Package extracted successfully!"
echo " Next steps:"
echo "1. Configure environment variables"
echo "2. Install Docker and Docker Compose"
echo "3. Start services with docker-compose"
"""
with open("download_package.sh", "w") as f:
f.write(script_content)
print(" Created download_package.sh")
print(" Copy this script to your server and run it")
def main():
"""Main function"""
print(" RichesReach Deployment Package Upload")
print("=" * 50)
deployment_package = "deployment/richesreach-production-20250908-113441.tar.gz"
if not Path(deployment_package).exists():
print(" Deployment package not found!")
print("Please run the build script first: ./scripts/build_production_simple.sh")
return
print(f" Found deployment package: {deployment_package}")
print(f" Size: {Path(deployment_package).stat().st_size / (1024*1024):.1f} MB")
print("\nChoose upload method:")
print("1. Upload to S3 (requires AWS CLI)")
print("2. Start HTTP server for download")
print("3. Create download script")
print("4. Manual instructions")
choice = input("\nEnter your choice (1-4): ").strip()
if choice == "1":
upload_via_s3()
elif choice == "2":
upload_via_http()
elif choice == "3":
create_download_script()
elif choice == "4":
print("\n Manual Upload Instructions:")
print("1. Use your cloud provider's console to access the server")
print("2. Upload the file through their file manager")
print("3. Or use a file transfer service like WeTransfer")
print("4. Or use scp with password authentication if enabled")
print(f"\nFile to upload: {deployment_package}")
else:
print(" Invalid choice")
if __name__ == "__main__":
main()
