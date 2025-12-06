// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title ERC-4626 Vault
 * @notice Standardized vault interface for auto-compounding DeFi positions
 * @dev Implements ERC-4626 tokenized vault standard
 */
contract ERC4626Vault is ERC20, Ownable, ReentrancyGuard {
    using SafeERC20 for IERC20;

    IERC20 public immutable asset;
    address public strategy;
    uint256 public totalAssetsStored;
    uint256 public lastHarvest;
    uint256 public harvestCooldown = 1 days;
    uint256 public performanceFee = 200; // 2% (basis points)
    uint256 public managementFee = 100; // 1% annually (basis points)
    uint256 public constant MAX_FEE = 1000; // 10% max

    event Deposit(address indexed caller, address indexed owner, uint256 assets, uint256 shares);
    event Withdraw(address indexed caller, address indexed receiver, address indexed owner, uint256 assets, uint256 shares);
    event Harvest(uint256 assets, uint256 fee);
    event StrategyUpdated(address indexed newStrategy);
    event FeesUpdated(uint256 performanceFee, uint256 managementFee);

    constructor(
        IERC20 _asset,
        string memory _name,
        string memory _symbol,
        address _owner
    ) ERC20(_name, _symbol) Ownable(_owner) {
        asset = _asset;
    }

    /**
     * @dev Total amount of underlying assets managed by vault
     */
    function totalAssets() public view returns (uint256) {
        if (strategy == address(0)) {
            return asset.balanceOf(address(this));
        }
        // In production, query strategy for total assets
        return totalAssetsStored;
    }

    /**
     * @dev Convert assets to shares
     */
    function convertToShares(uint256 assets) public view returns (uint256) {
        uint256 supply = totalSupply();
        if (supply == 0) return assets;
        return (assets * supply) / totalAssets();
    }

    /**
     * @dev Convert shares to assets
     */
    function convertToAssets(uint256 shares) public view returns (uint256) {
        uint256 supply = totalSupply();
        if (supply == 0) return shares;
        return (shares * totalAssets()) / supply;
    }

    /**
     * @dev Deposit assets and mint shares
     */
    function deposit(uint256 assets, address receiver) public nonReentrant returns (uint256 shares) {
        require(assets > 0, "Zero assets");
        
        shares = convertToShares(assets);
        require(shares > 0, "Zero shares");

        asset.safeTransferFrom(msg.sender, address(this), assets);
        
        // Deploy to strategy if set
        if (strategy != address(0)) {
            asset.forceApprove(strategy, assets);
            // Strategy.deposit(assets) - would call strategy contract
            totalAssetsStored += assets;
        }

        _mint(receiver, shares);
        emit Deposit(msg.sender, receiver, assets, shares);
    }

    /**
     * @dev Mint shares for assets
     */
    function mint(uint256 shares, address receiver) public nonReentrant returns (uint256 assets) {
        require(shares > 0, "Zero shares");
        
        assets = convertToAssets(shares);
        require(assets > 0, "Zero assets");

        asset.safeTransferFrom(msg.sender, address(this), assets);
        
        if (strategy != address(0)) {
            asset.forceApprove(strategy, assets);
            totalAssetsStored += assets;
        }

        _mint(receiver, shares);
        emit Deposit(msg.sender, receiver, assets, shares);
    }

    /**
     * @dev Withdraw assets by burning shares
     */
    function withdraw(uint256 assets, address receiver, address owner) public nonReentrant returns (uint256 shares) {
        require(assets > 0, "Zero assets");
        
        if (msg.sender != owner) {
            uint256 allowed = allowance(owner, msg.sender);
            require(allowed >= convertToShares(assets), "Insufficient allowance");
        }

        shares = convertToShares(assets);
        require(shares > 0, "Zero shares");
        require(balanceOf(owner) >= shares, "Insufficient shares");

        // Withdraw from strategy if needed
        if (strategy != address(0)) {
            // Strategy.withdraw(assets) - would call strategy contract
            totalAssetsStored -= assets;
        }

        _burn(owner, shares);
        asset.safeTransfer(receiver, assets);
        
        emit Withdraw(msg.sender, receiver, owner, assets, shares);
    }

    /**
     * @dev Redeem shares for assets
     */
    function redeem(uint256 shares, address receiver, address owner) public nonReentrant returns (uint256 assets) {
        require(shares > 0, "Zero shares");
        
        if (msg.sender != owner) {
            uint256 allowed = allowance(owner, msg.sender);
            require(allowed >= shares, "Insufficient allowance");
        }

        require(balanceOf(owner) >= shares, "Insufficient shares");
        
        assets = convertToAssets(shares);
        require(assets > 0, "Zero assets");

        if (strategy != address(0)) {
            totalAssetsStored -= assets;
        }

        _burn(owner, shares);
        asset.safeTransfer(receiver, assets);
        
        emit Withdraw(msg.sender, receiver, owner, assets, shares);
    }

    /**
     * @dev Harvest rewards and auto-compound (MEV-resistant)
     */
    function harvest() public nonReentrant {
        require(strategy != address(0), "No strategy");
        require(block.timestamp >= lastHarvest + harvestCooldown, "Cooldown active");

        uint256 beforeBalance = asset.balanceOf(address(this));
        
        // Call strategy harvest (would interact with AAVE/Compound/etc)
        // uint256 rewards = IStrategy(strategy).harvest();
        uint256 rewards = 0; // Placeholder
        
        uint256 afterBalance = asset.balanceOf(address(this));
        uint256 harvested = afterBalance - beforeBalance;

        if (harvested > 0) {
            // Calculate and take performance fee
            uint256 fee = (harvested * performanceFee) / 10000;
            if (fee > 0) {
                asset.safeTransfer(owner(), fee);
                harvested -= fee;
            }

            // Re-deposit harvested amount
            if (harvested > 0) {
                asset.forceApprove(strategy, harvested);
                totalAssetsStored += harvested;
            }

            emit Harvest(harvested, fee);
        }

        lastHarvest = block.timestamp;
    }

    /**
     * @dev Set strategy address
     */
    function setStrategy(address _strategy) public onlyOwner {
        require(_strategy != address(0), "Invalid strategy");
        strategy = _strategy;
        emit StrategyUpdated(_strategy);
    }

    /**
     * @dev Update fees
     */
    function setFees(uint256 _performanceFee, uint256 _managementFee) public onlyOwner {
        require(_performanceFee <= MAX_FEE && _managementFee <= MAX_FEE, "Fee too high");
        performanceFee = _performanceFee;
        managementFee = _managementFee;
        emit FeesUpdated(_performanceFee, _managementFee);
    }

    /**
     * @dev Set harvest cooldown
     */
    function setHarvestCooldown(uint256 _cooldown) public onlyOwner {
        harvestCooldown = _cooldown;
    }
}

