#!/usr/bin/env python3
"""
Deploy RichesReach AI to AWS with proper security group
"""
import boto3
import json
import os
import zipfile
import tempfile
from pathlib import Path

def create_security_group():
    """Create a security group for the RichesReach AI application"""
    ec2 = boto3.client('ec2', region_name='us-east-2')
    
    try:
        # Create security group
        response = ec2.create_security_group(
            GroupName='richesreach-ai-sg',
            Description='Security group for RichesReach AI application',
            TagSpecifications=[
                {
                    'ResourceType': 'security-group',
                    'Tags': [
                        {'Key': 'Name', 'Value': 'RichesReach-AI-SG'},
                        {'Key': 'Project', 'Value': 'RichesReach'}
                    ]
                }
            ]
        )
        
        security_group_id = response['GroupId']
        print(f"✅ Created security group: {security_group_id}")
        
        # Add inbound rules
        ec2.authorize_security_group_ingress(
            GroupId=security_group_id,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'SSH access'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 8000,
                    'ToPort': 8000,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'RichesReach AI API'}]
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 80,
                    'ToPort': 80,
                    'IpRanges': [{'CidrIp': '0.0.0.0/0', 'Description': 'HTTP access'}]
                }
            ]
        )
        
        print("✅ Added security group rules")
        return security_group_id
        
    except ec2.exceptions.ClientError as e:
        if 'already exists' in str(e):
            # Get existing security group
            response = ec2.describe_security_groups(
                Filters=[{'Name': 'group-name', 'Values': ['richesreach-ai-sg']}]
            )
            if response['SecurityGroups']:
                security_group_id = response['SecurityGroups'][0]['GroupId']
                print(f"✅ Using existing security group: {security_group_id}")
                return security_group_id
        raise e

def deploy_richesreach_ai():
    print("🚀 Deploying RichesReach AI to AWS...")
    
    # Initialize AWS clients
    ec2 = boto3.client('ec2', region_name='us-east-2')
    s3 = boto3.client('s3', region_name='us-east-2')
    
    try:
        # Create security group
        security_group_id = create_security_group()
        
        # Create deployment package
        print("📦 Creating deployment package...")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            package_path = Path(temp_dir) / "richesreach-ai.zip"
            
            # Create zip file with backend code
            with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                backend_path = Path(__file__).parent / "backend"
                
                # Add Python files
                for py_file in backend_path.rglob("*.py"):
                    zipf.write(py_file, py_file.relative_to(backend_path.parent))
                
                # Add requirements.txt
                req_file = backend_path / "requirements.txt"
                if req_file.exists():
                    zipf.write(req_file, "requirements.txt")
            
            # Upload to S3
            bucket_name = f"riches-reach-ai-deployment-{boto3.client('sts').get_caller_identity()['Account']}"
            
            try:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': 'us-east-2'}
                )
                print(f"✅ Created S3 bucket: {bucket_name}")
            except s3.exceptions.BucketAlreadyOwnedByYou:
                print(f"✅ Using existing S3 bucket: {bucket_name}")
            
            # Upload deployment package
            s3_key = "deployment/richesreach-ai.zip"
            s3.upload_file(str(package_path), bucket_name, s3_key)
            print(f"✅ Uploaded deployment package to s3://{bucket_name}/{s3_key}")
            
            # Create EC2 instance
            print("🖥️  Creating EC2 instance...")
            
            # Get the latest Amazon Linux 2 AMI
            response = ec2.describe_images(
                Owners=['amazon'],
                Filters=[
                    {'Name': 'name', 'Values': ['amzn2-ami-hvm-*-x86_64-gp2']},
                    {'Name': 'state', 'Values': ['available']}
                ]
            )
            
            if not response['Images']:
                print("❌ No suitable AMI found")
                return False
            
            # Sort by creation date and get the latest
            latest_ami = sorted(response['Images'], key=lambda x: x['CreationDate'], reverse=True)[0]
            ami_id = latest_ami['ImageId']
            
            # User data script to install and run the application
            user_data = f"""#!/bin/bash
yum update -y
yum install -y python3 python3-pip git

# Install application dependencies
pip3 install fastapi uvicorn boto3 requests pandas numpy scikit-learn

# Download and extract application
aws s3 cp s3://{bucket_name}/{s3_key} /tmp/richesreach-ai.zip
cd /tmp
unzip richesreach-ai.zip

# Install Python dependencies
if [ -f requirements.txt ]; then
    pip3 install -r requirements.txt
fi

# Start the application
cd backend
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > /var/log/richesreach.log 2>&1 &

# Create a simple health check
echo "#!/bin/bash" > /usr/local/bin/health-check.sh
echo "curl -f http://localhost:8000/health || exit 1" >> /usr/local/bin/health-check.sh
chmod +x /usr/local/bin/health-check.sh

echo "RichesReach AI deployed successfully!" > /var/log/deployment.log
"""
            
            # Launch EC2 instance
            response = ec2.run_instances(
                ImageId=ami_id,
                MinCount=1,
                MaxCount=1,
                InstanceType='t3.micro',
                UserData=user_data,
                SecurityGroupIds=[security_group_id],
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {'Key': 'Name', 'Value': 'RichesReach-AI'},
                            {'Key': 'Project', 'Value': 'RichesReach'},
                            {'Key': 'Environment', 'Value': 'Production'}
                        ]
                    }
                ]
            )
            
            instance_id = response['Instances'][0]['InstanceId']
            print(f"✅ Created EC2 instance: {instance_id}")
            
            # Wait for instance to be running
            print("⏳ Waiting for instance to be running...")
            waiter = ec2.get_waiter('instance_running')
            waiter.wait(InstanceIds=[instance_id])
            
            # Get public IP
            response = ec2.describe_instances(InstanceIds=[instance_id])
            public_ip = response['Reservations'][0]['Instances'][0]['PublicIpAddress']
            
            print(f"🎉 Deployment successful!")
            print(f"🌐 Your RichesReach AI is running at: http://{public_ip}:8000")
            print(f"🏥 Health check: http://{public_ip}:8000/health")
            print(f"📊 API docs: http://{public_ip}:8000/docs")
            print(f"🖥️  Instance ID: {instance_id}")
            print(f"🔒 Security Group: {security_group_id}")
            
            return True
            
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return False

if __name__ == "__main__":
    deploy_richesreach_ai()
