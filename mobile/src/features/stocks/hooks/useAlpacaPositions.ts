import { useState, useEffect, useMemo } from 'react';
import { useQuery } from '@apollo/client';
import { GET_ALPACA_POSITIONS } from '../../../graphql/tradingQueries';
import { tradingOfflineCache } from '../services/TradingOfflineCache';
import { AlpacaPosition } from '../types';

export const useAlpacaPositions = (accountId: number | null) => {
  const [cachedPositions, setCachedPositions] = useState<AlpacaPosition[]>([]);
  const [isOffline, setIsOffline] = useState(false);

  // Load cached data on mount
  useEffect(() => {
    const loadCache = async () => {
      const cached = await tradingOfflineCache.getPositions();
      if (cached) {
        setCachedPositions(cached);
      }
      const connected = await tradingOfflineCache.isConnected();
      setIsOffline(!connected);
    };
    loadCache();
  }, []);

  const { data, loading, error, refetch } = useQuery(GET_ALPACA_POSITIONS, {
    variables: { accountId: accountId || 0 },
    errorPolicy: 'all',
    skip: !accountId,
    fetchPolicy: 'cache-and-network',
    onCompleted: async (data) => {
      // Cache successful response
      if (data?.alpacaPositions) {
        await tradingOfflineCache.cachePositions(data.alpacaPositions);
        setCachedPositions(data.alpacaPositions);
      }
    },
  });

  // Use cached data if offline or if query failed
  const positions = useMemo<AlpacaPosition[]>(() => {
    return (data?.alpacaPositions as AlpacaPosition[]) || cachedPositions;
  }, [data, cachedPositions]);
  
  const isUsingCache = !data?.alpacaPositions && cachedPositions.length > 0;

  return {
    positions,
    loading: loading && cachedPositions.length === 0, // Don't show loading if we have cache
    error: isOffline ? null : error, // Suppress errors when offline
    refetch,
    isOffline,
    isUsingCache,
  };
};

