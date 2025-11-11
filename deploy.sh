#!/bin/bash
# Comprehensive Deployment Script for RichesReach
# Handles both mobile app (EAS) and backend (AWS) deployment

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
  echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
  echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
  echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
  echo -e "${RED}[ERROR]${NC} $1"
}

echo ""
echo "🚀 RichesReach Deployment"
echo "=========================="
echo ""

# Check what to deploy
echo "What would you like to deploy?"
echo "1) Mobile App (iOS/Android via EAS)"
echo "2) Backend (AWS ECS)"
echo "3) Both"
read -p "Enter choice (1-3): " DEPLOY_CHOICE

# Mobile App Deployment
deploy_mobile() {
  print_status "Starting mobile app deployment..."
  
  cd mobile
  
  # Check EAS login
  if ! eas whoami &>/dev/null; then
    print_warning "Not logged into EAS. Please login:"
    eas login
  fi
  
  # Ask for platform
  echo ""
  echo "Which platform?"
  echo "1) iOS"
  echo "2) Android"
  echo "3) Both"
  read -p "Enter choice (1-3): " PLATFORM_CHOICE
  
  case $PLATFORM_CHOICE in
    1)
      print_status "Building iOS production app..."
      eas build --platform ios --profile production
      print_success "iOS build started! Check status at: https://expo.dev"
      ;;
    2)
      print_status "Building Android production app..."
      eas build --platform android --profile production
      print_success "Android build started! Check status at: https://expo.dev"
      ;;
    3)
      print_status "Building for both platforms..."
      eas build --platform all --profile production
      print_success "Builds started for both platforms! Check status at: https://expo.dev"
      ;;
  esac
  
  # Ask about submission
  echo ""
  read -p "Submit to app stores? (y/n): " SUBMIT_CHOICE
  if [ "$SUBMIT_CHOICE" = "y" ]; then
    if [ "$PLATFORM_CHOICE" = "1" ] || [ "$PLATFORM_CHOICE" = "3" ]; then
      print_status "Submitting iOS to App Store..."
      eas submit --platform ios --profile production
    fi
    if [ "$PLATFORM_CHOICE" = "2" ] || [ "$PLATFORM_CHOICE" = "3" ]; then
      print_status "Submitting Android to Play Store..."
      eas submit --platform android --profile production
    fi
  fi
  
  cd ..
  print_success "Mobile deployment complete!"
}

# Backend Deployment
deploy_backend() {
  print_status "Starting backend deployment..."
  
  # Check AWS credentials
  if ! aws sts get-caller-identity &>/dev/null; then
    print_error "AWS credentials not configured. Please run 'aws configure' first."
    exit 1
  fi
  
  # Check if Docker is available
  if ! command -v docker &>/dev/null; then
    print_warning "Docker not found. Using AWS ECS deployment script..."
    
    if [ -f "deploy_to_production.sh" ]; then
      print_status "Running production deployment script..."
      bash deploy_to_production.sh
    else
      print_error "deploy_to_production.sh not found!"
      exit 1
    fi
  else
    print_status "Building and deploying Docker image to AWS ECS..."
    
    # Build Docker image
    print_status "Building Docker image..."
    docker build -f Dockerfile.production -t richesreach-ai:production .
    
    # Get AWS account ID and region
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    AWS_REGION=${AWS_REGION:-us-east-1}
    
    # ECR login
    print_status "Logging into ECR..."
    aws ecr get-login-password --region $AWS_REGION | \
      docker login --username AWS --password-stdin \
      $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
    
    # Create ECR repo if needed
    REPO_NAME="richesreach-ai"
    aws ecr describe-repositories --repository-names $REPO_NAME --region $AWS_REGION &>/dev/null || \
      aws ecr create-repository --repository-name $REPO_NAME --region $AWS_REGION
    
    # Tag and push
    ECR_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO_NAME:latest"
    print_status "Tagging and pushing to ECR..."
    docker tag richesreach-ai:production $ECR_URI
    docker push $ECR_URI
    
    # Update ECS service
    print_status "Updating ECS service..."
    aws ecs update-service \
      --cluster richesreach-cluster \
      --service richesreach-service \
      --force-new-deployment \
      --region $AWS_REGION &>/dev/null || \
      print_warning "ECS service update failed. Service may not exist yet."
    
    print_success "Backend deployment complete!"
  fi
}

# Execute based on choice
case $DEPLOY_CHOICE in
  1)
    deploy_mobile
    ;;
  2)
    deploy_backend
    ;;
  3)
    deploy_mobile
    echo ""
    deploy_backend
    ;;
  *)
    print_error "Invalid choice!"
    exit 1
    ;;
esac

echo ""
print_success "🎉 Deployment process completed!"
echo ""
print_status "Next steps:"
print_status "- Mobile: Monitor builds at https://expo.dev"
print_status "- Backend: Check ECS service status in AWS Console"
echo ""





