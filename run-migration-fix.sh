#!/bin/bash

# Run migration fix for the new production image
# Usage: ./run-migration-fix.sh [TASK_DEFINITION_REVISION]

REVISION=${1:-28}
echo "🔧 Running migration fix with task definition: riches-reach-ai-task:$REVISION"

aws ecs run-task \
  --cluster riches-reach-ai-production-cluster \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-037cb59936a709c87],securityGroups=[sg-007dff041138724c3],assignPublicIp=ENABLED}" \
  --task-definition riches-reach-ai-task:$REVISION \
  --overrides '{
    "containerOverrides": [{
      "name": "riches-reach-ai",
      "command": ["python","manage.py","migrate","--fake-initial","--noinput"]
    }]
  }' \
  --region us-east-1

echo "✅ Migration fix task started!"
echo "📊 Monitor with: aws logs describe-log-streams --log-group-name /ecs/riches-reach-ai --order-by LastEventTime --descending --max-items 1 --region us-east-1"
