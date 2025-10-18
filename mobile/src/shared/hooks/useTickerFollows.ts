import { useEffect, useMemo } from 'react';
import { useQuery, useSubscription } from '@apollo/client';
import { GET_MY_FOLLOWS, SUB_TICKER_POSTS } from '../../tickerFollows';
import { Alert } from 'react-native';

export default function useTickerFollows() {
  const { data, loading, refetch } = useQuery(GET_MY_FOLLOWS, { fetchPolicy: 'cache-and-network' });
  const symbols = useMemo(
    () => {
      const followedTickers = data?.me?.followedTickers;
      return Array.isArray(followedTickers) ? followedTickers : [];
    },
    [data]
  );

  // Optional toast/alert on new posts for followed tickers - DISABLED
  useSubscription(SUB_TICKER_POSTS, {
    skip: !symbols || !symbols.length,
    variables: { symbols: symbols || [] },
    // onData: ({ data }) => {
    //   const p = data.data?.tickerPostCreated;
    //   if (!p) return;
    //   const tick = (p.tickers?.[0] && `$${p.tickers[0]}`) || '';
    //   Alert.alert('New post on a followed ticker', `${tick} • ${p.title || p.kind}`);
    // },
  });

  const set: Set<string> = useMemo(() => new Set(symbols || []), [symbols]);

  return { loading, symbols, set, refetch };
}
