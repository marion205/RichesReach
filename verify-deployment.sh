#!/bin/bash

# Verify the production deployment
echo "🔍 Checking ECS service status..."

# Get service status
aws ecs describe-services \
  --cluster riches-reach-ai-production-cluster \
  --services riches-reach-ai-ai \
  --region us-east-1 \
  --query 'services[0].{Status:status,Running:runningCount,Desired:desiredCount,TaskDef:taskDefinition}' \
  --output table

echo ""
echo "🔍 Getting public IP..."

# Get the public IP
TASK_ARN=$(aws ecs list-tasks --cluster riches-reach-ai-production-cluster --service riches-reach-ai-ai --region us-east-1 --query 'taskArns[0]' --output text 2>/dev/null)

if [ "$TASK_ARN" != "None" ] && [ "$TASK_ARN" != "" ]; then
  ENI_ID=$(aws ecs describe-tasks --cluster riches-reach-ai-production-cluster --tasks $TASK_ARN --region us-east-1 --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value' --output text 2>/dev/null)
  
  if [ "$ENI_ID" != "None" ] && [ "$ENI_ID" != "" ]; then
    IP=$(aws ec2 describe-network-interfaces --network-interface-ids $ENI_ID --region us-east-1 --query 'NetworkInterfaces[0].Association.PublicIp' --output text 2>/dev/null)
    
    if [ "$IP" != "None" ] && [ "$IP" != "" ]; then
      echo "Public IP: $IP"
      echo ""
      echo "🔍 Testing endpoints..."
      
      # Test health endpoint
      echo "Health check:"
      curl -sS "http://$IP:8000/health/" -i
      echo ""
      
      # Test admin endpoint
      echo "Admin endpoint:"
      curl -I "http://$IP:8000/admin/" 2>/dev/null || echo "Admin endpoint not accessible"
      echo ""
      
      # Test root endpoint
      echo "Root endpoint:"
      curl -sS "http://$IP:8000/" -i
      echo ""
    else
      echo "❌ Could not get public IP"
    fi
  else
    echo "❌ Could not get network interface ID"
  fi
else
  echo "❌ No running tasks found"
fi

echo ""
echo "🔍 Latest logs:"
aws logs describe-log-streams \
  --log-group-name /ecs/riches-reach-ai \
  --order-by LastEventTime \
  --descending \
  --max-items 1 \
  --region us-east-1 \
  --query 'logStreams[0].logStreamName' \
  --output text | xargs -I {} aws logs get-log-events \
  --log-group-name /ecs/riches-reach-ai \
  --log-stream-name {} \
  --region us-east-1 \
  --query 'events[-10:].message' \
  --output text
