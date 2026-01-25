/**
 * Resilient Query Hook
 * Provides automatic retry, error handling, and fallback data for GraphQL queries
 */

import { useQuery, QueryHookOptions, DocumentNode } from '@apollo/client';
import { useState, useEffect } from 'react';
import logger from '../utils/logger';

interface UseResilientQueryOptions<TData, TVariables> 
  extends Omit<QueryHookOptions<TData, TVariables>, 'onError' | 'onCompleted'> {
  fallbackData?: TData;
  maxConsecutiveErrors?: number;
  onMaxErrorsReached?: () => void;
  onError?: (error: any) => void;
  onCompleted?: (data: TData) => void;
}

export function useResilientQuery<TData, TVariables>(
  query: DocumentNode,
  options: UseResilientQueryOptions<TData, TVariables> = {}
) {
  const {
    fallbackData,
    maxConsecutiveErrors = 3,
    onMaxErrorsReached,
    onError: userOnError,
    onCompleted: userOnCompleted,
    errorPolicy = 'all', // Return partial data even with errors
    fetchPolicy = 'cache-and-network', // Use cache when available
    ...queryOptions
  } = options;

  const [consecutiveErrors, setConsecutiveErrors] = useState(0);
  const [useFallback, setUseFallback] = useState(false);
  const [lastError, setLastError] = useState<any>(null);

  const result = useQuery<TData, TVariables>(query, {
    ...queryOptions,
    errorPolicy,
    fetchPolicy,
    // Add retry context for retry link
    context: {
      ...queryOptions.context,
      maxRetries: 2, // Let retry link handle initial retries
    },
    onError: (error) => {
      const networkError = error?.networkError as any;
      const statusCode = networkError?.statusCode;
      
      setLastError(error);
      
      // Only count server errors (500+) toward consecutive error limit
      if (statusCode >= 500) {
        setConsecutiveErrors(prev => {
          const newCount = prev + 1;
          
          if (newCount >= maxConsecutiveErrors) {
            logger.warn(`⚠️ Max consecutive errors (${maxConsecutiveErrors}) reached for query`, {
              query: query.definitions[0]?.name?.value || 'unknown',
              count: newCount,
              statusCode,
            });
            setUseFallback(true);
            onMaxErrorsReached?.();
          }
          
          return newCount;
        });
      } else {
        // Reset counter on non-server errors
        if (consecutiveErrors > 0) {
          setConsecutiveErrors(0);
        }
      }
      
      // Call user's error handler
      userOnError?.(error);
    },
    onCompleted: (data) => {
      // Reset error count on success
      if (consecutiveErrors > 0) {
        logger.log('✅ Query succeeded, resetting error counter', {
          query: query.definitions[0]?.name?.value || 'unknown',
          previousErrors: consecutiveErrors,
        });
        setConsecutiveErrors(0);
        setLastError(null);
        setUseFallback(false);
      }
      
      // Call user's completed handler
      userOnCompleted?.(data);
    },
  });

  // Use fallback data if we've hit max errors and fallback is provided
  const finalData = useFallback && fallbackData ? fallbackData : result.data;

  return {
    ...result,
    data: finalData,
    consecutiveErrors,
    useFallback,
    lastError,
    // Helper to manually reset error state
    resetErrorState: () => {
      setConsecutiveErrors(0);
      setLastError(null);
      setUseFallback(false);
    },
  };
}

