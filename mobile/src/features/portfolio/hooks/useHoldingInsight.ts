/**
 * useHoldingInsight - Fetch AI insights for a holding
 * Phase 3: AI insights with caching
 * 
 * Falls back gracefully if react-query is not available
 */

import React from 'react';
import { API_BASE } from '../../../config/api';

// Graceful fallback if @tanstack/react-query is not available
let useQuery: any = null;
try {
  const rq = require('@tanstack/react-query');
  useQuery = rq.useQuery;
} catch (e) {
  // React Query not available - will use fallback
}

export interface HoldingInsight {
  headline: string;
  drivers: string[];
}

/**
 * Fetch AI insight for a specific holding
 */
async function fetchHoldingInsight(ticker: string): Promise<HoldingInsight> {
  const response = await fetch(`${API_BASE}/api/coach/holding-insight?ticker=${ticker}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch insight for ${ticker}`);
  }

  return response.json();
}

/**
 * Hook to get AI insight for a holding
 * Caches for 5-15 minutes, falls back gracefully
 */
export function useHoldingInsight(ticker: string, enabled: boolean = true) {
  // Fallback if react-query not available
  if (!useQuery) {
    const [data, setData] = React.useState<HoldingInsight | null>(null);
    const [isLoading, setIsLoading] = React.useState(false);
    const [error, setError] = React.useState<Error | null>(null);

    React.useEffect(() => {
      if (!enabled || !ticker) return;
      
      let cancelled = false;
      setIsLoading(true);
      setError(null);
      
      fetchHoldingInsight(ticker)
        .then(result => {
          if (!cancelled) {
            setData(result);
            setIsLoading(false);
          }
        })
        .catch(err => {
          if (!cancelled) {
            setError(err);
            setIsLoading(false);
          }
        });

      return () => {
        cancelled = true;
      };
    }, [ticker, enabled]);

    return { data, isLoading, error };
  }

  // Use react-query if available
  return useQuery<HoldingInsight, Error>({
    queryKey: ['holding-insight', ticker],
    queryFn: () => fetchHoldingInsight(ticker),
    enabled: enabled && !!ticker,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 15 * 60 * 1000, // 15 minutes (formerly cacheTime)
    retry: 1,
    retryDelay: 1000,
  });
}

