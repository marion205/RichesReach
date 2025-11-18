import { useState, useEffect, useMemo } from 'react';
import { useQuery } from '@apollo/client';
import { GET_ALPACA_ORDERS } from '../../../graphql/tradingQueries';
import { tradingOfflineCache } from '../services/TradingOfflineCache';
import { AlpacaOrder } from '../types';

export const useAlpacaOrders = (accountId: number | null, status?: string) => {
  const [cachedOrders, setCachedOrders] = useState<AlpacaOrder[]>([]);
  const [isOffline, setIsOffline] = useState(false);

  // Load cached data on mount
  useEffect(() => {
    const loadCache = async () => {
      const cached = await tradingOfflineCache.getOrders();
      if (cached) {
        setCachedOrders(cached);
      }
      const connected = await tradingOfflineCache.isConnected();
      setIsOffline(!connected);
    };
    loadCache();
  }, []);

  const { data, loading, error, refetch } = useQuery(GET_ALPACA_ORDERS, {
    variables: { accountId: accountId || 0, status },
    errorPolicy: 'all',
    skip: !accountId,
    fetchPolicy: 'cache-first', // Use cache first for faster loads
    nextFetchPolicy: 'cache-first', // Keep using cache for subsequent loads
    onCompleted: async (data) => {
      // Cache successful response
      if (data?.alpacaOrders) {
        await tradingOfflineCache.cacheOrders(data.alpacaOrders);
        setCachedOrders(data.alpacaOrders);
      }
    },
  });

  // Use cached data if offline or if query failed
  const orders = useMemo<AlpacaOrder[]>(() => {
    return (data?.alpacaOrders as AlpacaOrder[]) || cachedOrders;
  }, [data, cachedOrders]);
  
  const isUsingCache = !data?.alpacaOrders && cachedOrders.length > 0;

  return {
    orders,
    loading: loading && cachedOrders.length === 0, // Don't show loading if we have cache
    error: isOffline ? null : error, // Suppress errors when offline
    refetch,
    isOffline,
    isUsingCache,
  };
};

