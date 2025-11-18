import { useState, useEffect } from 'react';
import { useQuery } from '@apollo/client';
import { GET_ALPACA_ACCOUNT } from '../../../graphql/tradingQueries';
import { tradingOfflineCache } from '../services/TradingOfflineCache';
import { AlpacaAccount } from '../types';

export const useAlpacaAccount = (userId: number = 1) => {
  const [cachedAccount, setCachedAccount] = useState<AlpacaAccount | null>(null);
  const [isOffline, setIsOffline] = useState(false);

  // Load cached data on mount
  useEffect(() => {
    const loadCache = async () => {
      const cached = await tradingOfflineCache.getAccount();
      if (cached) {
        setCachedAccount(cached);
      }
      const connected = await tradingOfflineCache.isConnected();
      setIsOffline(!connected);
    };
    loadCache();
  }, []);

  const { data, loading, error, refetch } = useQuery(GET_ALPACA_ACCOUNT, {
    variables: { userId },
    errorPolicy: 'all',
    skip: false,
    fetchPolicy: 'cache-and-network', // Use cache first, then network
    onCompleted: async (data) => {
      // Cache successful response
      if (data?.alpacaAccount) {
        await tradingOfflineCache.cacheAccount(data.alpacaAccount);
        setCachedAccount(data.alpacaAccount);
      }
    },
  });

  // Use cached data if offline or if query failed
  const account = data?.alpacaAccount || cachedAccount;
  const isUsingCache = !data?.alpacaAccount && !!cachedAccount;

  return {
    alpacaAccount: account,
    loading: loading && !cachedAccount, // Don't show loading if we have cache
    error: isOffline ? null : error, // Suppress errors when offline
    refetch,
    isOffline,
    isUsingCache,
  };
};

