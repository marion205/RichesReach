import { gql, useQuery } from '@apollo/client';
import { useEffect, useState } from 'react';

const GET_STOCKS = gql`
  query GetStocks($search: String) {
    stocks(search: $search) {
      id
      symbol
      companyName
      sector
      marketCap
      peRatio
      dividendYield
      beginnerFriendlyScore
      __typename
    }
  }
`;

const GET_ADVANCED_STOCK_SCREENING = gql`
  query GetAdvancedStockScreening(
    $sector: String
    $minMarketCap: Float
    $maxMarketCap: Float
    $minPeRatio: Float
    $maxPeRatio: Float
    $minBeginnerScore: Int
    $sortBy: String
    $limit: Int
  ) {
    advancedStockScreening(
      sector: $sector
      minMarketCap: $minMarketCap
      maxMarketCap: $maxMarketCap
      minPeRatio: $minPeRatio
      maxPeRatio: $maxPeRatio
      minBeginnerScore: $minBeginnerScore
      sortBy: $sortBy
      limit: $limit
    ) {
      symbol
      companyName
      sector
      marketCap
      peRatio
      dividendYield
      beginnerFriendlyScore
      currentPrice
      volatility
      debtRatio
      reasoning
      score
      mlScore
    }
  }
`;

export function useDebounced<T>(value: T, delay = 350) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setV(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return v;
}

export function useStockSearch(searchText: string, skip = false) {
  const debounced = useDebounced(searchText, 350);

  const stocks = useQuery(GET_STOCKS, {
    variables: { search: debounced || null },
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
    notifyOnNetworkStatusChange: true,
    skip: skip,
  });

  const screening = useQuery(GET_ADVANCED_STOCK_SCREENING, {
    variables: { limit: 50, sortBy: 'ml_score' },
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
    onError: (e) => console.warn('Advanced screening error:', e?.graphQLErrors ?? e?.message),
  });

  return {
    stocks,
    screening,
  };
}
