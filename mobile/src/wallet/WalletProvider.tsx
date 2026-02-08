/**
 * WalletProvider — React Context for wallet state.
 * Uses WalletConnect v2 Sign Client with AsyncStorage session persistence.
 * On mount, attempts to restore a previously saved session so users
 * don't have to reconnect every time they reopen the app.
 */
import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { ethers } from 'ethers';
import logger from '../utils/logger';
import {
  connectWallet,
  restoreSession,
  disconnectWallet,
  sendTx,
  initWC,
} from '../blockchain/wallet/walletConnect';
import { getReadProvider } from '../blockchain/web3Service';

// ---------- Types ----------

interface EVMState {
  provider: ethers.providers.JsonRpcProvider;
  address: string;
  chainId: number;
}

interface WalletContextValue {
  /** Raw WalletConnect client + session (null if not connected) */
  wcClient: any;
  wcSession: any;
  /** EVM state: provider, address, chainId */
  evm: EVMState | null;
  /** Connect to a wallet. chainIdWC format: "eip155:11155111" */
  connect: (chainIdWC?: string) => Promise<void>;
  /** Disconnect and clear persisted session */
  disconnect: () => Promise<void>;
  /** Switch EVM chain */
  switchChain: (chainId: number) => void;
  /** Sign a message */
  signMessage: (message: string) => Promise<string>;
  /** Send a raw transaction */
  sendTransaction: (tx: any) => Promise<string>;
  /** Convenience booleans */
  isConnected: boolean;
  address: string | null;
  chainId: number | null;
  /** True while restoring a previous session on app mount */
  isRestoring: boolean;
}

const Ctx = createContext<WalletContextValue | null>(null);

export const useWallet = () => {
  const ctx = useContext(Ctx);
  if (!ctx) {
    // Return a safe fallback for components that render outside the provider
    return {
      wcClient: null,
      wcSession: null,
      evm: null,
      connect: async () => { throw new Error('WalletProvider not mounted'); },
      disconnect: async () => {},
      switchChain: () => {},
      signMessage: async () => { throw new Error('Wallet not connected'); },
      sendTransaction: async () => { throw new Error('Wallet not connected'); },
      isConnected: false,
      address: null,
      chainId: null,
      isRestoring: false,
    } as WalletContextValue;
  }
  return ctx;
};

// ---------- Chain ID helpers ----------

const DEFAULT_CHAIN_WC = 'eip155:11155111'; // Sepolia

function parseChainId(wcAccount: string): number {
  // eip155:11155111:0xabc... => 11155111
  const parts = wcAccount.split(':');
  return parts.length >= 2 ? parseInt(parts[1], 10) : 11155111;
}

// ---------- Provider ----------

export function WalletProvider({ children }: { children: React.ReactNode }) {
  const [wcClient, setWcClient] = useState<any>(null);
  const [wcSession, setWcSession] = useState<any>(null);
  const [address, setAddress] = useState<string | null>(null);
  const [chainId, setChainId] = useState<number | null>(null);
  const [isRestoring, setIsRestoring] = useState(true);
  const mountedRef = useRef(true);

  // ---- Restore session on mount ----
  useEffect(() => {
    mountedRef.current = true;
    let cancelled = false;

    (async () => {
      try {
        const restored = await restoreSession();
        if (cancelled || !mountedRef.current) return;

        if (restored) {
          setWcClient(restored.client);
          setWcSession(restored.session);
          setAddress(restored.address);
          // Parse chain from first account
          const account = restored.session?.namespaces?.eip155?.accounts?.[0] || '';
          setChainId(parseChainId(account));
          logger.log('Wallet session restored:', restored.address?.slice(0, 8) + '...');
        }
      } catch (e) {
        logger.warn('Wallet session restore failed:', e);
      } finally {
        if (!cancelled && mountedRef.current) {
          setIsRestoring(false);
        }
      }
    })();

    return () => {
      cancelled = true;
      mountedRef.current = false;
    };
  }, []);

  // ---- EVM state (read-only provider) ----
  const evm: EVMState | null = address
    ? {
        provider: getReadProvider(),
        address,
        chainId: chainId || 11155111,
      }
    : null;

  // ---- Connect ----
  const connect = useCallback(async (chainIdWC: string = DEFAULT_CHAIN_WC) => {
    try {
      const result = await connectWallet(chainIdWC);
      setWcClient(result.client);
      setWcSession(result.session);
      setAddress(result.address);
      const account = result.session?.namespaces?.eip155?.accounts?.[0] || '';
      setChainId(parseChainId(account));
      logger.log('Wallet connected:', result.address?.slice(0, 8) + '...');
    } catch (error) {
      logger.error('Wallet connection failed:', error);
      throw error;
    }
  }, []);

  // ---- Disconnect ----
  const disconnect = useCallback(async () => {
    try {
      await disconnectWallet();
    } catch (error) {
      logger.warn('Wallet disconnect error:', error);
    }
    setWcClient(null);
    setWcSession(null);
    setAddress(null);
    setChainId(null);
    logger.log('Wallet disconnected');
  }, []);

  // ---- Switch chain (updates local state) ----
  const switchChain = useCallback((newChainId: number) => {
    setChainId(newChainId);
  }, []);

  // ---- Sign message ----
  const signMessage = useCallback(async (message: string): Promise<string> => {
    if (!wcClient || !wcSession || !address) {
      throw new Error('Wallet not connected');
    }
    const chainWC = `eip155:${chainId || 11155111}`;
    const signature = await wcClient.request({
      topic: wcSession.topic,
      chainId: chainWC,
      request: {
        method: 'personal_sign',
        params: [ethers.utils.hexlify(ethers.utils.toUtf8Bytes(message)), address],
      },
    });
    return signature as string;
  }, [wcClient, wcSession, address, chainId]);

  // ---- Send transaction ----
  const sendTransaction = useCallback(async (tx: any): Promise<string> => {
    if (!wcClient || !wcSession) {
      throw new Error('Wallet not connected');
    }
    const chainWC = `eip155:${chainId || 11155111}`;
    const hash = await sendTx({
      client: wcClient,
      session: wcSession,
      chainIdWC: chainWC,
      tx: { ...tx, from: address },
    });
    return hash;
  }, [wcClient, wcSession, address, chainId]);

  // ---- Context value ----
  const value: WalletContextValue = {
    wcClient,
    wcSession,
    evm,
    connect,
    disconnect,
    switchChain,
    signMessage,
    sendTransaction,
    isConnected: !!address && !!wcSession,
    address,
    chainId,
    isRestoring,
  };

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
