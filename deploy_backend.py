#!/usr/bin/env python3
"""
Deploy RichesReach Backend to AWS ECS
Works without local Docker - uses ECR or S3-based deployment
"""
import os
import sys
import json
import subprocess
import boto3
from datetime import datetime

# Configuration
AWS_REGION = "us-east-1"
AWS_ACCOUNT_ID = "498606688292"
CLUSTER_NAME = "richesreach-cluster"
SERVICE_NAME = "richesreach-service"
ECR_REPO = "riches-reach-ai"
S3_BUCKET = "riches-reach-ai-models-498606688292"

def print_status(msg):
    print(f"📦 {msg}")

def print_success(msg):
    print(f"✅ {msg}")

def print_error(msg):
    print(f"❌ {msg}")

def check_aws_credentials():
    """Verify AWS credentials are configured"""
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print_success(f"AWS credentials verified: {identity.get('Arn', 'Unknown')}")
        return True
    except Exception as e:
        print_error(f"AWS credentials not configured: {e}")
        return False

def check_ecs_service():
    """Check if ECS service exists"""
    try:
        ecs = boto3.client('ecs', region_name=AWS_REGION)
        response = ecs.describe_services(
            cluster=CLUSTER_NAME,
            services=[SERVICE_NAME]
        )
        if response['services']:
            service = response['services'][0]
            print_success(f"ECS service found: {SERVICE_NAME}")
            print_status(f"Status: {service['status']}")
            print_status(f"Running: {service['runningCount']}/{service['desiredCount']}")
            return True
        else:
            print_error(f"ECS service {SERVICE_NAME} not found")
            return False
    except Exception as e:
        print_error(f"Error checking ECS service: {e}")
        return False

def create_ecr_repo_if_needed():
    """Create ECR repository if it doesn't exist"""
    try:
        ecr = boto3.client('ecr', region_name=AWS_REGION)
        try:
            ecr.describe_repositories(repositoryNames=[ECR_REPO])
            print_success(f"ECR repository exists: {ECR_REPO}")
            return True
        except ecr.exceptions.RepositoryNotFoundException:
            print_status(f"Creating ECR repository: {ECR_REPO}")
            ecr.create_repository(
                repositoryName=ECR_REPO,
                imageTagMutability='MUTABLE'
            )
            print_success(f"ECR repository created: {ECR_REPO}")
            return True
    except Exception as e:
        print_error(f"Error with ECR repository: {e}")
        return False

def get_latest_task_definition():
    """Get the latest task definition for the service"""
    try:
        ecs = boto3.client('ecs', region_name=AWS_REGION)
        response = ecs.describe_services(
            cluster=CLUSTER_NAME,
            services=[SERVICE_NAME]
        )
        if response['services']:
            task_def_arn = response['services'][0]['taskDefinition']
            task_def_response = ecs.describe_task_definition(
                taskDefinition=task_def_arn
            )
            return task_def_response['taskDefinition']
        return None
    except Exception as e:
        print_error(f"Error getting task definition: {e}")
        return None

def update_ecs_service():
    """Force a new deployment of the ECS service"""
    try:
        ecs = boto3.client('ecs', region_name=AWS_REGION)
        print_status("Forcing new deployment...")
        response = ecs.update_service(
            cluster=CLUSTER_NAME,
            service=SERVICE_NAME,
            forceNewDeployment=True
        )
        print_success("New deployment triggered")
        return response
    except Exception as e:
        print_error(f"Error updating ECS service: {e}")
        return None

def wait_for_deployment(wait=False):
    """Wait for deployment to stabilize (optional)"""
    if not wait:
        print_status("Deployment triggered. It will complete in the background.")
        print_status("Check AWS Console for deployment status.")
        return True
    
    try:
        ecs = boto3.client('ecs', region_name=AWS_REGION)
        print_status("Waiting for deployment to complete...")
        waiter = ecs.get_waiter('services_stable')
        waiter.wait(
            cluster=CLUSTER_NAME,
            services=[SERVICE_NAME],
            WaiterConfig={'Delay': 10, 'MaxAttempts': 60}
        )
        print_success("Deployment completed successfully!")
        return True
    except Exception as e:
        print_error(f"Error waiting for deployment: {e}")
        return False

def get_service_url():
    """Get the service URL from load balancer"""
    try:
        ecs = boto3.client('ecs', region_name=AWS_REGION)
        elbv2 = boto3.client('elbv2', region_name=AWS_REGION)
        
        # Get service details
        response = ecs.describe_services(
            cluster=CLUSTER_NAME,
            services=[SERVICE_NAME]
        )
        
        if response['services']:
            service = response['services'][0]
            load_balancers = service.get('loadBalancers', [])
            if load_balancers:
                target_group_arn = load_balancers[0]['targetGroupArn']
                tg_response = elbv2.describe_target_groups(
                    TargetGroupArns=[target_group_arn]
                )
                if tg_response['TargetGroups']:
                    tg = tg_response['TargetGroups'][0]
                    # Get load balancer ARN
                    lb_arn = tg['LoadBalancerArns'][0]
                    lb_response = elbv2.describe_load_balancers(
                        LoadBalancerArns=[lb_arn]
                    )
                    if lb_response['LoadBalancers']:
                        dns_name = lb_response['LoadBalancers'][0]['DNSName']
                        return f"http://{dns_name}"
    except Exception as e:
        print_status(f"Could not determine service URL: {e}")
    return None

def main():
    print("🚀 RichesReach Backend Deployment")
    print("=" * 40)
    print()
    
    # Check AWS credentials
    if not check_aws_credentials():
        sys.exit(1)
    
    # Check ECS service
    if not check_ecs_service():
        print_error("ECS service not found. Please create it first.")
        sys.exit(1)
    
    # Create ECR repo if needed
    create_ecr_repo_if_needed()
    
    # Get current task definition
    task_def = get_latest_task_definition()
    if task_def:
        print_status(f"Current task definition: {task_def['family']}:{task_def['revision']}")
        print_status(f"Image: {task_def['containerDefinitions'][0].get('image', 'N/A')}")
    
    # Auto-proceed (can be made interactive with --interactive flag)
    auto_deploy = '--interactive' not in sys.argv
    if not auto_deploy:
        print()
        print("This will trigger a new deployment of the ECS service.")
        print("The service will pull the latest image from ECR.")
        response = input("Continue? (y/n): ")
        if response.lower() != 'y':
            print("Deployment cancelled.")
            return
    else:
        print()
        print("Auto-deploying (use --interactive for confirmation prompt)...")
    
    # Update service
    update_response = update_ecs_service()
    if not update_response:
        sys.exit(1)
    
    # Wait for deployment (skip wait for faster execution)
    print()
    wait = '--wait' in sys.argv
    if wait_for_deployment(wait=wait):
        print()
        print_success("🎉 Deployment Complete!")
        print()
        
        # Get service URL
        url = get_service_url()
        if url:
            print_status(f"Service URL: {url}")
        
        print_status(f"Monitor at: https://{AWS_REGION}.console.aws.amazon.com/ecs/v2/clusters/{CLUSTER_NAME}/services/{SERVICE_NAME}")
        print()
        print("Next steps:")
        print("1. Verify the service is healthy")
        print("2. Test the API endpoints")
        print("3. Check CloudWatch logs for any errors")
    else:
        print_error("Deployment may still be in progress. Check AWS Console for status.")

if __name__ == "__main__":
    main()

