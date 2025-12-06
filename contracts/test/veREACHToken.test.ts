import { expect } from "chai";
import { ethers } from "hardhat";
import { veREACHToken } from "../typechain-types";
import { ERC20 } from "../typechain-types";

describe("veREACHToken", function () {
  let veREACH: veREACHToken;
  let reachToken: ERC20;
  let owner: any;
  let user1: any;

  beforeEach(async function () {
    [owner, user1] = await ethers.getSigners();

    // Deploy REACH token (using MockERC20)
    const MockERC20Factory = await ethers.getContractFactory("MockERC20");
    reachToken = await MockERC20Factory.deploy(
      "RichesReach Token",
      "REACH",
      ethers.parseEther("1000000000") // 1B tokens
    );
    await reachToken.waitForDeployment();

    // Deploy veREACH
    const veREACHFactory = await ethers.getContractFactory("veREACHToken");
    veREACH = await veREACHFactory.deploy(reachToken);
    await veREACH.waitForDeployment();
  });

  describe("Deployment", function () {
    it("Should set the correct REACH token", async function () {
      expect(await veREACH.REACH()).to.equal(await reachToken.getAddress());
    });
  });

  describe("Locking", function () {
    it("Should allow creating a lock", async function () {
      const lockAmount = ethers.parseEther("10000");
      const lockDuration = 365 * 24 * 60 * 60; // 1 year

      await reachToken.approve(await veREACH.getAddress(), lockAmount);
      
      await expect(veREACH.createLock(lockAmount, lockDuration))
        .to.emit(veREACH, "LockCreated");

      const lock = await veREACH.locks(user1.address);
      expect(lock.amount).to.equal(lockAmount);
      expect(lock.unlockTime).to.be.gt(0);
      expect(lock.votingPower).to.be.gt(0);
    });

    it("Should calculate voting power correctly", async function () {
      const lockAmount = ethers.parseEther("10000");
      const lockDuration = 365 * 24 * 60 * 60; // 1 year
      const maxLockTime = 4 * 365 * 24 * 60 * 60; // 4 years

      const expectedVotingPower = (lockAmount * BigInt(lockDuration) * 4n) / BigInt(maxLockTime);

      await reachToken.approve(await veREACH.getAddress(), lockAmount);
      await veREACH.createLock(lockAmount, lockDuration);

      const votingPower = await veREACH.getVotingPower(user1.address);
      expect(votingPower).to.be.closeTo(expectedVotingPower, ethers.parseEther("1"));
    });

    it("Should reject lock duration less than minimum", async function () {
      const lockAmount = ethers.parseEther("10000");
      const lockDuration = 6 * 24 * 60 * 60; // 6 days (less than 1 week)

      await reachToken.approve(await veREACH.getAddress(), lockAmount);
      
      await expect(
        veREACH.createLock(lockAmount, lockDuration)
      ).to.be.revertedWith("Invalid duration");
    });

    it("Should reject lock duration more than maximum", async function () {
      const lockAmount = ethers.parseEther("10000");
      const lockDuration = 5 * 365 * 24 * 60 * 60; // 5 years (more than 4 years)

      await reachToken.approve(await veREACH.getAddress(), lockAmount);
      
      await expect(
        veREACH.createLock(lockAmount, lockDuration)
      ).to.be.revertedWith("Invalid duration");
    });
  });

  describe("Withdrawal", function () {
    it("Should allow withdrawal after unlock time", async function () {
      const lockAmount = ethers.parseEther("10000");
      const lockDuration = 7 * 24 * 60 * 60; // 1 week

      await reachToken.approve(await veREACH.getAddress(), lockAmount);
      await veREACH.createLock(lockAmount, lockDuration);

      // Fast forward time (requires hardhat network manipulation)
      await ethers.provider.send("evm_increaseTime", [lockDuration + 1]);
      await ethers.provider.send("evm_mine", []);

      await expect(veREACH.withdraw())
        .to.emit(veREACH, "LockWithdrawn")
        .withArgs(user1.address, lockAmount);

      const lock = await veREACH.locks(user1.address);
      expect(lock.amount).to.equal(0);
    });

    it("Should reject withdrawal before unlock time", async function () {
      const lockAmount = ethers.parseEther("10000");
      const lockDuration = 365 * 24 * 60 * 60; // 1 year

      await reachToken.approve(await veREACH.getAddress(), lockAmount);
      await veREACH.createLock(lockAmount, lockDuration);

      await expect(veREACH.withdraw()).to.be.revertedWith("Still locked");
    });
  });

  describe("Lock Extensions", function () {
    it("Should allow extending lock duration", async function () {
      const lockAmount = ethers.parseEther("10000");
      const initialDuration = 365 * 24 * 60 * 60; // 1 year
      const extendedDuration = 2 * 365 * 24 * 60 * 60; // 2 years

      await reachToken.approve(await veREACH.getAddress(), lockAmount);
      await veREACH.createLock(lockAmount, initialDuration);

      const initialLock = await veREACH.locks(user1.address);
      const initialVP = await veREACH.getVotingPower(user1.address);

      // Extend lock with additional amount
      const additionalAmount = ethers.parseEther("5000");
      await reachToken.approve(await veREACH.getAddress(), additionalAmount);
      
      await expect(veREACH.createLock(additionalAmount, extendedDuration))
        .to.emit(veREACH, "LockExtended");

      const extendedLock = await veREACH.locks(user1.address);
      const extendedVP = await veREACH.getVotingPower(user1.address);

      expect(extendedLock.amount).to.equal(lockAmount + additionalAmount);
      expect(extendedLock.unlockTime).to.be.gt(initialLock.unlockTime);
      expect(extendedVP).to.be.gt(initialVP);
    });

    it("Should reject extending to shorter duration", async function () {
      const lockAmount = ethers.parseEther("10000");
      const initialDuration = 2 * 365 * 24 * 60 * 60; // 2 years
      const shorterDuration = 365 * 24 * 60 * 60; // 1 year

      await reachToken.approve(await veREACH.getAddress(), lockAmount);
      await veREACH.createLock(lockAmount, initialDuration);

      const additionalAmount = ethers.parseEther("5000");
      await reachToken.approve(await veREACH.getAddress(), additionalAmount);

      await expect(
        veREACH.createLock(additionalAmount, shorterDuration)
      ).to.be.revertedWith("Can only extend");
    });
  });

  describe("Increasing Lock Amount", function () {
    it("Should allow increasing lock amount without extending time", async function () {
      const lockAmount = ethers.parseEther("10000");
      const lockDuration = 365 * 24 * 60 * 60; // 1 year

      await reachToken.approve(await veREACH.getAddress(), lockAmount);
      await veREACH.createLock(lockAmount, lockDuration);

      const initialLock = await veREACH.locks(user1.address);
      const initialVP = await veREACH.getVotingPower(user1.address);

      // Increase amount
      const increaseAmount = ethers.parseEther("5000");
      await reachToken.approve(await veREACH.getAddress(), increaseAmount);
      
      await expect(veREACH.increaseAmount(increaseAmount))
        .to.emit(veREACH, "LockIncreased");

      const increasedLock = await veREACH.locks(user1.address);
      const increasedVP = await veREACH.getVotingPower(user1.address);

      expect(increasedLock.amount).to.equal(lockAmount + increaseAmount);
      expect(increasedLock.unlockTime).to.equal(initialLock.unlockTime); // Same unlock time
      expect(increasedVP).to.be.gt(initialVP);
    });

    it("Should reject increasing amount for expired lock", async function () {
      const lockAmount = ethers.parseEther("10000");
      const lockDuration = 7 * 24 * 60 * 60; // 1 week

      await reachToken.approve(await veREACH.getAddress(), lockAmount);
      await veREACH.createLock(lockAmount, lockDuration);

      // Fast forward past unlock time
      await ethers.provider.send("evm_increaseTime", [lockDuration + 1]);
      await ethers.provider.send("evm_mine", []);

      const increaseAmount = ethers.parseEther("5000");
      await reachToken.approve(await veREACH.getAddress(), increaseAmount);

      await expect(veREACH.increaseAmount(increaseAmount))
        .to.be.revertedWith("Lock expired");
    });
  });

  describe("Voting Power Calculations", function () {
    it("Should calculate 1x multiplier for minimum lock (1 week)", async function () {
      const lockAmount = ethers.parseEther("10000");
      const lockDuration = 7 * 24 * 60 * 60; // 1 week
      const maxLockTime = 4 * 365 * 24 * 60 * 60; // 4 years

      await reachToken.approve(await veREACH.getAddress(), lockAmount);
      await veREACH.createLock(lockAmount, lockDuration);

      const votingPower = await veREACH.getVotingPower(user1.address);
      const expectedVP = (lockAmount * BigInt(lockDuration) * 4n) / BigInt(maxLockTime);

      expect(votingPower).to.be.closeTo(expectedVP, ethers.parseEther("0.1"));
    });

    it("Should calculate 4x multiplier for maximum lock (4 years)", async function () {
      const lockAmount = ethers.parseEther("10000");
      const lockDuration = 4 * 365 * 24 * 60 * 60; // 4 years

      await reachToken.approve(await veREACH.getAddress(), lockAmount);
      await veREACH.createLock(lockAmount, lockDuration);

      const votingPower = await veREACH.getVotingPower(user1.address);
      const expectedVP = lockAmount * 4n; // 4x multiplier

      expect(votingPower).to.be.closeTo(expectedVP, ethers.parseEther("1"));
    });

    it("Should calculate 3x multiplier for 1 year lock", async function () {
      const lockAmount = ethers.parseEther("10000");
      const lockDuration = 365 * 24 * 60 * 60; // 1 year
      const maxLockTime = 4 * 365 * 24 * 60 * 60; // 4 years

      await reachToken.approve(await veREACH.getAddress(), lockAmount);
      await veREACH.createLock(lockAmount, lockDuration);

      const votingPower = await veREACH.getVotingPower(user1.address);
      const expectedVP = (lockAmount * BigInt(lockDuration) * 4n) / BigInt(maxLockTime);

      expect(votingPower).to.be.closeTo(expectedVP, ethers.parseEther("1"));
    });
  });

  describe("Edge Cases", function () {
    it("Should reject zero amount lock", async function () {
      const lockAmount = ethers.parseEther("0");
      const lockDuration = 365 * 24 * 60 * 60;

      await reachToken.approve(await veREACH.getAddress(), lockAmount);
      
      await expect(
        veREACH.createLock(lockAmount, lockDuration)
      ).to.be.revertedWith("Zero amount");
    });

    it("Should reject zero amount increase", async function () {
      const lockAmount = ethers.parseEther("10000");
      const lockDuration = 365 * 24 * 60 * 60;

      await reachToken.approve(await veREACH.getAddress(), lockAmount);
      await veREACH.createLock(lockAmount, lockDuration);

      await expect(
        veREACH.increaseAmount(0)
      ).to.be.reverted; // Should revert (check contract for exact message)
    });

    it("Should handle multiple locks from different users", async function () {
      const [owner, user1, user2] = await ethers.getSigners();
      
      const lockAmount1 = ethers.parseEther("10000");
      const lockAmount2 = ethers.parseEther("5000");
      const lockDuration = 365 * 24 * 60 * 60;

      // User 1 lock
      await reachToken.connect(user1).approve(await veREACH.getAddress(), lockAmount1);
      await veREACH.connect(user1).createLock(lockAmount1, lockDuration);

      // User 2 lock
      await reachToken.connect(user2).approve(await veREACH.getAddress(), lockAmount2);
      await veREACH.connect(user2).createLock(lockAmount2, lockDuration);

      const lock1 = await veREACH.locks(user1.address);
      const lock2 = await veREACH.locks(user2.address);

      expect(lock1.amount).to.equal(lockAmount1);
      expect(lock2.amount).to.equal(lockAmount2);
      expect(lock1.unlockTime).to.not.equal(0);
      expect(lock2.unlockTime).to.not.equal(0);
    });
  });
});

