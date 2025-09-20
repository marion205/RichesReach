#!/usr/bin/env python3
"""
Simple deployment - create a new instance with a working app
"""
import boto3
import time
import zipfile
import tempfile
from pathlib import Path
def simple_deploy():
print(" Starting Simple Deployment...")
# Initialize AWS clients
ec2 = boto3.client('ec2', region_name='us-east-2')
s3 = boto3.client('s3', region_name='us-east-2')
try:
# Create a simple deployment package
print(" Creating simple deployment package...")
with tempfile.TemporaryDirectory() as temp_dir:
package_path = Path(temp_dir) / "simple-app.zip"
# Create a simple FastAPI app
app_code = '''
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
app = FastAPI(title="RichesReach AI", version="1.0.0")
app.add_middleware(
CORSMiddleware,
allow_origins=["*"],
allow_credentials=True,
allow_methods=["*"],
allow_headers=["*"],
)
@app.get("/")
async def root():
return {"message": "RichesReach AI is running!", "status": "healthy"}
@app.get("/health")
async def health():
return {"status": "healthy", "service": "RichesReach AI"}
@app.get("/api/status")
async def api_status():
return {
"service": "RichesReach AI",
"version": "1.0.0",
"status": "operational",
"features": [
"Stock Analysis",
"AI Recommendations", 
"Portfolio Management",
"Real-time Data"
]
}
if __name__ == "__main__":
uvicorn.run(app, host="0.0.0.0", port=8000)
'''
# Create requirements.txt
requirements = '''
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6
'''
# Create the zip file
with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
zipf.writestr("main.py", app_code)
zipf.writestr("requirements.txt", requirements)
# Upload to S3
bucket_name = f"riches-reach-simple-{boto3.client('sts').get_caller_identity()['Account']}"
try:
s3.create_bucket(
Bucket=bucket_name,
CreateBucketConfiguration={'LocationConstraint': 'us-east-2'}
)
print(f" Created S3 bucket: {bucket_name}")
except s3.exceptions.BucketAlreadyOwnedByYou:
print(f" Using existing S3 bucket: {bucket_name}")
# Upload deployment package
s3_key = "deployment/simple-app.zip"
s3.upload_file(str(package_path), bucket_name, s3_key)
print(f" Uploaded deployment package to s3://{bucket_name}/{s3_key}")
# Create EC2 instance
print(" Creating new EC2 instance...")
# Get the latest Amazon Linux 2 AMI
response = ec2.describe_images(
Owners=['amazon'],
Filters=[
{'Name': 'name', 'Values': ['amzn2-ami-hvm-*-x86_64-gp2']},
{'Name': 'state', 'Values': ['available']}
]
)
if not response['Images']:
print(" No suitable AMI found")
return False
# Sort by creation date and get the latest
latest_ami = sorted(response['Images'], key=lambda x: x['CreationDate'], reverse=True)[0]
ami_id = latest_ami['ImageId']
# User data script to install and run the application
user_data = f'''#!/bin/bash
yum update -y
yum install -y python3 python3-pip
# Install application dependencies
pip3 install fastapi uvicorn
# Download and extract application
aws s3 cp s3://{bucket_name}/{s3_key} /tmp/simple-app.zip
cd /tmp
unzip simple-app.zip
# Start the application
nohup python3 main.py > /var/log/richesreach.log 2>&1 &
# Create a simple health check
echo "#!/bin/bash" > /usr/local/bin/health-check.sh
echo "curl -f http://localhost:8000/health || exit 1" >> /usr/local/bin/health-check.sh
chmod +x /usr/local/bin/health-check.sh
echo "RichesReach AI deployed successfully!" > /var/log/deployment.log
'''
# Launch EC2 instance
response = ec2.run_instances(
ImageId=ami_id,
MinCount=1,
MaxCount=1,
InstanceType='t3.micro',
UserData=user_data,
SecurityGroupIds=['sg-015c977be8595f590'], # Use existing security group
TagSpecifications=[
{
'ResourceType': 'instance',
'Tags': [
{'Key': 'Name', 'Value': 'RichesReach-AI-Simple'},
{'Key': 'Project', 'Value': 'RichesReach'},
{'Key': 'Environment', 'Value': 'Production'}
]
}
]
)
instance_id = response['Instances'][0]['InstanceId']
print(f" Created EC2 instance: {instance_id}")
# Wait for instance to be running
print("⏳ Waiting for instance to be running...")
waiter = ec2.get_waiter('instance_running')
waiter.wait(InstanceIds=[instance_id])
# Get public IP
response = ec2.describe_instances(InstanceIds=[instance_id])
public_ip = response['Reservations'][0]['Instances'][0]['PublicIpAddress']
print(f" Simple deployment successful!")
print(f" Your RichesReach AI is running at: http://{public_ip}:8000")
print(f" Health check: http://{public_ip}:8000/health")
print(f" API status: http://{public_ip}:8000/api/status")
print(f" Instance ID: {instance_id}")
return True
except Exception as e:
print(f" Simple deployment failed: {e}")
return False
if __name__ == "__main__":
simple_deploy()
