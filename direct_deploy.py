#!/usr/bin/env python3
"""
Direct deployment - embed the app directly in user data
"""
import boto3
import time

def direct_deploy():
    print("🚀 Starting Direct Deployment...")
    
    # Initialize AWS client
    ec2 = boto3.client('ec2', region_name='us-east-2')
    
    try:
        # Create user data script with embedded app
        user_data = '''#!/bin/bash
apt-get update
apt-get install -y python3 python3-pip

# Create the FastAPI app
cat > /tmp/app.py << 'EOF'
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
EOF

# Create requirements file
cat > /tmp/requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
EOF

# Install dependencies
pip3 install -r /tmp/requirements.txt

# Start the app
cd /tmp
nohup python3 app.py > app.log 2>&1 &

# Wait and check status
sleep 15
echo "=== App Status ==="
ps aux | grep python3
echo "=== Port Status ==="
netstat -tlnp | grep 8000
echo "=== App Log ==="
tail -20 app.log
'''
        
        # Launch new instance
        print("🚀 Launching new instance...")
        
        response = ec2.run_instances(
            ImageId='ami-019b9d054031a0268',  # Ubuntu 20.04 LTS
            MinCount=1,
            MaxCount=1,
            InstanceType='t2.micro',
            KeyName='richesreach-key',
            SecurityGroupIds=['sg-015c977be8595f590'],
            UserData=user_data,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {'Key': 'Name', 'Value': 'RichesReach-Direct'},
                        {'Key': 'Project', 'Value': 'RichesReach-AI'}
                    ]
                }
            ]
        )
        
        instance_id = response['Instances'][0]['InstanceId']
        print(f"✅ Instance launched: {instance_id}")
        
        # Wait for instance to be running
        print("⏳ Waiting for instance to be running...")
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        
        # Get public IP
        response = ec2.describe_instances(InstanceIds=[instance_id])
        public_ip = response['Reservations'][0]['Instances'][0]['PublicIpAddress']
        
        print(f"🌐 Public IP: {public_ip}")
        print(f"🔗 Test URL: http://{public_ip}:8000/health")
        print("⏳ Application is starting up...")
        print("💡 Wait 2-3 minutes for the application to fully start")
        
        return public_ip
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    direct_deploy()
