#!/usr/bin/env python3
"""
Update GitHub Actions IAM policy to include PassRole permission for riches-reach-streaming-role
"""
import json
import boto3
import sys
from pathlib import Path

def update_github_actions_policy():
    """Update the GitHub Actions IAM policy to include streaming role PassRole permission"""
    
    # Initialize AWS IAM client
    try:
        iam = boto3.client('iam', region_name='us-east-1')
        print("SUCCESS: AWS IAM client initialized")
    except Exception as e:
        print(f"ERROR: Failed to initialize AWS IAM client: {e}")
        return False
    
    # Read the updated policy from file
    policy_file = Path(__file__).parent.parent / "iam-permissions-policy.json"
    try:
        with open(policy_file, 'r') as f:
            policy_document = json.load(f)
        print(f"SUCCESS: Read policy from {policy_file}")
    except Exception as e:
        print(f"ERROR: Failed to read policy file: {e}")
        return False
    
    # GitHub Actions role name
    role_name = "GitHubActionsDeployRole"
    
    try:
        # Get the current policy
        response = iam.get_role_policy(
            RoleName=role_name,
            PolicyName="GitHubActionsPolicy"
        )
        current_policy = json.loads(response['PolicyDocument'])
        print("SUCCESS: Retrieved current policy")
        
        # Update the policy with the new document
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName="GitHubActionsPolicy",
            PolicyDocument=json.dumps(policy_document)
        )
        print("SUCCESS: Updated GitHub Actions IAM policy")
        
        # Verify the update
        response = iam.get_role_policy(
            RoleName=role_name,
            PolicyName="GitHubActionsPolicy"
        )
        updated_policy = json.loads(response['PolicyDocument'])
        
        # Check if the streaming role PassRole permission is present
        has_streaming_permission = False
        for statement in updated_policy.get('Statement', []):
            if (statement.get('Sid') == 'PassStreamingRole' and 
                'iam:PassRole' in statement.get('Action', []) and
                'riches-reach-streaming-role' in statement.get('Resource', '')):
                has_streaming_permission = True
                break
        
        if has_streaming_permission:
            print("SUCCESS: Verified that PassRole permission for riches-reach-streaming-role is present")
            return True
        else:
            print("WARNING: PassRole permission for riches-reach-streaming-role not found in updated policy")
            return False
            
    except iam.exceptions.NoSuchEntityException:
        print(f"ERROR: Role {role_name} or policy GitHubActionsPolicy not found")
        print("You may need to create the role and policy first")
        return False
    except Exception as e:
        print(f"ERROR: Failed to update IAM policy: {e}")
        return False

def main():
    """Main function"""
    print("Updating GitHub Actions IAM Policy")
    print("=" * 40)
    
    success = update_github_actions_policy()
    
    if success:
        print("\nSUCCESS: GitHub Actions IAM policy updated successfully!")
        print("The role now has PassRole permission for riches-reach-streaming-role")
        print("You can now retry your ECS deployment")
    else:
        print("\nERROR: Failed to update GitHub Actions IAM policy")
        print("Please check the error messages above and try again")
        sys.exit(1)

if __name__ == "__main__":
    main()
