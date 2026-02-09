import { ethers } from "hardhat";
import * as fs from "fs";
import * as path from "path";

/**
 * Approve RepairForwarder on a source vault so it can withdraw on behalf of the user.
 *
 * Required env vars:
 *   VAULT_ADDRESS   - the ERC-4626 vault the user wants to allow repairs from
 *   FORWARDER_ADDRESS - (optional) override; otherwise read from deployments/<network>.json
 *   APPROVE_AMOUNT  - (optional) share amount to approve, default: max uint256
 *
 * Usage:
 *   VAULT_ADDRESS=0x... npm run approve-forwarder:local
 *   VAULT_ADDRESS=0x... npm run approve-forwarder:amoy
 */
async function main() {
  const [signer] = await ethers.getSigners();
  const network = await ethers.provider.getNetwork();
  const networkName =
    network.name === "unknown"
      ? network.chainId === 1337n
        ? "localhost"
        : "network-" + network.chainId.toString()
      : network.name;

  // Resolve forwarder address
  let forwarderAddress = process.env.FORWARDER_ADDRESS;
  if (!forwarderAddress) {
    const deploymentPath = path.join(
      __dirname,
      `../deployments/${networkName}.json`
    );
    if (!fs.existsSync(deploymentPath)) {
      console.error(
        `No deployment file at ${deploymentPath}. Deploy RepairForwarder first or set FORWARDER_ADDRESS.`
      );
      process.exit(1);
    }
    const deployment = JSON.parse(fs.readFileSync(deploymentPath, "utf-8"));
    forwarderAddress = deployment.contracts?.RepairForwarder?.address;
    if (!forwarderAddress) {
      console.error(
        "RepairForwarder not found in deployment file. Deploy it first."
      );
      process.exit(1);
    }
  }

  const vaultAddress = process.env.VAULT_ADDRESS;
  if (!vaultAddress) {
    console.error("Set VAULT_ADDRESS env var to the source vault address.");
    process.exit(1);
  }

  const approveAmount = process.env.APPROVE_AMOUNT
    ? BigInt(process.env.APPROVE_AMOUNT)
    : ethers.MaxUint256;

  console.log("Approving RepairForwarder on vault");
  console.log("  Signer:          ", signer.address);
  console.log("  Vault:           ", vaultAddress);
  console.log("  RepairForwarder: ", forwarderAddress);
  console.log(
    "  Amount (shares):  ",
    approveAmount === ethers.MaxUint256 ? "MAX (unlimited)" : approveAmount.toString()
  );

  // ERC-20 approve ABI (vault shares are ERC-20 tokens)
  const erc20Abi = [
    "function approve(address spender, uint256 amount) external returns (bool)",
    "function allowance(address owner, address spender) external view returns (uint256)",
    "function symbol() external view returns (string)",
  ];

  const vault = new ethers.Contract(vaultAddress, erc20Abi, signer);

  const symbol = await vault.symbol();
  console.log(`\nVault share token: ${symbol}`);

  const tx = await vault.approve(forwarderAddress, approveAmount);
  console.log("Approval tx sent:", tx.hash);
  await tx.wait();
  console.log("Approval confirmed.");

  const allowance = await vault.allowance(signer.address, forwarderAddress);
  console.log("Current allowance:", allowance.toString());

  console.log(
    "\nRepairForwarder is now approved to withdraw from this vault on your behalf."
  );
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
