import { useSyncExternalStore } from 'react';
import { useQuery } from '@apollo/client';
import { gql } from '@apollo/client';
import { useEffect } from 'react';

type Point = { date: string; value: number };

// Fallback mock data (used only if GraphQL fails)
const FALLBACK_HISTORY: Point[] = [
  { date: '2023-09-08', value: 10000 },
  { date: '2023-10-08', value: 10200 },
  { date: '2023-11-08', value: 10500 },
  { date: '2023-12-08', value: 10800 },
  { date: '2024-01-08', value: 11000 },
  { date: '2024-02-08', value: 11200 },
  { date: '2024-03-08', value: 11500 },
  { date: '2024-04-08', value: 11800 },
  { date: '2024-05-08', value: 12000 },
  { date: '2024-06-08', value: 12200 },
  { date: '2024-07-08', value: 12500 },
  { date: '2024-08-08', value: 12800 },
  { date: '2024-08-15', value: 12900 },
  { date: '2024-08-22', value: 13000 },
  { date: '2024-08-29', value: 13050 },
  { date: '2024-09-01', value: 13100 },
  { date: '2024-09-08', value: 13100 },
];

let history: Point[] = FALLBACK_HISTORY;

const listeners = new Set<() => void>();
const emit = () => listeners.forEach(l => l());

export function setPortfolioHistory(next: Point[]) {
  history = next.slice().sort((a, b) => +new Date(a.date) - +new Date(b.date));
  emit();
}

export function appendHistoryPoint(p: Point) {
  setPortfolioHistory([...history, p]);
}

// GraphQL query for portfolio history
const GET_PORTFOLIO_HISTORY = gql`
  query GetPortfolioHistory($days: Int, $timeframe: String) {
    portfolioHistory(days: $days, timeframe: $timeframe) {
      date
      value
      change
      changePercent
    }
  }
`;

/**
 * Hook to fetch and use portfolio history from GraphQL
 * Automatically updates the shared store when data is fetched
 */
export function usePortfolioHistoryFromGraphQL(days: number = 365, timeframe?: string) {
  const { data, loading, error, refetch } = useQuery(GET_PORTFOLIO_HISTORY, {
    variables: { days, timeframe },
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
    pollInterval: 300000, // Poll every 5 minutes for updates
  });

  useEffect(() => {
    if (data?.portfolioHistory && Array.isArray(data.portfolioHistory)) {
      const historyPoints: Point[] = data.portfolioHistory.map((item: any) => ({
        date: item.date,
        value: item.value || 0,
      }));
      
      if (historyPoints.length > 0) {
        setPortfolioHistory(historyPoints);
      }
    }
  }, [data]);

  return {
    history: data?.portfolioHistory || [],
    loading,
    error,
    refetch,
  };
}

/**
 * Legacy hook - now fetches from GraphQL but falls back to mock data
 * This maintains backward compatibility with existing components
 */
export function usePortfolioHistory() {
  // Try to fetch from GraphQL (but don't block if it fails)
  const { data } = useQuery(GET_PORTFOLIO_HISTORY, {
    variables: { days: 365 },
    fetchPolicy: 'cache-first',
    errorPolicy: 'all',
    skip: false, // Always try to fetch
  });

  useEffect(() => {
    if (data?.portfolioHistory && Array.isArray(data.portfolioHistory)) {
      const historyPoints: Point[] = data.portfolioHistory.map((item: any) => ({
        date: item.date,
        value: item.value || 0,
      }));
      
      if (historyPoints.length > 0) {
        setPortfolioHistory(historyPoints);
      }
    }
  }, [data]);

  return useSyncExternalStore(
    (l) => { listeners.add(l); return () => listeners.delete(l); },
    () => history,
    () => history
  );
}
