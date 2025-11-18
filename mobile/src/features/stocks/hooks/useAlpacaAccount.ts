import { useQuery } from '@apollo/client';
import { GET_ALPACA_ACCOUNT } from '../../../graphql/tradingQueries';

export const useAlpacaAccount = (userId: number = 1) => {
  const { data, loading, error, refetch } = useQuery(GET_ALPACA_ACCOUNT, {
    variables: { userId },
    errorPolicy: 'all',
    skip: false,
  });

  return {
    alpacaAccount: data?.alpacaAccount || null,
    loading,
    error,
    refetch,
  };
};

