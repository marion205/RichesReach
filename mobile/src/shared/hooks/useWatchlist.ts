import { gql, useMutation, useQuery } from '@apollo/client';
import { Alert } from 'react-native';

export const GET_MY_WATCHLIST = gql`
  query GetMyWatchlist {
    myWatchlist {
      id
      stock {
        symbol
      }
      addedAt
      notes
      targetPrice
    }
  }
`;

const ADD_TO_WATCHLIST = gql`
  mutation AddToWatchlist($symbol: String!, $companyName: String, $notes: String) {
    addToWatchlist(symbol: $symbol, companyName: $companyName, notes: $notes) {
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
        Alert.alert('Success', res.addToWatchlist.message);
      }
    },
    update: (cache) => {
      // Simple refetch; if you prefer, write cache manually
      cache.evict({ fieldName: 'myWatchlist' });
      cache.gc();
    },
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
    addToWatchlist: (symbol: string, companyName?: string, notes?: string) => add({ variables: { symbol, companyName, notes } }),
    removeFromWatchlist: (symbol: string) => remove({ variables: { symbol } }),
  };
}
