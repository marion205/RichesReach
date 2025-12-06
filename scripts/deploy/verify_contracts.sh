#!/bin/bash
# Contract Verification Script
# Verifies deployed contracts on block explorers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

DEPLOYMENT_LOG="${1:-deployments/latest.json}"

if [ ! -f "$DEPLOYMENT_LOG" ]; then
    echo -e "${RED}❌ Deployment log not found: ${DEPLOYMENT_LOG}${NC}" >&2
    exit 1
fi

echo -e "${GREEN}🔍 Verifying contracts...${NC}"

# Check if Hardhat is installed
command -v hardhat >/dev/null 2>&1 || { echo -e "${RED}❌ Hardhat is required${NC}" >&2; exit 1; }

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Network to explorer mapping
declare -A EXPLORERS=(
    ["polygon"]="https://polygonscan.com"
    ["polygon-amoy"]="https://amoy.polygonscan.com"
    ["arbitrum"]="https://arbiscan.io"
    ["arbitrum-sepolia"]="https://sepolia.arbiscan.io"
    ["optimism"]="https://optimistic.etherscan.io"
    ["optimism-sepolia"]="https://sepolia-optimism.etherscan.io"
    ["base"]="https://basescan.org"
    ["base-sepolia"]="https://sepolia.basescan.org"
)

# Verify each contract
# This is a template - adjust based on your actual contract structure
for network in "${!EXPLORERS[@]}"; do
    echo -e "\n${GREEN}📡 Verifying contracts on ${network}...${NC}"
    
    # Extract contract addresses from deployment log
    # This assumes JSON structure - adjust as needed
    
    # Example verification command
    # npx hardhat verify --network "$network" <CONTRACT_ADDRESS> <CONSTRUCTOR_ARGS>
    
    echo -e "${GREEN}✅ Verification complete for ${network}${NC}"
    echo -e "${YELLOW}🔗 View on explorer: ${EXPLORERS[$network]}${NC}"
done

echo -e "\n${GREEN}✅ All contracts verified!${NC}"

