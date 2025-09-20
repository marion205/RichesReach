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
    print("☁️ Uploading deployment package to S3...")
    
    deployment_package = "deployment/richesreach-production-20250908-113441.tar.gz"
    if not Path(deployment_package).exists():
        print("❌ Deployment package not found!")
        return False
    
    try:
        # Upload to S3 (you'll need to configure your bucket)
        bucket_name = input("Enter your S3 bucket name: ").strip()
        if not bucket_name:
            print("❌ Bucket name is required!")
            return False
        
        # Upload the file
        s3_key = f"deployments/richesreach-production.tar.gz"
        cmd = f"aws s3 cp {deployment_package} s3://{bucket_name}/{s3_key}"
        
        print(f"📤 Uploading to s3://{bucket_name}/{s3_key}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Upload successful!")
            print(f"🌐 Download URL: https://{bucket_name}.s3.amazonaws.com/{s3_key}")
            return True
        else:
            print(f"❌ Upload failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error uploading to S3: {e}")
        return False

def upload_via_scp():
    """Upload deployment package via SCP"""
    print("📡 Uploading deployment package via SCP...")
    
    deployment_package = "deployment/richesreach-production-20250908-113441.tar.gz"
    if not Path(deployment_package).exists():
        print("❌ Deployment package not found!")
        return False
    
    try:
        # Get server details
        server_host = input("Enter server hostname/IP: ").strip()
        if not server_host:
            print("❌ Server hostname is required!")
            return False
        
        username = input("Enter username: ").strip()
        if not username:
            print("❌ Username is required!")
            return False
        
        remote_path = input("Enter remote path (default: /home/{username}/): ").strip()
        if not remote_path:
            remote_path = f"/home/{username}/"
        
        # Upload the file
        cmd = f"scp {deployment_package} {username}@{server_host}:{remote_path}"
        print(f"📤 Uploading to {username}@{server_host}:{remote_path}")
        
        result = subprocess.run(cmd, shell=True)
        
        if result.returncode == 0:
            print("✅ Upload successful!")
            print(f"📁 File uploaded to: {remote_path}")
            return True
        else:
            print("❌ Upload failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error uploading via SCP: {e}")
        return False

def upload_via_rsync():
    """Upload deployment package via rsync"""
    print("🔄 Uploading deployment package via rsync...")
    
    deployment_package = "deployment/richesreach-production-20250908-113441.tar.gz"
    if not Path(deployment_package).exists():
        print("❌ Deployment package not found!")
        return False
    
    try:
        # Get server details
        server_host = input("Enter server hostname/IP: ").strip()
        if not server_host:
            print("❌ Server hostname is required!")
            return False
        
        username = input("Enter username: ").strip()
        if not username:
            print("❌ Username is required!")
            return False
        
        remote_path = input("Enter remote path (default: /home/{username}/): ").strip()
        if not remote_path:
            remote_path = f"/home/{username}/"
        
        # Upload the file
        cmd = f"rsync -avz --progress {deployment_package} {username}@{server_host}:{remote_path}"
        print(f"📤 Uploading to {username}@{server_host}:{remote_path}")
        
        result = subprocess.run(cmd, shell=True)
        
        if result.returncode == 0:
            print("✅ Upload successful!")
            print(f"📁 File uploaded to: {remote_path}")
            return True
        else:
            print("❌ Upload failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error uploading via rsync: {e}")
        return False

def main():
    """Main function"""
    print("🚀 RichesReach Deployment Upload Tool")
    print("=" * 50)
    print("Choose your upload method:")
    print("1. Upload to S3 (recommended for AWS)")
    print("2. Upload via SCP")
    print("3. Upload via rsync")
    print("4. Exit")
    
    while True:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            success = upload_via_s3()
            break
        elif choice == "2":
            success = upload_via_scp()
            break
        elif choice == "3":
            success = upload_via_rsync()
            break
        elif choice == "4":
            print("👋 Goodbye!")
            return
        else:
            print("❌ Invalid choice. Please enter 1-4.")
    
    if success:
        print("\n🎉 Upload completed successfully!")
        print("\nNext steps:")
        print("1. SSH into your server")
        print("2. Extract the deployment package")
        print("3. Run the deployment script")
        print("4. Start your services")
    else:
        print("\n❌ Upload failed. Please check your configuration and try again.")

if __name__ == "__main__":
    main()