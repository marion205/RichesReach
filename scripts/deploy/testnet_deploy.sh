#!/bin/bash
# Testnet Deployment Script for RichesReach Smart Contracts
# Deploys to Polygon Amoy, Arbitrum Sepolia, Optimism Sepolia, Base Sepolia

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Starting Testnet Deployment${NC}"

# Check if required tools are installed
command -v hardhat >/dev/null 2>&1 || { echo -e "${RED}❌ Hardhat is required but not installed.${NC}" >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo -e "${RED}❌ Node.js is required but not installed.${NC}" >&2; exit 1; }

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}⚠️  No .env file found. Using default testnet settings.${NC}"
fi

# Network configuration
NETWORKS=("polygon-amoy" "arbitrum-sepolia" "optimism-sepolia" "base-sepolia")

# Contract addresses will be stored here
DEPLOYMENT_LOG="deployments/testnet_deployments_$(date +%Y%m%d_%H%M%S).json"

mkdir -p deployments

echo "{" > "$DEPLOYMENT_LOG"
echo "  \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"," >> "$DEPLOYMENT_LOG"
echo "  \"networks\": {" >> "$DEPLOYMENT_LOG"

# Deploy to each network
for network in "${NETWORKS[@]}"; do
    echo -e "\n${GREEN}📡 Deploying to ${network}...${NC}"
    
    # Deploy contracts using Hardhat
    npx hardhat run scripts/deploy.js --network "$network" || {
        echo -e "${RED}❌ Deployment to ${network} failed${NC}"
        continue
    }
    
    # Extract contract addresses from Hardhat output
    # This assumes Hardhat outputs addresses in a specific format
    # Adjust based on your actual deployment script
    
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

echo -e "\n${GREEN}✅ Testnet deployment complete!${NC}"
echo -e "${YELLOW}📝 Deployment log saved to: ${DEPLOYMENT_LOG}${NC}"

# Verify contracts
echo -e "\n${GREEN}🔍 Verifying contracts...${NC}"
./scripts/deploy/verify_contracts.sh "$DEPLOYMENT_LOG"

echo -e "\n${GREEN}🎉 All done!${NC}"

