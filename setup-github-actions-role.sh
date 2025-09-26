#!/bin/bash

# Create IAM role for GitHub Actions to push to ECR
# This script sets up the necessary IAM role and policies

echo "Creating IAM role for GitHub Actions ECR push..."

# Create the trust policy for GitHub OIDC
cat > github-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::498606688292:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:marioncollins/RichesReach:*"
        }
      }
    }
  ]
}
EOF

# Create the role
aws iam create-role \
  --role-name GHA_ECR_PushRole \
  --assume-role-policy-document file://github-trust-policy.json \
  --description "Role for GitHub Actions to push to ECR" \
  --region us-east-1

# Create the policy for ECR push permissions
cat > ecr-push-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:PutImage"
      ],
      "Resource": "arn:aws:ecr:us-east-1:498606688292:repository/riches-reach-ai-ai-service"
    }
  ]
}
EOF

# Create the policy
aws iam create-policy \
  --policy-name GHA_ECR_PushPolicy \
  --policy-document file://ecr-push-policy.json \
  --description "Policy for GitHub Actions to push to ECR" \
  --region us-east-1

# Attach the policy to the role
aws iam attach-role-policy \
  --role-name GHA_ECR_PushRole \
  --policy-arn arn:aws:iam::498606688292:policy/GHA_ECR_PushPolicy \
  --region us-east-1

echo "✅ IAM role setup complete!"
echo "Role ARN: arn:aws:iam::498606688292:role/GHA_ECR_PushRole"
echo ""
echo "Next steps:"
echo "1. Push your changes to GitHub to trigger the build"
echo "2. Monitor the Actions tab in your GitHub repo"
echo "3. Once built, update ECS with the new image"

# Clean up temporary files
rm -f github-trust-policy.json ecr-push-policy.json
