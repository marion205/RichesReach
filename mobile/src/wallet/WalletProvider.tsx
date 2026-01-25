import React, { createContext, useContext, useMemo } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ethers } from 'ethers';
import logger from '../utils/logger';

// Optional WalletConnect - only import if available
let WalletConnectProvider: any = null;
let useWalletConnect: any = null;

try {
  const walletConnect = require('@walletconnect/react-native-dapp');
  WalletConnectProvider = walletConnect.default || walletConnect.WalletConnectProvider;
  useWalletConnect = walletConnect.useWalletConnect;
} catch (e) {
  logger.warn('WalletConnect not available - blockchain features will be limited');
}

const Ctx = createContext<any>(null);
export const useWallet = () => useContext(Ctx);

export function WalletProvider({ children }: {children: React.ReactNode}) {
  // If WalletConnect is not available, just render children directly
  if (!WalletConnectProvider) {
    return <Inner>{children}</Inner>;
  }

  return (
    <WalletConnectProvider 
      redirectUrl="richesreach://"
      storageOptions={{ asyncStorage: AsyncStorage }}
      qrcodeModalOptions={{ 
        mobileLinks: ['metamask','rainbow','trust','coinbase','walletconnect'] 
      }}
    >
      <Inner>{children}</Inner>
    </WalletConnectProvider>
  );
}

function Inner({ children }: {children: React.ReactNode}) {
  const connector = useWalletConnect ? useWalletConnect() : { 
    connected: false, 
    accounts: [], 
    chainId: null,
    connect: async () => { throw new Error('WalletConnect not available'); },
    killSession: async () => {},
    updateSession: async () => {}
  };
  
  const evm = useMemo(() => {
    if (!connector.connected || !connector.accounts?.length) return null;
    try {
      const provider = new ethers.providers.Web3Provider(connector as any);
      return { 
        provider, 
        signer: provider.getSigner(),
        address: connector.accounts[0],
        chainId: connector.chainId
      };
    } catch (error) {
      logger.warn('Failed to create EVM provider:', error);
      return null;
    }
  }, [connector.connected, connector.accounts, connector.chainId]);

  const connect = async () => {
    if (!useWalletConnect) {
      throw new Error('WalletConnect not available - install @walletconnect/react-native-dapp');
    }
    try {
      await connector.connect();
    } catch (error) {
      logger.error('Wallet connection failed:', error);
      throw error;
    }
  };

  const disconnect = async () => {
    if (!useWalletConnect) return;
    try {
      await connector.killSession();
    } catch (error) {
      logger.error('Wallet disconnection failed:', error);
    }
  };

  const switchChain = async (chainId: number) => {
    if (!useWalletConnect) {
      throw new Error('WalletConnect not available');
    }
    try {
      await connector.updateSession({
        chainId,
        accounts: connector.accounts,
      });
    } catch (error) {
      logger.error('Chain switch failed:', error);
      throw error;
    }
  };

  const signMessage = async (message: string) => {
    if (!evm?.signer) throw new Error('Wallet not connected');
    return await evm.signer.signMessage(message);
  };

  const sendTransaction = async (transaction: any) => {
    if (!evm?.signer) throw new Error('Wallet not connected');
    return await evm.signer.sendTransaction(transaction);
  };

  return (
    <Ctx.Provider value={{ 
      connector, 
      evm, 
      connect, 
      disconnect, 
      switchChain,
      signMessage,
      sendTransaction,
      isConnected: connector.connected || false,
      address: evm?.address || null,
      chainId: evm?.chainId || null
    }}>
      {children}
    </Ctx.Provider>
  );
}
