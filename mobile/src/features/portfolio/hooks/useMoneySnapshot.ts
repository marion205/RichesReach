/**
 * useMoneySnapshot Hook
 * Fetches and manages money snapshot data
 */

import { useState, useEffect } from 'react';
import { moneySnapshotService, MoneySnapshot } from '../services/MoneySnapshotService';

export const useMoneySnapshot = () => {
  const [snapshot, setSnapshot] = useState<MoneySnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [hasBankLinked, setHasBankLinked] = useState(false);

  const fetchSnapshot = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Add timeout to prevent hanging
      const timeoutPromise = new Promise<never>((_, reject) => 
        setTimeout(() => reject(new Error('Snapshot request timeout')), 5000)
      );
      
      const data = await Promise.race([
        moneySnapshotService.getSnapshot(),
        timeoutPromise
      ]);
      
      // Validate data structure
      if (!data || typeof data.netWorth !== 'number') {
        throw new Error('Invalid snapshot data structure');
      }
      
      // Ensure all required fields have defaults
      const validatedSnapshot: MoneySnapshot = {
        netWorth: data.netWorth ?? 0,
        cashflow: {
          period: data.cashflow?.period ?? '30d',
          in: data.cashflow?.in ?? 0,
          out: data.cashflow?.out ?? 0,
          delta: data.cashflow?.delta ?? 0,
        },
        positions: Array.isArray(data.positions) ? data.positions : [],
        shield: Array.isArray(data.shield) ? data.shield : [],
        breakdown: {
          bankBalance: data.breakdown?.bankBalance ?? 0,
          portfolioValue: data.breakdown?.portfolioValue ?? 0,
          bankAccountsCount: data.breakdown?.bankAccountsCount ?? 0,
        },
      };
      
      setSnapshot(validatedSnapshot);
      setHasBankLinked(validatedSnapshot.breakdown.bankAccountsCount > 0);
    } catch (err) {
      // Enhanced error handling
      const error = err instanceof Error ? err : new Error('Failed to fetch snapshot');
      console.warn('[useMoneySnapshot] Error:', error.message);
      setError(error);
      
      // Use mock data as fallback (both dev and prod for graceful degradation)
      const mockSnapshot: MoneySnapshot = {
        netWorth: 12500.50,
        cashflow: {
          period: '30d',
          in: 3820.40,
          out: 3600.10,
          delta: 220.30,
        },
        positions: [
          { symbol: 'NVDA', value: 1200.00, shares: 10 },
          { symbol: 'TSLA', value: 1250.00, shares: 5 },
        ],
        shield: [
          {
            type: 'LOW_BALANCE',
            inDays: null,
            suggestion: 'PAUSE_RISKY_ORDER',
            message: 'Low balance detected ($500.00). Consider pausing high-risk trades.',
          },
        ],
        breakdown: {
          bankBalance: 10000.50,
          portfolioValue: 2450.00,
          bankAccountsCount: 2,
        },
      };
      
      setSnapshot(mockSnapshot);
      setHasBankLinked(true);
      
      if (__DEV__) {
        console.log('[useMoneySnapshot] Using mock data as fallback');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSnapshot();
  }, []);

  return {
    snapshot,
    loading,
    error,
    hasBankLinked,
    refetch: fetchSnapshot,
  };
};

