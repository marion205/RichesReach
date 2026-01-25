/**
 * Custom hook for wallet management
 * Provides wallet connection state and blockchain operations
 */

import { useState, useEffect, useCallback } from 'react';
import Web3Service, { WalletInfo, AAVEReserve, AAVEUserAccount } from '../../services/Web3Service';
import logger from '../../utils/logger';

export interface UseWalletReturn {
  // Wallet state
  walletInfo: WalletInfo | null;
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;

  // Wallet actions
  connectWallet: () => Promise<void>;
  disconnectWallet: () => void;
  switchNetwork: (chainId: number) => Promise<void>;

  // AAVE data
  aaveReserves: AAVEReserve[];
  userAccountData: AAVEUserAccount | null;
  isLoadingAAVEData: boolean;

  // AAVE actions
  supplyAsset: (assetAddress: string, amount: string) => Promise<string>;
  withdrawAsset: (assetAddress: string, amount: string) => Promise<string>;
  borrowAsset: (assetAddress: string, amount: string, interestRateMode: number) => Promise<string>;
  repayAsset: (assetAddress: string, amount: string, rateMode: number) => Promise<string>;
  toggleCollateral: (assetAddress: string, useAsCollateral: boolean) => Promise<string>;

  // Utility functions
  refreshAccountData: () => Promise<void>;
  refreshReserves: () => Promise<void>;
}

export const useWallet = (): UseWalletReturn => {
  const [walletInfo, setWalletInfo] = useState<WalletInfo | null>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aaveReserves, setAAVEReserves] = useState<AAVEReserve[]>([]);
  const [userAccountData, setUserAccountData] = useState<AAVEUserAccount | null>(null);
  const [isLoadingAAVEData, setIsLoadingAAVEData] = useState(false);

  // Initialize wallet state
  useEffect(() => {
    const initWallet = async () => {
      try {
        const currentWalletInfo = Web3Service.getWalletInfo();
        if (currentWalletInfo) {
          setWalletInfo(currentWalletInfo);
          await refreshAAVEData();
        }
      } catch (err) {
        // Wallet not connected on init - this is expected
      }
    };

    initWallet();
  }, []);

  // Listen for wallet changes
  useEffect(() => {
    const handleAccountsChanged = (accounts: string[]) => {
      if (accounts.length === 0) {
        // Wallet disconnected
        setWalletInfo(null);
        setUserAccountData(null);
      } else {
        // Wallet connected or account changed
        refreshWalletInfo();
      }
    };

    const handleChainChanged = (chainId: string) => {
      // Network changed
      refreshWalletInfo();
    };

    if (typeof window !== 'undefined' && (window as any).ethereum) {
      (window as any).ethereum.on('accountsChanged', handleAccountsChanged);
      (window as any).ethereum.on('chainChanged', handleChainChanged);

      return () => {
        (window as any).ethereum.removeListener('accountsChanged', handleAccountsChanged);
        (window as any).ethereum.removeListener('chainChanged', handleChainChanged);
      };
    }
  }, []);

  const refreshWalletInfo = useCallback(async () => {
    try {
      const currentWalletInfo = Web3Service.getWalletInfo();
      setWalletInfo(currentWalletInfo);
      
      if (currentWalletInfo?.isConnected) {
        await refreshAAVEData();
      }
    } catch (err) {
      logger.error('Failed to refresh wallet info:', err);
    }
  }, []);

  const refreshAAVEData = useCallback(async () => {
    if (!Web3Service.isWalletConnected()) return;

    setIsLoadingAAVEData(true);
    try {
      const [reserves, accountData] = await Promise.all([
        Web3Service.getAAVEReserves(),
        Web3Service.getUserAccountData(),
      ]);

      setAAVEReserves(reserves);
      setUserAccountData(accountData);
    } catch (err) {
      logger.error('Failed to refresh AAVE data:', err);
      setError('Failed to load AAVE data');
    } finally {
      setIsLoadingAAVEData(false);
    }
  }, []);

  const connectWallet = useCallback(async () => {
    setIsConnecting(true);
    setError(null);

    try {
      const walletInfo = await Web3Service.connectWallet();
      setWalletInfo(walletInfo);
      await refreshAAVEData();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to connect wallet';
      setError(errorMessage);
      throw err;
    } finally {
      setIsConnecting(false);
    }
  }, [refreshAAVEData]);

  const disconnectWallet = useCallback(() => {
    Web3Service.disconnectWallet();
    setWalletInfo(null);
    setUserAccountData(null);
    setAAVEReserves([]);
    setError(null);
  }, []);

  const switchNetwork = useCallback(async (chainId: number) => {
    try {
      await Web3Service.switchNetwork(chainId);
      await refreshWalletInfo();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to switch network';
      setError(errorMessage);
      throw err;
    }
  }, [refreshWalletInfo]);

  const supplyAsset = useCallback(async (assetAddress: string, amount: string): Promise<string> => {
    try {
      const txHash = await Web3Service.supplyAsset(assetAddress, amount);
      await refreshAAVEData(); // Refresh data after transaction
      return txHash;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to supply asset';
      setError(errorMessage);
      throw err;
    }
  }, [refreshAAVEData]);

  const withdrawAsset = useCallback(async (assetAddress: string, amount: string): Promise<string> => {
    try {
      const txHash = await Web3Service.withdrawAsset(assetAddress, amount);
      await refreshAAVEData(); // Refresh data after transaction
      return txHash;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to withdraw asset';
      setError(errorMessage);
      throw err;
    }
  }, [refreshAAVEData]);

  const borrowAsset = useCallback(async (
    assetAddress: string, 
    amount: string, 
    interestRateMode: number
  ): Promise<string> => {
    try {
      const txHash = await Web3Service.borrowAsset(assetAddress, amount, interestRateMode);
      await refreshAAVEData(); // Refresh data after transaction
      return txHash;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to borrow asset';
      setError(errorMessage);
      throw err;
    }
  }, [refreshAAVEData]);

  const repayAsset = useCallback(async (
    assetAddress: string, 
    amount: string, 
    rateMode: number
  ): Promise<string> => {
    try {
      const txHash = await Web3Service.repayAsset(assetAddress, amount, rateMode);
      await refreshAAVEData(); // Refresh data after transaction
      return txHash;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to repay asset';
      setError(errorMessage);
      throw err;
    }
  }, [refreshAAVEData]);

  const toggleCollateral = useCallback(async (
    assetAddress: string, 
    useAsCollateral: boolean
  ): Promise<string> => {
    try {
      const txHash = await Web3Service.toggleCollateral(assetAddress, useAsCollateral);
      await refreshAAVEData(); // Refresh data after transaction
      return txHash;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to toggle collateral';
      setError(errorMessage);
      throw err;
    }
  }, [refreshAAVEData]);

  const refreshAccountData = useCallback(async () => {
    if (!Web3Service.isWalletConnected()) return;

    try {
      const accountData = await Web3Service.getUserAccountData();
      setUserAccountData(accountData);
    } catch (err) {
      logger.error('Failed to refresh account data:', err);
      setError('Failed to refresh account data');
    }
  }, []);

  const refreshReserves = useCallback(async () => {
    try {
      const reserves = await Web3Service.getAAVEReserves();
      setAAVEReserves(reserves);
    } catch (err) {
      logger.error('Failed to refresh reserves:', err);
      setError('Failed to refresh reserves');
    }
  }, []);

  return {
    // Wallet state
    walletInfo,
    isConnected: walletInfo?.isConnected || false,
    isConnecting,
    error,

    // Wallet actions
    connectWallet,
    disconnectWallet,
    switchNetwork,

    // AAVE data
    aaveReserves,
    userAccountData,
    isLoadingAAVEData,

    // AAVE actions
    supplyAsset,
    withdrawAsset,
    borrowAsset,
    repayAsset,
    toggleCollateral,

    // Utility functions
    refreshAccountData,
    refreshReserves,
  };
};

export default useWallet;
