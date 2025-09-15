#!/usr/bin/env python3
"""
Direct Deployment Script - No Docker Required!
Deploys RichesReach AI code directly to AWS ECS
"""
import subprocess
import json
import os
import zipfile
import tempfile
import shutil
from pathlib import Path
def run_command(command, description):
"""Run a command and return the result"""
print(f" {description}...")
try:
result = subprocess.run(command, shell=True, capture_output=True, text=True)
if result.returncode == 0:
print(f"SUCCESS: {description} completed")
return result.stdout.strip()
else:
print(f"ERROR: {description} failed: {result.stderr}")
return None
except Exception as e:
print(f"ERROR: {description} failed: {e}")
return None
def create_deployment_package():
"""Create a deployment package with your code"""
print(" Creating deployment package...")
# Create temporary directory
with tempfile.TemporaryDirectory() as temp_dir:
package_path = os.path.join(temp_dir, "riches-reach-ai.zip")
# Files to include in deployment
include_files = [
"main.py",
"core/",
".env.production"
]
# Create zip package
with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
for item in include_files:
if os.path.isfile(item):
zipf.write(item, item)
elif os.path.isdir(item):
for root, dirs, files in os.walk(item):
for file in files:
file_path = os.path.join(root, file)
arc_name = os.path.relpath(file_path, '.')
zipf.write(file_path, arc_name)
print(f"SUCCESS: Deployment package created: {package_path}")
return package_path
def deploy_to_s3(package_path):
"""Upload deployment package to S3"""
print("Uploading to S3...")
bucket_name = "riches-reach-ai-models-498606688292"
s3_key = "deployments/riches-reach-ai-latest.zip"
upload_cmd = f"aws s3 cp {package_path} s3://{bucket_name}/{s3_key} --region us-east-1"
result = run_command(upload_cmd, "Uploading deployment package to S3")
if result:
print(f"SUCCESS: Package uploaded to s3://{bucket_name}/{s3_key}")
return f"s3://{bucket_name}/{s3_key}"
return None
def create_ecs_task_definition():
"""Create a new ECS task definition with your code"""
print(" Creating ECS task definition...")
# Create a simple task definition that runs your code
task_def = {
"family": "riches-reach-ai-task",
"networkMode": "awsvpc",
"requiresCompatibilities": ["FARGATE"],
"cpu": "512",
"memory": "1024",
"executionRoleArn": "arn:aws:iam::498606688292:role/ecsTaskExecutionRole",
"taskRoleArn": "arn:aws:iam::498606688292:role/ecsTaskRole",
"containerDefinitions": [
{
"name": "ai-service",
"image": "python:3.10-slim",
"portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
"essential": True,
"command": [
"/bin/bash", "-c",
"pip install fastapi uvicorn && python -c \"import urllib.request; urllib.request.urlretrieve('https://riches-reach-ai-models-498606688292.s3.amazonaws.com/deployments/riches-reach-ai-latest.zip', '/tmp/code.zip'); import zipfile; zipfile.ZipFile('/tmp/code.zip').extractall('/app'); import os; os.chdir('/app'); import subprocess; subprocess.run(['uvicorn', 'main:app', '--host', '0.0.0.0', '--port', '8000'])\""
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
json.dump(task_def, f, indent=2)
print(f"SUCCESS: Task definition saved to {task_def_file}")
return task_def_file
def register_task_definition(task_def_file):
"""Register the new task definition with ECS"""
print(" Registering task definition...")
register_cmd = f"aws ecs register-task-definition --cli-input-json file://{task_def_file} --region us-east-1"
result = run_command(register_cmd, "Registering task definition")
if result:
# Extract the new task definition ARN
try:
task_def_data = json.loads(result)
new_task_def_arn = task_def_data['taskDefinition']['taskDefinitionArn']
print(f"SUCCESS: New task definition registered: {new_task_def_arn}")
return new_task_def_arn
except:
print("WARNING: Could not extract task definition ARN")
return None
return None
def update_ecs_service(new_task_def_arn):
"""Update the ECS service to use the new task definition"""
if not new_task_def_arn:
print("ERROR: Cannot update service without task definition ARN")
return False
print(" Updating ECS service...")
update_cmd = f"aws ecs update-service --cluster riches-reach-ai-production-cluster --service riches-reach-ai-ai --task-definition {new_task_def_arn} --region us-east-1"
result = run_command(update_cmd, "Updating ECS service")
if result:
print("SUCCESS: ECS service update initiated")
return True
return False
def deploy_direct():
"""Main deployment function"""
print("DIRECT DEPLOYMENT - No Docker Required!")
print("=" * 50)
# Step 1: Create deployment package
package_path = create_deployment_package()
if not package_path:
print("ERROR: Failed to create deployment package")
return
# Step 2: Upload to S3
s3_location = deploy_to_s3(package_path)
if not s3_location:
print("ERROR: Failed to upload to S3")
return
# Step 3: Create task definition
task_def_file = create_ecs_task_definition()
# Step 4: Register task definition
new_task_def_arn = register_task_definition(task_def_file)
# Step 5: Update ECS service
if update_ecs_service(new_task_def_arn):
print("\nSUCCESS: DIRECT DEPLOYMENT COMPLETED!")
print("Your RichesReach AI code is now being deployed to AWS!")
print("\nNext steps:")
print("1. Monitor deployment: aws ecs describe-services --cluster riches-reach-ai-production-cluster --services riches-reach-ai-ai")
print("2. Check logs: aws logs describe-log-groups --log-group-name-prefix /ecs/riches-reach-ai")
else:
print("\nERROR: Deployment failed at service update step")
if __name__ == "__main__":
deploy_direct()
