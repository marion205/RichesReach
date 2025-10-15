#!/usr/bin/env python3
"""
Create GitHub Actions IAM role and policy for ECS deployment
"""
import json
import boto3
import sys
from pathlib import Path

def create_github_actions_role():
    """Create the GitHub Actions IAM role and policy"""
    
    # Initialize AWS IAM client
    try:
        iam = boto3.client('iam', region_name='us-east-1')
        print("SUCCESS: AWS IAM client initialized")
    except Exception as e:
        print(f"ERROR: Failed to initialize AWS IAM client: {e}")
        return False
    
    # Read the trust policy
    trust_policy_file = Path(__file__).parent.parent / "iam-trust-policy.json"
    try:
        with open(trust_policy_file, 'r') as f:
            trust_policy = json.load(f)
        print(f"SUCCESS: Read trust policy from {trust_policy_file}")
    except Exception as e:
        print(f"ERROR: Failed to read trust policy file: {e}")
        return False
    
    # Read the permissions policy
    permissions_policy_file = Path(__file__).parent.parent / "iam-permissions-policy.json"
    try:
        with open(permissions_policy_file, 'r') as f:
            permissions_policy = json.load(f)
        print(f"SUCCESS: Read permissions policy from {permissions_policy_file}")
    except Exception as e:
        print(f"ERROR: Failed to read permissions policy file: {e}")
        return False
    
    role_name = "GitHubActionsDeployRole"
    policy_name = "GitHubActionsPolicy"
    
    try:
        # Create the IAM role
        print(f"Creating IAM role: {role_name}")
        iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Role for GitHub Actions to deploy to ECS"
        )
        print(f"SUCCESS: Created IAM role {role_name}")
        
        # Attach the permissions policy
        print(f"Attaching policy {policy_name} to role {role_name}")
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(permissions_policy)
        )
        print(f"SUCCESS: Attached policy {policy_name} to role {role_name}")
        
        # Wait a moment for the role to be fully created
        import time
        time.sleep(5)
        
        print("SUCCESS: GitHub Actions IAM role and policy created successfully!")
        return True
        
    except iam.exceptions.EntityAlreadyExistsException:
        print(f"Role {role_name} already exists. Updating policy...")
        try:
            iam.put_role_policy(
                RoleName=role_name,
                PolicyName=policy_name,
                PolicyDocument=json.dumps(permissions_policy)
            )
            print(f"SUCCESS: Updated policy {policy_name} for existing role {role_name}")
            return True
        except Exception as e:
            print(f"ERROR: Failed to update existing role policy: {e}")
            return False
    except Exception as e:
        print(f"ERROR: Failed to create IAM role: {e}")
        return False

def main():
    """Main function"""
    print("Creating GitHub Actions IAM Role and Policy")
    print("=" * 45)
    
    success = create_github_actions_role()
    
    if success:
        print("\nSUCCESS: GitHub Actions IAM role and policy created/updated successfully!")
        print("The role now has all necessary permissions including PassRole for riches-reach-streaming-role")
        print("You can now retry your ECS deployment")
    else:
        print("\nERROR: Failed to create/update GitHub Actions IAM role and policy")
        print("Please check the error messages above and try again")
        sys.exit(1)

if __name__ == "__main__":
    main()
