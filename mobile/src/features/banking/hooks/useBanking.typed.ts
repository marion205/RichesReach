/**
 * TYPED VERSION: Banking hooks with generated GraphQL types
 *
 * This replaces manual interfaces with generated types for full type safety.
 */

import { useQuery, useMutation } from '@apollo/client';
import { gql } from '@apollo/client';
import type {
  ExtendedQueryBankAccountsQuery,
  ExtendedQueryBankTransactionsQuery,
  ExtendedQueryBankTransactionsQueryVariables,
  ExtendedMutationLinkBankAccountMutation,
  ExtendedMutationLinkBankAccountMutationVariables,
  BankAccountType,
  BankTransactionType,
} from '../../../generated/graphql';

// ✅ Using generated types
export type BankAccount = BankAccountType;
export type BankTransaction = BankTransactionType;

const GET_BANK_ACCOUNTS = gql`
  query GetBankAccounts {
    bankAccounts {
      id
      accountType
      accountSubtype
      balanceCurrent
      balanceAvailable
      name
      officialName
      mask
    }
  }
`;

const GET_BANK_TRANSACTIONS = gql`
  query GetBankTransactions($accountId: ID, $startDate: Date, $endDate: Date) {
    bankTransactions(accountId: $accountId, startDate: $startDate, endDate: $endDate) {
      id
      accountId
      amount
      date
      name
      merchantName
      category
      primaryCategory
      detailedCategory
      accountOwner
      pending
      isoCurrencyCode
    }
  }
`;

const GET_BUDGET_DATA = gql`
  query GetBudgetData {
    bankAccounts {
      id
      accountType
      balanceCurrent
      balanceAvailable
    }
    bankTransactions {
      id
      amount
      date
      name
      category
      primaryCategory
    }
  }
`;

const GET_SPENDING_ANALYSIS = gql`
  query GetSpendingAnalysis($startDate: Date, $endDate: Date) {
    bankTransactions(startDate: $startDate, endDate: $endDate) {
      id
      amount
      date
      name
      category
      primaryCategory
      detailedCategory
      merchantName
    }
  }
`;

/**
 * Hook to fetch user's bank accounts
 *
 * @returns Typed bank accounts with loading/error states
 */
export const useBankAccounts = () => {
  const { data, loading, error, refetch } = useQuery<ExtendedQueryBankAccountsQuery>(
    GET_BANK_ACCOUNTS,
    {
      fetchPolicy: 'cache-and-network',
      errorPolicy: 'all',
    }
  );

  return {
    // ✅ Fully typed bank accounts
    accounts: (data?.bankAccounts || []) as BankAccountType[],
    loading,
    error,
    refetch,
  };
};

/**
 * Hook to fetch bank transactions
 *
 * @param accountId - Optional account ID to filter by
 * @param startDate - Optional start date
 * @param endDate - Optional end date
 * @returns Typed transactions with loading/error states
 */
export const useBankTransactions = (accountId?: string, startDate?: string, endDate?: string) => {
  const { data, loading, error, refetch } = useQuery<
    ExtendedQueryBankTransactionsQuery,
    ExtendedQueryBankTransactionsQueryVariables
  >(GET_BANK_TRANSACTIONS, {
    variables: { accountId, startDate, endDate },
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  return {
    // ✅ Fully typed transactions
    transactions: (data?.bankTransactions || []) as BankTransactionType[],
    loading,
    error,
    refetch,
  };
};

/**
 * Hook to fetch budget data (accounts + transactions)
 *
 * @returns Typed budget data
 */
export const useBudgetData = () => {
  const { data, loading, error, refetch } = useQuery(GET_BUDGET_DATA, {
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  return {
    accounts: (data?.bankAccounts || []) as BankAccountType[],
    transactions: (data?.bankTransactions || []) as BankTransactionType[],
    loading,
    error,
    refetch,
  };
};

/**
 * Hook to fetch spending analysis
 *
 * @param startDate - Start date for analysis
 * @param endDate - End date for analysis
 * @returns Typed spending analysis
 */
export const useSpendingAnalysis = (startDate?: string, endDate?: string) => {
  const { data, loading, error, refetch } = useQuery(GET_SPENDING_ANALYSIS, {
    variables: { startDate, endDate },
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  return {
    transactions: (data?.bankTransactions || []) as BankTransactionType[],
    loading,
    error,
    refetch,
  };
};

/**
 * Typed helper: Calculate total account balance
 */
export function calculateTotalBalance(accounts: BankAccountType[]): number {
  // ✅ TypeScript knows balanceCurrent exists and is nullable
  return accounts.reduce((sum, account) => sum + (account.balanceCurrent ?? 0), 0);
}

/**
 * Typed helper: Calculate total spending by category
 */
export function calculateSpendingByCategory(
  transactions: BankTransactionType[]
): Record<string, number> {
  const spending: Record<string, number> = {};

  // ✅ TypeScript knows all transaction fields
  transactions.forEach(transaction => {
    if (transaction.amount && transaction.amount < 0) {
      const category = transaction.primaryCategory || transaction.category || 'Other';
      spending[category] = (spending[category] || 0) + Math.abs(transaction.amount);
    }
  });

  return spending;
}

/**
 * Typed helper: Get transactions for a specific category
 */
export function getTransactionsByCategory(
  transactions: BankTransactionType[],
  category: string
): BankTransactionType[] {
  // ✅ TypeScript knows category fields
  return transactions.filter(
    transaction =>
      transaction.primaryCategory === category ||
      transaction.category === category ||
      transaction.detailedCategory === category
  );
}

/**
 * Typed helper: Calculate monthly spending
 */
export function calculateMonthlySpending(
  transactions: BankTransactionType[],
  month: number,
  year: number
): number {
  // ✅ TypeScript knows date and amount fields
  return transactions
    .filter(transaction => {
      if (!transaction.date) {
        return false;
      }
      const transactionDate = new Date(transaction.date);
      return (
        transactionDate.getMonth() === month &&
        transactionDate.getFullYear() === year &&
        (transaction.amount ?? 0) < 0
      );
    })
    .reduce((sum, transaction) => sum + Math.abs(transaction.amount ?? 0), 0);
}
