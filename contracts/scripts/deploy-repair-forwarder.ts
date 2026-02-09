import { ethers } from "hardhat";
import * as fs from "fs";
import * as path from "path";

/**
 * Deploy RepairForwarder (meta-tx forwarder for relayer-submitted repairs).
 *
 * Usage:
 *   npx hardhat run scripts/deploy-repair-forwarder.ts --network localhost
 *   npx hardhat run scripts/deploy-repair-forwarder.ts --network polygonAmoy
 */
async function main() {
  const [deployer] = await ethers.getSigners();
  const network = await ethers.provider.getNetwork();
  const networkName =
    network.name === "unknown"
      ? network.chainId === 1337n
        ? "localhost"
        : "network-" + network.chainId.toString()
      : network.name;

  console.log("Deploying RepairForwarder with account:", deployer.address);
  const balance = await ethers.provider.getBalance(deployer.address);
  console.log("Account balance:", ethers.formatEther(balance));

  // Deploy RepairForwarder
  console.log("\nDeploying RepairForwarder...");
  const RepairForwarder = await ethers.getContractFactory("RepairForwarder");
  const forwarder = await RepairForwarder.deploy();
  await forwarder.waitForDeployment();
  const forwarderAddress = await forwarder.getAddress();
  console.log("RepairForwarder deployed to:", forwarderAddress);

  // Read or create deployment file
  const deploymentPath = path.join(
    __dirname,
    `../deployments/${networkName}.json`
  );
  let deploymentInfo: Record<string, any> = {};
  if (fs.existsSync(deploymentPath)) {
    deploymentInfo = JSON.parse(fs.readFileSync(deploymentPath, "utf-8"));
  } else {
    deploymentInfo = {
      network: networkName,
      chainId: network.chainId.toString(),
      deployer: deployer.address,
      timestamp: new Date().toISOString(),
      contracts: {},
    };
  }

  // Add RepairForwarder to deployment info
  deploymentInfo.contracts.RepairForwarder = {
    address: forwarderAddress,
    deployedAt: new Date().toISOString(),
  };

  fs.mkdirSync(path.dirname(deploymentPath), { recursive: true });
  fs.writeFileSync(deploymentPath, JSON.stringify(deploymentInfo, null, 2));
  console.log("Deployment info saved to:", deploymentPath);

  // Summary
  console.log("\n" + "=".repeat(60));
  console.log("DEPLOYMENT SUMMARY");
  console.log("=".repeat(60));
  console.log(`Network:            ${networkName}`);
  console.log(`Chain ID:           ${network.chainId}`);
  console.log(`Deployer:           ${deployer.address}`);
  console.log(`RepairForwarder:    ${forwarderAddress}`);
  console.log("=".repeat(60));

  // Backend env instructions
  console.log("\nAdd to your backend .env:");
  console.log(`  REPAIR_FORWARDER_ADDRESS=${forwarderAddress}`);

  // Verification (only for non-local networks)
  if (network.chainId !== 1337n && network.chainId !== 31337n) {
    console.log("\nTo verify on block explorer:");
    console.log(
      `  npx hardhat verify --network ${networkName} ${forwarderAddress}`
    );
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
