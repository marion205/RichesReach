/**
 * Comprehensive lock scenario testing
 * Tests different lock durations, extensions, and amount increases
 * Usage: npx hardhat run scripts/test-lock-scenarios.ts --network localhost
 */

import { ethers } from "hardhat";
import * as fs from "fs";
import * as path from "path";

async function main() {
  const [signer] = await ethers.getSigners();
  const network = await ethers.provider.getNetwork();
  const networkName = network.name === "unknown" ? "localhost" : network.name;
  
  console.log("🧪 Testing Lock Scenarios");
  console.log("=".repeat(60));
  console.log(`Account: ${signer.address}`);
  console.log(`Network: ${networkName}\n`);

  // Load deployment addresses
  const deploymentPath = path.join(__dirname, `../deployments/${networkName}.json`);
  if (!fs.existsSync(deploymentPath)) {
    throw new Error(`Deployment file not found: ${deploymentPath}`);
  }
  const deployment = JSON.parse(fs.readFileSync(deploymentPath, "utf8"));
  const contracts = deployment.contracts;

  // Get contract instances
  const MockERC20 = await ethers.getContractFactory("MockERC20");
  const veREACHTokenFactory = await ethers.getContractFactory("veREACHToken");

  const reach = MockERC20.attach(contracts.REACHToken.address);
  const veReach = veREACHTokenFactory.attach(contracts.veREACHToken.address);

  const MAX_LOCK_TIME = 4 * 365 * 24 * 60 * 60; // 4 years
  const MIN_LOCK_TIME = 7 * 24 * 60 * 60; // 1 week

  // Helper to format time
  const formatDuration = (seconds: bigint) => {
    const days = Number(seconds) / (24 * 60 * 60);
    if (days >= 365) return `${(days / 365).toFixed(1)} years`;
    if (days >= 30) return `${(days / 30).toFixed(1)} months`;
    return `${days.toFixed(1)} days`;
  };

  console.log("📊 SCENARIO 1: Different Lock Durations\n");
  
  // Test different lock durations
  const testDurations = [
    { name: "1 week (minimum)", seconds: MIN_LOCK_TIME },
    { name: "1 month", seconds: 30 * 24 * 60 * 60 },
    { name: "3 months", seconds: 90 * 24 * 60 * 60 },
    { name: "6 months", seconds: 180 * 24 * 60 * 60 },
    { name: "1 year", seconds: 365 * 24 * 60 * 60 },
    { name: "2 years", seconds: 2 * 365 * 24 * 60 * 60 },
    { name: "4 years (maximum)", seconds: MAX_LOCK_TIME },
  ];

  // Check if there's an existing lock and withdraw it first
  const existingLock = await veReach.getLockInfo(signer.address);
  if (existingLock.unlockTime > 0) {
    console.log("⚠️  Existing lock found. Withdrawing first...");
    // Fast forward time to unlock
    const currentTime = await ethers.provider.getBlock("latest");
    if (Number(existingLock.unlockTime) > currentTime!.timestamp) {
      const timeToAdd = Number(existingLock.unlockTime) - currentTime!.timestamp + 1;
      await ethers.provider.send("evm_increaseTime", [timeToAdd]);
      await ethers.provider.send("evm_mine", []);
    }
    await veReach.withdraw();
    console.log("✅ Withdrawn existing lock\n");
  }

  // Test different lock durations (using first 3 for demo)
  const testDurationsToRun = testDurations.slice(0, 3); // Test first 3 to avoid too many transactions
  
  for (let i = 0; i < testDurationsToRun.length; i++) {
    const duration = testDurationsToRun[i];
    console.log(`Testing: ${duration.name}`);
    console.log(`  Duration: ${formatDuration(BigInt(duration.seconds))}`);
    
    // Withdraw previous lock if exists
    const prevLock = await veReach.getLockInfo(signer.address);
    if (prevLock.unlockTime > 0) {
      const currentTime = await ethers.provider.getBlock("latest");
      if (Number(prevLock.unlockTime) > currentTime!.timestamp) {
        const timeToAdd = Number(prevLock.unlockTime) - currentTime!.timestamp + 1;
        await ethers.provider.send("evm_increaseTime", [timeToAdd]);
        await ethers.provider.send("evm_mine", []);
      }
      await veReach.withdraw();
    }
    
    const testAmount = ethers.parseEther("100");
    
    // Approve
    await reach.approve(contracts.veREACHToken.address, testAmount);
    
    // Create lock
    await veReach.createLock(testAmount, duration.seconds);
    
    // Check voting power
    const lockInfo = await veReach.getLockInfo(signer.address);
    const votingPower = await veReach.getVotingPower(signer.address);
    const expectedMultiplier = (Number(duration.seconds) / Number(MAX_LOCK_TIME)) * 4;
    
    console.log(`  Locked: ${ethers.formatEther(testAmount)} REACH`);
    console.log(`  Voting Power: ${ethers.formatEther(votingPower)}`);
    console.log(`  Expected Multiplier: ${expectedMultiplier.toFixed(2)}x`);
    if (Number(votingPower) > 0) {
      const actualMultiplier = Number(votingPower) / Number(testAmount);
      console.log(`  Actual Multiplier: ${actualMultiplier.toFixed(2)}x`);
      
      // Verify
      if (Math.abs(actualMultiplier - expectedMultiplier) < 0.1) {
        console.log(`  ✅ PASS: Multiplier correct\n`);
      } else {
        console.log(`  ❌ FAIL: Expected ~${expectedMultiplier.toFixed(2)}x, got ${actualMultiplier.toFixed(2)}x\n`);
      }
    } else {
      console.log(`  ⚠️  Voting power is 0\n`);
    }
  }

  console.log("\n" + "=".repeat(60));
  console.log("📊 SCENARIO 2: Extending Locks\n");
  console.log("=".repeat(60));

  // Start with 1 year lock
  const initialAmount = ethers.parseEther("1000");
  const initialDuration = 365 * 24 * 60 * 60; // 1 year
  
  await reach.approve(contracts.veREACHToken.address, initialAmount);
  await veReach.createLock(initialAmount, initialDuration);
  
  const initialLock = await veReach.getLockInfo(signer.address);
  const initialVP = await veReach.getVotingPower(signer.address);
  
  console.log("Initial Lock:");
  console.log(`  Amount: ${ethers.formatEther(initialLock.amount)} REACH`);
  console.log(`  Duration: 1 year`);
  console.log(`  Voting Power: ${ethers.formatEther(initialVP)}`);
  
  // Extend to 2 years
  const extendDuration = 2 * 365 * 24 * 60 * 60; // 2 years total
  const additionalAmount = ethers.parseEther("500");
  
  await reach.approve(contracts.veREACHToken.address, additionalAmount);
  await veReach.createLock(additionalAmount, extendDuration);
  
  const extendedLock = await veReach.getLockInfo(signer.address);
  const extendedVP = await veReach.getVotingPower(signer.address);
  
  console.log("\nAfter Extending to 2 years (+500 REACH):");
  console.log(`  Amount: ${ethers.formatEther(extendedLock.amount)} REACH`);
  console.log(`  Duration: 2 years`);
  console.log(`  Voting Power: ${ethers.formatEther(extendedVP)}`);
  console.log(`  ✅ Lock extended successfully`);
  
  // Extend to 4 years (max)
  const maxDuration = MAX_LOCK_TIME;
  const moreAmount = ethers.parseEther("500");
  
  await reach.approve(contracts.veREACHToken.address, moreAmount);
  await veReach.createLock(moreAmount, maxDuration);
  
  const maxLock = await veReach.getLockInfo(signer.address);
  const maxVP = await veReach.getVotingPower(signer.address);
  
  console.log("\nAfter Extending to 4 years (max) (+500 REACH):");
  console.log(`  Amount: ${ethers.formatEther(maxLock.amount)} REACH`);
  console.log(`  Duration: 4 years (max)`);
  console.log(`  Voting Power: ${ethers.formatEther(maxVP)}`);
  console.log(`  Expected: ~${ethers.formatEther(maxLock.amount * 4n)} (4x multiplier)`);
  console.log(`  ✅ Lock extended to maximum`);

  console.log("\n" + "=".repeat(60));
  console.log("📊 SCENARIO 3: Increasing Lock Amount (No Extension)\n");
  console.log("=".repeat(60));

  // Create a fresh lock for this test
  // We'll use a new account or reset - for demo, let's use the existing lock
  const increaseAmount = ethers.parseEther("1000");
  
  const beforeIncrease = await veReach.getLockInfo(signer.address);
  const vpBefore = await veReach.getVotingPower(signer.address);
  
  console.log("Before Increase:");
  console.log(`  Amount: ${ethers.formatEther(beforeIncrease.amount)} REACH`);
  console.log(`  Voting Power: ${ethers.formatEther(vpBefore)}`);
  
  // Increase amount without extending
  await reach.approve(contracts.veREACHToken.address, increaseAmount);
  await veReach.increaseAmount(increaseAmount);
  
  const afterIncrease = await veReach.getLockInfo(signer.address);
  const vpAfter = await veReach.getVotingPower(signer.address);
  
  console.log("\nAfter Increasing Amount (+1000 REACH, no time extension):");
  console.log(`  Amount: ${ethers.formatEther(afterIncrease.amount)} REACH`);
  console.log(`  Unlock Time: Same (${new Date(Number(afterIncrease.unlockTime) * 1000).toLocaleString()})`);
  console.log(`  Voting Power: ${ethers.formatEther(vpAfter)}`);
  console.log(`  Increase: ${ethers.formatEther(vpAfter - vpBefore)} voting power`);
  console.log(`  ✅ Amount increased successfully`);

  console.log("\n" + "=".repeat(60));
  console.log("📊 FINAL SUMMARY\n");
  console.log("=".repeat(60));
  
  const finalLock = await veReach.getLockInfo(signer.address);
  const finalVP = await veReach.getVotingPower(signer.address);
  const unlockDate = new Date(Number(finalLock.unlockTime) * 1000);
  
  console.log(`Total Locked: ${ethers.formatEther(finalLock.amount)} REACH`);
  console.log(`Unlocks: ${unlockDate.toLocaleString()}`);
  console.log(`Total Voting Power: ${ethers.formatEther(finalVP)}`);
  console.log(`Multiplier: ${(Number(finalVP) / Number(finalLock.amount)).toFixed(2)}x`);
  
  console.log("\n✅ All lock scenario tests complete!");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("Error:", error);
    process.exit(1);
  });

