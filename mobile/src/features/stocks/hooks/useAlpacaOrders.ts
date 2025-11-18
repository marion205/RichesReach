import { useQuery } from '@apollo/client';
import { useMemo } from 'react';
import { GET_ALPACA_ORDERS } from '../../../graphql/tradingQueries';

export const useAlpacaOrders = (accountId: number | null, status?: string) => {
  const { data, loading, error, refetch } = useQuery(GET_ALPACA_ORDERS, {
    variables: { accountId: accountId || 0, status },
    errorPolicy: 'all',
    skip: !accountId,
  });

  const orders = useMemo(() => data?.alpacaOrders ?? [], [data]);

  return {
    orders,
    loading,
    error,
    refetch,
  };
};

