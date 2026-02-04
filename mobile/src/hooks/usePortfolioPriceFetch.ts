/**
 * usePortfolioPriceFetch: fetches real-time prices for portfolio holdings with
 * debounce, cleanup, and loading/error state. Prevents leaks and duplicate fetches.
 */
import { useState, useCallback, useRef, useEffect } from 'react';
import logger from '../utils/logger';

export interface HoldingForPrice {
  symbol?: string;
  stock?: { symbol?: string };
  [key: string]: unknown;
}

export interface UsePortfolioPriceFetchOptions {
  /** Debounce delay in ms before starting fetch (default 100) */
  debounceMs?: number;
  /** Only run when this string changes (e.g. JSON.stringify(stablePortfolioData)) */
  portfolioDataKey?: string;
}

export interface UsePortfolioPriceFetchResult {
  loadingPrices: boolean;
  realTimePrices: { [symbol: string]: number };
  error: Error | null;
  fetchPrices: (holdings: HoldingForPrice[]) => Promise<void>;
}

export function usePortfolioPriceFetch(
  holdings: HoldingForPrice[],
  options: UsePortfolioPriceFetchOptions = {}
): UsePortfolioPriceFetchResult {
  const { debounceMs = 100, portfolioDataKey } = options;
  const [loadingPrices, setLoadingPrices] = useState(false);
  const [realTimePrices, setRealTimePrices] = useState<{ [symbol: string]: number }>({});
  const [error, setError] = useState<Error | null>(null);

  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const fetchingRef = useRef(false);
  const mountedRef = useRef(true);
  const lastKeyRef = useRef<string>('');

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
  }, []);

  const fetchPrices = useCallback(async (holdingsToFetch: HoldingForPrice[]) => {
    if (holdingsToFetch.length === 0) {
      if (mountedRef.current) {
        setLoadingPrices(false);
        setError(null);
      }
      fetchingRef.current = false;
      return;
    }
    if (fetchingRef.current) return;
    fetchingRef.current = true;
    if (mountedRef.current) {
      setLoadingPrices(true);
      setError(null);
    }
    try {
      const symbols = holdingsToFetch
        .map((h) => h.stock?.symbol || h.symbol)
        .filter(Boolean) as string[];
      if (symbols.length === 0) {
        if (mountedRef.current) setLoadingPrices(false);
        fetchingRef.current = false;
        return;
      }
      const { SecureMarketDataService } = await import(
        '../features/stocks/services/SecureMarketDataService'
      );
      const service = SecureMarketDataService.getInstance();
      const quotes = await service.fetchQuotes(symbols);
      const prices: { [symbol: string]: number } = {};
      quotes.forEach((quote) => {
        if (quote.price > 0) prices[quote.symbol] = quote.price;
      });
      if (mountedRef.current) {
        setRealTimePrices(prices);
        setLoadingPrices(false);
        setError(null);
      }
    } catch (err) {
      const e = err instanceof Error ? err : new Error(String(err));
      logger.error('[usePortfolioPriceFetch] Error fetching prices:', e);
      if (mountedRef.current) {
        setError(e);
        setLoadingPrices(false);
        const mockPrices: { [symbol: string]: number } = {};
        holdingsToFetch.forEach((h) => {
          const symbol = h.stock?.symbol || h.symbol;
          const price = (h as any).currentPrice ?? (h.stock as any)?.currentPrice;
          if (symbol && typeof price === 'number' && price > 0) mockPrices[symbol] = price;
        });
        setRealTimePrices(mockPrices);
      }
    } finally {
      fetchingRef.current = false;
    }
  }, []);

  useEffect(() => {
    const key = portfolioDataKey ?? JSON.stringify(
      holdings.map((h) => ({ symbol: h.stock?.symbol || h.symbol }))
    );
    if (key === '' || key === lastKeyRef.current) return;
    lastKeyRef.current = key;
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    timeoutRef.current = setTimeout(() => {
      timeoutRef.current = null;
      const allHoldings = holdings.length > 0 ? holdings : [];
      if (allHoldings.length > 0) fetchPrices(allHoldings);
      else if (mountedRef.current) setLoadingPrices(false);
    }, debounceMs);
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };
  }, [holdings, portfolioDataKey, debounceMs, fetchPrices]);

  return { loadingPrices, realTimePrices, error, fetchPrices };
}
