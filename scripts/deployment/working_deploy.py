#!/usr/bin/env python3
"""
Working deployment - create a server with a properly configured app
"""
import boto3
import time
import zipfile
import tempfile
from pathlib import Path
def working_deploy():
print(" Starting Working Deployment...")
# Initialize AWS clients
ec2 = boto3.client('ec2', region_name='us-east-2')
try:
# Create a working deployment package
print(" Creating working deployment package...")
with tempfile.TemporaryDirectory() as temp_dir:
package_path = Path(temp_dir) / "working-app.zip"
# Create a proper FastAPI app with all dependencies
app_code = '''
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
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
@app.get("/api/test")
async def test():
return {"message": "API is working", "timestamp": "2024-09-08"}
if __name__ == "__main__":
port = int(os.environ.get("PORT", 8000))
uvicorn.run(app, host="0.0.0.0", port=port)
'''
requirements_code = '''
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
'''
# Create the zip file
with zipfile.ZipFile(package_path, 'w') as zipf:
zipf.writestr("app.py", app_code)
zipf.writestr("requirements.txt", requirements_code)
zipf.writestr("run.sh", '''#!/bin/bash
cd /tmp
unzip -o app.zip
pip3 install -r requirements.txt
python3 app.py
''')
# Upload to S3
s3 = boto3.client('s3', region_name='us-east-2')
bucket_name = 'richesreach-deployments'
try:
s3.head_bucket(Bucket=bucket_name)
except:
s3.create_bucket(Bucket=bucket_name)
s3.upload_file(str(package_path), bucket_name, 'working-app.zip')
print(f" Uploaded to S3: s3://{bucket_name}/working-app.zip")
# Create user data script
user_data = f'''#!/bin/bash
apt-get update
apt-get install -y python3 python3-pip unzip
pip3 install boto3
# Download and run the app
cd /tmp
aws s3 cp s3://{bucket_name}/working-app.zip app.zip
unzip -o app.zip
pip3 install -r requirements.txt
# Start the app
nohup python3 app.py > app.log 2>&1 &
# Wait a moment and check if it's running
sleep 10
ps aux | grep python3
netstat -tlnp | grep 8000
'''
# Launch new instance
print(" Launching new instance...")
response = ec2.run_instances(
ImageId='ami-0c02fb55956c7d316', # Ubuntu 20.04 LTS
MinCount=1,
MaxCount=1,
InstanceType='t2.micro',
KeyName='richesreach-key',
SecurityGroupIds=['sg-0a8b5c6d7e8f9a0b1'],
UserData=user_data,
TagSpecifications=[
{
'ResourceType': 'instance',
'Tags': [
{'Key': 'Name', 'Value': 'RichesReach-Working'},
{'Key': 'Project', 'Value': 'RichesReach-AI'}
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
print("⏳ Application is starting up...")
print(" Wait 2-3 minutes for the application to fully start")
return True
except Exception as e:
print(f" Error: {e}")
return False
if __name__ == "__main__":
working_deploy()
