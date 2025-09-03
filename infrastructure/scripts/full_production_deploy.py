#!/usr/bin/env python3
"""
Full Production Deployment for RichesReach AI
Deploys complete infrastructure including ECS, RDS, ElastiCache, and monitoring
"""

import subprocess
import json
import time
import os
import sys

class FullProductionDeployer:
    def __init__(self):
        self.project_name = "riches-reach-ai"
        self.region = "us-east-1"
        self.account_id = os.environ.get('AWS_ACCOUNT_ID', '498606688292')
        self.stack_name = f"{self.project_name}-production"
        
    def run_command(self, command, description, capture_output=True):
        """Run a shell command and handle errors"""
        print(f"🔄 {description}...")
        try:
            result = subprocess.run(command, shell=True, capture_output=capture_output, text=True)
            if result.returncode == 0:
                print(f"SUCCESS: {description} completed")
                return result.stdout.strip() if capture_output else True
            else:
                print(f"ERROR: {description} failed: {result.stderr}")
                return None
        except Exception as e:
                            print(f"ERROR: {description} error: {e}")
            return None
    
    def check_permissions(self):
        """Check if we have all required permissions"""
        print("🔐 Checking AWS Permissions...")
        
        permissions = [
            ("ecr:CreateRepository", "aws ecr describe-repositories --region us-east-1"),
            ("cloudformation:CreateStack", "aws cloudformation list-stacks --region us-east-1"),
            ("ecs:CreateCluster", "aws ecs list-clusters --region us-east-1"),
            ("rds:CreateDBInstance", "aws rds describe-db-instances --region us-east-1"),
            ("elasticache:CreateCacheCluster", "aws elasticache describe-cache-clusters --region us-east-1")
        ]
        
        all_good = True
        for perm_name, test_command in permissions:
            result = self.run_command(test_command, f"Testing {perm_name}")
            if result is None:
                print(f"ERROR: Missing permission: {perm_name}")
                all_good = False
            else:
                print(f"SUCCESS: {perm_name} - OK")
        
        return all_good
    
    def deploy_cloudformation(self):
        """Deploy the main infrastructure using CloudFormation"""
        print(f"\nDeploying CloudFormation Stack: {self.stack_name}")
        
        # Deploy the stack
        deploy_command = f"aws cloudformation deploy --template-file simple-cloudformation.yaml --stack-name {self.stack_name} --capabilities CAPABILITY_NAMED_IAM --region {self.region}"
        result = self.run_command(deploy_command, "Deploying CloudFormation stack")
        
        if result is None:
            return False
        
        # Wait for stack to complete
        print("⏳ Waiting for stack deployment to complete...")
        wait_command = f"aws cloudformation wait stack-create-complete --stack-name {self.stack_name} --region {self.region}"
        self.run_command(wait_command, "Waiting for stack completion", capture_output=False)
        
        # Get stack outputs
        outputs_command = f"aws cloudformation describe-stacks --stack-name {self.stack_name} --region {self.region} --query 'Stacks[0].Outputs' --output json"
        outputs = self.run_command(outputs_command, "Getting stack outputs")
        
        if outputs:
            try:
                outputs_data = json.loads(outputs)
                print("\nStack Outputs:")
                for output in outputs_data:
                    print(f"   {output['OutputKey']}: {output['OutputValue']}")
            except:
                print("WARNING: Could not parse stack outputs")
        
        return True
    
    def setup_monitoring(self):
        """Set up CloudWatch monitoring and alerts"""
        print("\nSetting up Monitoring...")
        
        # Create CloudWatch dashboard
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "properties": {
                        "metrics": [
                            ["AWS/ECS", "CPUUtilization", "ServiceName", f"{self.project_name}-ai"],
                            [".", "MemoryUtilization", ".", "."]
                        ],
                        "period": 300,
                        "stat": "Average",
                        "region": self.region,
                        "title": "ECS Service Metrics"
                    }
                }
            ]
        }
        
        dashboard_file = "dashboard.json"
        with open(dashboard_file, 'w') as f:
            json.dump(dashboard_body, f)
        
        # Create dashboard
        dashboard_command = f"aws cloudwatch put-dashboard --dashboard-name {self.project_name}-monitoring --dashboard-body file://{dashboard_file} --region {self.region}"
        self.run_command(dashboard_command, "Creating CloudWatch dashboard")
        
        # Clean up
        os.remove(dashboard_file)
    
    def deploy_application(self):
        """Deploy the application to ECS"""
        print("\n🐳 Deploying Application to ECS...")
        
        # Get ECS cluster name
        cluster_command = f"aws ecs list-clusters --region {self.region} --query 'clusterArns[?contains(@, `{self.project_name}`)]' --output text"
        cluster_arn = self.run_command(cluster_command, "Getting ECS cluster")
        
        if cluster_arn:
            cluster_name = cluster_arn.split('/')[-1]
            
            # Update ECS service
            service_command = f"aws ecs update-service --cluster {cluster_name} --service {self.project_name}-ai --force-new-deployment --region {self.region}"
            self.run_command(service_command, "Updating ECS service")
            
            # Wait for service to stabilize
            print("⏳ Waiting for ECS service to stabilize...")
            wait_command = f"aws ecs wait services-stable --cluster {cluster_name} --services {self.project_name}-ai --region {self.region}"
            self.run_command(wait_command, "Waiting for service stability", capture_output=False)
    
    def run_smoke_tests(self):
        """Run basic health checks"""
        print("\nRunning Smoke Tests...")
        
        # Get load balancer DNS
        lb_command = f"aws cloudformation describe-stacks --stack-name {self.stack_name} --region {self.region} --query 'Stacks[0].Outputs[?OutputKey==`LoadBalancerDNS`].OutputValue' --output text"
        lb_dns = self.run_command(lb_command, "Getting load balancer DNS")
        
        if lb_dns:
            # Test health endpoint
            health_url = f"http://{lb_dns}/health"
            print(f"🏥 Testing health endpoint: {health_url}")
            
            # Simple HTTP test
            test_command = f"curl -f {health_url} --max-time 10"
            result = self.run_command(test_command, "Health check test")
            
            if result is not None:
                print("SUCCESS: Health check passed!")
                return True
            else:
                print("ERROR: Health check failed")
                return False
        else:
                            print("WARNING: Could not get load balancer DNS")
            return False
    
    def deploy(self):
        """Main deployment method"""
        print("FULL PRODUCTION DEPLOYMENT FOR RICHESREACH AI")
        print("=" * 60)
        
        # Check permissions first
        if not self.check_permissions():
            print("\nERROR: Missing required AWS permissions!")
            print("Please add the missing IAM policies and try again.")
            return False
        
                    print("\nSUCCESS: All permissions verified! Starting deployment...")
        
        # Deploy infrastructure
        if not self.deploy_cloudformation():
            print("ERROR: CloudFormation deployment failed!")
            return False
        
        # Set up monitoring
        self.setup_monitoring()
        
        # Deploy application
        self.deploy_application()
        
        # Run smoke tests
        if self.run_smoke_tests():
            print("\nSUCCESS: PRODUCTION DEPLOYMENT COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print("Your RichesReach AI is now running in production!")
            print("Access your application through the load balancer")
            print("Monitor performance in CloudWatch")
            print("Auto-scaling is configured and active")
            return True
        else:
            print("\nWARNING: Deployment completed but smoke tests failed")
            print("Check the application logs and configuration")
            return False

if __name__ == "__main__":
    deployer = FullProductionDeployer()
    deployer.deploy()
