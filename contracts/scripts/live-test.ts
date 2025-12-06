/**
 * Live test script for Polygon Amoy
 * Tests: Mint REACH → Deposit to vault → Lock → Get veREACH voting power
 * Usage: npx hardhat run scripts/live-test.ts --network polygonAmoy
 */

import { ethers } from "hardhat";
import * as fs from "fs";
import * as path from "path";

async function main() {
  const [user] = await ethers.getSigners();
  const network = await ethers.provider.getNetwork();
  
  console.log("User:", user.address);
  console.log("Network:", network.name);

  // Load deployment addresses
  const deploymentPath = path.join(__dirname, "../deployments/polygonAmoy.json");
  if (!fs.existsSync(deploymentPath)) {
    throw new Error(`Deployment file not found: ${deploymentPath}\n\nRun: npm run deploy:amoy first`);
  }
  
  const deployment = JSON.parse(fs.readFileSync(deploymentPath, "utf8"));
  const contracts = deployment.contracts;
  
  const REACH = contracts.REACHToken?.address;
  const VAULT = contracts.ReachVault?.address || contracts.ERC4626Vault?.address;
  const VEREACH = contracts.veREACHToken?.address;
  
  if (!REACH || !VAULT || !VEREACH) {
    throw new Error(`Missing contracts. Found: ${Object.keys(contracts).join(", ")}`);
  }

  console.log("\n📦 Contract Addresses:");
  console.log(`REACH: ${REACH}`);
  console.log(`Vault: ${VAULT}`);
  console.log(`veREACH: ${VEREACH}\n`);

  // Get contract instances
  const MockERC20 = await ethers.getContractFactory("MockERC20");
  const ERC4626Vault = await ethers.getContractFactory("ERC4626Vault");
  const veREACHToken = await ethers.getContractFactory("veREACHToken");

  const reach = MockERC20.attach(REACH);
  const vault = ERC4626Vault.attach(VAULT);
  const ve = veREACHToken.attach(VEREACH);

  // Check initial balance
  const initialReach = await reach.balanceOf(user.address);
  console.log(`Initial REACH balance: ${ethers.formatEther(initialReach)} REACH`);

  if (initialReach === 0n) {
    console.log("\n⚠️  No REACH tokens! If you're the deployer, you should have the full supply.");
    console.log("   Otherwise, you need to get REACH tokens first.");
    return;
  }

  // 1. Approve vault
  console.log("\n1. Approving vault to spend 10000 REACH...");
  await (await reach.approve(VAULT, ethers.parseEther("10000"))).wait();
  console.log("   ✅ Approved");

  // 2. Deposit to vault
  console.log("2. Depositing 10000 REACH to vault...");
  await (await vault.deposit(ethers.parseEther("10000"), user.address)).wait();
  console.log("   ✅ Deposited → got rREACH shares");

  // 3. Approve veREACH to spend REACH (not vault shares - veREACH locks REACH tokens)
  console.log("3. Approving veREACH to spend 5000 REACH...");
  await (await reach.approve(VEREACH, ethers.parseEther("5000"))).wait();
  console.log("   ✅ Approved");

  // 4. Lock REACH for 4 years (veREACH locks REACH tokens, not vault shares)
  console.log("4. Locking 5000 REACH for 4 years...");
  const fourYears = Math.floor(Date.now() / 1000) + 4 * 365 * 24 * 3600;
  await (await ve.createLock(ethers.parseEther("5000"), fourYears)).wait();
  console.log("   ✅ Locked 5000 REACH for 4 years → created veREACH");

  // 5. Get voting power
  const vp = await ve.getVotingPower(user.address);
  const lockInfo = await ve.getLockInfo(user.address);
  const unlockDate = new Date(Number(lockInfo.unlockTime) * 1000);

  console.log(`\n✅ SUCCESS!`);
  console.log(`   Locked: ${ethers.formatEther(lockInfo.amount)} REACH`);
  console.log(`   Voting power: ${ethers.formatEther(vp)} veREACH`);
  console.log(`   Unlocks: ${unlockDate.toLocaleString()}`);
  console.log(`   Expected: ~20000 veREACH (5000 REACH × 4x multiplier)\n`);

  console.log("🌐 Live on Polygon Amoy:");
  console.log(`REACH   → https://amoy.polygonscan.com/address/${REACH}`);
  console.log(`Vault   → https://amoy.polygonscan.com/address/${VAULT}`);
  console.log(`veREACH → https://amoy.polygonscan.com/address/${VEREACH}`);
}

main().catch((e) => console.error("Error:", e.message || e));
