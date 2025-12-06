import { ethers } from "hardhat";
import { MIN_SAFE_BALANCE_MATIC } from "../config/testnet";

async function main() {
  const [deployer] = await ethers.getSigners();
  const network = await ethers.provider.getNetwork();
  
  console.log("\n📊 Wallet Status Check");
  console.log("=" .repeat(50));
  console.log(`Network: ${network.name} (Chain ID: ${network.chainId})`);
  console.log(`Address: ${deployer.address}`);
  
  const balance = await ethers.provider.getBalance(deployer.address);
  const balanceInMatic = ethers.formatEther(balance);
  
  console.log(`Balance: ${balanceInMatic} MATIC`);
  
  // Estimate deployment cost
  const estimatedGas = 6_000_000n; // ~6M gas for all 3 contracts
  const gasPrice = await ethers.provider.getFeeData();
  const estimatedCost = estimatedGas * (gasPrice.gasPrice || 30_000_000_000n);
  const estimatedCostInMatic = ethers.formatEther(estimatedCost);
  
  console.log(`\n💰 Estimated Deployment Cost: ~${estimatedCostInMatic} MATIC`);
  console.log(`   Minimum Safe Balance: ${MIN_SAFE_BALANCE_MATIC} MATIC`);
  
  if (parseFloat(balanceInMatic) < MIN_SAFE_BALANCE_MATIC) {
    console.log("\n⚠️  Insufficient balance for deployment");
    console.log("\n🚰 Get testnet MATIC from:");
    console.log("   • Alchemy: https://www.alchemy.com/faucets/polygon-amoy");
    console.log("   • QuickNode: https://faucet.quicknode.com/polygon/amoy");
    console.log("   • Chainlink: https://faucets.chain.link/polygon-amoy");
    console.log("   • Polygon Discord: #amoy-faucet channel");
    console.log("\n💡 To request from Polygon Support (100 MATIC max):");
    console.log("   Run: npm run request-matic");
  } else if (parseFloat(balanceInMatic) < 1) {
    console.log("\n✅ Enough for deployment! (~0.6 MATIC needed)");
    console.log("   Run: npm run deploy:amoy");
  } else {
    console.log("\n✅ Plenty of MATIC! Ready to deploy.");
    console.log("   Run: npm run deploy:amoy");
  }
  
  console.log("\n" + "=".repeat(50));
}

main().catch((error) => {
  console.error("Error:", error.message);
  process.exitCode = 1;
});

