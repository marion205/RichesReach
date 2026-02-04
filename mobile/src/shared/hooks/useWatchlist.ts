import { gql, useMutation, useQuery } from '@apollo/client';
import { Alert } from 'react-native';
import logger from '../../utils/logger';

export const GET_MY_WATCHLIST = gql`
  query GetMyWatchlist {
    myWatchlist {
      id
      stock {
        symbol
        companyName
        currentPrice
      }
      addedAt
      notes
      targetPrice
    }
  }
`;

const ADD_TO_WATCHLIST = gql`
  mutation AddToWatchlist($symbol: String!, $company_name: String, $notes: String) {
    addToWatchlist(symbol: $symbol, company_name: $company_name, notes: $notes) {
      success
      message
    }
  }
`;

const REMOVE_FROM_WATCHLIST = gql`
  mutation RemoveFromWatchlist($symbol: String!) {
    removeFromWatchlist(symbol: $symbol) {
      success
      message
    }
  }
`;

export function useWatchlist(skip = false) {
  const list = useQuery(GET_MY_WATCHLIST, { 
    fetchPolicy: 'cache-and-network',
    skip: skip
  });

  const [add] = useMutation(ADD_TO_WATCHLIST, {
    onCompleted: (res) => {
      if (res?.addToWatchlist?.success) {
        // Don't show alert here - let the calling component handle it
      }
    },
    update: (cache, { data }, { variables }) => {
      if (data?.addToWatchlist?.success && variables) {
        // Try optimistic update first
        try {
          const existing = cache.readQuery({ query: GET_MY_WATCHLIST });
          const newItem = {
            __typename: 'WatchlistItem',
            id: `temp-${variables.symbol}-${Date.now()}`,
            stock: {
              __typename: 'Stock',
              symbol: variables.symbol,
              companyName: variables.company_name || variables.symbol,
              currentPrice: null,
            },
            addedAt: new Date().toISOString(),
            notes: variables.notes || '',
            targetPrice: null,
          };
          
          cache.writeQuery({
            query: GET_MY_WATCHLIST,
            data: {
              myWatchlist: [
                ...((existing as any)?.myWatchlist || []),
                newItem,
              ],
            },
          });
        } catch (e) {
          // If optimistic update fails, evict and refetch
          cache.evict({ fieldName: 'myWatchlist' });
          cache.gc();
        }
      }
    },
    refetchQueries: [{ query: GET_MY_WATCHLIST }], // Force refetch after mutation
    awaitRefetchQueries: true, // Wait for refetch to complete
  });

  const [remove] = useMutation(REMOVE_FROM_WATCHLIST, {
    optimisticResponse: {
      removeFromWatchlist: { __typename: 'RemoveFromWatchlist', success: true, message: 'Removed.' },
    },
    update: (cache, { data }, { variables }) => {
      const prev: any = cache.readQuery({ query: GET_MY_WATCHLIST });
      if (!prev?.myWatchlist) return;
      cache.writeQuery({
        query: GET_MY_WATCHLIST,
        data: {
          myWatchlist: prev.myWatchlist.filter((w: any) => w.stock.symbol !== variables?.symbol),
        },
      });
    },
  });

  return {
    list,
    addToWatchlist: (symbol: string, companyName?: string, notes?: string) => add({ variables: { symbol, company_name: companyName, notes } }),
    removeFromWatchlist: (symbol: string) => remove({ variables: { symbol } }),
  };
}
