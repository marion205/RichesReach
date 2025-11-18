import { useQuery } from '@apollo/client';
import { useMemo } from 'react';
import { GET_ALPACA_POSITIONS } from '../../../graphql/tradingQueries';

export const useAlpacaPositions = (accountId: number | null) => {
  const { data, loading, error, refetch } = useQuery(GET_ALPACA_POSITIONS, {
    variables: { accountId: accountId || 0 },
    errorPolicy: 'all',
    skip: !accountId,
  });

  const positions = useMemo(() => data?.alpacaPositions ?? [], [data]);

  return {
    positions,
    loading,
    error,
    refetch,
  };
};

