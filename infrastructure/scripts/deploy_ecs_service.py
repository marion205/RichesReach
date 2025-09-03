#!/usr/bin/env python3
"""
Deploy RichesReach AI Application to ECS
"""

import subprocess
import json
import os

class ECSDeployer:
    def __init__(self):
        self.project_name = "riches-reach-ai"
        self.region = "us-east-1"
        self.cluster_name = "riches-reach-ai-production-cluster"
        
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
    
    def create_task_definition(self):
        """Create ECS task definition"""
        task_def = {
            "family": f"{self.project_name}-task",
            "networkMode": "awsvpc",
            "requiresCompatibilities": ["FARGATE"],
            "cpu": "512",
            "memory": "1024",
            "executionRoleArn": f"arn:aws:iam::{os.environ.get('AWS_ACCOUNT_ID', '498606688292')}:role/riches-reach-ai-production-ecs-execution-role",
            "taskRoleArn": f"arn:aws:iam::{os.environ.get('AWS_ACCOUNT_ID', '498606688292')}:role/riches-reach-ai-production-ecs-task-role",
            "containerDefinitions": [
                {
                    "name": "ai-service",
                    "image": "python:3.10-slim",
                    "portMappings": [
                        {
                            "containerPort": 8000,
                            "protocol": "tcp"
                        }
                    ],
                    "essential": True,
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": f"/ecs/{self.project_name}-production",
                            "awslogs-region": self.region,
                            "awslogs-stream-prefix": "ecs"
                        }
                    },
                    "command": [
                        "sh", "-c",
                        "pip install fastapi uvicorn && echo 'RichesReach AI Service Starting...' && sleep 3600"
                    ]
                }
            ]
        }
        
        # Write task definition to file
        with open("task-definition.json", "w") as f:
            json.dump(task_def, f, indent=2)
        
        # Register task definition
        register_cmd = f"aws ecs register-task-definition --cli-input-json file://task-definition.json --region {self.region}"
        result = self.run_command(register_cmd, "Registering ECS task definition")
        
        # Clean up
        os.remove("task-definition.json")
        
        return result
    
    def create_service(self):
        """Create ECS service"""
        # Get subnet and security group from CloudFormation outputs
        subnet_cmd = f"aws cloudformation describe-stacks --stack-name {self.project_name}-production --region {self.region} --query 'Stacks[0].Outputs[?OutputKey==`SubnetId`].OutputValue' --output text"
        subnet_id = self.run_command(subnet_cmd, "Getting subnet ID")
        
        sg_cmd = f"aws cloudformation describe-stacks --stack-name {self.project_name}-production --region {self.region} --query 'Stacks[0].Outputs[?OutputKey==`SecurityGroupId`].OutputValue' --output text"
        security_group_id = self.run_command(sg_cmd, "Getting security group ID")
        
        if subnet_id and security_group_id:
            # Create service
            service_cmd = f"""aws ecs create-service \
                --cluster {self.cluster_name} \
                --service-name {self.project_name}-ai \
                --task-definition {self.project_name}-task \
                --desired-count 1 \
                --launch-type FARGATE \
                --network-configuration "awsvpcConfiguration={{subnets=[{subnet_id}],securityGroups=[{security_group_id}],assignPublicIp=ENABLED}}" \
                --region {self.region}"""
            
            return self.run_command(service_cmd, "Creating ECS service")
        
        return None
    
    def deploy(self):
        """Main deployment method"""
        print("Deploying RichesReach AI to ECS")
        print("=" * 40)
        
        # Create task definition
        if not self.create_task_definition():
            print("ERROR: Failed to create task definition")
            return False
        
        # Create service
        if not self.create_service():
            print("ERROR: Failed to create ECS service")
            return False
        
        print("\nSUCCESS: ECS Service Deployed Successfully!")
        print(f"🌐 Cluster: {self.cluster_name}")
        print(f"🔗 Service: {self.project_name}-ai")
        print("\nNext Steps:")
        print("1. 🐳 Build and push Docker image to ECR")
        print("2. 🔄 Update service with production image")
        print("3. Monitor service health")
        print("4. Scale as needed")
        
        return True

if __name__ == "__main__":
    deployer = ECSDeployer()
    deployer.deploy()
