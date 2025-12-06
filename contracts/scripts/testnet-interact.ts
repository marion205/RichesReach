/**
 * Testnet interaction script - full flow test
 * Usage: npx hardhat run scripts/testnet-interact.ts --network polygonAmoy
 * 
 * Make sure you have:
 * 1. Deployed contracts to Polygon Amoy
 * 2. Some REACH tokens (or be the deployer with full supply)
 * 3. Some MATIC for gas
 */

import { ethers } from "hardhat";
import * as fs from "fs";
import * as path from "path";

async function main() {
  const [signer] = await ethers.getSigners();
  const network = await ethers.provider.getNetwork();
  const networkName = network.name === "unknown" ? "polygonAmoy" : network.name;
  
  console.log("🧪 Testing contracts on Polygon Amoy testnet...");
  console.log("Account:", signer.address);
  console.log("Network:", networkName);

  // Check balance
  const balance = await ethers.provider.getBalance(signer.address);
  console.log(`MATIC balance: ${ethers.formatEther(balance)} MATIC`);
  
  if (balance < ethers.parseEther("0.01")) {
    console.log("⚠️  Low MATIC balance! Get more from faucet.");
  }

  // Load deployment addresses
  const deploymentPath = path.join(__dirname, `../deployments/${networkName}.json`);
  if (!fs.existsSync(deploymentPath)) {
    throw new Error(`Deployment file not found: ${deploymentPath}\n\nRun: npm run deploy:amoy`);
  }
  const deployment = JSON.parse(fs.readFileSync(deploymentPath, "utf8"));
  
  const contracts = deployment.contracts;
  const REACHToken = contracts.REACHToken;
  const ReachVault = contracts.ReachVault;
  const veREACHTokenInfo = contracts.veREACHToken;
  
  if (!REACHToken || !ReachVault || !veREACHTokenInfo) {
    throw new Error(`Missing contracts. Found: ${Object.keys(contracts).join(", ")}`);
  }

  console.log("\n📦 Contract Addresses:");
  console.log(`  REACH: ${REACHToken.address}`);
  console.log(`  ReachVault: ${ReachVault.address}`);
  console.log(`  veREACH: ${veREACHTokenInfo.address}`);

  // Get contract instances
  const MockERC20 = await ethers.getContractFactory("MockERC20");
  const ERC4626Vault = await ethers.getContractFactory("ERC4626Vault");
  const veREACHTokenFactory = await ethers.getContractFactory("veREACHToken");

  const reach = MockERC20.attach(REACHToken.address);
  const vault = ERC4626Vault.attach(ReachVault.address);
  const veReach = veREACHTokenFactory.attach(veREACHTokenInfo.address);

  console.log("\n" + "=".repeat(60));
  console.log("📊 CURRENT STATE");
  console.log("=".repeat(60));
  
  const reachBalance = await reach.balanceOf(signer.address);
  console.log(`REACH balance: ${ethers.formatEther(reachBalance)} REACH`);

  if (reachBalance === 0n) {
    console.log("\n⚠️  No REACH tokens! You need REACH to test.");
    console.log("   If you're the deployer, you should have the full supply.");
    console.log("   Otherwise, get REACH from the deployer or mint if you have permissions.");
    return;
  }

  // Test 1: Deposit to vault
  console.log("\n🧪 Test 1: Deposit 100 REACH to vault...");
  try {
    const depositAmount = ethers.parseEther("100");
    
    // Approve
    console.log("   Approving vault...");
    const approveTx = await reach.approve(ReachVault.address, depositAmount);
    await approveTx.wait();
    console.log("   ✅ Approved");

    // Deposit
    console.log("   Depositing...");
    const depositTx = await vault.deposit(depositAmount, signer.address);
    const receipt = await depositTx.wait();
    console.log(`   ✅ Deposited! Tx: ${receipt.hash}`);
    
    const vaultShares = await vault.balanceOf(signer.address);
    console.log(`   Got ${ethers.formatEther(vaultShares)} rREACH shares`);
  } catch (error: any) {
    console.log(`   ❌ Failed: ${error.message}`);
  }

  // Test 2: Lock REACH
  console.log("\n🧪 Test 2: Lock 50 REACH for 1 year...");
  try {
    const lockAmount = ethers.parseEther("50");
    const oneYear = 365 * 24 * 60 * 60;
    
    // Approve
    console.log("   Approving veREACH...");
    const approveTx = await reach.approve(veREACHTokenInfo.address, lockAmount);
    await approveTx.wait();
    console.log("   ✅ Approved");

    // Lock
    console.log("   Locking...");
    const lockTx = await veReach.createLock(lockAmount, oneYear);
    const receipt = await lockTx.wait();
    console.log(`   ✅ Locked! Tx: ${receipt.hash}`);
    
    const lockInfo = await veReach.getLockInfo(signer.address);
    const votingPower = await veReach.getVotingPower(signer.address);
    const unlockDate = new Date(Number(lockInfo.unlockTime) * 1000);
    
    console.log(`   Locked: ${ethers.formatEther(lockInfo.amount)} REACH`);
    console.log(`   Unlocks: ${unlockDate.toLocaleString()}`);
    console.log(`   Voting power: ${ethers.formatEther(votingPower)}`);
  } catch (error: any) {
    console.log(`   ❌ Failed: ${error.message}`);
  }

  // Final state
  console.log("\n" + "=".repeat(60));
  console.log("📊 FINAL STATE");
  console.log("=".repeat(60));
  console.log(`REACH: ${ethers.formatEther(await reach.balanceOf(signer.address))} REACH`);
  console.log(`Vault shares: ${ethers.formatEther(await vault.balanceOf(signer.address))} rREACH`);
  
  const lockInfo = await veReach.getLockInfo(signer.address);
  if (lockInfo.unlockTime > 0n) {
    const votingPower = await veReach.getVotingPower(signer.address);
    console.log(`Locked: ${ethers.formatEther(lockInfo.amount)} REACH`);
    console.log(`Voting power: ${ethers.formatEther(votingPower)}`);
  } else {
    console.log(`Locked: 0 REACH`);
  }
  console.log("=".repeat(60));

  console.log("\n✅ Testnet interaction complete!");
  console.log("\n🔍 View on Polygonscan:");
  console.log(`   REACH: https://amoy.polygonscan.com/address/${REACHToken.address}`);
  console.log(`   Vault: https://amoy.polygonscan.com/address/${ReachVault.address}`);
  console.log(`   veREACH: https://amoy.polygonscan.com/address/${veREACHTokenInfo.address}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });

