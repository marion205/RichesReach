#!/usr/bin/env python3
"""
Direct Deployment Script for RichesReach AI
Deploys the application directly to AWS without Docker
"""

import os
import sys
import json
import subprocess
import boto3
from pathlib import Path

def run_command(command, description):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"SUCCESS: {description} completed")
            return result
        else:
            print(f"ERROR: {description} failed: {result.stderr}")
            return result
    except Exception as e:
        print(f"ERROR: {description} failed: {e}")
        return None

def create_deployment_package():
    """Create a deployment package with all necessary files"""
    print("Creating deployment package...")
    
    # Create package directory
    package_dir = "deployment_package"
    if os.path.exists(package_dir):
        import shutil
        shutil.rmtree(package_dir)
    os.makedirs(package_dir)
    
    # Copy backend files
    backend_files = [
        "backend/core/",
        "backend/requirements.txt",
        "backend/main.py",
        "backend/manage.py"
    ]
    
    for file_path in backend_files:
        if os.path.exists(file_path):
            if os.path.isdir(file_path):
                import shutil
                shutil.copytree(file_path, os.path.join(package_dir, file_path))
            else:
                import shutil
                os.makedirs(os.path.dirname(os.path.join(package_dir, file_path)), exist_ok=True)
                shutil.copy2(file_path, os.path.join(package_dir, file_path))
    
    # Create deployment script
    deploy_script = f"""#!/bin/bash
cd /tmp
python3 -m pip install -r requirements.txt
python3 main.py
"""
    
    with open(os.path.join(package_dir, "deploy.sh"), "w") as f:
        f.write(deploy_script)
    
    # Make script executable
    os.chmod(os.path.join(package_dir, "deploy.sh"), 0o755)
    
    # Create zip package
    import zipfile
    package_path = "richesreach_deployment.zip"
    
    with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, package_dir)
                zipf.write(file_path, arc_name)
                print(f"  Added: {arc_name}")
    
    print(f"SUCCESS: Deployment package created: {package_path}")
    print(f"Package size: {os.path.getsize(package_path) / 1024:.1f} KB")
    
    return package_path

def upload_to_s3(package_path, bucket_name):
    """Upload the deployment package to S3"""
    print("Uploading to S3...")
    
    try:
        s3_client = boto3.client('s3')
        
        # Create bucket if it doesn't exist
        try:
            s3_client.head_bucket(Bucket=bucket_name)
        except:
            s3_client.create_bucket(Bucket=bucket_name)
        
        # Upload package
        s3_key = f"deployments/{os.path.basename(package_path)}"
        s3_client.upload_file(package_path, bucket_name, s3_key)
        
        print(f"SUCCESS: Package uploaded to s3://{bucket_name}/{s3_key}")
        return s3_key
        
    except Exception as e:
        print(f"ERROR: Failed to upload to S3: {e}")
        return None

def deploy_to_ecs(bucket_name, s3_key):
    """Deploy the application to ECS"""
    print("Deploying to ECS...")
    
    try:
        ecs_client = boto3.client('ecs')
        
        # Get cluster and service names
        cluster_name = "riches-reach-ai-production-cluster"
        service_name = "riches-reach-ai-ai"
        
        # Create task definition
        task_definition = {
            "family": "riches-reach-ai-task",
            "networkMode": "awsvpc",
            "requiresCompatibilities": ["FARGATE"],
            "cpu": "256",
            "memory": "512",
            "executionRoleArn": "arn:aws:iam::498606688292:role/ecsTaskExecutionRole",
            "taskRoleArn": "arn:aws:iam::498606688292:role/ecsTaskRole",
            "containerDefinitions": [
                {
                    "name": "riches-reach-ai",
                    "image": "python:3.10-slim",
                    "essential": True,
                    "portMappings": [
                        {
                            "containerPort": 8000,
                            "protocol": "tcp"
                        }
                    ],
                    "environment": [
                        {
                            "name": "S3_BUCKET",
                            "value": bucket_name
                        },
                        {
                            "name": "S3_KEY",
                            "value": s3_key
                        }
                    ],
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": "/ecs/riches-reach-ai",
                            "awslogs-region": "us-east-1",
                            "awslogs-stream-prefix": "ecs"
                        }
                    }
                }
            ]
        }
        
        # Save task definition to file
        task_def_file = "task-definition.json"
        with open(task_def_file, 'w') as f:
            json.dump(task_definition, f, indent=2)
        
        print(f"SUCCESS: Task definition saved to {task_def_file}")
        
        # Register task definition
        response = ecs_client.register_task_definition(
            family=task_definition["family"],
            networkMode=task_definition["networkMode"],
            requiresCompatibilities=task_definition["requiresCompatibilities"],
            cpu=task_definition["cpu"],
            memory=task_definition["memory"],
            executionRoleArn=task_definition["executionRoleArn"],
            taskRoleArn=task_definition["taskRoleArn"],
            containerDefinitions=task_definition["containerDefinitions"]
        )
        
        new_task_def_arn = response['taskDefinition']['taskDefinitionArn']
        print(f"SUCCESS: New task definition registered: {new_task_def_arn}")
        
        # Update service
        try:
            ecs_client.update_service(
                cluster=cluster_name,
                service=service_name,
                taskDefinition=new_task_def_arn
            )
            print("SUCCESS: ECS service update initiated")
        except Exception as e:
            print(f"Warning: Could not update service: {e}")
            print("You may need to update the service manually")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to deploy to ECS: {e}")
        return False

def main():
    """Main deployment function"""
    print("DIRECT DEPLOYMENT - No Docker Required! (FIXED)")
    print("=" * 50)
    
    # Configuration
    bucket_name = "riches-reach-ai-deployment"
    
    try:
        # Step 1: Create deployment package
        package_path = create_deployment_package()
        if not package_path:
            print("ERROR: Failed to create deployment package")
            return False
        
        # Step 2: Upload to S3
        s3_key = upload_to_s3(package_path, bucket_name)
        if not s3_key:
            print("ERROR: Failed to upload to S3")
            return False
        
        # Step 3: Deploy to ECS
        if deploy_to_ecs(bucket_name, s3_key):
            print("\nDIRECT DEPLOYMENT COMPLETED!")
            print("\nNext steps:")
            print("1. Check ECS console for service status")
            print("2. Monitor logs in CloudWatch")
            print("3. Test the application endpoint")
            
            # Cleanup
            if os.path.exists(package_path):
                os.remove(package_path)
                print(f"Cleaned up: {package_path}")
            
            return True
        else:
            print("\nDeployment failed at service update step")
            return False
            
    except Exception as e:
        print(f"ERROR: Deployment failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
