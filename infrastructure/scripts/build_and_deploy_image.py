#!/usr/bin/env python3
"""
Build and Deploy RichesReach AI Docker Image to ECR and ECS
"""

import subprocess
import json
import os
import time

class DockerImageDeployer:
    def __init__(self):
        self.project_name = "riches-reach-ai"
        self.region = "us-east-1"
        self.account_id = os.environ.get('AWS_ACCOUNT_ID', '498606688292')
        self.ecr_repo_name = f"{self.project_name}-ai"
        self.image_tag = "latest"
        
    def run_command(self, command, description):
        """Run a shell command and handle errors"""
        print(f"🔄 {description}...")
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ {description} completed")
                return result.stdout.strip()
            else:
                print(f"❌ {description} failed: {result.stderr}")
                return None
        except Exception as e:
            print(f"❌ {description} error: {e}")
            return None
    
    def get_ecr_login_token(self):
        """Get ECR login token"""
        login_cmd = f"aws ecr get-login-password --region {self.region}"
        token = self.run_command(login_cmd, "Getting ECR login token")
        
        if token:
            # Login to ECR
            docker_login_cmd = f"echo '{token}' | docker login --username AWS --password-stdin {self.account_id}.dkr.ecr.{self.region}.amazonaws.com"
            return self.run_command(docker_login_cmd, "Logging into ECR")
        
        return None
    
    def build_docker_image(self):
        """Build Docker image"""
        image_name = f"{self.account_id}.dkr.ecr.{self.region}.amazonaws.com/{self.ecr_repo_name}:{self.image_tag}"
        
        build_cmd = f"docker build -f Dockerfile.production -t {image_name} ."
        result = self.run_command(build_cmd, "Building Docker image")
        
        if result:
            return image_name
        return None
    
    def push_to_ecr(self, image_name):
        """Push image to ECR"""
        push_cmd = f"docker push {image_name}"
        return self.run_command(push_cmd, "Pushing image to ECR")
    
    def update_ecs_service(self, image_name):
        """Update ECS service with new image"""
        # Create new task definition
        task_def_cmd = f"aws ecs describe-task-definition --task-definition {self.project_name}-task --region {self.region} --query 'taskDefinition' --output json"
        task_def = self.run_command(task_def_cmd, "Getting current task definition")
        
        if not task_def:
            return False
        
        try:
            task_def_data = json.loads(task_def)
            
            # Update image in container definitions
            for container in task_def_data['containerDefinitions']:
                if container['name'] == 'ai-service':
                    container['image'] = image_name
            
            # Remove fields that can't be included in register-task-definition
            task_def_data.pop('taskDefinitionArn', None)
            task_def_data.pop('revision', None)
            task_def_data.pop('status', None)
            task_def_data.pop('requiresAttributes', None)
            task_def_data.pop('placementConstraints', None)
            task_def_data.pop('compatibilities', None)
            task_def_data.pop('registeredAt', None)
            task_def_data.pop('registeredBy', None)
            
            # Write updated task definition to file
            with open("updated-task-definition.json", "w") as f:
                json.dump(task_def_data, f, indent=2)
            
            # Register new task definition
            register_cmd = f"aws ecs register-task-definition --cli-input-json file://updated-task-definition.json --region {self.region}"
            result = self.run_command(register_cmd, "Registering updated task definition")
            
            # Clean up
            os.remove("updated-task-definition.json")
            
            if result:
                # Update ECS service
                update_cmd = f"aws ecs update-service --cluster {self.project_name}-production-cluster --service {self.project_name}-ai --task-definition {self.project_name}-task --region {self.region}"
                return self.run_command(update_cmd, "Updating ECS service")
            
        except Exception as e:
            print(f"❌ Error updating ECS service: {e}")
            return False
        
        return False
    
    def wait_for_service_update(self):
        """Wait for ECS service to stabilize"""
        print("⏳ Waiting for ECS service to stabilize...")
        
        wait_cmd = f"aws ecs wait services-stable --cluster {self.project_name}-production-cluster --services {self.project_name}-ai --region {self.region}"
        result = self.run_command(wait_cmd, "Waiting for service stability")
        
        if result:
            print("✅ ECS service updated successfully!")
            return True
        else:
            print("❌ ECS service update failed or timed out")
            return False
    
    def deploy(self):
        """Main deployment method"""
        print("🚀 Building and Deploying RichesReach AI Docker Image")
        print("=" * 60)
        
        # Step 1: Login to ECR
        if not self.get_ecr_login_token():
            print("❌ Failed to login to ECR")
            return False
        
        # Step 2: Build Docker image
        image_name = self.build_docker_image()
        if not image_name:
            print("❌ Failed to build Docker image")
            return False
        
        # Step 3: Push to ECR
        if not self.push_to_ecr(image_name):
            print("❌ Failed to push image to ECR")
            return False
        
        # Step 4: Update ECS service
        if not self.update_ecs_service(image_name):
            print("❌ Failed to update ECS service")
            return False
        
        # Step 5: Wait for service to stabilize
        if not self.wait_for_service_update():
            print("❌ Service failed to stabilize")
            return False
        
        print("\n🎉 Docker Image Deployed Successfully!")
        print(f"🐳 Image: {image_name}")
        print(f"🌐 Service: {self.project_name}-ai")
        print(f"📊 Cluster: {self.project_name}-production-cluster")
        
        return True

if __name__ == "__main__":
    deployer = DockerImageDeployer()
    deployer.deploy()
