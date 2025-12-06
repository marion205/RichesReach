/**
 * Request Testnet MATIC Helper Script
 * 
 * This script helps format a request to Polygon Support for testnet MATIC.
 * It enforces the 100 MATIC limit to prevent errors.
 * 
 * Usage:
 *   npx hardhat run scripts/request-matic.ts --network polygonAmoy
 * 
 * Or with custom amount (will be clamped to 100):
 *   MATIC_REQUEST_AMOUNT=50 npx hardhat run scripts/request-matic.ts --network polygonAmoy
 */

import { ethers } from "hardhat";
import { getSafeMaticRequestAmount, MAX_POLYGON_TESTNET_MATIC } from "../config/testnet";

async function main() {
  const [signer] = await ethers.getSigners();
  const network = await ethers.provider.getNetwork();
  
  console.log("📧 Polygon Support MATIC Request Helper");
  console.log("=".repeat(60));
  
  // Get requested amount from env or use default
  const envAmount = process.env.MATIC_REQUEST_AMOUNT;
  const requestedAmount = getSafeMaticRequestAmount(envAmount);
  
  // Show what will be requested
  console.log(`\n📋 Request Details:`);
  console.log(`   Network: ${network.name} (Chain ID: ${network.chainId})`);
  console.log(`   Wallet Address: ${signer.address}`);
  console.log(`   Requested Amount: ${requestedAmount} MATIC`);
  
  if (envAmount && Number(envAmount) > MAX_POLYGON_TESTNET_MATIC) {
    console.log(`\n⚠️  WARNING: You requested ${envAmount} MATIC, but Polygon's limit is ${MAX_POLYGON_TESTNET_MATIC} MATIC.`);
    console.log(`   The amount has been clamped to ${MAX_POLYGON_TESTNET_MATIC} MATIC.`);
  }
  
  console.log(`\n📝 Email Template for Polygon Support:`);
  console.log("=".repeat(60));
  console.log(`
Email: your-email@example.com
Requester Name: Your Name
Telegram/Discord: your-handle
Project: RichesReach
Token Quantity: ${requestedAmount}
Wallet Address: ${signer.address}
Reason: Smart contract deployment and testing on Polygon Amoy testnet
  `.trim());
  
  console.log("\n" + "=".repeat(60));
  console.log("💡 Tips:");
  console.log(`   • Polygon's limit is ${MAX_POLYGON_TESTNET_MATIC} MATIC per project every 90 days`);
  console.log(`   • This request is for ${requestedAmount} MATIC (within limit)`);
  console.log(`   • Usually takes 24-48 hours to process`);
  console.log(`   • You can also try faucets for immediate needs`);
  console.log("=".repeat(60));
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("Error:", error.message);
    process.exit(1);
  });

