// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title veREACH Token
 * @notice Vote-escrowed REACH token for governance and revenue sharing
 * @dev Inspired by Curve's veCRV model
 */
contract veREACHToken is Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    IERC20 public immutable REACH;
    
    struct Lock {
        uint256 amount;
        uint256 unlockTime;
        uint256 votingPower;
    }

    mapping(address => Lock) public locks;
    mapping(address => uint256) public totalVotingPower;
    uint256 public totalLocked;
    uint256 public constant MAX_LOCK_TIME = 4 * 365 days; // 4 years max
    uint256 public constant MIN_LOCK_TIME = 1 weeks; // 1 week minimum

    event LockCreated(address indexed user, uint256 amount, uint256 unlockTime, uint256 votingPower);
    event LockExtended(address indexed user, uint256 newUnlockTime, uint256 newVotingPower);
    event LockIncreased(address indexed user, uint256 additionalAmount, uint256 newVotingPower);
    event LockWithdrawn(address indexed user, uint256 amount);
    event RevenueDistributed(uint256 totalAmount, uint256 perVoteAmount);

    constructor(IERC20 _reach) Ownable(msg.sender) {
        REACH = _reach;
    }

    /**
     * @dev Create or extend a lock
     */
    function createLock(uint256 amount, uint256 lockDuration) public nonReentrant {
        require(amount > 0, "Zero amount");
        require(lockDuration >= MIN_LOCK_TIME && lockDuration <= MAX_LOCK_TIME, "Invalid duration");
        
        Lock storage userLock = locks[msg.sender];
        uint256 unlockTime = block.timestamp + lockDuration;
        
        if (userLock.unlockTime == 0) {
            // New lock
            REACH.safeTransferFrom(msg.sender, address(this), amount);
            userLock.amount = amount;
            userLock.unlockTime = unlockTime;
            userLock.votingPower = calculateVotingPower(amount, lockDuration);
            
            totalLocked += amount;
            totalVotingPower[msg.sender] = userLock.votingPower;
            
            emit LockCreated(msg.sender, amount, unlockTime, userLock.votingPower);
        } else {
            // Extend existing lock
            require(unlockTime > userLock.unlockTime, "Can only extend");
            
            REACH.safeTransferFrom(msg.sender, address(this), amount);
            userLock.amount += amount;
            userLock.unlockTime = unlockTime;
            
            uint256 oldVotingPower = userLock.votingPower;
            userLock.votingPower = calculateVotingPower(userLock.amount, lockDuration);
            
            totalLocked += amount;
            totalVotingPower[msg.sender] = userLock.votingPower;
            
            emit LockExtended(msg.sender, unlockTime, userLock.votingPower);
            emit LockIncreased(msg.sender, amount, userLock.votingPower);
        }
    }

    /**
     * @dev Increase lock amount without extending time
     */
    function increaseAmount(uint256 amount) public nonReentrant {
        require(amount > 0, "Zero amount");
        
        Lock storage userLock = locks[msg.sender];
        require(userLock.unlockTime > block.timestamp, "Lock expired");
        
        REACH.safeTransferFrom(msg.sender, address(this), amount);
        userLock.amount += amount;
        
        uint256 remainingTime = userLock.unlockTime - block.timestamp;
        uint256 oldVotingPower = userLock.votingPower;
        userLock.votingPower = calculateVotingPower(userLock.amount, remainingTime);
        
        totalLocked += amount;
        totalVotingPower[msg.sender] = userLock.votingPower;
        
        emit LockIncreased(msg.sender, amount, userLock.votingPower);
    }

    /**
     * @dev Withdraw after unlock time
     */
    function withdraw() public nonReentrant {
        Lock storage userLock = locks[msg.sender];
        require(userLock.unlockTime > 0, "No lock");
        require(block.timestamp >= userLock.unlockTime, "Still locked");
        
        uint256 amount = userLock.amount;
        uint256 votingPower = userLock.votingPower;
        
        delete locks[msg.sender];
        totalLocked -= amount;
        totalVotingPower[msg.sender] = 0;
        
        REACH.safeTransfer(msg.sender, amount);
        emit LockWithdrawn(msg.sender, amount);
    }

    /**
     * @dev Calculate voting power based on amount and duration
     * Formula: votingPower = amount * (lockDuration / MAX_LOCK_TIME)
     * Max 4x multiplier for 4-year lock
     */
    function calculateVotingPower(uint256 amount, uint256 duration) public pure returns (uint256) {
        if (duration > MAX_LOCK_TIME) {
            duration = MAX_LOCK_TIME;
        }
        // Linear scaling: 1x for 1 week, 4x for 4 years
        return (amount * duration) / MAX_LOCK_TIME * 4;
    }

    /**
     * @dev Get user's voting power
     */
    function getVotingPower(address user) public view returns (uint256) {
        Lock memory userLock = locks[user];
        if (userLock.unlockTime == 0 || block.timestamp >= userLock.unlockTime) {
            return 0;
        }
        return userLock.votingPower;
    }

    /**
     * @dev Get user's lock info
     */
    function getLockInfo(address user) public view returns (Lock memory) {
        return locks[user];
    }

    /**
     * @dev Distribute revenue to veREACH holders (called by owner/governance)
     */
    function distributeRevenue(uint256 totalAmount) public onlyOwner {
        require(totalAmount > 0, "Zero amount");
        require(totalLocked > 0, "No locks");
        
        // Calculate per voting power share
        uint256 totalVotingPowerSum = 0;
        // In production, would iterate through all locks or use snapshot
        // For now, simplified distribution
        
        REACH.safeTransferFrom(msg.sender, address(this), totalAmount);
        
        // Distribute proportionally (simplified - would need efficient distribution mechanism)
        emit RevenueDistributed(totalAmount, 0);
    }

    /**
     * @dev Emergency withdraw (only owner, for safety)
     */
    function emergencyWithdraw(address token, uint256 amount) public onlyOwner {
        IERC20(token).safeTransfer(owner(), amount);
    }
}

