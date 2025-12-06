/**
 * Example interaction script - demonstrates full flow
 * Usage: npx hardhat run scripts/interact-example.ts --network localhost
 */

import { ethers } from "hardhat";
import * as fs from "fs";
import * as path from "path";

async function main() {
  const [signer] = await ethers.getSigners();
  const network = await ethers.provider.getNetwork();
  const networkName = network.name === "unknown" ? "localhost" : network.name;
  
  console.log("🚀 Starting interaction example...");
  console.log("Account:", signer.address);
  console.log("Network:", networkName);

  // Load deployment addresses
  const deploymentPath = path.join(__dirname, `../deployments/${networkName}.json`);
  if (!fs.existsSync(deploymentPath)) {
    throw new Error(`Deployment file not found: ${deploymentPath}`);
  }
  const deployment = JSON.parse(fs.readFileSync(deploymentPath, "utf8"));
  
  const contracts = deployment.contracts;
  
  // Handle both old (MockUSDC) and new (ReachVault) deployment structures
  const REACHToken = contracts.REACHToken;
  const ReachVault = contracts.ReachVault || contracts.ERC4626Vault;
  const veREACHTokenInfo = contracts.veREACHToken;
  const MockUSDC = contracts.MockUSDC; // Old deployments
  
  // Determine which asset the vault uses
  const vaultAsset = ReachVault?.asset || MockUSDC?.address;
  const isOldDeployment = !!MockUSDC;
  
  if (!REACHToken || !ReachVault || !veREACHTokenInfo) {
    throw new Error(`Missing contracts in deployment file. Found: ${Object.keys(contracts).join(", ")}`);
  }
  
  if (isOldDeployment) {
    console.log("⚠️  Using old deployment structure (vault uses Mock USDC, not REACH)");
    console.log("   Redeploy with updated script to use REACH as vault asset");
  }

  // Get contract instances
  const MockERC20 = await ethers.getContractFactory("MockERC20");
  const ERC4626Vault = await ethers.getContractFactory("ERC4626Vault");
  const veREACHTokenFactory = await ethers.getContractFactory("veREACHToken");

  const reach = MockERC20.attach(REACHToken.address);
  const vault = ERC4626Vault.attach(ReachVault.address);
  const veReach = veREACHTokenFactory.attach(veREACHTokenInfo.address);

  console.log("\n" + "=".repeat(60));
  console.log("📊 INITIAL STATE");
  console.log("=".repeat(60));
  
  const initialReach = await reach.balanceOf(signer.address);
  console.log(`REACH balance: ${ethers.formatEther(initialReach)} REACH`);

  // For old deployments, we'll skip vault deposit and go straight to locking REACH
  if (isOldDeployment) {
    console.log("\n⚠️  Skipping vault deposit (old deployment uses Mock USDC)");
    console.log("   Going straight to locking REACH...");
  } else {
    // Step 1: Approve vault to spend REACH
    console.log("\n📝 Step 1: Approving vault to spend 1000 REACH...");
    const approveTx = await reach.approve(ReachVault.address, ethers.parseEther("1000"));
    await approveTx.wait();
    console.log("✅ Approved");

    // Step 2: Deposit 1000 REACH to vault
    console.log("\n📝 Step 2: Depositing 1000 REACH to vault...");
    const depositTx = await vault.deposit(ethers.parseEther("1000"), signer.address);
    await depositTx.wait();
    console.log("✅ Deposited 1000 REACH");
    
    const vaultShares = await vault.balanceOf(signer.address);
    console.log(`   Got ${ethers.formatEther(vaultShares)} rREACH shares`);
  }

  // Step 3: Approve veREACH to spend REACH
  const stepNum = isOldDeployment ? 1 : 3;
  console.log(`\n📝 Step ${stepNum}: Approving veREACH to spend 500 REACH...`);
  const approveVeTx = await reach.approve(veREACHTokenInfo.address, ethers.parseEther("500"));
  await approveVeTx.wait();
  console.log("✅ Approved");

  // Step 4: Lock 500 REACH for 4 years (max lock = max voting power)
  console.log(`\n📝 Step ${stepNum + 1}: Locking 500 REACH for 4 years (max lock)...`);
  const fourYears = 4 * 365 * 24 * 60 * 60; // 4 years in seconds
  const lockTx = await veReach.createLock(
    ethers.parseEther("500"),
    fourYears
  );
  await lockTx.wait();
  console.log("✅ Locked 500 REACH for 4 years");

  // Step 5: Check voting power
  const finalStepNum = isOldDeployment ? 3 : 5;
  console.log(`\n📝 Step ${finalStepNum}: Checking voting power...`);
  const lockInfo = await veReach.getLockInfo(signer.address);
  const votingPower = await veReach.getVotingPower(signer.address);
  const unlockDate = new Date(Number(lockInfo.unlockTime) * 1000);
  
  console.log("\n" + "=".repeat(60));
  console.log("📊 FINAL STATE");
  console.log("=".repeat(60));
  console.log(`REACH balance: ${ethers.formatEther(await reach.balanceOf(signer.address))} REACH`);
  if (!isOldDeployment) {
    console.log(`Vault shares: ${ethers.formatEther(await vault.balanceOf(signer.address))} rREACH`);
  }
  console.log(`Locked REACH: ${ethers.formatEther(lockInfo.amount)} REACH`);
  console.log(`Unlocks: ${unlockDate.toLocaleString()}`);
  console.log(`Voting power: ${ethers.formatEther(votingPower)}`);
  console.log("=".repeat(60));

  // Expected: 500 REACH * 4x multiplier = 2000 voting power
  const expectedVotingPower = ethers.parseEther("2000");
  if (votingPower >= expectedVotingPower * 99n / 100n) { // Allow 1% rounding
    console.log("\n✅ SUCCESS! Voting power is correct (4x multiplier for 4-year lock)");
  } else {
    console.log(`\n⚠️  Expected ~2000 voting power, got ${ethers.formatEther(votingPower)}`);
  }

  console.log("\n🎉 Interaction example complete!");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });

