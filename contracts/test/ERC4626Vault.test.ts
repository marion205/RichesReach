import { expect } from "chai";
import { ethers } from "hardhat";
import { ERC4626Vault } from "../typechain-types";
import { ERC20 } from "../typechain-types";

describe("ERC4626Vault", function () {
  let vault: ERC4626Vault;
  let asset: ERC20;
  let owner: any;
  let user1: any;
  let user2: any;

  beforeEach(async function () {
    [owner, user1, user2] = await ethers.getSigners();

    // Deploy mock ERC20 asset (using MockERC20)
    const MockERC20Factory = await ethers.getContractFactory("MockERC20");
    asset = await MockERC20Factory.deploy("Test USDC", "USDC", ethers.parseEther("1000000"));
    await asset.waitForDeployment();

    // Deploy vault
    const VaultFactory = await ethers.getContractFactory("ERC4626Vault");
    vault = await VaultFactory.deploy(
      await asset.getAddress(),
      "Test Vault",
      "tVAULT",
      owner.address
    );
    await vault.waitForDeployment();
  });

  describe("Deployment", function () {
    it("Should set the correct asset", async function () {
      expect(await vault.asset()).to.equal(await asset.getAddress());
    });

    it("Should set the correct owner", async function () {
      expect(await vault.owner()).to.equal(owner.address);
    });
  });

  describe("Deposit", function () {
    it("Should allow deposit and mint shares", async function () {
      const depositAmount = ethers.parseEther("1000");
      await asset.approve(await vault.getAddress(), depositAmount);
      
      await expect(vault.deposit(depositAmount, user1.address))
        .to.emit(vault, "Deposit");

      const shares = await vault.balanceOf(user1.address);
      expect(shares).to.be.gt(0);
    });

    it("Should reject zero deposit", async function () {
      await expect(
        vault.deposit(0, user1.address)
      ).to.be.revertedWith("Zero assets");
    });
  });

  describe("Withdraw", function () {
    beforeEach(async function () {
      const depositAmount = ethers.parseEther("1000");
      await asset.approve(await vault.getAddress(), depositAmount);
      await vault.deposit(depositAmount, user1.address);
    });

    it("Should allow withdraw and burn shares", async function () {
      const shares = await vault.balanceOf(user1.address);
      const withdrawAmount = await vault.convertToAssets(shares);

      await expect(
        vault.withdraw(withdrawAmount, user1.address, user1.address)
      ).to.emit(vault, "Withdraw");

      const remainingShares = await vault.balanceOf(user1.address);
      expect(remainingShares).to.equal(0);
    });
  });

  describe("Conversion", function () {
    it("Should convert assets to shares correctly", async function () {
      const assets = ethers.parseEther("1000");
      const shares = await vault.convertToShares(assets);
      expect(shares).to.equal(assets); // 1:1 initially
    });

    it("Should convert shares to assets correctly", async function () {
      const shares = ethers.parseEther("1000");
      const assets = await vault.convertToAssets(shares);
      expect(assets).to.equal(shares); // 1:1 initially
    });
  });
});

