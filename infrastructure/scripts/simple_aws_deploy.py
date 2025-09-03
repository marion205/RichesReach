#!/usr/bin/env python3
"""
Simple AWS Deployment for RichesReach AI
Uses AWS CLI commands instead of CloudFormation for basic deployment
"""

import subprocess
import json
import time
import os
import boto3

class SimpleAWSDeployer:
    def __init__(self):
        self.project_name = "riches-reach-ai"
        self.region = "us-east-1"
        self.account_id = os.environ.get('AWS_ACCOUNT_ID', '498606688292')
        
    def run_command(self, command, description):
        """Run a shell command and handle errors"""
        print(f"🔄 {description}...")
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"SUCCESS: {description} completed")
                return result.stdout.strip()
            else:
                print(f"ERROR: {description} failed: {result.stderr}")
                return None
        except Exception as e:
            print(f"ERROR: {description} error: {e}")
            return None
    
    def create_s3_bucket(self):
        """Create S3 bucket for ML models"""
        bucket_name = f"{self.project_name}-models-{self.account_id}"
        command = f"aws s3 mb s3://{bucket_name} --region {self.region}"
        return self.run_command(command, f"Creating S3 bucket {bucket_name}")
    
    def create_ecr_repository(self):
        """Create ECR repository for Docker images"""
        repo_name = f"{self.project_name}-ai"
        command = f"aws ecr create-repository --repository-name {repo_name} --region {self.region}"
        return self.run_command(command, f"Creating ECR repository {repo_name}")
    
    def create_ec2_instance(self):
        """Create a simple EC2 instance for testing"""
        # Get latest Amazon Linux 2 AMI
        ami_command = "aws ec2 describe-images --owners amazon --filters 'Name=name,Values=amzn2-ami-hvm-*-x86_64-gp2' 'Name=state,Values=available' --query 'sort_by(Images, &CreationDate)[-1].ImageId' --output text --region us-east-1"
        ami_id = self.run_command(ami_command, "Getting latest Amazon Linux 2 AMI")
        
        if ami_id:
            # Create security group
            sg_command = f"aws ec2 create-security-group --group-name {self.project_name}-sg --description 'Security group for RichesReach AI' --region {self.region}"
            sg_result = self.run_command(sg_command, "Creating security group")
            
            if sg_result:
                # Extract security group ID from output
                sg_id = sg_result.split('"GroupId": "')[1].split('"')[0] if '"GroupId": "' in sg_result else None
                
                if sg_id:
                    # Add SSH access
                    ssh_command = f"aws ec2 authorize-security-group-ingress --group-id {sg_id} --protocol tcp --port 22 --cidr 0.0.0.0/0 --region {self.region}"
                    self.run_command(ssh_command, "Adding SSH access to security group")
                    
                    # Add HTTP access
                    http_command = f"aws ec2 authorize-security-group-ingress --group-id {sg_id} --protocol tcp --port 80 --cidr 0.0.0.0/0 --region {self.region}"
                    self.run_command(http_command, "Adding HTTP access to security group")
                    
                    # Create EC2 instance
                    instance_command = f"aws ec2 run-instances --image-id {ami_id} --count 1 --instance-type t2.micro --key-name default --security-group-ids {sg_id} --tag-specifications 'ResourceType=instance,Tags=[{{Key=Name,Value={self.project_name}-ai}}]' --region {self.region}"
                    return self.run_command(instance_command, "Creating EC2 instance")
        
        return None
    
    def test_services(self):
        """Test various AWS services"""
        print("\nTesting AWS Services...")
        
        # Test S3
        s3_test = self.run_command("aws s3 ls --region us-east-1", "Testing S3 access")
        
        # Test EC2
        ec2_test = self.run_command("aws ec2 describe-instances --region us-east-1 --query 'Reservations[0:1].Instances[0:1].InstanceId' --output table", "Testing EC2 access")
        
        # Test IAM
        iam_test = self.run_command("aws iam get-user --region us-east-1", "Testing IAM access")
        
        return s3_test is not None and ec2_test is not None and iam_test is not None
    
    def deploy(self):
        """Main deployment method"""
        print("Simple AWS Deployment for RichesReach AI")
        print("=" * 50)
        
        # Test services first
        if not self.test_services():
            print("ERROR: AWS service tests failed. Please check your permissions.")
            return False
        
        print("\n📦 Creating AWS Resources...")
        
        # Create S3 bucket
        self.create_s3_bucket()
        
        # Create ECR repository
        self.create_ecr_repository()
        
        # Create EC2 instance (optional)
        print("\n🐳 Note: EC2 instance creation requires additional permissions.")
        print("   You can create it manually in the AWS Console if needed.")
        
        print("\nSUCCESS: Simple deployment completed!")
        print("\nNext Steps:")
        print("1. 🐳 Install Docker locally for containerization")
        print("2. 📦 Build and push Docker image to ECR")
        print("3. Deploy to EC2 or ECS")
        print("4. Set up monitoring and scaling")
        
        return True

def test_aws_services():
    """Test basic AWS service connectivity"""
    print("\nTesting AWS Services...")
    
    # Test S3
    try:
        s3 = boto3.client('s3')
        response = s3.list_buckets()
        print(f"SUCCESS: S3 access - {len(response['Buckets'])} buckets found")
    except Exception as e:
        print(f"ERROR: S3 access failed - {e}")
    
    # Test ECS
    try:
        ecs = boto3.client('ecs')
        response = ecs.list_clusters()
        print(f"SUCCESS: ECS access - {len(response['clusterArns'])} clusters found")
    except Exception as e:
        print(f"ERROR: ECS access failed - {e}")
    
    # Test CloudWatch
    try:
        cloudwatch = boto3.client('cloudwatch')
        response = cloudwatch.list_metrics(Namespace='AWS/ECS')
        print(f"SUCCESS: CloudWatch access - {len(response['Metrics'])} ECS metrics found")
    except Exception as e:
        print(f"ERROR: CloudWatch access failed - {e}")

def main():
    """Main deployment function"""
    print("Simple AWS Deployment for RichesReach AI")
    print("=" * 50)
    
    # Check AWS credentials
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"SUCCESS: AWS credentials valid - Account: {identity['Account']}")
    except Exception as e:
        print(f"ERROR: AWS credentials not valid - {e}")
        print("Please run 'aws configure' first")
        return
    
    # Test AWS services
    test_aws_services()
    
    # Check current ECS status
    print("\nCurrent ECS Status:")
    try:
        ecs = boto3.client('ecs')
        clusters = ecs.list_clusters()
        
        for cluster_arn in clusters['clusterArns']:
            cluster_name = cluster_arn.split('/')[-1]
            print(f"  Cluster: {cluster_name}")
            
            services = ecs.list_services(cluster=cluster_arn)
            for service_arn in services['serviceArns']:
                service_name = service_arn.split('/')[-1]
                print(f"    Service: {service_name}")
    except Exception as e:
        print(f"ERROR: Could not check ECS status - {e}")
    
    # Check current tasks
    print("\nCurrent Tasks:")
    try:
        for cluster_arn in clusters['clusterArns']:
            tasks = ecs.list_tasks(cluster=cluster_arn)
            for task_arn in tasks['taskArns']:
                task_name = task_arn.split('/')[-1]
                print(f"  Task: {task_name}")
    except Exception as e:
        print(f"ERROR: Could not check tasks - {e}")
    
    # Deployment options
    print("\nDeployment Options:")
    print("1. Deploy to existing ECS cluster")
    print("2. Create new ECS cluster")
    print("3. Update existing service")
    print("4. Check service logs")
    
    print("\nSimple deployment check completed!")
    print("\nNext Steps:")
    print("1. Choose deployment option")
    print("2. Configure deployment parameters")
    print("3. Deploy to AWS")
    print("4. Monitor deployment status")

if __name__ == "__main__":
    deployer = SimpleAWSDeployer()
    deployer.deploy()
