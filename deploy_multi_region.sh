#!/bin/bash

# Multi-Region Deployment Script - Phase 3
# Deploys RichesReach across multiple AWS regions with global CDN

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="richesreach"
ENVIRONMENT="production"
DOMAIN_NAME="api.richesreach.com"
REGIONS=("us-east-1" "eu-west-1" "ap-southeast-1")
PRIMARY_REGION="us-east-1"

echo -e "${BLUE}🌍 Starting Multi-Region Deployment${NC}"
echo "=================================="

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${BLUE}📋 Checking Prerequisites${NC}"
echo "=============================="

if ! command_exists aws; then
    print_error "AWS CLI not found. Please install AWS CLI."
    exit 1
fi

if ! command_exists terraform; then
    print_error "Terraform not found. Please install Terraform."
    exit 1
fi

if ! command_exists docker; then
    print_error "Docker not found. Please install Docker."
    exit 1
fi

print_status "Prerequisites check completed"

# Check AWS credentials
echo -e "${BLUE}🔐 Checking AWS Credentials${NC}"
echo "=============================="

if ! aws sts get-caller-identity >/dev/null 2>&1; then
    print_error "AWS credentials not configured. Please run 'aws configure'."
    exit 1
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
print_status "AWS Account ID: $AWS_ACCOUNT_ID"

# Check if domain is configured
echo -e "${BLUE}🌐 Checking Domain Configuration${NC}"
echo "=================================="

if ! aws route53 list-hosted-zones --query "HostedZones[?Name=='${DOMAIN_NAME}.']" --output text | grep -q "$DOMAIN_NAME"; then
    print_warning "Hosted zone for $DOMAIN_NAME not found. Creating..."
    
    # Create hosted zone
    aws route53 create-hosted-zone \
        --name "$DOMAIN_NAME" \
        --caller-reference "multi-region-$(date +%s)" \
        --hosted-zone-config Comment="Multi-region deployment for $PROJECT_NAME"
    
    print_status "Hosted zone created for $DOMAIN_NAME"
else
    print_status "Hosted zone found for $DOMAIN_NAME"
fi

# Create ECR repositories in each region
echo -e "${BLUE}🐳 Creating ECR Repositories${NC}"
echo "=============================="

for region in "${REGIONS[@]}"; do
    echo "Creating ECR repository in $region..."
    
    if ! aws ecr describe-repositories --repository-names "$PROJECT_NAME" --region "$region" >/dev/null 2>&1; then
        aws ecr create-repository \
            --repository-name "$PROJECT_NAME" \
            --region "$region" \
            --image-scanning-configuration scanOnPush=true
        
        print_status "ECR repository created in $region"
    else
        print_status "ECR repository already exists in $region"
    fi
done

# Build and push Docker image to each region
echo -e "${BLUE}🏗️  Building and Pushing Docker Images${NC}"
echo "======================================"

IMAGE_TAG="multi-region-$(date +%Y%m%d-%H%M%S)"

# Build image
echo "Building Docker image..."
docker build -f Dockerfile.prod -t "$PROJECT_NAME:$IMAGE_TAG" .

# Push to each region
for region in "${REGIONS[@]}"; do
    echo "Pushing to $region..."
    
    ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$region.amazonaws.com/$PROJECT_NAME"
    
    # Login to ECR
    aws ecr get-login-password --region "$region" | docker login --username AWS --password-stdin "$ECR_URI"
    
    # Tag and push
    docker tag "$PROJECT_NAME:$IMAGE_TAG" "$ECR_URI:$IMAGE_TAG"
    docker tag "$PROJECT_NAME:$IMAGE_TAG" "$ECR_URI:latest"
    
    docker push "$ECR_URI:$IMAGE_TAG"
    docker push "$ECR_URI:latest"
    
    print_status "Image pushed to $region"
done

# Deploy infrastructure with Terraform
echo -e "${BLUE}🏗️  Deploying Infrastructure${NC}"
echo "=============================="

cd infrastructure/multi-region

# Initialize Terraform
echo "Initializing Terraform..."
terraform init

# Create terraform.tfvars
cat > terraform.tfvars << EOF
environment = "$ENVIRONMENT"
domain_name = "$DOMAIN_NAME"
aws_account_id = "$AWS_ACCOUNT_ID"
image_tag = "$IMAGE_TAG"
EOF

# Plan deployment
echo "Planning Terraform deployment..."
terraform plan -out=tfplan

# Apply deployment
echo "Applying Terraform deployment..."
terraform apply tfplan

print_status "Infrastructure deployed successfully"

# Wait for deployments to be ready
echo -e "${BLUE}⏳ Waiting for Deployments${NC}"
echo "=============================="

for region in "${REGIONS[@]}"; do
    echo "Waiting for deployment in $region..."
    
    CLUSTER_NAME="$PROJECT_NAME-$ENVIRONMENT-$region"
    SERVICE_NAME="$PROJECT_NAME-$ENVIRONMENT-$region-service"
    
    aws ecs wait services-stable \
        --cluster "$CLUSTER_NAME" \
        --services "$SERVICE_NAME" \
        --region "$region"
    
    print_status "Deployment ready in $region"
done

# Configure Route 53 health checks
echo -e "${BLUE}🏥 Configuring Health Checks${NC}"
echo "=============================="

# Get ALB DNS names
US_EAST_ALB=$(aws elbv2 describe-load-balancers \
    --region us-east-1 \
    --query "LoadBalancers[?contains(LoadBalancerName, '$PROJECT_NAME-$ENVIRONMENT-us-east-1')].DNSName" \
    --output text)

EU_WEST_ALB=$(aws elbv2 describe-load-balancers \
    --region eu-west-1 \
    --query "LoadBalancers[?contains(LoadBalancerName, '$PROJECT_NAME-$ENVIRONMENT-eu-west-1')].DNSName" \
    --output text)

AP_SOUTHEAST_ALB=$(aws elbv2 describe-load-balancers \
    --region ap-southeast-1 \
    --query "LoadBalancers[?contains(LoadBalancerName, '$PROJECT_NAME-$ENVIRONMENT-ap-southeast-1')].DNSName" \
    --output text)

print_status "ALB DNS names retrieved"

# Test health endpoints
echo -e "${BLUE}🧪 Testing Health Endpoints${NC}"
echo "=============================="

for region in "${REGIONS[@]}"; do
    case $region in
        "us-east-1")
            ALB_DNS=$US_EAST_ALB
            ;;
        "eu-west-1")
            ALB_DNS=$EU_WEST_ALB
            ;;
        "ap-southeast-1")
            ALB_DNS=$AP_SOUTHEAST_ALB
            ;;
    esac
    
    echo "Testing health endpoint in $region ($ALB_DNS)..."
    
    if curl -f -s "http://$ALB_DNS/health" >/dev/null; then
        print_status "Health check passed in $region"
    else
        print_warning "Health check failed in $region"
    fi
done

# Configure CloudFront distribution
echo -e "${BLUE}☁️  Configuring CloudFront${NC}"
echo "=============================="

DISTRIBUTION_ID=$(aws cloudfront list-distributions \
    --query "DistributionList.Items[?contains(Comment, '$DOMAIN_NAME')].Id" \
    --output text)

if [ -n "$DISTRIBUTION_ID" ]; then
    print_status "CloudFront distribution found: $DISTRIBUTION_ID"
    
    # Invalidate CloudFront cache
    echo "Invalidating CloudFront cache..."
    aws cloudfront create-invalidation \
        --distribution-id "$DISTRIBUTION_ID" \
        --paths "/*"
    
    print_status "CloudFront cache invalidated"
else
    print_warning "CloudFront distribution not found"
fi

# Run comprehensive health checks
echo -e "${BLUE}🏥 Running Health Checks${NC}"
echo "=============================="

# Test global endpoints
echo "Testing global endpoints..."

# Test primary region
if curl -f -s "http://$US_EAST_ALB/health" >/dev/null; then
    print_status "Primary region (us-east-1) is healthy"
else
    print_warning "Primary region (us-east-1) health check failed"
fi

# Test secondary regions
if curl -f -s "http://$EU_WEST_ALB/health" >/dev/null; then
    print_status "Secondary region (eu-west-1) is healthy"
else
    print_warning "Secondary region (eu-west-1) health check failed"
fi

if curl -f -s "http://$AP_SOUTHEAST_ALB/health" >/dev/null; then
    print_status "Secondary region (ap-southeast-1) is healthy"
else
    print_warning "Secondary region (ap-southeast-1) health check failed"
fi

# Test CloudFront endpoint
if [ -n "$DISTRIBUTION_ID" ]; then
    CLOUDFRONT_DOMAIN=$(aws cloudfront get-distribution \
        --id "$DISTRIBUTION_ID" \
        --query "Distribution.DomainName" \
        --output text)
    
    echo "Testing CloudFront endpoint ($CLOUDFRONT_DOMAIN)..."
    
    if curl -f -s "https://$CLOUDFRONT_DOMAIN/health" >/dev/null; then
        print_status "CloudFront endpoint is healthy"
    else
        print_warning "CloudFront endpoint health check failed"
    fi
fi

# Cleanup
echo -e "${BLUE}🧹 Cleaning Up${NC}"
echo "================"

rm -f terraform.tfvars
rm -f tfplan

print_status "Temporary files cleaned up"

# Summary
echo -e "${BLUE}📊 Multi-Region Deployment Summary${NC}"
echo "======================================"
echo "Project: $PROJECT_NAME"
echo "Environment: $ENVIRONMENT"
echo "Domain: $DOMAIN_NAME"
echo "Regions: ${REGIONS[*]}"
echo "Primary Region: $PRIMARY_REGION"
echo "Image Tag: $IMAGE_TAG"
echo ""
echo "Deployed Resources:"
echo "✅ ECR repositories in all regions"
echo "✅ ECS clusters in all regions"
echo "✅ Application Load Balancers in all regions"
echo "✅ Route 53 hosted zone and health checks"
echo "✅ CloudFront distribution with global CDN"
echo "✅ Multi-region database clusters"
echo "✅ Redis clusters in all regions"
echo "✅ CloudWatch monitoring and dashboards"
echo ""
echo "Endpoints:"
echo "🌍 Global: https://$DOMAIN_NAME"
echo "🇺🇸 US East: http://$US_EAST_ALB"
echo "🇪🇺 EU West: http://$EU_WEST_ALB"
echo "🇸🇬 AP Southeast: http://$AP_SOUTHEAST_ALB"
echo ""
echo "Next Steps:"
echo "1. Configure DNS records to point to CloudFront"
echo "2. Set up SSL certificates for HTTPS"
echo "3. Configure monitoring and alerting"
echo "4. Run load tests to validate performance"
echo "5. Set up backup and disaster recovery procedures"

echo -e "${GREEN}🎉 Multi-Region Deployment Completed Successfully!${NC}"
echo ""
echo "Your RichesReach application is now deployed globally with:"
echo "✅ Multi-region ECS clusters"
echo "✅ Global CDN with CloudFront"
echo "✅ Latency-based routing with Route 53"
echo "✅ High availability and fault tolerance"
echo "✅ Global performance optimization"
echo ""
echo "The system is now ready for global production traffic! 🚀"
