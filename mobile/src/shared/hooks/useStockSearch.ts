import { gql, useQuery, useLazyQuery } from '@apollo/client';
import { useEffect, useState } from 'react';
import logger from '../../utils/logger';

const GET_STOCKS = gql`
  query GetStocks($search: String, $limit: Int, $offset: Int) {
    stocks(search: $search, limit: $limit, offset: $offset) {
      id
      symbol
      companyName
      sector
      marketCap
      peRatio
      dividendYield
      beginnerFriendlyScore
      currentPrice
      beginnerScoreBreakdown {
        score
        factors {
          name
          weight
          value
          contrib
          detail
        }
        notes
      }
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

const GET_STOCK_CHART_DATA = gql`
  query GetStockChartData($symbol: String!) {
    stockChartData(symbol: $symbol) {
      symbol
      currentPrice
      change
      changePercent
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
  const [allStocks, setAllStocks] = useState<any[]>([]);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [realTimeStocks, setRealTimeStocks] = useState<any[]>([]);

  // Clear results when search text changes
  useEffect(() => {
    if (searchText !== debounced) {
      setAllStocks([]);
      setRealTimeStocks([]);
    }
  }, [searchText, debounced]);

  // Popular stock symbols for real-time fallback - ordered by popularity
  const popularSymbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'AMZN', 'NVDA', 'META', 'NFLX', 'AMD', 'INTC'];
  
  const [getStockData] = useLazyQuery(GET_STOCK_CHART_DATA, {
    onCompleted: (data) => {
      if (data?.stockChartData) {
        const stockData = data.stockChartData;
        setRealTimeStocks(prev => {
          const existing = prev.find(s => s.symbol === stockData.symbol);
          if (existing) {
            return prev;
          }
          const newStock = {
            id: stockData.symbol,
            symbol: stockData.symbol,
            companyName: getCompanyName(stockData.symbol),
            currentPrice: stockData.currentPrice,
            change: stockData.change,
            changePercent: stockData.changePercent,
            sector: getSectorForSymbol(stockData.symbol),
            beginnerFriendlyScore: 80,
            __typename: 'Stock',
            // Add detailed breakdown for budget impact analysis
            beginnerScoreBreakdown: {
              score: 80,
              factors: [
                {
                  name: 'Market Cap',
                  weight: 0.25,
                  value: 0.8,
                  contrib: 20,
                  detail: 'Large cap stock with stable market presence'
                },
                {
                  name: 'Volatility',
                  weight: 0.2,
                  value: 0.7,
                  contrib: 14,
                  detail: 'Moderate volatility suitable for most investors'
                },
                {
                  name: 'Liquidity',
                  weight: 0.2,
                  value: 0.9,
                  contrib: 18,
                  detail: 'High trading volume ensures easy entry/exit'
                },
                {
                  name: 'Growth Potential',
                  weight: 0.2,
                  value: 0.75,
                  contrib: 15,
                  detail: 'Strong growth prospects in technology sector'
                },
                {
                  name: 'Dividend Yield',
                  weight: 0.15,
                  value: 0.6,
                  contrib: 9,
                  detail: 'Modest dividend providing steady income'
                }
              ],
              notes: [
                'Suitable for long-term investment',
                'Good for portfolio diversification',
                'Consider dollar-cost averaging approach'
              ]
            }
          };
          const updatedStocks = [...prev, newStock];
          return updatedStocks;
        });
      }
    }
  });

  const getCompanyName = (symbol: string) => {
    const names: { [key: string]: string } = {
      'AAPL': 'Apple Inc.',
      'MSFT': 'Microsoft Corporation',
      'GOOGL': 'Alphabet Inc.',
      'TSLA': 'Tesla Inc.',
      'AMZN': 'Amazon.com Inc.',
      'NVDA': 'NVIDIA Corporation',
      'META': 'Meta Platforms Inc.',
      'NFLX': 'Netflix Inc.',
      'AMD': 'Advanced Micro Devices Inc.',
      'INTC': 'Intel Corporation',
      'GM': 'General Motors Company',
      'F': 'Ford Motor Company',
      'BAC': 'Bank of America Corporation',
      'JPM': 'JPMorgan Chase & Co.',
      'WMT': 'Walmart Inc.',
      'JNJ': 'Johnson & Johnson',
      'PG': 'Procter & Gamble Company',
      'KO': 'Coca-Cola Company',
      'PFE': 'Pfizer Inc.',
      'DIS': 'Walt Disney Company',
      'NKE': 'Nike Inc.',
      'HD': 'Home Depot Inc.',
      'V': 'Visa Inc.',
      'MA': 'Mastercard Inc.',
      'CRM': 'Salesforce Inc.',
      'ADBE': 'Adobe Inc.',
      'PYPL': 'PayPal Holdings Inc.',
      'UBER': 'Uber Technologies Inc.',
      'SPOT': 'Spotify Technology S.A.',
      'SQ': 'Block Inc.',
      'C': 'Citigroup Inc.',
      'WFC': 'Wells Fargo & Company'
    };
    return names[symbol] || `${symbol} Corporation`;
  };

  const getSectorForSymbol = (symbol: string) => {
    const sectors: { [key: string]: string } = {
      // Technology
      'AAPL': 'Technology',
      'MSFT': 'Technology',
      'GOOGL': 'Technology',
      'GOOG': 'Technology',
      'TSLA': 'Technology',
      'AMZN': 'Technology',
      'NVDA': 'Technology',
      'META': 'Technology',
      'FB': 'Technology',
      'NFLX': 'Technology',
      'AMD': 'Technology',
      'INTC': 'Technology',
      'CRM': 'Technology',
      'ADBE': 'Technology',
      'PYPL': 'Technology',
      'UBER': 'Technology',
      'SPOT': 'Technology',
      'SQ': 'Technology',
      // Financial Services
      'BAC': 'Financial Services',
      'JPM': 'Financial Services',
      'C': 'Financial Services',
      'WFC': 'Financial Services',
      'V': 'Financial Services',
      'MA': 'Financial Services',
      // Consumer Goods
      'GM': 'Consumer Discretionary',
      'F': 'Consumer Discretionary',
      'WMT': 'Consumer Staples',
      'JNJ': 'Healthcare',
      'PG': 'Consumer Staples',
      'KO': 'Consumer Staples',
      'PFE': 'Healthcare',
      'DIS': 'Communication Services',
      'NKE': 'Consumer Discretionary',
      'HD': 'Consumer Discretionary'
    };
    return sectors[symbol] || 'Technology';
  };

  const getSymbolSuggestions = (searchTerm: string): string[] => {
    // AI-like symbol suggestions based on common patterns and related companies
    const suggestions: { [key: string]: string[] } = {
      'GENERAL': ['GM', 'GE'],
      'MOTORS': ['GM', 'F', 'TSLA'],
      'FORD': ['F'],
      'BANK': ['BAC', 'JPM', 'WFC', 'C'],
      'AMERICA': ['BAC', 'AAL', 'AMZN'],
      'APPLE': ['AAPL'],
      'MICROSOFT': ['MSFT'],
      'GOOGLE': ['GOOGL', 'GOOG'],
      'TESLA': ['TSLA'],
      'AMAZON': ['AMZN'],
      'NVIDIA': ['NVDA'],
      'META': ['META', 'FB'],
      'NETFLIX': ['NFLX'],
      'AMD': ['AMD'],
      'INTEL': ['INTC'],
      'JOHNSON': ['JNJ'],
      'PROCTER': ['PG'],
      'COCA': ['KO'],
      'PFIZER': ['PFE'],
      'DISNEY': ['DIS'],
      'NIKE': ['NKE'],
      'HOME': ['HD'],
      'VISA': ['V'],
      'MASTERCARD': ['MA'],
      'SALESFORCE': ['CRM'],
      'ADOBE': ['ADBE'],
      'PAYPAL': ['PYPL'],
      'UBER': ['UBER'],
      'SPOTIFY': ['SPOT'],
      'SQUARE': ['SQ']
    };
    
    const searchUpper = searchTerm.toUpperCase();
    const foundSuggestions: string[] = [];
    
    // Look for exact matches in suggestion keys
    for (const [key, symbols] of Object.entries(suggestions)) {
      if (key.includes(searchUpper) || searchUpper.includes(key)) {
        foundSuggestions.push(...symbols);
      }
    }
    
    // Remove duplicates and return
    return [...new Set(foundSuggestions)];
  };

  const stocks = useQuery(GET_STOCKS, {
    variables: { 
      search: debounced || null,
      limit: 10,
      offset: 0
    },
    fetchPolicy: 'network-only', // Force network request to avoid cache issues
    errorPolicy: 'all',
    notifyOnNetworkStatusChange: true,
    skip: skip,
    onCompleted: (data) => {
      if (data?.stocks && data.stocks.length > 0 && (!debounced || !debounced.trim())) {
        setAllStocks(data.stocks);
        setHasMore(data.stocks.length === 10);
        setRealTimeStocks([]); // Clear real-time results when database has results
      } else if (debounced && debounced.trim()) {
        // Force clear all results to ensure fresh search
        setAllStocks([]);
        setRealTimeStocks([]);
        // If database search returns empty, try real-time data for any matching symbol
        const searchUpper = debounced.trim().toUpperCase();
        
        // First check if the search term exactly matches a popular symbol
        const matchingPopularSymbols = popularSymbols.filter(symbol => 
          symbol.includes(searchUpper) || searchUpper.includes(symbol)
        );
        
        // If no popular symbols match, try the search term as a direct symbol
        // Also try common variations and related symbols for AI-like search
        let symbolsToSearch = matchingPopularSymbols;
        
        if (symbolsToSearch.length === 0) {
          // Try the search term as a direct symbol
          symbolsToSearch = [searchUpper];
          
          // Add AI-like symbol suggestions based on common patterns
          const symbolSuggestions = getSymbolSuggestions(searchUpper);
          symbolsToSearch = [...symbolsToSearch, ...symbolSuggestions];
        }
        
        if (symbolsToSearch.length > 0) {
          // Sort matching symbols by their position in popularSymbols array to maintain order
          const sortedMatchingSymbols = symbolsToSearch.sort((a, b) => {
            const aIndex = popularSymbols.indexOf(a);
            const bIndex = popularSymbols.indexOf(b);
            // If both are in popularSymbols, sort by their position
            if (aIndex !== -1 && bIndex !== -1) return aIndex - bIndex;
            // If only one is in popularSymbols, prioritize it
            if (aIndex !== -1) return -1;
            if (bIndex !== -1) return 1;
            // If neither is in popularSymbols, maintain original order
            return 0;
          });
          sortedMatchingSymbols.forEach((symbol) => {
            getStockData({ variables: { symbol } });
          });
        }
      }
    }
  });

  const loadMoreStocks = async () => {
    if (loadingMore || !hasMore) return;
    
    setLoadingMore(true);
    try {
      const result = await stocks.fetchMore({
        variables: {
          search: debounced || null,
          limit: 10,
          offset: allStocks.length
        },
        updateQuery: (prev, { fetchMoreResult }) => {
          if (!fetchMoreResult?.stocks) return prev;
          
          const newStocks = fetchMoreResult.stocks;
          setAllStocks(prev => [...prev, ...newStocks]);
          setHasMore(newStocks.length === 10);
          
          return {
            ...prev,
            stocks: [...(prev.stocks || []), ...newStocks]
          };
        }
      });
    } catch (error) {
      logger.error('Error loading more stocks:', error);
    } finally {
      setLoadingMore(false);
    }
  };

  const screening = useQuery(GET_ADVANCED_STOCK_SCREENING, {
    variables: { limit: 50, sortBy: 'ml_score' },
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
    onError: (e) => logger.warn('Advanced screening error:', e?.graphQLErrors ?? e?.message),
  });

  // Combine database results with real-time results
  const combinedStocks = allStocks.length > 0 ? allStocks : realTimeStocks;

  return {
    stocks: {
      ...stocks,
      data: { stocks: combinedStocks },
      loadMore: loadMoreStocks,
      hasMore,
      loadingMore,
      realTimeStocks // Expose real-time stocks separately
    },
    screening,
  };
}
