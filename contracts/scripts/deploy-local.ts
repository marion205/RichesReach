import { ethers } from "hardhat";
import * as fs from "fs";
import * as path from "path";

/**
 * Deploy to local Hardhat network
 * No testnet tokens needed - uses fake ETH from Hardhat node
 */
async function main() {
  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with account:", deployer.address);
  console.log("Account balance:", ethers.formatEther(await ethers.provider.getBalance(deployer.address)), "ETH");

  // Deploy REACH Token first (1 billion supply, 18 decimals)
  console.log("\n📦 Deploying REACH Token...");
  const MockERC20 = await ethers.getContractFactory("MockERC20");
  const reachToken = await MockERC20.deploy(
    "RichesReach Token",
    "REACH",
    ethers.parseEther("1000000000") // 1B tokens
  );
  await reachToken.waitForDeployment();
  const reachAddress = await reachToken.getAddress();
  console.log("✅ REACH Token deployed to:", reachAddress);

  // Deploy ReachVault (ERC-4626 vault using REACH as underlying)
  console.log("\n📦 Deploying ReachVault...");
  const ERC4626Vault = await ethers.getContractFactory("ERC4626Vault");
  const vault = await ERC4626Vault.deploy(
    reachAddress, // REACH is the underlying asset
    "RichesReach Vault",
    "rREACH",
    deployer.address
  );
  await vault.waitForDeployment();
  const vaultAddress = await vault.getAddress();
  console.log("✅ ReachVault deployed to:", vaultAddress);

  // Deploy veREACH Token
  console.log("\n📦 Deploying veREACH Token...");
  const veREACHToken = await ethers.getContractFactory("veREACHToken");

  // Deploy veREACH
  const veREACH = await veREACHToken.deploy(reachToken);
  await veREACH.waitForDeployment();
  const veREACHAddress = await veREACH.getAddress();
  console.log("✅ veREACH Token deployed to:", veREACHAddress);

  // Save deployment addresses
  const deploymentInfo = {
    network: "localhost",
    chainId: (await ethers.provider.getNetwork()).chainId.toString(),
    deployer: deployer.address,
    timestamp: new Date().toISOString(),
    contracts: {
      REACHToken: {
        address: reachAddress,
        name: "RichesReach Token",
        symbol: "REACH",
        totalSupply: "1000000000",
        decimals: 18,
      },
      ReachVault: {
        address: vaultAddress,
        asset: reachAddress,
        name: "RichesReach Vault",
        symbol: "rREACH",
      },
      veREACHToken: {
        address: veREACHAddress,
        reachToken: reachAddress,
      },
    },
  };

  const deploymentPath = path.join(__dirname, `../deployments/localhost.json`);
  fs.mkdirSync(path.dirname(deploymentPath), { recursive: true });
  fs.writeFileSync(deploymentPath, JSON.stringify(deploymentInfo, null, 2));
  console.log("\n✅ Deployment info saved to:", deploymentPath);

  // Print summary
  console.log("\n" + "=".repeat(60));
  console.log("📋 DEPLOYMENT SUMMARY (LOCAL)");
  console.log("=".repeat(60));
  console.log(`Network: localhost (Hardhat)`);
  console.log(`Chain ID: ${deploymentInfo.chainId}`);
  console.log(`Deployer: ${deployer.address}`);
  console.log("\n📦 Contracts:");
  console.log(`  REACH Token: ${reachAddress}`);
  console.log(`  ReachVault: ${vaultAddress}`);
  console.log(`  veREACH Token: ${veREACHAddress}`);
  console.log("=".repeat(60));
  console.log("\n💡 This is a LOCAL deployment for testing.");
  console.log("   To deploy to Polygon Amoy, get testnet tokens first.");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });

