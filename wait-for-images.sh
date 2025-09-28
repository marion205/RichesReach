#!/bin/bash
# Wait for OIDC pipeline to produce ECR images, then hot-swap

echo "⏳ Waiting for OIDC pipeline to produce ECR images..."
echo ""

while true; do
  echo "Checking for ECR images..."
  IMAGES=$(aws ecr describe-images --repository-name riches-reach-ai \
    --query 'imageDetails[].imageTags' --output text 2>/dev/null || echo "")
  
  if [ -n "$IMAGES" ] && [ "$IMAGES" != "None" ]; then
    echo "✅ ECR images found!"
    echo ""
    echo "Latest images:"
    aws ecr describe-images --repository-name riches-reach-ai \
      --query 'reverse(sort_by(imageDetails,& imagePushedAt))[0:3].[imageTags,imagePushedAt]' --output table
    echo ""
    echo "🚀 Running hot-swap..."
    ./hot-swap-service.sh
    break
  else
    echo "❌ No images yet - OIDC pipeline still building"
    echo "Check GitHub Actions: https://github.com/marion205/RichesReach/actions"
    echo ""
    echo "Waiting 30 seconds before next check..."
    sleep 30
  fi
done
