#!/usr/bin/env python3
"""
Check the status of the deployed RichesReach AI application
"""
import boto3
import requests
import time
import subprocess

def check_application_status():
    print("🔍 Checking RichesReach AI deployment status...")
    
    # Get instance details
    ec2 = boto3.client('ec2', region_name='us-east-2')
    
    try:
        response = ec2.describe_instances(
            InstanceIds=['i-0cf93dd9f7f54ce93']
        )
        
        instance = response['Reservations'][0]['Instances'][0]
        public_ip = instance['PublicIpAddress']
        state = instance['State']['Name']
        
        print(f"🖥️  Instance Status: {state}")
        print(f"🌐 Public IP: {public_ip}")
        
        if state != 'running':
            print("❌ Instance is not running")
            return False
        
        # Check if the application is responding
        print("⏳ Checking application health...")
        
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                # Try to connect to the application
                response = requests.get(f"http://{public_ip}:8000/health", timeout=5)
                if response.status_code == 200:
                    print("✅ Application is running and healthy!")
                    print(f"🌐 API Documentation: http://{public_ip}:8000/docs")
                    print(f"🏥 Health Check: http://{public_ip}:8000/health")
                    return True
                else:
                    print(f"⚠️  Application responded with status {response.status_code}")
            except requests.exceptions.ConnectionError:
                print(f"⏳ Attempt {attempt + 1}/{max_attempts}: Application not ready yet...")
                time.sleep(30)  # Wait 30 seconds between attempts
            except requests.exceptions.Timeout:
                print(f"⏳ Attempt {attempt + 1}/{max_attempts}: Request timed out...")
                time.sleep(30)
            except Exception as e:
                print(f"⚠️  Attempt {attempt + 1}/{max_attempts}: Error - {e}")
                time.sleep(30)
        
        print("❌ Application did not start within the expected time")
        print("🔧 Possible issues:")
        print("   - Application is still installing dependencies")
        print("   - Port 8000 is not accessible")
        print("   - Application failed to start")
        
        return False
        
    except Exception as e:
        print(f"❌ Error checking deployment: {e}")
        return False

def check_security_group():
    """Check if the security group allows traffic on port 8000"""
    print("🔒 Checking security group configuration...")
    
    ec2 = boto3.client('ec2', region_name='us-east-2')
    
    try:
        response = ec2.describe_security_groups(
            GroupIds=['sg-015c977be8595f590']
        )
        
        security_group = response['SecurityGroups'][0]
        print(f"✅ Security Group: {security_group['GroupName']}")
        
        # Check inbound rules
        for rule in security_group['IpPermissions']:
            if rule.get('FromPort') == 8000:
                print("✅ Port 8000 is open for inbound traffic")
                return True
        
        print("❌ Port 8000 is not open in security group")
        return False
        
    except Exception as e:
        print(f"❌ Error checking security group: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("RICHESREACH AI DEPLOYMENT STATUS CHECK")
    print("=" * 50)
    
    # Check security group first
    sg_ok = check_security_group()
    
    if sg_ok:
        # Check application status
        app_ok = check_application_status()
        
        if app_ok:
            print("\n🎉 SUCCESS: Your RichesReach AI is running!")
        else:
            print("\n⚠️  The application may still be starting up.")
            print("💡 Try again in a few minutes, or check the AWS console for logs.")
    else:
        print("\n❌ Security group configuration issue detected.")
        print("💡 The application may not be accessible due to firewall rules.")
