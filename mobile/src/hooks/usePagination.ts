/**
 * Pagination Hook
 * 
 * Reusable hook for cursor-based pagination with "Load More" functionality.
 * Works with GraphQL queries that return paginated data.
 */

import { useState, useCallback, useMemo } from 'react';
import { ApolloError } from '@apollo/client';

export interface PaginationInfo {
  hasNextPage: boolean;
  hasPreviousPage: boolean;
  startCursor?: string;
  endCursor?: string;
}

export interface PaginatedData<T> {
  items: T[];
  pageInfo: PaginationInfo;
}

export interface UsePaginationOptions<T> {
  initialItems?: T[];
  pageSize?: number;
  onLoadMore?: (cursor: string) => Promise<PaginatedData<T>>;
}

export interface UsePaginationReturn<T> {
  items: T[];
  loading: boolean;
  loadingMore: boolean;
  hasMore: boolean;
  error: ApolloError | Error | null;
  loadMore: () => Promise<void>;
  refresh: () => Promise<void>;
  reset: () => void;
}

/**
 * Hook for managing paginated data with "Load More" functionality
 */
export function usePagination<T>(
  options: UsePaginationOptions<T>
): UsePaginationReturn<T> {
  const { initialItems = [], pageSize = 20, onLoadMore } = options;

  const [items, setItems] = useState<T[]>(initialItems);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<ApolloError | Error | null>(null);
  const [pageInfo, setPageInfo] = useState<PaginationInfo>({
    hasNextPage: false,
    hasPreviousPage: false,
  });
  const [endCursor, setEndCursor] = useState<string | undefined>();

  const hasMore = useMemo(() => pageInfo.hasNextPage, [pageInfo.hasNextPage]);

  const loadMore = useCallback(async () => {
    if (!onLoadMore || !hasMore || loadingMore) {
      return;
    }

    setLoadingMore(true);
    setError(null);

    try {
      const result = await onLoadMore(endCursor || '');
      
      if (result.items && result.items.length > 0) {
        setItems(prev => [...prev, ...result.items]);
        setPageInfo(result.pageInfo);
        setEndCursor(result.pageInfo.endCursor);
      } else {
        setPageInfo(prev => ({ ...prev, hasNextPage: false }));
      }
    } catch (err) {
      setError(err as Error);
      console.error('Error loading more items:', err);
    } finally {
      setLoadingMore(false);
    }
  }, [onLoadMore, hasMore, loadingMore, endCursor]);

  const refresh = useCallback(async () => {
    if (!onLoadMore) {
      return;
    }

    setLoading(true);
    setError(null);
    setItems([]);
    setEndCursor(undefined);

    try {
      const result = await onLoadMore('');
      
      if (result.items) {
        setItems(result.items);
        setPageInfo(result.pageInfo);
        setEndCursor(result.pageInfo.endCursor);
      }
    } catch (err) {
      setError(err as Error);
      console.error('Error refreshing items:', err);
    } finally {
      setLoading(false);
    }
  }, [onLoadMore]);

  const reset = useCallback(() => {
    setItems(initialItems);
    setPageInfo({
      hasNextPage: false,
      hasPreviousPage: false,
    });
    setEndCursor(undefined);
    setError(null);
  }, [initialItems]);

  return {
    items,
    loading,
    loadingMore,
    hasMore,
    error,
    loadMore,
    refresh,
    reset,
  };
}

