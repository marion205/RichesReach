/**
 * Web3 Service for blockchain integration
 * Handles wallet connection, transaction signing, and AAVE interactions
 */

import { ethers } from 'ethers';
import logger from '../utils/logger';

export interface WalletInfo {
  address: string;
  chainId: number;
  isConnected: boolean;
  balance?: string;
}

export interface AAVEReserve {
  symbol: string;
  address: string;
  decimals: number;
  ltv: number;
  liquidationThreshold: number;
  variableBorrowRate: number;
  stableBorrowRate: number;
  supplyRate: number;
}

export interface AAVEUserAccount {
  totalCollateralETH: string;
  totalDebtETH: string;
  availableBorrowsETH: string;
  currentLiquidationThreshold: string;
  ltv: string;
  healthFactor: string;
}

class Web3Service {
  private provider: ethers.providers.Web3Provider | null = null;
  private signer: ethers.Signer | null = null;
  private walletInfo: WalletInfo | null = null;
  private aaveLendingPool: ethers.Contract | null = null;

  // AAVE V2 Mainnet addresses
  private readonly AAVE_LENDING_POOL_ADDRESS = '0x7d2768dE32b0b80b7a3454c06BdAc94A69DDc7A9';
  private readonly AAVE_LENDING_POOL_ABI = [
    // Core functions
    'function deposit(address asset, uint256 amount, address onBehalfOf, uint16 referralCode) external',
    'function withdraw(address asset, uint256 amount, address to) external returns (uint256)',
    'function borrow(address asset, uint256 amount, uint256 interestRateMode, uint16 referralCode, address onBehalfOf) external',
    'function repay(address asset, uint256 amount, uint256 rateMode, address onBehalfOf) external returns (uint256)',
    'function setUserUseReserveAsCollateral(address asset, bool useAsCollateral) external',
    'function getUserAccountData(address user) external view returns (uint256, uint256, uint256, uint256, uint256, uint256)',
    'function getReserveData(address asset) external view returns (tuple)',
    'function getReservesList() external view returns (address[])',
  ];

  constructor() {
    this.initializeProvider();
  }

  private async initializeProvider() {
    try {
      // Check if Web3 is available (MetaMask, etc.)
      if (typeof window !== 'undefined' && (window as any).ethereum) {
        this.provider = new ethers.providers.Web3Provider((window as any).ethereum);
        this.signer = this.provider.getSigner();
        this.aaveLendingPool = new ethers.Contract(
          this.AAVE_LENDING_POOL_ADDRESS,
          this.AAVE_LENDING_POOL_ABI,
          this.signer
        );
      }
    } catch (error) {
      logger.log('Web3 provider not available:', error);
    }
  }

  /**
   * Connect to wallet (MetaMask, WalletConnect, etc.)
   */
  async connectWallet(): Promise<WalletInfo> {
    try {
      if (!this.provider) {
        throw new Error('Web3 provider not available. Please install MetaMask or another Web3 wallet.');
      }

      // Request account access
      await (window as any).ethereum.request({ method: 'eth_requestAccounts' });
      
      // Get account info
      const address = await this.signer!.getAddress();
      const network = await this.provider.getNetwork();
      const balance = await this.provider.getBalance(address);

      this.walletInfo = {
        address,
        chainId: network.chainId,
        isConnected: true,
        balance: ethers.utils.formatEther(balance),
      };

      return this.walletInfo;
    } catch (error) {
      logger.error('Failed to connect wallet:', error);
      throw new Error('Failed to connect wallet. Please try again.');
    }
  }

  /**
   * Disconnect wallet
   */
  disconnectWallet() {
    this.walletInfo = null;
    this.signer = null;
    this.provider = null;
    this.aaveLendingPool = null;
  }

  /**
   * Get current wallet info
   */
  getWalletInfo(): WalletInfo | null {
    return this.walletInfo;
  }

  /**
   * Check if wallet is connected
   */
  isWalletConnected(): boolean {
    return this.walletInfo?.isConnected || false;
  }

  /**
   * Switch to a specific network (Ethereum Mainnet, Polygon, etc.)
   */
  async switchNetwork(chainId: number): Promise<void> {
    try {
      await (window as any).ethereum.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: `0x${chainId.toString(16)}` }],
      });
    } catch (error) {
      logger.error('Failed to switch network:', error);
      throw new Error('Failed to switch network. Please try again.');
    }
  }

  /**
   * Get AAVE reserves list
   */
  async getAAVEReserves(): Promise<AAVEReserve[]> {
    try {
      if (!this.aaveLendingPool) {
        throw new Error('AAVE contract not initialized');
      }

      const reservesAddresses = await this.aaveLendingPool.getReservesList();
      const reserves: AAVEReserve[] = [];

      for (const address of reservesAddresses) {
        try {
          const reserveData = await this.aaveLendingPool!.getReserveData(address);
          // Parse reserve data and create AAVEReserve object
          // This is a simplified version - you'd need to parse the full reserve data
          reserves.push({
            symbol: 'UNKNOWN', // You'd get this from a token registry
            address,
            decimals: 18, // Default, you'd get this from the token contract
            ltv: 0.7, // Default, you'd get this from reserve data
            liquidationThreshold: 0.8, // Default
            variableBorrowRate: 0.05, // Default
            stableBorrowRate: 0.06, // Default
            supplyRate: 0.03, // Default
          });
        } catch (error) {
          logger.log(`Failed to get data for reserve ${address}:`, error);
        }
      }

      return reserves;
    } catch (error) {
      logger.error('Failed to get AAVE reserves:', error);
      throw new Error('Failed to fetch AAVE reserves');
    }
  }

  /**
   * Get user's AAVE account data
   */
  async getUserAccountData(): Promise<AAVEUserAccount> {
    try {
      if (!this.aaveLendingPool || !this.walletInfo) {
        throw new Error('Wallet not connected');
      }

      const accountData = await this.aaveLendingPool.getUserAccountData(this.walletInfo.address);
      
      return {
        totalCollateralETH: ethers.utils.formatEther(accountData[0]),
        totalDebtETH: ethers.utils.formatEther(accountData[1]),
        availableBorrowsETH: ethers.utils.formatEther(accountData[2]),
        currentLiquidationThreshold: ethers.utils.formatEther(accountData[3]),
        ltv: ethers.utils.formatEther(accountData[4]),
        healthFactor: ethers.utils.formatEther(accountData[5]),
      };
    } catch (error) {
      logger.error('Failed to get user account data:', error);
      throw new Error('Failed to fetch account data');
    }
  }

  /**
   * Supply assets to AAVE
   */
  async supplyAsset(assetAddress: string, amount: string, onBehalfOf?: string): Promise<string> {
    try {
      if (!this.aaveLendingPool || !this.signer) {
        throw new Error('Wallet not connected');
      }

      const tx = await this.aaveLendingPool.deposit(
        assetAddress,
        ethers.utils.parseEther(amount),
        onBehalfOf || this.walletInfo!.address,
        0 // referral code
      );

      const receipt = await tx.wait();
      return receipt.transactionHash;
    } catch (error) {
      logger.error('Failed to supply asset:', error);
      throw new Error('Failed to supply asset');
    }
  }

  /**
   * Withdraw assets from AAVE
   */
  async withdrawAsset(assetAddress: string, amount: string): Promise<string> {
    try {
      if (!this.aaveLendingPool || !this.signer) {
        throw new Error('Wallet not connected');
      }

      const tx = await this.aaveLendingPool.withdraw(
        assetAddress,
        ethers.utils.parseEther(amount),
        this.walletInfo!.address
      );

      const receipt = await tx.wait();
      return receipt.transactionHash;
    } catch (error) {
      logger.error('Failed to withdraw asset:', error);
      throw new Error('Failed to withdraw asset');
    }
  }

  /**
   * Borrow assets from AAVE
   */
  async borrowAsset(
    assetAddress: string, 
    amount: string, 
    interestRateMode: number, // 1 = stable, 2 = variable
    onBehalfOf?: string
  ): Promise<string> {
    try {
      if (!this.aaveLendingPool || !this.signer) {
        throw new Error('Wallet not connected');
      }

      const tx = await this.aaveLendingPool.borrow(
        assetAddress,
        ethers.utils.parseEther(amount),
        interestRateMode,
        0, // referral code
        onBehalfOf || this.walletInfo!.address
      );

      const receipt = await tx.wait();
      return receipt.transactionHash;
    } catch (error) {
      logger.error('Failed to borrow asset:', error);
      throw new Error('Failed to borrow asset');
    }
  }

  /**
   * Repay borrowed assets
   */
  async repayAsset(
    assetAddress: string, 
    amount: string, 
    rateMode: number,
    onBehalfOf?: string
  ): Promise<string> {
    try {
      if (!this.aaveLendingPool || !this.signer) {
        throw new Error('Wallet not connected');
      }

      const tx = await this.aaveLendingPool.repay(
        assetAddress,
        ethers.utils.parseEther(amount),
        rateMode,
        onBehalfOf || this.walletInfo!.address
      );

      const receipt = await tx.wait();
      return receipt.transactionHash;
    } catch (error) {
      logger.error('Failed to repay asset:', error);
      throw new Error('Failed to repay asset');
    }
  }

  /**
   * Toggle collateral usage for an asset
   */
  async toggleCollateral(assetAddress: string, useAsCollateral: boolean): Promise<string> {
    try {
      if (!this.aaveLendingPool || !this.signer) {
        throw new Error('Wallet not connected');
      }

      const tx = await this.aaveLendingPool.setUserUseReserveAsCollateral(
        assetAddress,
        useAsCollateral
      );

      const receipt = await tx.wait();
      return receipt.transactionHash;
    } catch (error) {
      logger.error('Failed to toggle collateral:', error);
      throw new Error('Failed to toggle collateral');
    }
  }

  /**
   * Estimate gas for a transaction
   */
  async estimateGas(transaction: any): Promise<string> {
    try {
      if (!this.provider) {
        throw new Error('Provider not available');
      }

      const gasEstimate = await this.provider.estimateGas(transaction);
      return gasEstimate.toString();
    } catch (error) {
      logger.error('Failed to estimate gas:', error);
      throw new Error('Failed to estimate gas');
    }
  }

  /**
   * Get current gas price
   */
  async getGasPrice(): Promise<string> {
    try {
      if (!this.provider) {
        throw new Error('Provider not available');
      }

      const gasPrice = await this.provider.getGasPrice();
      return ethers.utils.formatUnits(gasPrice, 'gwei');
    } catch (error) {
      logger.error('Failed to get gas price:', error);
      throw new Error('Failed to get gas price');
    }
  }
}

// Export singleton instance
const web3ServiceInstance = new Web3Service();
export default web3ServiceInstance;

// Export class type for type annotations
export type { Web3Service as Web3ServiceType };
