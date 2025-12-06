#!/bin/bash
# Mainnet Deployment Script for RichesReach Smart Contracts
# WARNING: This deploys to production networks. Use with caution!

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${RED}⚠️  MAINNET DEPLOYMENT${NC}"
echo -e "${YELLOW}This will deploy contracts to production networks.${NC}"
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${RED}Deployment cancelled.${NC}"
    exit 1
fi

# Check if required tools are installed
command -v hardhat >/dev/null 2>&1 || { echo -e "${RED}❌ Hardhat is required but not installed.${NC}" >&2; exit 1; }

# Load environment variables
if [ ! -f .env ]; then
    echo -e "${RED}❌ .env file is required for mainnet deployment${NC}" >&2; exit 1
fi

export $(cat .env | grep -v '^#' | xargs)

# Verify required environment variables
if [ -z "$MAINNET_PRIVATE_KEY" ]; then
    echo -e "${RED}❌ MAINNET_PRIVATE_KEY is required${NC}" >&2; exit 1
fi

# Network configuration
NETWORKS=("polygon" "arbitrum" "optimism" "base")

# Contract addresses will be stored here
DEPLOYMENT_LOG="deployments/mainnet_deployments_$(date +%Y%m%d_%H%M%S).json"

mkdir -p deployments

echo "{" > "$DEPLOYMENT_LOG"
echo "  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"," >> "$DEPLOYMENT_LOG"
echo "  \"networks\": {" >> "$DEPLOYMENT_LOG"

# Deploy to each network
for network in "${NETWORKS[@]}"; do
    echo -e "\n${GREEN}📡 Deploying to ${network} mainnet...${NC}"
    
    # Confirm each network deployment
    read -p "Deploy to ${network}? (yes/no): " network_confirm
    if [ "$network_confirm" != "yes" ]; then
        echo -e "${YELLOW}⏭️  Skipping ${network}${NC}"
        continue
    fi
    
    # Deploy contracts
    npx hardhat run scripts/deploy.js --network "$network" || {
        echo -e "${RED}❌ Deployment to ${network} failed${NC}"
        continue
    }
    
    echo -e "    \"$network\": {" >> "$DEPLOYMENT_LOG"
    echo -e "      \"status\": \"deployed\"," >> "$DEPLOYMENT_LOG"
    echo -e "      \"contracts\": {}" >> "$DEPLOYMENT_LOG"
    echo -e "    }," >> "$DEPLOYMENT_LOG"
    
    echo -e "${GREEN}✅ Successfully deployed to ${network}${NC}"
done

# Remove trailing comma
sed -i '' '$ s/,$//' "$DEPLOYMENT_LOG"

echo "  }" >> "$DEPLOYMENT_LOG"
echo "}" >> "$DEPLOYMENT_LOG"

echo -e "\n${GREEN}✅ Mainnet deployment complete!${NC}"
echo -e "${YELLOW}📝 Deployment log saved to: ${DEPLOYMENT_LOG}${NC}"

# Verify contracts
echo -e "\n${GREEN}🔍 Verifying contracts...${NC}"
./scripts/deploy/verify_contracts.sh "$DEPLOYMENT_LOG"

echo -e "\n${GREEN}🎉 All done!${NC}"

