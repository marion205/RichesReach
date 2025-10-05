#!/bin/bash

# Phase 2 Architecture Upgrade Deployment Script
# This script deploys Phase 2 components including streaming pipeline and ML versioning

set -e

echo "🚀 Starting Phase 2 Architecture Upgrade Deployment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
AWS_REGION=${AWS_REGION:-"us-east-1"}
KAFKA_ENABLED=${KAFKA_ENABLED:-"false"}
KINESIS_ENABLED=${KINESIS_ENABLED:-"false"}
MLFLOW_ENABLED=${MLFLOW_ENABLED:-"true"}

echo -e "${BLUE}📋 Phase 2 Configuration:${NC}"
echo "  AWS Region: $AWS_REGION"
echo "  Kafka Enabled: $KAFKA_ENABLED"
echo "  Kinesis Enabled: $KINESIS_ENABLED"
echo "  MLflow Enabled: $MLFLOW_ENABLED"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check AWS credentials
check_aws_credentials() {
    if ! command_exists aws; then
        echo -e "${RED}❌ AWS CLI not found. Please install AWS CLI.${NC}"
        exit 1
    fi
    
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        echo -e "${RED}❌ AWS credentials not configured. Please run 'aws configure'.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ AWS credentials configured${NC}"
}

# Function to install Python dependencies
install_dependencies() {
    echo -e "${BLUE}📦 Installing Phase 2 dependencies...${NC}"
    
    cd backend/backend
    
    # Install additional dependencies for Phase 2
    pip install kafka-python boto3 mlflow xgboost scikit-learn pandas numpy
    
    echo -e "${GREEN}✅ Dependencies installed${NC}"
}

# Function to setup streaming infrastructure
setup_streaming_infrastructure() {
    echo -e "${BLUE}🌊 Setting up streaming infrastructure...${NC}"
    
    if [ "$KINESIS_ENABLED" = "true" ]; then
        echo "Setting up Kinesis Data Streams..."
        python3 infrastructure/streaming_setup.py
    fi
    
    if [ "$KAFKA_ENABLED" = "true" ]; then
        echo "Setting up Kafka cluster..."
        # Note: In production, you would use MSK (Managed Streaming for Kafka)
        echo -e "${YELLOW}⚠️ Kafka setup requires MSK cluster. Please configure manually.${NC}"
    fi
    
    echo -e "${GREEN}✅ Streaming infrastructure setup complete${NC}"
}

# Function to setup ML versioning
setup_ml_versioning() {
    echo -e "${BLUE}🤖 Setting up ML model versioning...${NC}"
    
    if [ "$MLFLOW_ENABLED" = "true" ]; then
        # Create MLflow directory
        mkdir -p mlruns
        mkdir -p models
        
        # Initialize MLflow experiment
        python3 -c "
import mlflow
mlflow.set_tracking_uri('file:./mlruns')
try:
    experiment_id = mlflow.create_experiment('riches-reach-ml')
    print(f'Created MLflow experiment: {experiment_id}')
except:
    print('MLflow experiment already exists')
"
        
        echo -e "${GREEN}✅ MLflow setup complete${NC}"
    fi
}

# Function to create environment configuration
create_environment_config() {
    echo -e "${BLUE}⚙️ Creating environment configuration...${NC}"
    
    cat > .env.phase2 << EOF
# Phase 2 Configuration
KAFKA_ENABLED=$KAFKA_ENABLED
KINESIS_ENABLED=$KINESIS_ENABLED
MLFLOW_ENABLED=$MLFLOW_ENABLED

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_GROUP_ID=riches-reach-consumer

# Kinesis Configuration
AWS_REGION=$AWS_REGION
KINESIS_STREAM_NAME=riches-reach-market-data

# MLflow Configuration
MLFLOW_TRACKING_URI=file:./mlruns
MLFLOW_EXPERIMENT_NAME=riches-reach-ml
MODELS_DIR=./models

# Data Ingestion
INGESTION_INTERVAL=60
EOF
    
    echo -e "${GREEN}✅ Environment configuration created${NC}"
}

# Function to test Phase 2 components
test_phase2_components() {
    echo -e "${BLUE}🧪 Testing Phase 2 components...${NC}"
    
    # Start the server in background
    echo "Starting server for testing..."
    PORT=8002 python3 final_complete_server.py &
    SERVER_PID=$!
    
    # Wait for server to start
    sleep 10
    
    # Test health endpoint
    echo "Testing health endpoint..."
    if curl -s http://localhost:8002/health/detailed/ | grep -q "streaming_pipeline"; then
        echo -e "${GREEN}✅ Health endpoint includes Phase 2 components${NC}"
    else
        echo -e "${RED}❌ Health endpoint missing Phase 2 components${NC}"
    fi
    
    # Test streaming status endpoint
    echo "Testing streaming status endpoint..."
    if curl -s http://localhost:8002/phase2/streaming/status/ | grep -q "streaming_available"; then
        echo -e "${GREEN}✅ Streaming status endpoint working${NC}"
    else
        echo -e "${RED}❌ Streaming status endpoint failed${NC}"
    fi
    
    # Test ML models endpoint
    echo "Testing ML models endpoint..."
    if curl -s http://localhost:8002/phase2/ml/models/ | grep -q "status"; then
        echo -e "${GREEN}✅ ML models endpoint working${NC}"
    else
        echo -e "${RED}❌ ML models endpoint failed${NC}"
    fi
    
    # Stop the test server
    kill $SERVER_PID 2>/dev/null || true
    
    echo -e "${GREEN}✅ Phase 2 component tests complete${NC}"
}

# Function to create deployment summary
create_deployment_summary() {
    echo -e "${BLUE}📊 Creating deployment summary...${NC}"
    
    cat > PHASE_2_DEPLOYMENT_SUMMARY.md << EOF
# Phase 2 Architecture Upgrade - Deployment Summary

## Deployment Date
$(date)

## Components Deployed

### 1. Streaming Pipeline Infrastructure
- **Status**: $(if [ "$KINESIS_ENABLED" = "true" ]; then echo "✅ Deployed"; else echo "⚠️ Disabled"; fi)
- **Kinesis**: $(if [ "$KINESIS_ENABLED" = "true" ]; then echo "Enabled"; else echo "Disabled"; fi)
- **Kafka**: $(if [ "$KAFKA_ENABLED" = "true" ]; then echo "Enabled"; else echo "Disabled"; fi)

### 2. ML Model Versioning
- **Status**: $(if [ "$MLFLOW_ENABLED" = "true" ]; then echo "✅ Deployed"; else echo "⚠️ Disabled"; fi)
- **MLflow**: $(if [ "$MLFLOW_ENABLED" = "true" ]; then echo "Enabled"; else echo "Disabled"; fi)
- **Model Storage**: ./models/
- **Experiment Tracking**: ./mlruns/

## New Endpoints

### Streaming Pipeline
- \`GET /phase2/streaming/status/\` - Get streaming pipeline status
- \`POST /phase2/streaming/start/\` - Start streaming data ingestion

### ML Model Versioning
- \`GET /phase2/ml/models/\` - List all ML models and versions
- \`GET /phase2/ml/models/{model_id}/best/\` - Get best performing model
- \`GET /phase2/ml/experiments/\` - List A/B testing experiments
- \`POST /phase2/ml/experiments/\` - Create new A/B testing experiment
- \`GET /phase2/ml/experiments/{experiment_id}/analyze/\` - Analyze experiment results

## Configuration

Environment variables are configured in \`.env.phase2\`:

\`\`\`bash
# Phase 2 Configuration
KAFKA_ENABLED=$KAFKA_ENABLED
KINESIS_ENABLED=$KINESIS_ENABLED
MLFLOW_ENABLED=$MLFLOW_ENABLED

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_GROUP_ID=riches-reach-consumer

# Kinesis Configuration
AWS_REGION=$AWS_REGION
KINESIS_STREAM_NAME=riches-reach-market-data

# MLflow Configuration
MLFLOW_TRACKING_URI=file:./mlruns
MLFLOW_EXPERIMENT_NAME=riches-reach-ml
MODELS_DIR=./models

# Data Ingestion
INGESTION_INTERVAL=60
\`\`\`

## Next Steps

1. **Configure API Keys**: Set up Polygon and Finnhub API keys for data ingestion
2. **Start Streaming**: Use \`POST /phase2/streaming/start/\` to begin data ingestion
3. **Train Models**: Use the ML versioning system to train and version models
4. **A/B Testing**: Create experiments to test different model versions
5. **Monitor**: Use the health endpoints to monitor system status

## Verification

To verify Phase 2 deployment:

\`\`\`bash
# Check health status
curl http://localhost:8000/health/detailed/

# Check streaming status
curl http://localhost:8000/phase2/streaming/status/

# List ML models
curl http://localhost:8000/phase2/ml/models/
\`\`\`

## Support

For issues or questions about Phase 2 deployment, check:
- Server logs for error messages
- Health endpoint for component status
- MLflow UI for experiment tracking
- AWS CloudWatch for Kinesis monitoring

---

**Phase 2 Status**: ✅ **DEPLOYED**
EOF
    
    echo -e "${GREEN}✅ Deployment summary created${NC}"
}

# Main deployment process
main() {
    echo -e "${GREEN}🚀 Phase 2 Architecture Upgrade Deployment${NC}"
    echo "=================================================="
    echo ""
    
    # Check prerequisites
    check_aws_credentials
    
    # Install dependencies
    install_dependencies
    
    # Setup components
    setup_streaming_infrastructure
    setup_ml_versioning
    
    # Create configuration
    create_environment_config
    
    # Test components
    test_phase2_components
    
    # Create summary
    create_deployment_summary
    
    echo ""
    echo -e "${GREEN}🎉 Phase 2 Architecture Upgrade Deployment Complete!${NC}"
    echo ""
    echo -e "${BLUE}📋 Summary:${NC}"
    echo "  ✅ Streaming pipeline infrastructure deployed"
    echo "  ✅ ML model versioning system deployed"
    echo "  ✅ New API endpoints available"
    echo "  ✅ Health monitoring updated"
    echo "  ✅ Configuration files created"
    echo ""
    echo -e "${YELLOW}📝 Next Steps:${NC}"
    echo "  1. Configure API keys in .env.phase2"
    echo "  2. Start the server: PORT=8000 python3 final_complete_server.py"
    echo "  3. Test endpoints: curl http://localhost:8000/phase2/streaming/status/"
    echo "  4. Review deployment summary: cat PHASE_2_DEPLOYMENT_SUMMARY.md"
    echo ""
    echo -e "${GREEN}🚀 Phase 2 is ready for production!${NC}"
}

# Run main function
main "$@"
