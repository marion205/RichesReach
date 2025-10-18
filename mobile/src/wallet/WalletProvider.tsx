import React, { createContext, useContext, useMemo } from 'react';
import WalletConnectProvider, { useWalletConnect } from '@walletconnect/react-native-dapp';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { ethers } from 'ethers';

const Ctx = createContext<any>(null);
export const useWallet = () => useContext(Ctx);

export function WalletProvider({ children }: {children: React.ReactNode}) {
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
  const connector = useWalletConnect();
  
  const evm = useMemo(() => {
    if (!connector.connected) return null;
    const provider = new ethers.providers.Web3Provider(connector as any);
    return { 
      provider, 
      signer: provider.getSigner(),
      address: connector.accounts[0],
      chainId: connector.chainId
    };
  }, [connector.connected, connector.accounts, connector.chainId]);

  const connect = async () => {
    try {
      await connector.connect();
    } catch (error) {
      console.error('Wallet connection failed:', error);
      throw error;
    }
  };

  const disconnect = async () => {
    try {
      await connector.killSession();
    } catch (error) {
      console.error('Wallet disconnection failed:', error);
    }
  };

  const switchChain = async (chainId: number) => {
    try {
      await connector.updateSession({
        chainId,
        accounts: connector.accounts,
      });
    } catch (error) {
      console.error('Chain switch failed:', error);
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
      isConnected: connector.connected,
      address: evm?.address,
      chainId: evm?.chainId
    }}>
      {children}
    </Ctx.Provider>
  );
}
