/**
 * Minimal interaction script for deployed contracts
 * Usage: npx hardhat run scripts/interact.ts --network polygonAmoy
 */

import { ethers } from "hardhat";
import * as fs from "fs";
import * as path from "path";

async function main() {
  const [signer] = await ethers.getSigners();
  const network = await ethers.provider.getNetwork();
  const networkName = network.name === "unknown" ? "localhost" : network.name;
  
  console.log("Interacting with contracts as:", signer.address);
  console.log("Network:", networkName);

  // Load deployment addresses
  const deploymentPath = path.join(__dirname, `../deployments/${networkName}.json`);
  if (!fs.existsSync(deploymentPath)) {
    throw new Error(`Deployment file not found: ${deploymentPath}\n\nRun deployment first: npm run deploy:${networkName === "localhost" ? "local" : networkName}`);
  }
  const deployment = JSON.parse(fs.readFileSync(deploymentPath, "utf8"));
  
  // Handle both old (MockUSDC) and new (ReachVault) deployment structures
  const contracts = deployment.contracts;
  const REACHToken = contracts.REACHToken || contracts.REACHToken;
  const ReachVault = contracts.ReachVault || contracts.ERC4626Vault;
  const veREACHTokenInfo = contracts.veREACHToken;
  
  if (!REACHToken || !ReachVault || !veREACHTokenInfo) {
    throw new Error(`Missing contracts in deployment file. Found: ${Object.keys(contracts).join(", ")}`);
  }

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

  // Check REACH balance
  const reachBalance = await reach.balanceOf(signer.address);
  console.log(`REACH balance: ${ethers.formatEther(reachBalance)} REACH`);

  // Check vault shares
  const vaultShares = await vault.balanceOf(signer.address);
  console.log(`Vault shares: ${ethers.formatEther(vaultShares)} rREACH`);

  // Check veREACH lock
  const lockInfo = await veReach.getLockInfo(signer.address);
  if (lockInfo.unlockTime > 0n) {
    const unlockDate = new Date(Number(lockInfo.unlockTime) * 1000);
    console.log(`veREACH lock: ${ethers.formatEther(lockInfo.amount)} REACH locked`);
    console.log(`  Unlocks: ${unlockDate.toLocaleString()}`);
    console.log(`  Voting power: ${ethers.formatEther(lockInfo.votingPower)}`);
  } else {
    console.log(`veREACH lock: No lock found`);
  }

  console.log("\n" + "=".repeat(60));
  console.log("🎯 INTERACTION OPTIONS");
  console.log("=".repeat(60));
  console.log("\n1. Mint REACH (if you're the deployer)");
  console.log("2. Deposit REACH to vault");
  console.log("3. Lock REACH → get veREACH");
  console.log("4. Check voting power");

  // Example: If user has REACH, deposit to vault
  if (reachBalance > 0n) {
    console.log("\n💡 You have REACH! You can:");
    console.log("  - Deposit to vault: vault.deposit(amount, signer.address)");
    console.log("  - Lock REACH: veReach.createLock(amount, duration)");
  } else {
    console.log("\n💡 You need REACH first. If you're the deployer, you can mint some.");
  }

  // Example interactions (commented out - uncomment to use)
  /*
  // 1. Mint REACH (only if you're the deployer)
  console.log("\n📝 Minting 1000 REACH...");
  await reach.mint(signer.address, ethers.parseEther("1000"));
  console.log("✅ Minted 1000 REACH");

  // 2. Approve vault to spend REACH
  console.log("\n📝 Approving vault to spend REACH...");
  await reach.approve(ReachVault.address, ethers.parseEther("100"));
  console.log("✅ Approved");

  // 3. Deposit 100 REACH to vault
  console.log("\n📝 Depositing 100 REACH to vault...");
  const depositTx = await vault.deposit(ethers.parseEther("100"), signer.address);
  await depositTx.wait();
  console.log("✅ Deposited 100 REACH, got vault shares");

  // 4. Lock 50 REACH for 1 year
  console.log("\n📝 Locking 50 REACH for 1 year...");
  await reach.approve(veREACHTokenInfo.address, ethers.parseEther("50"));
  const lockTx = await veReach.createLock(
    ethers.parseEther("50"),
    365 * 24 * 60 * 60 // 1 year in seconds
  );
  await lockTx.wait();
  console.log("✅ Locked 50 REACH, got veREACH voting power");

  // 5. Check voting power
  const votingPower = await veReach.getVotingPower(signer.address);
  console.log(`\n✅ Your voting power: ${ethers.formatEther(votingPower)}`);
  */
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });

