#!/bin/bash

set -euo pipefail

REGION=us-east-1
REPO=riches-reach-ai-ai-service
REG=498606688292.dkr.ecr.$REGION.amazonaws.com

echo "Waiting for latest-prod image to be available..."

# Wait for latest-prod to appear
while true; do
  if aws ecr describe-images --region $REGION \
    --repository-name $REPO \
    --image-ids imageTag=latest-prod \
    --query 'imageDetails[0].imageDigest' --output text 2>/dev/null; then
    break
  fi
  echo "Waiting for latest-prod image..."
  sleep 10
done

# get digest for latest-prod
DIGEST=$(aws ecr describe-images --region $REGION \
  --repository-name $REPO \
  --image-ids imageTag=latest-prod \
  --query 'imageDetails[0].imageDigest' --output text)

echo "Found latest-prod with digest: $DIGEST"

# fetch current TD as JSON
aws ecs describe-task-definition \
  --task-definition riches-reach-ai-task \
  --region $REGION --query 'taskDefinition' > td.json

# set image by digest + set a normal, clean start command
jq --arg img "$REG/$REPO@$DIGEST" '
  del(.taskDefinitionArn,.revision,.status,.requiresAttributes,.compatibilities,.registeredAt,.registeredBy)
  | .containerDefinitions[0].image = $img
  | .containerDefinitions[0].command = ["/bin/sh","-lc",
    "python manage.py migrate --noinput && python manage.py collectstatic --noinput || true && exec gunicorn richesreach.asgi:application -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --workers 3 --timeout 60"
  ]
' td.json > td-clean.json

echo "Created clean task definition with image: $REG/$REPO@$DIGEST"

# register + update service
REV=$(aws ecs register-task-definition --cli-input-json file://td-clean.json \
  --region $REGION --query 'taskDefinition.revision' --output text)

echo "Registered new task definition revision: $REV"

aws ecs update-service --cluster riches-reach-ai-production-cluster \
  --service riches-reach-ai-ai \
  --task-definition riches-reach-ai-task:$REV \
  --region $REGION >/dev/null

echo "Service update initiated. Waiting for deployment to complete..."

aws ecs wait services-stable --cluster riches-reach-ai-production-cluster \
  --services riches-reach-ai-ai --region $REGION

echo "Deployment completed successfully!"

# Get the public IP and test
TASK_ARN=$(aws ecs list-tasks --cluster riches-reach-ai-production-cluster --service riches-reach-ai-ai --region us-east-1 --query 'taskArns[0]' --output text)
ENI_ID=$(aws ecs describe-tasks --cluster riches-reach-ai-production-cluster --tasks "$TASK_ARN" --region us-east-1 --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text)
IP=$(aws ec2 describe-network-interfaces --network-interface-ids "$ENI_ID" --region us-east-1 --query 'NetworkInterfaces[0].Association.PublicIp' --output text)

echo "Application is running at: http://$IP:8000"
echo "Testing health endpoint..."
curl -sS "http://$IP:8000/health/" -i

echo "Testing admin endpoint..."
curl -I "http://$IP:8000/admin/"

echo "Clean deployment completed successfully!"
