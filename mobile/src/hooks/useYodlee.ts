/**
 * React Native Hook for Yodlee Integration
 * Provides easy access to Yodlee services with state management
 */

import { useState, useCallback } from 'react';
import { Alert } from 'react-native';
import yodleeService, { 
  FastLinkSession, 
  FastLinkResult, 
  BankAccount, 
  BankTransaction 
} from '../services/YodleeService';

export interface UseYodleeReturn {
  // State
  isLoading: boolean;
  isAvailable: boolean;
  accounts: BankAccount[];
  transactions: BankTransaction[];
  error: string | null;
  fastLinkSession: FastLinkSession | null;
  
  // Actions
  checkAvailability: () => Promise<boolean>;
  linkBankAccount: () => Promise<FastLinkSession | null>;
  fetchAccounts: () => Promise<void>;
  refreshAccount: (bankLinkId: number) => Promise<void>;
  getTransactions: (accountId: number) => Promise<void>;
  deleteBankLink: (bankLinkId: number) => Promise<void>;
  clearError: () => void;
  clearSession: () => void;
}

export const useYodlee = (): UseYodleeReturn => {
  const [isLoading, setIsLoading] = useState(false);
  const [isAvailable, setIsAvailable] = useState(false);
  const [accounts, setAccounts] = useState<BankAccount[]>([]);
  const [transactions, setTransactions] = useState<BankTransaction[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [fastLinkSession, setFastLinkSession] = useState<FastLinkSession | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const checkAvailability = useCallback(async (): Promise<boolean> => {
    try {
      setIsLoading(true);
      setError(null);
      
      const available = await yodleeService.checkAvailability();
      setIsAvailable(available);
      
      if (!available) {
        setError('Bank linking is currently unavailable. Please try again later.');
      }
      
      return available;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to check availability';
      setError(errorMessage);
      setIsAvailable(false);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const linkBankAccount = useCallback(async (): Promise<FastLinkSession | null> => {
    try {
      setIsLoading(true);
      setError(null);

      // Check if Yodlee is available
      const available = await checkAvailability();
      if (!available) {
        setError('Yodlee bank linking is currently unavailable');
        return null;
      }

      // Create FastLink session
      const session = await yodleeService.createFastLinkSession();
      setFastLinkSession(session);
      
      // Return session for WebView to use
      return session;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start bank linking';
      setError(errorMessage);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [checkAvailability]);

  const clearSession = useCallback(() => {
    setFastLinkSession(null);
  }, []);

  const fetchAccounts = useCallback(async (): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      const result = await yodleeService.fetchAccounts();
      if (result.success) {
        setAccounts(result.accounts);
      } else {
        setError('Failed to fetch accounts');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch accounts';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const refreshAccount = useCallback(async (bankLinkId: number): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      const result = await yodleeService.refreshAccount(bankLinkId);
      if (result.success) {
        Alert.alert('Success', result.message);
        // Refresh accounts list
        await fetchAccounts();
      } else {
        setError(result.message);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to refresh account';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [fetchAccounts]);

  const getTransactions = useCallback(async (accountId: number): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      const result = await yodleeService.getTransactions(accountId);
      if (result.success) {
        setTransactions(result.transactions);
      } else {
        setError('Failed to fetch transactions');
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch transactions';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const deleteBankLink = useCallback(async (bankLinkId: number): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);

      const result = await yodleeService.deleteBankLink(bankLinkId);
      if (result.success) {
        Alert.alert('Success', result.message);
        // Refresh accounts list
        await fetchAccounts();
      } else {
        setError(result.message);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete bank link';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }, [fetchAccounts]);

  return {
    // State
    isLoading,
    isAvailable,
    accounts,
    transactions,
    error,
    fastLinkSession,
    
    // Actions
    checkAvailability,
    linkBankAccount,
    fetchAccounts,
    refreshAccount,
    getTransactions,
    deleteBankLink,
    clearError,
    clearSession,
  };
};

export default useYodlee;