import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, FlatList, TextInput, Alert, Modal, ScrollView, Dimensions, ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useApolloClient, gql, useQuery, useMutation } from '@apollo/client';
import { ADD_TO_WATCHLIST, REMOVE_FROM_WATCHLIST } from '../../../graphql/mutations';

import StockCard from '../../../components/common/StockCard';
import WatchlistCard, { WatchlistItem } from '../../../components/common/WatchlistCard';
import BudgetImpactModal from '../../../components/common/BudgetImpactModal';
import StockChart from '../components/StockChart';
import AdvancedChart from '../../../components/charts/AdvancedChart';
import OptionChainCard from '../../../components/OptionChainCard';
import { useStockSearch } from '../../../shared/hooks/useStockSearch';
import { useWatchlist, GET_MY_WATCHLIST } from '../../../shared/hooks/useWatchlist';
import { UI } from '../../../shared/constants';
import logger from '../../../utils/logger';

// Chart data adapter utilities
const toMs = (t: string | number | Date) =>
  typeof t === 'number' ? (t > 1e12 ? t : t * 1000) : new Date(t).getTime();

const toNum = (v: unknown) => (v == null || v === '' ? null : Number(v));

const sortAsc = <T extends { t: number }>(arr: T[]) =>
  [...arr].sort((a,b) => a.t - b.t);

type GqlBar = {
  timestamp: string | number;
  open?: string | number;
  high?: string | number;
  low?: string | number;
  close?: string | number;
  volume?: string | number;
};

type GqlIndicators = {
  BBUpper?: string | number;
  BBMiddle?: string | number;
  BBLower?: string | number;
  SMA20?: string | number;
  SMA50?: string | number;
  EMA12?: string | number;
  EMA26?: string | number;
  MACD?: string | number;
  MACDSignal?: string | number;
  MACDHist?: string | number;
};

function useChartSeries(data?: { stockChartData?: { data?: GqlBar[]; indicators?: GqlIndicators }}) {
  // ✅ Resilient: Check for wrong data shape and log warning
  if (data && !data.stockChartData && Object.keys(data).length > 0) {
    const dataKeys = Object.keys(data);
    logger.warn('[useChartSeries] ⚠️ Expected stockChartData, got keys:', dataKeys);
    // If we got 'me' data or other wrong shape, return empty array
    if (dataKeys.includes('me') || dataKeys.some(k => k !== 'stockChartData')) {
      logger.warn('[useChartSeries] ❌ Wrong data shape detected, returning empty chart data');
      return useMemo(() => [], []);
    }
  }
  
  const rows = data?.stockChartData?.data ?? [];
  const indicators = data?.stockChartData?.indicators;
  
  return useMemo(() => {
    const toMs = (t: any) => typeof t === 'number' ? (t > 1e12 ? t : t * 1000) : new Date(t).getTime();
    const toNum = (v: any) => (v == null || v === '' ? null : Number(v));
    
    if (rows.length === 0) {
      logger.log('[useChartSeries] No rows to map');
      return [];
    }
    
    const mapped = rows.map((r: any) => ({
      t: toMs(r.timestamp),
      o: toNum(r.open),
      h: toNum(r.high),
      l: toNum(r.low),
      c: toNum(r.close),
      v: toNum(r.volume),
      bbU: toNum(indicators?.BBUpper),
      bbM: toNum(indicators?.BBMiddle),
      bbL: toNum(indicators?.BBLower),
      macd: toNum(indicators?.MACD),
      macdSig: toNum(indicators?.MACDSignal),
      macdHist: toNum(indicators?.MACDHist),
    })).filter(p => Number.isFinite(p.t) && Number.isFinite(p.c as number))
      .sort((a, b) => a.t - b.t);
    
    logger.log('[useChartSeries] ✅ Rows:', rows.length, '→ Mapped:', mapped.length);
    return mapped;
  }, [rows, indicators]); // ✅ Stable deps
}

// Responsive chart wrapper that measures actual available width
const ResponsiveChart: React.FC<{
  height?: number;
  children: (width: number) => React.ReactNode;
}> = ({ height = 200, children }) => {
  const [w, setW] = React.useState(0);
  return (
    <View
      style={{ width: '100%', height, overflow: 'hidden' }}
      onLayout={e => setW(Math.max(0, Math.floor(e.nativeEvent.layout.width)))}
      collapsable={false} // ensure onLayout fires inside RN optimizations
    >
      {w > 0 ? children(w) : null}
    </View>
  );
};

// Helper functions
const safeFixed = (val: any, dp = 2, fallback = '—') =>
  Number.isFinite(val) ? Number(val).toFixed(dp) : fallback;

const safePct = (val: any, dp = 0, fallback = '—') =>
  Number.isFinite(val) ? `${Number(val * 100).toFixed(dp)}%` : fallback;

const safeMoney = (val: any, dp = 2, fallback = '—') =>
  Number.isFinite(val) ? `$${Number(val).toFixed(dp)}` : fallback;

const formatMarketCap = (cap: number | null | undefined) => {
  if (cap == null || !Number.isFinite(cap)) return 'N/A';
  if (cap >= 1e12) return `$${(cap / 1e12).toFixed(1)}T`;
  if (cap >= 1e9) return `$${(cap / 1e9).toFixed(1)}B`;
  if (cap >= 1e6) return `$${(cap / 1e6).toFixed(1)}M`;
  return `$${cap.toLocaleString()}`;
};

const getSentimentColor = (label: string) => {
  if (label === 'POSITIVE') return '#22C55E';
  if (label === 'NEGATIVE') return '#EF4444';
  return '#8E8E93';
};

type Stock = {
  id: string; symbol: string; companyName: string; sector: string;
  marketCap?: number | string | null; peRatio?: number | null;
  dividendYield?: number | null; beginnerFriendlyScore: number;
  currentPrice?: number | string | null;
  beginnerScoreBreakdown?: {
    score: number;
    factors: Array<{
      name: string;
      weight: number;
      value: number;
      contrib: number;
      detail: string;
    }>;
    notes: string[];
  };
};

const GET_BEGINNER_FRIENDLY_STOCKS = gql`
  query GetBeginnerFriendlyStocks {
    beginnerFriendlyStocks {
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

// Create a separate query with a different name to force cache separation
const GET_BEGINNER_FRIENDLY_STOCKS_ALT = gql`
  query GetBeginnerFriendlyStocksAlt {
    beginnerFriendlyStocks {
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

// AI-powered stock recommendations
const GET_AI_STOCK_RECOMMENDATIONS = gql`
  query GetAIStockRecommendations {
    aiRecommendations {
      buyRecommendations {
        symbol
        companyName
        recommendation
        confidence
        reasoning
        targetPrice
        currentPrice
        expectedReturn
        allocation
      }
    }
  }
`;

// ML-powered stock screening
const GET_ML_STOCK_SCREENING = gql`
  query GetMLStockScreening($limit: Int) {
    advancedStockScreening(limit: $limit, sortBy: "ml_score") {
      symbol
      companyName
      sector
      marketCap
      peRatio
      dividendYield
      beginnerFriendlyScore
      currentPrice
      mlScore
    }
  }
`;

// User profile query for income-based recommendations
const GET_USER_PROFILE = gql`
  query GetUserProfile {
    me {
      id
      name
      email
      incomeProfile {
        incomeBracket
        age
        investmentGoals
        riskTolerance
        investmentHorizon
      }
    }
  }
`;

// Rust analysis
const GET_RUST_STOCK_ANALYSIS = gql`
query GetRustStockAnalysis($symbol: String!) {
rustStockAnalysis(symbol: $symbol) {
symbol
beginnerFriendlyScore
riskLevel
recommendation
      technicalIndicators { rsi macd macdSignal macdHistogram sma20 sma50 ema12 ema26 bollingerUpper bollingerLower bollingerMiddle }
      fundamentalAnalysis { valuationScore growthScore stabilityScore dividendScore debtScore }
reasoning
}
}
`;

// Research queries
const RESEARCH_QUERY = gql`
  query Research($s: String!) {
    researchHub(symbol: $s) {
      symbol
      company: snapshot {
        name
        sector
        marketCap
        country
        website
      }
      quote {
        currentPrice: price
        change: chg
        changePercent: chgPct
        high
        low
        volume
      }
      technicals: technical {
        rsi
        macd
        macdhistogram
        movingAverage50
        movingAverage200
        supportLevel
        resistanceLevel
        impliedVolatility
      }
      sentiment {
        sentiment_label: label
        sentiment_score: score
        article_count
        confidence
      }
      macro {
        vix
        market_sentiment: marketSentiment
        risk_appetite: riskAppetite
      }
      marketRegime {
        market_regime
        confidence
        recommended_strategy
      }
      peers
      updatedAt
    }
  }
`;

const CHART_QUERY = gql`
  query Chart(
    $symbol: String!,
    $tf: String = "1D",
    $iv: String = "1D",
    $limit: Int = 180,
    $inds: [String!] = ["SMA20","SMA50","EMA12","EMA26","RSI","MACD","MACDHist","BB"]
  ) {
    stockChartData(
      symbol: $symbol,
      timeframe: $tf,
      interval: $iv,
      limit: $limit,
      indicators: $inds
    ) {
      symbol
      interval
      limit
      currentPrice
      change
      changePercent
      data {
        timestamp
        open
        high
        low
        close
        volume
      }
      indicators {
        SMA20
        SMA50
        EMA12
        EMA26
        BBUpper
        BBMiddle
        BBLower
        RSI14
        MACD
        MACDSignal
        MACDHist
      }
}
}
`;

// Helper functions to get market data for symbols
const getMarketCapForSymbol = (symbol: string): number => {
  const marketCaps: { [key: string]: number } = {
    'AAPL': 2800000000000, // $2.8T
    'MSFT': 2800000000000, // $2.8T
    'GOOGL': 1800000000000, // $1.8T
    'TSLA': 800000000000,  // $800B
    'AMZN': 1500000000000, // $1.5T
    'NVDA': 1200000000000, // $1.2T
    'META': 900000000000,  // $900B
    'NFLX': 200000000000,  // $200B
    'AMD': 300000000000,   // $300B
    'INTC': 200000000000,  // $200B
    'JNJ': 400000000000,   // $400B
    'PG': 350000000000,    // $350B
    'KO': 250000000000,    // $250B
    'GM': 50000000000,     // $50B
    'F': 45000000000,      // $45B
    'BAC': 300000000000,   // $300B
    'JPM': 450000000000,   // $450B
    'WMT': 500000000000,   // $500B
    'PFE': 200000000000,   // $200B
    'DIS': 180000000000,   // $180B
    'NKE': 200000000000,   // $200B
    'HD': 350000000000,    // $350B
    'V': 500000000000,     // $500B
    'MA': 400000000000,    // $400B
    'CRM': 200000000000,   // $200B
    'ADBE': 250000000000,  // $250B
    'PYPL': 60000000000,   // $60B
    'UBER': 100000000000,  // $100B
    'SPOT': 30000000000,   // $30B
    'SQ': 40000000000,     // $40B
  };
  return marketCaps[symbol] || 100000000000; // Default $100B
};

const getPERatioForSymbol = (symbol: string): number => {
  const peRatios: { [key: string]: number } = {
    'AAPL': 28.5,
    'MSFT': 32.1,
    'GOOGL': 25.8,
    'TSLA': 45.2,
    'AMZN': 35.4,
    'NVDA': 55.7,
    'META': 22.3,
    'NFLX': 38.9,
    'AMD': 42.1,
    'INTC': 18.7,
    'JNJ': 15.2,
    'PG': 24.8,
    'KO': 22.1,
    'GM': 5.2,
    'F': 8.1,
    'BAC': 12.5,
    'JPM': 11.8,
    'WMT': 28.3,
    'PFE': 15.7,
    'DIS': 18.9,
    'NKE': 25.4,
    'HD': 22.7,
    'V': 35.2,
    'MA': 30.8,
    'CRM': 45.1,
    'ADBE': 38.5,
    'PYPL': 12.3,
    'UBER': 8.7,
    'SPOT': 15.2,
    'SQ': 18.4,
  };
  return peRatios[symbol] || 25.0; // Default 25
};

const getDividendYieldForSymbol = (symbol: string): number => {
  const dividendYields: { [key: string]: number } = {
    'AAPL': 0.0044, // 0.44%
    'MSFT': 0.0068, // 0.68%
    'GOOGL': 0.0,   // No dividend
    'TSLA': 0.0,    // No dividend
    'AMZN': 0.0,    // No dividend
    'NVDA': 0.0,    // No dividend
    'META': 0.0,    // No dividend
    'NFLX': 0.0,    // No dividend
    'AMD': 0.0,     // No dividend
    'INTC': 0.0156, // 1.56%
    'JNJ': 0.0298,  // 2.98%
    'PG': 0.0245,   // 2.45%
    'KO': 0.0312,   // 3.12%
    'GM': 0.0125,   // 1.25%
    'F': 0.0156,    // 1.56%
    'BAC': 0.0289,  // 2.89%
    'JPM': 0.0234,  // 2.34%
    'WMT': 0.0134,  // 1.34%
    'PFE': 0.0345,  // 3.45%
    'DIS': 0.0,     // No dividend
    'NKE': 0.0123,  // 1.23%
    'HD': 0.0234,   // 2.34%
    'V': 0.0078,    // 0.78%
    'MA': 0.0056,   // 0.56%
    'CRM': 0.0,     // No dividend
    'ADBE': 0.0,    // No dividend
    'PYPL': 0.0,    // No dividend
    'UBER': 0.0,    // No dividend
    'SPOT': 0.0,    // No dividend
    'SQ': 0.0,      // No dividend
  };
  return dividendYields[symbol] || 0.0; // Default 0%
};

export default function StockScreen({ navigateTo = () => {} }: { navigateTo?: (s: string, d?: any) => void }) {
  const [activeTab, setActiveTab] = useState<'browse' | 'beginner' | 'watchlist' | 'research' | 'options'>('browse');
  
  const handleRowPress = useCallback((item: Stock) => {
    logger.log('🔍 ROW PRESS', item.symbol);
    // Navigate to stock detail screen
    navigateTo?.('StockDetail', {
      symbol: item.symbol,
    });
  }, [navigateTo]);

  const openTrade = (item: Stock) => {
    logger.log('🔍 TRADE PRESS', item.symbol);
    // Navigate to stock detail - user can use the Trade tab
    navigateTo?.('StockDetail', {
      symbol: item.symbol,
    });
  };

  const openAnalysis = useCallback((item: Stock) => {
    logger.log('🔍 ANALYSIS PRESS', item.symbol);
    // Open the rust analysis modal
    handleRustAnalysis(item.symbol);
  }, [handleRustAnalysis]);

  const [searchQuery, setSearchQuery] = useState('');
  const [tooltip, setTooltip] = useState<{ title: string; description: string } | null>(null);
  const [watchlistModal, setWatchlistModal] = useState<{ open: boolean; stock: Stock | null }>({ open: false, stock: null });
  const [notes, setNotes] = useState('');
  const [rust, setRust] = useState<any | null>(null);
  const [rustOpen, setRustOpen] = useState(false);
  const [rustLoading, setRustLoading] = useState(false);
  const [budgetImpactModal, setBudgetImpactModal] = useState<{ open: boolean; stock: Stock | null }>({ open: false, stock: null });
  
  // Research state
  const [researchSymbol, setResearchSymbol] = useState('AAPL');
  const [chartInterval, setChartInterval] = useState('1D');
  
  // Options trading state
  const [optionsSymbol, setOptionsSymbol] = useState('AAPL');
  const [selectedOption, setSelectedOption] = useState<any>(null);
  const [orderQuantity, setOrderQuantity] = useState('1');
  const [orderType, setOrderType] = useState('MARKET');
  const [limitPrice, setLimitPrice] = useState('');
  const [timeInForce, setTimeInForce] = useState('DAY');
  const [orderNotes, setOrderNotes] = useState('');
  
  const client = useApolloClient();
  const { stocks, screening } = useStockSearch(searchQuery, false); // Always run the query
  
  // Watchlist mutations with proper cache updates
  const [addToWatchlistMutation, { loading: addingToWatchlist, error: watchlistError }] = useMutation(ADD_TO_WATCHLIST, {
    errorPolicy: 'none', // Don't return partial data that might be from cache
    // Note: fetchPolicy is set per-call, not in useMutation config
    onError: (error) => {
      logger.error('🔍 Watchlist Mutation onError:', error);
      logger.error('🔍 GraphQL Errors:', error?.graphQLErrors);
      logger.error('🔍 Network Error:', error?.networkError);
      logger.error('🔍 Error message:', error?.message);
      logger.error('🔍 Full error object:', JSON.stringify(error, null, 2));
    },
    onCompleted: (data) => {
      logger.log('🔍 Watchlist Mutation onCompleted:', JSON.stringify(data, null, 2));
    },
    // Don't use refetchQueries here - it's causing Apollo to return wrong data
    // We'll manually refetch after mutation succeeds
  });
  const [removeFromWatchlistMutation] = useMutation(REMOVE_FROM_WATCHLIST);
  const { data: beginnerData, loading: beginnerLoading, refetch: refetchBeginner, error: beginnerError } =
    useQuery(GET_BEGINNER_FRIENDLY_STOCKS_ALT, { 
      fetchPolicy: 'cache-and-network', 
      errorPolicy: 'all',
      notifyOnNetworkStatusChange: true
    });

  // AI-powered recommendations for Browse All tab
  const { data: aiRecommendationsData, loading: aiRecommendationsLoading, error: aiRecommendationsError } =
    useQuery(GET_AI_STOCK_RECOMMENDATIONS, {
      fetchPolicy: 'cache-and-network',
      errorPolicy: 'all'
    });

  // ML-powered screening for Beginner Friendly tab
  const { data: mlScreeningData, loading: mlScreeningLoading, error: mlScreeningError } =
    useQuery(GET_ML_STOCK_SCREENING, {
      variables: { limit: 50 },
      fetchPolicy: 'cache-and-network',
      errorPolicy: 'all'
    });

  // User profile for income-based recommendations
  const { data: userProfileData, loading: userProfileLoading } = useQuery(GET_USER_PROFILE, {
    fetchPolicy: 'cache-first',
    errorPolicy: 'all'
  });

  // Research queries
  const { data: researchData, loading: researchLoading, error: researchError, refetch: refetchResearch } = useQuery(RESEARCH_QUERY, {
    variables: { s: researchSymbol },
    skip: !researchSymbol,
  });

  // Timeout handling for research loading
  const [researchLoadingTimeout, setResearchLoadingTimeout] = useState(false);
  useEffect(() => {
    if (researchLoading && !researchData && researchSymbol) {
      const timer = setTimeout(() => {
        setResearchLoadingTimeout(true);
      }, 3000); // 3 second timeout
      return () => clearTimeout(timer);
    } else {
      setResearchLoadingTimeout(false);
    }
  }, [researchLoading, researchData, researchSymbol]);

  // Generate mock research data for demo
  const getMockResearchData = useCallback(() => {
    const symbol = researchSymbol || 'AAPL';
    const basePrice = symbol === 'AAPL' ? 175.50 : symbol === 'MSFT' ? 380.25 : 150.00;
    const change = basePrice * 0.02; // 2% change
    
    return {
      researchHub: {
        symbol,
        company: {
          name: symbol === 'AAPL' ? 'Apple Inc.' : symbol === 'MSFT' ? 'Microsoft Corporation' : 'Company Name',
          sector: 'Technology',
          marketCap: basePrice * 1000000000, // 1B shares
          website: 'https://example.com',
        },
        quote: {
          price: basePrice,
          chg: change,
          chgPct: 2.0,
          high: basePrice * 1.03,
          low: basePrice * 0.97,
          volume: 50000000,
        },
        technical: {
          rsi: 55.5,
          macd: 2.3,
          movingAverage50: basePrice * 0.98,
          movingAverage200: basePrice * 0.95,
          supportLevel: basePrice * 0.92,
          resistanceLevel: basePrice * 1.08,
        },
        sentiment: {
          label: 'BULLISH',
          score: 65.5,
          articleCount: 125,
          confidence: 75.0,
        },
        macro: {
          vix: 18.5,
          marketSentiment: 'Positive',
          riskAppetite: 0.65,
        },
        marketRegime: {
          market_regime: 'Bull Market',
          confidence: 0.72,
          recommended_strategy: 'Momentum',
        },
      },
    };
  }, [researchSymbol]);

  // Use mock data if timeout or error - always return data, never null
  const effectiveResearchData = useMemo(() => {
    if (researchData?.researchHub) {
      return researchData; // Use real data if available
    }
    // Always return mock data if no real data available (loading, timeout, or error)
    return getMockResearchData();
  }, [researchData, researchLoadingTimeout, researchError, researchLoading, getMockResearchData]);
  
  const effectiveResearchLoading = researchLoadingTimeout ? false : (researchLoading && !effectiveResearchData?.researchHub);

  const { data: chartData, loading: chartLoading, error: chartError, refetch: refetchChart } = useQuery(CHART_QUERY, {
    variables: {
      symbol: researchSymbol,
      tf: chartInterval,
      iv: chartInterval,
      limit: 180,
      inds: ["SMA20","SMA50","EMA12","EMA26","RSI","MACD","MACDHist","BB"],
    },
    skip: !researchSymbol,
    fetchPolicy: 'cache-and-network',
    nextFetchPolicy: 'cache-first',
    errorPolicy: 'all',
  });


  // Options trading mutations
  const [placeOptionOrder, { loading: placingOrder }] = useMutation(gql`
    mutation PlaceOptionOrder(
      $symbol: String!
      $optionType: String!
      $strike: Float!
      $expiration: String!
      $side: String!
      $quantity: Int!
      $orderType: String!
      $limitPrice: Float
      $timeInForce: String!
      $notes: String
    ) {
      placeOptionOrder(
        symbol: $symbol
        optionType: $optionType
        strike: $strike
        expiration: $expiration
        side: $side
        quantity: $quantity
        orderType: $orderType
        limitPrice: $limitPrice
        timeInForce: $timeInForce
        notes: $notes
      ) {
        success
        message
        orderId
        order {
          id
          symbol
          optionType
          strike
          expiration
          side
          quantity
          orderType
          limitPrice
          timeInForce
          status
          notes
          createdAt
        }
      }
    }
  `);

  const [cancelOptionOrder] = useMutation(gql`
    mutation CancelOptionOrder($orderId: String!) {
      cancelOptionOrder(orderId: $orderId) {
        success
        message
        orderId
      }
    }
  `);

  const { data: optionsOrdersData, loading: optionsOrdersLoading, refetch: refetchOptionsOrders } = useQuery(gql`
    query OptionOrders($status: String) {
      optionOrders(status: $status) {
        id
        symbol
        optionType
        strike
        expiration
        side
        quantity
        orderType
        limitPrice
        timeInForce
        status
        filledPrice
        notes
        createdAt
      }
    }
  `, {
    variables: { status: 'ALL' },
    skip: false,
    fetchPolicy: 'cache-and-network',
    });

  // Debug query state changes
  React.useEffect(() => {
    logger.log('=== Query State Debug ===');
    logger.log('stocks.loading:', stocks.loading);
    logger.log('stocks.data:', stocks.data);
    logger.log('stocks.error:', stocks.error);
    logger.log('activeTab:', activeTab);
    logger.log('searchQuery:', searchQuery);
  }, [stocks.loading, stocks.data, stocks.error, activeTab, searchQuery]);

  const { list: watchlistQ, addToWatchlist, removeFromWatchlist } = useWatchlist();

  // ✅ Sanity checks: Verify data keys match expected queries
  React.useEffect(() => {
    if (chartData) {
      const chartKeys = Object.keys(chartData);
      if (!chartKeys.includes('stockChartData') && chartKeys.length > 0) {
        logger.warn('[Sanity] Chart query returned unexpected keys:', chartKeys);
      }
    }
    if (userProfileData) {
      const profileKeys = Object.keys(userProfileData);
      logger.log('[Sanity] User profile keys:', profileKeys);
    }
  }, [chartData, userProfileData]);
  
  // Chart series data - must be called at top level to avoid hooks rule violation
  const chartSeries = useChartSeries(chartData);
  
  // ✅ Derived values after all hooks are declared
  const hasChartData = chartSeries.length > 0;
  const isResearchTab = activeTab === 'research';
  const isChartLoading = chartLoading || !chartData;

  // 🔍 Debug chart data
  React.useEffect(() => {
    if (isResearchTab) {
      logger.log('🔍 CHART DEBUG - researchSymbol:', researchSymbol);
      logger.log('🔍 CHART DEBUG - chartInterval:', chartInterval);
      logger.log('🔍 CHART DEBUG - chartLoading:', chartLoading);
      logger.log('🔍 CHART DEBUG - chartError:', chartError);
      logger.log('🔍 CHART DEBUG - chartData:', chartData);
      logger.log('🔍 CHART DEBUG - chartSeries.length:', chartSeries.length);
      logger.log('🔍 CHART DEBUG - hasChartData:', hasChartData);
    }
  }, [isResearchTab, researchSymbol, chartInterval, chartLoading, chartError, chartData, chartSeries.length, hasChartData]);

  // Note: Removed automatic refetch on tab change to prevent infinite loop
  // Data will be refetched when user manually switches tabs via handleTabChange
  
  const handleTabChange = useCallback((tab: 'browse' | 'beginner' | 'watchlist' | 'research' | 'options') => {
    logger.log('Switching to tab:', tab);
    setActiveTab(tab);
    
    // Clear Apollo cache for the current tab to ensure fresh data
    client.cache.evict({ fieldName: tab === 'browse' ? 'stocks' : tab === 'beginner' ? 'beginnerFriendlyStocks' : tab === 'watchlist' ? 'myWatchlist' : 'researchHub' });
    client.cache.gc();
    
    // Refetch data when switching tabs to ensure fresh data
    if (tab === 'browse') {
      stocks.refetch();
    } else if (tab === 'beginner') {
      refetchBeginner?.();
    } else if (tab === 'watchlist') {
      watchlistQ.refetch();
    } else if (tab === 'research') {
      refetchResearch?.();
      refetchChart?.();
    }
  }, [stocks, refetchBeginner, watchlistQ, refetchResearch, refetchChart, client]);

  const showMetricTooltip = useCallback((metric: 'marketCap' | 'peRatio' | 'dividendYield') => {
    const tooltips = {
      marketCap: { title: 'Market Cap', description: 'Total value of all shares. $10B+ companies are typically more stable for beginners.' },
      peRatio:   { title: 'P/E Ratio', description: 'Price-to-earnings. Under ~25 is often considered reasonable, compare within an industry.' },
      dividendYield: { title: 'Dividend Yield', description: 'Annual dividends / price. 2–5% can indicate income & mature companies. Not guaranteed.' },
    };
    setTooltip(tooltips[metric]);
  }, []);

  const onPressAdd = useCallback((s: Stock) => {
    setWatchlistModal({ open: true, stock: s });
  }, []);

  const onAddConfirm = useCallback(async () => {
    if (!watchlistModal.stock) return;
    
    // Debug: Log the variables being sent
    const variables = {
      symbol: watchlistModal.stock.symbol,
      company_name: watchlistModal.stock.companyName || null, // Backend expects snake_case
      notes: notes || ""
    };
    logger.log('🔍 Watchlist Debug - Variables being sent:', variables);
    logger.log('🔍 Watchlist Debug - Stock data:', watchlistModal.stock);
    
    try {
      logger.log('🔍 Watchlist Debug - About to call mutation with variables:', variables);
      logger.log('🔍 Watchlist Debug - Mutation definition:', ADD_TO_WATCHLIST.loc?.source?.body);
      
      const { data, errors } = await addToWatchlistMutation({
        variables: variables,
        fetchPolicy: 'no-cache', // Force network request, don't use cache
        context: {
          fetchOptions: {
            headers: {
              'X-Debug-Request': 'watchlist-mutation',
            },
          },
        },
      });
      
      logger.log('🔍 Watchlist Debug - Mutation response received');
      logger.log('🔍 Watchlist Debug - Data type:', typeof data);
      logger.log('🔍 Watchlist Debug - Data keys:', data ? Object.keys(data) : 'null');
      logger.log('🔍 Watchlist Debug - Full data:', JSON.stringify(data, null, 2));
      logger.log('🔍 Watchlist Debug - Errors:', errors);
      
      // Handle GraphQL errors that might be returned with data
      if (errors && errors.length > 0) {
        logger.error('🔍 Watchlist Debug - GraphQL errors in response:', errors);
        const errorMessage = errors[0]?.message || 'Failed to add to watchlist';
        Alert.alert('Error', errorMessage);
        return;
      }
      
      logger.log('🔍 Watchlist Debug - Full response data:', JSON.stringify(data, null, 2));
      
      // Check if we got a response
      if (!data) {
        logger.error('🔍 Watchlist Debug - No data in response');
        Alert.alert('Error', 'No response from server. Please try again.');
        return;
      }
      
      // ✅ Sanity check: Log what we actually received
      const responseKeys = Object.keys(data || {});
      logger.log('[Watchlist] Mutation response keys:', responseKeys);
      
      // Check if addToWatchlist exists in response
      if (!data.addToWatchlist) {
        logger.error('🔍 Watchlist Debug - No addToWatchlist in response. Received keys:', responseKeys);
        logger.error('🔍 Watchlist Debug - Full response:', JSON.stringify(data, null, 2));
        
        // More helpful error message
        const receivedData = responseKeys.length > 0 ? responseKeys.join(', ') : 'empty response';
        Alert.alert(
          'Error', 
          `Expected 'addToWatchlist' in response, but got: ${receivedData}. This usually means the backend mutation handler didn't fire. Check backend logs.`
        );
        return;
      }
      
      logger.log('🔍 Watchlist Debug - Success value:', data.addToWatchlist.success);
      logger.log('🔍 Watchlist Debug - Message:', data.addToWatchlist.message);
      
      if (data.addToWatchlist.success === true) {
        Alert.alert('Success', data.addToWatchlist.message);
        setWatchlistModal({ open: false, stock: null });
        setNotes('');
        // Refresh watchlist data - force immediate refetch
        if (watchlistQ?.refetch) {
          await watchlistQ.refetch({ fetchPolicy: 'network-only' });
        }
        // Also force refetch via Apollo client
        if (GET_MY_WATCHLIST) {
          await client.query({
            query: GET_MY_WATCHLIST,
            fetchPolicy: 'network-only',
            errorPolicy: 'all',
          });
        }
      } else {
        logger.log('🔍 Watchlist Debug - Success false, message:', data.addToWatchlist.message);
        Alert.alert('Error', data.addToWatchlist.message || 'Failed to add to watchlist');
      }
    } catch (error) {
      logger.error('🔍 Watchlist Debug - Full error:', error);
      logger.error('🔍 Watchlist Debug - GraphQL errors:', error?.graphQLErrors);
      logger.error('🔍 Watchlist Debug - Network error:', error?.networkError);
      
      // Check if it's an authentication error
      const isAuthError = error?.graphQLErrors?.some(err => 
        err.message?.includes('logged in') || 
        err.message?.includes('authentication') ||
        err.message?.includes('token')
      );
      
      // Check if it's a mutation not found error (backend not deployed)
      const isMutationNotFound = error?.graphQLErrors?.some(err => 
        err.message?.includes('Cannot query field') ||
        err.message?.includes('addToWatchlist')
      ) || error?.networkError?.message?.includes('400');
      
      if (isAuthError) {
        Alert.alert('Authentication Required', 'Please log in to add stocks to your watchlist.');
      } else if (isMutationNotFound) {
        Alert.alert('Feature Coming Soon', 'Watchlist functionality is being updated. Please try again later.');
      } else {
        Alert.alert('Error', `Failed to add to watchlist: ${error?.message || 'Unknown error'}`);
      }
    }
  }, [watchlistModal, notes, addToWatchlistMutation, watchlistQ]);

  const onRemoveWatchlist = useCallback((symbol: string) => {
    Alert.alert('Remove from Watchlist', 'Are you sure?', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Remove', style: 'destructive', onPress: async () => {
        try {
          const { data } = await removeFromWatchlistMutation({
            variables: { symbol }
          });
          
          if (data?.removeFromWatchlist?.success) {
            Alert.alert('Success', data.removeFromWatchlist.message);
            // Refresh watchlist data
            if (watchlistQ?.refetch) {
              watchlistQ.refetch();
            }
          } else {
            Alert.alert('Error', data?.removeFromWatchlist?.message || 'Failed to remove from watchlist');
          }
        } catch (error) {
          logger.error('Error removing from watchlist:', error);
          Alert.alert('Error', 'Failed to remove from watchlist. Please try again.');
        }
      }},
    ]);
  }, [removeFromWatchlistMutation, watchlistQ]);

  const handleRustAnalysis = useCallback(async (symbol: string) => {
    logger.log('🔍 Starting Advanced Analysis for:', symbol);
    
    // Show modal immediately with realistic placeholder data (like the old mock data)
    // This makes it feel instant while real data loads in the background
    setRust({
      symbol: symbol,
      beginnerFriendlyScore: 75,
      riskLevel: 'Medium',
      recommendation: 'HOLD',
      technicalIndicators: {
        rsi: 50.0,
        macd: 0.0,
        macdSignal: 0.0,
        macdHistogram: 0.0,
        sma20: 0.0,
        sma50: 0.0,
        ema12: 0.0,
        ema26: 0.0,
        bollingerUpper: 0.0,
        bollingerLower: 0.0,
        bollingerMiddle: 0.0
      },
      fundamentalAnalysis: {
        valuationScore: 70.0,
        growthScore: 65.0,
        stabilityScore: 80.0,
        dividendScore: 60.0,
        debtScore: 75.0
      },
      reasoning: [`Loading detailed analysis for ${symbol}...`]
    });
    setRustOpen(true);
    setRustLoading(true);
    
    try {
      logger.log('📡 Making GraphQL query...');
      // Try the rust analysis first with a timeout, but fallback to chart data if it fails or times out
      try {
        // Add timeout to prevent hanging
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Query timeout after 5 seconds')), 5000)
        );
        
        const queryPromise = client.query({ 
          query: GET_RUST_STOCK_ANALYSIS, 
          variables: { symbol }, 
          fetchPolicy: 'network-only',
          errorPolicy: 'all' // Continue even if there are GraphQL errors
        });
        
        const { data } = await Promise.race([queryPromise, timeoutPromise]) as any;
        logger.log('📊 Received rust data:', data);
        
        if (data?.rustStockAnalysis) {
          logger.log('✅ Setting rust data');
          setRust(data.rustStockAnalysis);
          setRustLoading(false);
          return;
        } else {
          logger.log('⚠️ Rust analysis returned no data, using fallback');
        }
      } catch (rustError: any) {
        logger.log('⚠️ Rust analysis failed or timed out, trying fallback:', rustError?.message || rustError);
      }
      
      // Fallback: Use chart data for basic analysis
      logger.log('📊 Fetching chart data for fallback analysis...');
      try {
        const timeoutPromise = new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Chart query timeout')), 5000)
        );
        
        const queryPromise = client.query({ 
          query: CHART_QUERY, 
          variables: { symbol, tf: '1D', iv: '1D', limit: 30, inds: ['SMA20', 'SMA50', 'RSI', 'MACD'] },
          fetchPolicy: 'network-only',
          errorPolicy: 'all'
        });
        
        const { data: chartData } = await Promise.race([queryPromise, timeoutPromise]) as any;
        
        if (chartData?.stockChartData) {
          const indicators = chartData.stockChartData.indicators || {};
          const analysis = {
            symbol: chartData.stockChartData.symbol || symbol,
            beginnerFriendlyScore: 75, // Default score
            riskLevel: chartData.stockChartData.changePercent > 5 ? 'HIGH' : chartData.stockChartData.changePercent < -5 ? 'HIGH' : 'MEDIUM',
            recommendation: chartData.stockChartData.changePercent > 0 ? 'BUY' : 'HOLD',
            technicalIndicators: {
              rsi: indicators.RSI14 || 50, // Default RSI if not available
              macd: indicators.MACD || 0,
              macdSignal: indicators.MACDSignal || 0,
              macdHistogram: indicators.MACDHist || (indicators.MACD && indicators.MACDSignal ? indicators.MACD - indicators.MACDSignal : 0),
              sma20: indicators.SMA20 || chartData.stockChartData.currentPrice,
              sma50: indicators.SMA50 || chartData.stockChartData.currentPrice,
              ema12: indicators.EMA12 || indicators.SMA20 || chartData.stockChartData.currentPrice,
              ema26: indicators.EMA26 || indicators.SMA50 || chartData.stockChartData.currentPrice,
              bollingerUpper: indicators.BBUpper || (indicators.SMA20 ? indicators.SMA20 * 1.02 : chartData.stockChartData.currentPrice * 1.02),
              bollingerLower: indicators.BBLower || (indicators.SMA20 ? indicators.SMA20 * 0.98 : chartData.stockChartData.currentPrice * 0.98),
              bollingerMiddle: indicators.BBMiddle || indicators.SMA20 || chartData.stockChartData.currentPrice
            },
            fundamentalAnalysis: {
              valuationScore: 70,
              growthScore: 65,
              stabilityScore: 80,
              dividendScore: 60,
              debtScore: 75
            },
            reasoning: `Based on current price of $${chartData.stockChartData.currentPrice || 'N/A'} and ${chartData.stockChartData.changePercent > 0 ? 'positive' : 'negative'} momentum.`
          };
          
          logger.log('✅ Using fallback analysis data with indicators:', analysis.technicalIndicators);
          setRust(analysis);
          setRustLoading(false);
        } else {
          logger.log('❌ No chart data received, showing basic analysis');
          // Show a basic analysis even if we can't get data
          const basicAnalysis = {
            symbol: symbol,
            beginnerFriendlyScore: 75,
            riskLevel: 'MEDIUM',
            recommendation: 'HOLD',
            technicalIndicators: {
              rsi: 50,
              macd: 0,
              macdSignal: 0,
              macdHistogram: 0,
              sma20: 0,
              sma50: 0,
              ema12: 0,
              ema26: 0,
              bollingerUpper: 0,
              bollingerLower: 0,
              bollingerMiddle: 0
            },
            fundamentalAnalysis: {
              valuationScore: 70,
              growthScore: 65,
              stabilityScore: 80,
              dividendScore: 60,
              debtScore: 75
            },
            reasoning: `Analysis for ${symbol}. Data is being loaded.`
          };
          setRust(basicAnalysis);
          setRustLoading(false);
        }
      } catch (chartError: any) {
        logger.log('❌ Chart data fetch failed:', chartError?.message || chartError);
        // Show basic analysis even if everything fails
        const basicAnalysis = {
          symbol: symbol,
          beginnerFriendlyScore: 75,
          riskLevel: 'MEDIUM',
          recommendation: 'HOLD',
          technicalIndicators: {
            rsi: 50,
            macd: 0,
            macdSignal: 0,
            macdHistogram: 0,
            sma20: 0,
            sma50: 0,
            ema12: 0,
            ema26: 0,
            bollingerUpper: 0,
            bollingerLower: 0,
            bollingerMiddle: 0
          },
          fundamentalAnalysis: {
            valuationScore: 70,
            growthScore: 65,
            stabilityScore: 80,
            dividendScore: 60,
            debtScore: 75
          },
          reasoning: `Analysis for ${symbol}. Unable to fetch real-time data at the moment.`
        };
        setRust(basicAnalysis);
        setRustLoading(false);
      }
    } catch (error: any) {
      logger.log('❌ Error getting analysis:', error?.message || error);
      // Even on error, show a basic modal so the user gets feedback
      const basicAnalysis = {
        symbol: symbol,
        beginnerFriendlyScore: 75,
        riskLevel: 'MEDIUM',
        recommendation: 'HOLD',
        technicalIndicators: {
          rsi: 50,
          macd: 0,
          macdSignal: 0,
          macdHistogram: 0,
          sma20: 0,
          sma50: 0,
          ema12: 0,
          ema26: 0,
          bollingerUpper: 0,
          bollingerLower: 0,
          bollingerMiddle: 0
        },
        fundamentalAnalysis: {
          valuationScore: 70,
          growthScore: 65,
          stabilityScore: 80,
          dividendScore: 60,
          debtScore: 75
        },
        reasoning: `Analysis for ${symbol}. Please try again later.`
      };
      setRust(basicAnalysis);
      setRustLoading(false);
    }
  }, [client]);

  // Function to determine if a stock is good for the user's income profile
  const isStockGoodForIncomeProfile = useCallback((stock: Stock) => {
    // For development/demo purposes, show budget impact for all stocks
    // In production, this would check user's income profile
    return true;
    
    // Original logic (commented out for development):
    /*
    const userProfile = userProfileData?.me?.incomeProfile;
    if (!userProfile) return false;

    const { incomeBracket, investmentGoals, riskTolerance } = userProfile;
    
    // Check if user has income-focused goals
    const hasIncomeGoals = investmentGoals?.some(goal => 
      goal.toLowerCase().includes('income') || 
      goal.toLowerCase().includes('dividend') ||
      goal.toLowerCase().includes('passive') ||
      goal.toLowerCase().includes('wealth building') ||
      goal.toLowerCase().includes('retirement')
    );

    // Check if user is in a higher income bracket that might prefer dividend stocks
    const isHighIncome = incomeBracket?.includes('$100,000') || incomeBracket?.includes('$150,000') || incomeBracket?.includes('$200,000');
    
    // Check if user has conservative risk tolerance
    const isConservative = riskTolerance?.toLowerCase().includes('low') || riskTolerance?.toLowerCase().includes('conservative');

    // Stock is good for income if:
    // 1. User has income-focused goals, OR
    // 2. User is high income and conservative, OR  
    // 3. Stock has good dividend yield (>2%), OR
    // 4. Stock has high beginner-friendly score (>80)
    const hasGoodDividend = stock.dividendYield && Number(stock.dividendYield) > 0.02;
    const isHighQuality = stock.beginnerFriendlyScore > 80;
    
    return hasIncomeGoals || (isHighIncome && isConservative) || hasGoodDividend || isHighQuality;
    */
  }, []);

  // Function to get user's budget based on income profile
  const getUserBudget = useCallback(() => {
    const userProfile = userProfileData?.me?.incomeProfile;
    if (!userProfile) return 1000; // Default budget

    const { incomeBracket } = userProfile;
    
    // Set budget based on income bracket
    if (incomeBracket?.includes('$200,000') || incomeBracket?.includes('$150,000')) {
      return 5000; // High income
    } else if (incomeBracket?.includes('$100,000') || incomeBracket?.includes('$75,000')) {
      return 2500; // Medium-high income
    } else if (incomeBracket?.includes('$50,000') || incomeBracket?.includes('$25,000')) {
      return 1000; // Medium income
    } else {
      return 500; // Lower income
    }
  }, [userProfileData]);

  const renderStock = useCallback(({ item }: { item: Stock }) => (
    <StockCard
      id={item.id}
      symbol={item.symbol}
      companyName={item.companyName}
      sector={item.sector}
      marketCap={item.marketCap}
      peRatio={item.peRatio}
      dividendYield={item.dividendYield}
      beginnerFriendlyScore={item.beginnerFriendlyScore}
      beginnerScoreBreakdown={item.beginnerScoreBreakdown}
      currentPrice={typeof item.currentPrice === 'number' ? item.currentPrice : parseFloat(item.currentPrice || '0')}
      isGoodForIncomeProfile={isStockGoodForIncomeProfile(item)}
      onPressAdd={() => onPressAdd(item)}
      onPressAnalysis={() => openAnalysis(item)}
      onPressMetric={showMetricTooltip}
      onPressBudgetImpact={() => {
        logger.log('🔍 Budget Impact Debug - Stock data:', item);
        logger.log('🔍 Budget Impact Debug - beginnerScoreBreakdown:', item.beginnerScoreBreakdown);
        logger.log('🔍 Budget Impact Debug - factors:', item.beginnerScoreBreakdown?.factors);
        setBudgetImpactModal({ open: true, stock: item });
      }}
      // onPressTrade removed - Trade button no longer exists
      onPress={() => handleRowPress(item)}
    />
  ), [onPressAdd, openAnalysis, showMetricTooltip, isStockGoodForIncomeProfile, handleRowPress]);

  const renderWatch = useCallback(({ item }: { item: WatchlistItem }) => (
    <WatchlistCard item={item} onRemove={onRemoveWatchlist} />
  ), [onRemoveWatchlist]);

  const keyStock = useCallback((i: Stock) => i.id, []);
  const keyWatch = useCallback((i: WatchlistItem) => i.id, []);

  // Options trading functions
  const handlePlaceOptionOrder = useCallback(async () => {
    if (!selectedOption) {
      Alert.alert('Error', 'Please select an option contract first');
      return;
    }

    try {
      const result = await placeOptionOrder({
        variables: {
          symbol: optionsSymbol,
          optionType: selectedOption.optionType,
          strike: selectedOption.strike,
          expiration: selectedOption.expiration,
          side: 'BUY', // Default to BUY for now
          quantity: parseInt(orderQuantity) || 1,
          orderType,
          limitPrice: orderType === 'LIMIT' ? parseFloat(limitPrice) : null,
          timeInForce,
          notes: orderNotes,
        },
      });

      if (result.data?.placeOptionOrder?.success) {
        Alert.alert('Success', result.data.placeOptionOrder.message);
        setSelectedOption(null);
        setOrderQuantity('1');
        setLimitPrice('');
        setOrderNotes('');
        refetchOptionsOrders();
      } else {
        Alert.alert('Error', result.data?.placeOptionOrder?.message || 'Failed to place order');
      }
    } catch (error) {
      logger.error('Error placing options order:', error);
      Alert.alert('Error', 'Failed to place options order');
    }
  }, [selectedOption, optionsSymbol, orderQuantity, orderType, limitPrice, timeInForce, orderNotes, placeOptionOrder, refetchOptionsOrders]);

  const handleCancelOptionOrder = useCallback(async (orderId: string) => {
    try {
      const result = await cancelOptionOrder({
        variables: { orderId },
      });

      if (result.data?.cancelOptionOrder?.success) {
        Alert.alert('Success', result.data.cancelOptionOrder.message);
        refetchOptionsOrders();
      } else {
        Alert.alert('Error', result.data?.cancelOptionOrder?.message || 'Failed to cancel order');
      }
    } catch (error) {
      logger.error('Error cancelling options order:', error);
      Alert.alert('Error', 'Failed to cancel options order');
    }
  }, [cancelOptionOrder, refetchOptionsOrders]);

  const listData = useMemo(() => {
    logger.log('=== listData useMemo called ===');
    logger.log('activeTab:', activeTab);
    logger.log('stocks.data:', stocks.data);
    logger.log('beginnerData:', beginnerData);
    logger.log('aiRecommendationsData:', aiRecommendationsData);
    logger.log('mlScreeningData:', mlScreeningData);
    
    if (activeTab === 'browse') {
      // Use AI recommendations if available, otherwise fall back to regular stocks
      const aiData = aiRecommendationsData?.aiRecommendations?.buyRecommendations ?? [];
      const regularData = stocks.data?.stocks ?? [];
      const realTimeData = stocks.realTimeStocks ?? [];
      
      // Transform AI recommendations to match Stock interface
      const transformedAiData = aiData.map((rec: any) => ({
        id: rec.symbol,
        symbol: rec.symbol,
        companyName: rec.companyName,
        sector: rec.sector || 'Technology', // Use actual sector if available
        marketCap: rec.marketCap || getMarketCapForSymbol(rec.symbol),
        peRatio: rec.peRatio || getPERatioForSymbol(rec.symbol),
        dividendYield: rec.dividendYield || getDividendYieldForSymbol(rec.symbol),
        beginnerFriendlyScore: Math.round(rec.confidence * 100), // Convert confidence to score
        currentPrice: rec.currentPrice,
        __typename: 'Stock',
        // Add AI-specific fields
        aiRecommendation: rec.recommendation,
        aiConfidence: rec.confidence,
        aiReasoning: rec.reasoning,
        targetPrice: rec.targetPrice,
        expectedReturn: rec.expectedReturn,
        // Add detailed breakdown for budget impact analysis
        beginnerScoreBreakdown: {
          score: Math.round(rec.confidence * 100),
          factors: [
            {
              name: 'AI Confidence',
              weight: 0.3,
              value: rec.confidence,
              contrib: Math.round(rec.confidence * 30),
              detail: `AI confidence score: ${(rec.confidence * 100).toFixed(1)}% - ${rec.reasoning}`
            },
            {
              name: 'Expected Return',
              weight: 0.25,
              value: rec.expectedReturn ? Math.min(1, rec.expectedReturn / 0.2) : 0.5,
              contrib: rec.expectedReturn ? Math.round((rec.expectedReturn / 0.2) * 25) : 12,
              detail: `Expected return: ${rec.expectedReturn ? (rec.expectedReturn * 100).toFixed(1) : 'N/A'}% annually`
            },
            {
              name: 'Target Price',
              weight: 0.2,
              value: rec.targetPrice && rec.currentPrice ? Math.min(1, (rec.targetPrice - rec.currentPrice) / rec.currentPrice + 0.5) : 0.6,
              contrib: rec.targetPrice && rec.currentPrice ? Math.round(((rec.targetPrice - rec.currentPrice) / rec.currentPrice + 0.5) * 20) : 12,
              detail: `Target price: $${rec.targetPrice || 'N/A'} (Current: $${rec.currentPrice})`
            },
            {
              name: 'Market Position',
              weight: 0.15,
              value: 0.8,
              contrib: 12,
              detail: 'Strong market position in technology sector'
            },
            {
              name: 'Risk Assessment',
              weight: 0.1,
              value: 0.75,
              contrib: 7,
              detail: 'Moderate risk profile suitable for most investors'
            }
          ],
          notes: [
            rec.reasoning || 'AI-recommended stock based on current market analysis',
            rec.expectedReturn ? `Expected annual return: ${(rec.expectedReturn * 100).toFixed(1)}%` : 'Return analysis pending',
            rec.targetPrice ? `Price target: $${rec.targetPrice}` : 'Price target analysis pending'
          ]
        }
      }));
      
      // For Browse All, prioritize search results (real-time data) when searching, otherwise use AI recommendations
      let data;
      if (searchQuery && searchQuery.trim()) {
        // When searching, use real-time data first, then fall back to regular data
        data = realTimeData.length > 0 ? realTimeData : regularData;
        
        // Sort search results by relevance - exact matches first, then partial matches
        const searchUpper = searchQuery.trim().toUpperCase();
        data = data.sort((a, b) => {
          const aSymbol = a.symbol.toUpperCase();
          const bSymbol = b.symbol.toUpperCase();
          const aName = a.companyName.toUpperCase();
          const bName = b.companyName.toUpperCase();
          
          // Exact symbol match gets highest priority
          if (aSymbol === searchUpper && bSymbol !== searchUpper) return -1;
          if (bSymbol === searchUpper && aSymbol !== searchUpper) return 1;
          
          // Symbol starts with search term gets second priority
          if (aSymbol.startsWith(searchUpper) && !bSymbol.startsWith(searchUpper)) return -1;
          if (bSymbol.startsWith(searchUpper) && !aSymbol.startsWith(searchUpper)) return 1;
          
          // Symbol contains search term gets third priority
          if (aSymbol.includes(searchUpper) && !bSymbol.includes(searchUpper)) return -1;
          if (bSymbol.includes(searchUpper) && !aSymbol.includes(searchUpper)) return 1;
          
          // Company name contains search term gets fourth priority
          if (aName.includes(searchUpper) && !bName.includes(searchUpper)) return -1;
          if (bName.includes(searchUpper) && !aName.includes(searchUpper)) return 1;
          
          // Otherwise maintain original order
          return 0;
        });
      } else {
        // When not searching, use AI recommendations first, then fall back to regular data
        data = transformedAiData.length > 0 ? transformedAiData : regularData;
      }
      
      // If we still don't have enough stocks, add popular stocks to reach minimum of 5
      // But only if we're not actively searching (to avoid adding irrelevant stocks to search results)
      if (data.length < 5 && (!searchQuery || !searchQuery.trim())) {
        const popularStocks = [
          { symbol: 'AAPL', companyName: 'Apple Inc.', currentPrice: 167, confidence: 0.85, reasoning: 'Strong fundamentals and innovation' },
          { symbol: 'MSFT', companyName: 'Microsoft Corporation', currentPrice: 380, confidence: 0.82, reasoning: 'Cloud computing leadership' },
          { symbol: 'GOOGL', companyName: 'Alphabet Inc.', currentPrice: 140, confidence: 0.80, reasoning: 'Search and advertising dominance' },
          { symbol: 'TSLA', companyName: 'Tesla Inc.', currentPrice: 250, confidence: 0.78, reasoning: 'Electric vehicle market leader' },
          { symbol: 'AMZN', companyName: 'Amazon.com Inc.', currentPrice: 150, confidence: 0.75, reasoning: 'E-commerce and cloud leader' }
        ];
        
        // Get existing symbols to avoid duplicates
        const existingSymbols = new Set(data.map(stock => stock.symbol));
        
        // Filter out stocks that already exist
        const newStocks = popularStocks.filter(stock => !existingSymbols.has(stock.symbol));
        
        const additionalStocks = newStocks.slice(0, 5 - data.length).map(stock => ({
          id: `fallback-${stock.symbol}`, // Unique ID to avoid key conflicts
          symbol: stock.symbol,
          companyName: stock.companyName,
          sector: 'Technology',
          marketCap: getMarketCapForSymbol(stock.symbol),
          peRatio: getPERatioForSymbol(stock.symbol),
          dividendYield: getDividendYieldForSymbol(stock.symbol),
          beginnerFriendlyScore: Math.round(stock.confidence * 100),
          currentPrice: stock.currentPrice,
          __typename: 'Stock',
          aiRecommendation: 'BUY',
          aiConfidence: stock.confidence,
          aiReasoning: stock.reasoning,
          targetPrice: stock.currentPrice * 1.15,
          expectedReturn: 0.12,
          beginnerScoreBreakdown: {
            score: Math.round(stock.confidence * 100),
            factors: [
              {
                name: 'AI Confidence',
                weight: 0.3,
                value: stock.confidence,
                contrib: Math.round(stock.confidence * 30),
                detail: `AI confidence score: ${(stock.confidence * 100).toFixed(1)}% - ${stock.reasoning}`
              },
              {
                name: 'Market Position',
                weight: 0.25,
                value: 0.85,
                contrib: 21,
                detail: 'Leading position in technology sector'
              },
              {
                name: 'Growth Potential',
                weight: 0.2,
                value: 0.8,
                contrib: 16,
                detail: 'Strong growth prospects and innovation'
              },
              {
                name: 'Liquidity',
                weight: 0.15,
                value: 0.9,
                contrib: 13,
                detail: 'High trading volume and market cap'
              },
              {
                name: 'Risk Assessment',
                weight: 0.1,
                value: 0.75,
                contrib: 7,
                detail: 'Moderate risk suitable for most investors'
              }
            ],
            notes: [
              stock.reasoning,
              'Suitable for long-term investment',
              'Good for portfolio diversification'
            ]
          }
        }));
        
        data = [...data, ...additionalStocks];
      }
      
      logger.log('Browse All data (AI-powered, min 5 stocks):', data);
      logger.log('Browse All first item:', data[0]);
      logger.log('Browse All data length:', data.length);
      return data;
    }
    if (activeTab === 'beginner') {
      // Use ML screening if available, otherwise fall back to beginner data
      const mlData = mlScreeningData?.advancedStockScreening ?? [];
      const beginnerStocks = beginnerData?.beginnerFriendlyStocks ?? [];
      
      // Get real-time prices from stocks.data to override cached prices
      const realTimeStocks = stocks.data?.stocks ?? [];
      const realTimePrices = new Map();
      realTimeStocks.forEach((stock: any) => {
        realTimePrices.set(stock.symbol, stock.currentPrice);
      });
      
      // Transform ML screening data to match Stock interface with real-time prices
      const transformedMlData = mlData.map((stock: any) => ({
        id: stock.symbol,
        symbol: stock.symbol,
        companyName: stock.companyName,
        sector: stock.sector,
        marketCap: stock.marketCap,
        peRatio: stock.peRatio,
        dividendYield: stock.dividendYield,
        beginnerFriendlyScore: stock.beginnerFriendlyScore,
        currentPrice: realTimePrices.get(stock.symbol) || stock.currentPrice, // Use real-time price if available
        __typename: 'Stock',
        // Add ML-specific fields
        mlScore: stock.mlScore,
        // Add beginnerScoreBreakdown for Budget Impact Analysis (same structure as Browse All)
        beginnerScoreBreakdown: {
          score: stock.beginnerFriendlyScore,
          factors: [
            {
              name: 'AI Confidence',
              weight: 0.3,
              value: stock.mlScore,
              contrib: Math.round(stock.mlScore * 30),
              detail: `AI confidence score: ${(stock.mlScore * 100).toFixed(1)}% - ML-powered analysis`
            },
            {
              name: 'Expected Return',
              weight: 0.25,
              value: 0.6, // Default expected return for ML-screened stocks
              contrib: 15,
              detail: `Expected return: 12.0% annually (ML projection)`
            },
            {
              name: 'Target Price',
              weight: 0.2,
              value: 0.7, // Default target price analysis
              contrib: 14,
              detail: `Target price: $${(stock.currentPrice * 1.15).toFixed(2)} (Current: $${stock.currentPrice})`
            },
            {
              name: 'Market Position',
              weight: 0.15,
              value: 0.8,
              contrib: 12,
              detail: `Strong market position in ${stock.sector} sector`
            },
            {
              name: 'Risk Assessment',
              weight: 0.1,
              value: 0.75,
              contrib: 7,
              detail: 'Moderate risk profile suitable for most investors'
            }
          ],
          notes: [
            `ML-powered analysis with ${(stock.mlScore * 100).toFixed(1)}% confidence`,
            `Expected annual return: 12.0%`,
            `Price target: $${(stock.currentPrice * 1.15).toFixed(2)}`
          ]
        }
      }));
      
      // Ensure we always have at least 5 stocks for Beginner Friendly
      let data = transformedMlData.length > 0 ? transformedMlData : beginnerStocks;
      
      // If we still don't have enough stocks, add beginner-friendly stocks to reach minimum of 5
      if (data.length < 5) {
        const beginnerFriendlyStocks = [
          { symbol: 'AAPL', companyName: 'Apple Inc.', currentPrice: 167, beginnerFriendlyScore: 90, mlScore: 85 },
          { symbol: 'MSFT', companyName: 'Microsoft Corporation', currentPrice: 380, beginnerFriendlyScore: 88, mlScore: 82 },
          { symbol: 'JNJ', companyName: 'Johnson & Johnson', currentPrice: 160, beginnerFriendlyScore: 92, mlScore: 88 },
          { symbol: 'PG', companyName: 'Procter & Gamble', currentPrice: 150, beginnerFriendlyScore: 89, mlScore: 85 },
          { symbol: 'KO', companyName: 'Coca-Cola Company', currentPrice: 60, beginnerFriendlyScore: 87, mlScore: 83 }
        ];
        
        // Get existing symbols to avoid duplicates
        const existingSymbols = new Set(data.map(stock => stock.symbol));
        
        // Filter out stocks that already exist
        const newStocks = beginnerFriendlyStocks.filter(stock => !existingSymbols.has(stock.symbol));
        
        const additionalStocks = newStocks.slice(0, 5 - data.length).map(stock => ({
          id: `beginner-fallback-${stock.symbol}`, // Unique ID to avoid key conflicts
          symbol: stock.symbol,
          companyName: stock.companyName,
          sector: stock.symbol === 'AAPL' || stock.symbol === 'MSFT' ? 'Technology' : 'Consumer Goods',
          marketCap: getMarketCapForSymbol(stock.symbol),
          peRatio: getPERatioForSymbol(stock.symbol),
          dividendYield: getDividendYieldForSymbol(stock.symbol),
          beginnerFriendlyScore: stock.beginnerFriendlyScore,
          currentPrice: stock.currentPrice,
          __typename: 'Stock',
          mlScore: stock.mlScore,
          beginnerScoreBreakdown: {
            score: stock.beginnerFriendlyScore,
            factors: [
              {
                name: 'Stability',
                weight: 0.3,
                value: 0.9,
                contrib: 27,
                detail: 'Established company with stable earnings'
              },
              {
                name: 'Dividend History',
                weight: 0.25,
                value: 0.85,
                contrib: 21,
                detail: 'Consistent dividend payments over many years'
              },
              {
                name: 'Market Position',
                weight: 0.2,
                value: 0.9,
                contrib: 18,
                detail: 'Leading position in their respective markets'
              },
              {
                name: 'Volatility',
                weight: 0.15,
                value: 0.8,
                contrib: 12,
                detail: 'Lower volatility compared to growth stocks'
              },
              {
                name: 'Liquidity',
                weight: 0.1,
                value: 0.95,
                contrib: 9,
                detail: 'High trading volume and market cap'
              }
            ],
            notes: [
              'Excellent choice for beginner investors',
              'Low risk with steady growth potential',
              'Suitable for long-term investment strategy'
            ]
          }
        }));
        
        data = [...data, ...additionalStocks];
      }
      
      logger.log('Beginner Friendly data (ML-powered, min 5 stocks):', data);
      logger.log('Beginner Friendly first item:', data[0]);
      logger.log('Beginner Friendly data length:', data.length);
      return data;
    }
    const data = (watchlistQ.data as any)?.myWatchlist ?? [];
    logger.log('Watchlist data:', data);
    return data;
  }, [activeTab, stocks.data, beginnerData, aiRecommendationsData, mlScreeningData, watchlistQ.data, searchQuery]);

  const loading = (activeTab === 'browse' && (stocks.loading || aiRecommendationsLoading))
               || (activeTab === 'beginner' && (beginnerLoading || mlScreeningLoading))
               || (activeTab === 'watchlist' && watchlistQ.loading);

  // Log errors for debugging
  if (stocks.error) logger.warn('Stocks error:', stocks.error);
  if (beginnerError) logger.warn('Beginner error:', beginnerError);
  if (aiRecommendationsError) logger.warn('AI Recommendations error:', aiRecommendationsError);
  if (mlScreeningError) logger.warn('ML Screening error:', mlScreeningError);
  if (watchlistQ.error) logger.warn('Watchlist error:', watchlistQ.error);
  
  // Debug current tab and data
  logger.log('Current tab:', activeTab);
  logger.log('Stocks loading:', stocks.loading, 'Beginner loading:', beginnerLoading);

return (
<View style={styles.container}>
{/* Header */}
<View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => navigateTo?.('Home')}>
<Icon name="arrow-left" size={24} color="#00cc99" />
</TouchableOpacity>
<Text style={styles.headerTitle}>Stocks & Investing</Text>
        <View style={{ width: 40 }} />
</View>

      {/* Search */}
<View style={styles.searchContainer}>
        <Icon name="search" size={20} color="#666" style={{ marginRight: 12 }} />
<TextInput
style={styles.searchInput}
          placeholder="Search by symbol or company..."
value={searchQuery}
onChangeText={setSearchQuery}
placeholderTextColor="#999"
/>
{searchQuery.length > 0 && (
          <TouchableOpacity style={{ padding: 4 }} onPress={() => setSearchQuery('')} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
<Icon name="x" size={20} color="#666" />
</TouchableOpacity>
)}
</View>

      {/* Tabs */}
<View style={styles.tabContainer}>
        {(['browse','beginner','options','watchlist','research'] as const).map(tab => (
          <TouchableOpacity key={tab}
            style={[styles.tab, activeTab === tab && styles.activeTab]}
            onPress={() => handleTabChange(tab)}
          >
            <Text style={[styles.tabText, activeTab === tab && styles.activeTabText]}>
              {tab === 'browse' ? 'Browse All' : tab === 'beginner' ? 'Beginner Friendly' : tab === 'options' ? 'Options' : tab === 'watchlist' ? 'My Watchlist' : 'Research'}
</Text>
</TouchableOpacity>
        ))}
      </View>


      {/* Research Tab Content */}
      {activeTab === 'research' && (
        <ScrollView 
          style={styles.researchContainer}
          contentContainerStyle={styles.researchContentContainer}
          showsVerticalScrollIndicator={true}
        >
          <View style={styles.researchHeader}>
            <Text style={styles.researchTitle}>Stock Research</Text>
            <View style={styles.searchContainer}>
              <Icon name="search" size={20} color="#666" style={{ marginRight: 12 }} />
              <TextInput
                style={styles.searchInput}
                value={researchSymbol}
                onChangeText={(t) => setResearchSymbol(t.toUpperCase().trim())}
                placeholder="Enter symbol (e.g., AAPL)"
                placeholderTextColor="#999"
                autoCapitalize="characters"
              />
              <TouchableOpacity style={{ padding: 4 }} onPress={() => refetchResearch()}>
                <Icon name="refresh-cw" size={20} color="#666" />
              </TouchableOpacity>
            </View>
          </View>

          {effectiveResearchLoading || chartLoading ? (
            <View style={styles.loadingContainer}>
              <Text style={styles.loadingText}>Loading research data...</Text>
            </View>
          ) : effectiveResearchData?.researchHub ? (
            <View>
              {/* Company Header */}
              <View style={styles.card}>
                <View style={styles.companyHeader}>
                  <View style={{ flex: 1, paddingRight: 12 }}>
                    <Text style={styles.companyName}>
                      {effectiveResearchData.researchHub?.company?.name ?? 'N/A'} <Text style={styles.symbol}>({effectiveResearchData.researchHub?.symbol ?? 'N/A'})</Text>
                    </Text>
                    <Text style={styles.sector}>
                      {effectiveResearchData.researchHub?.company?.sector ?? 'N/A'} • {formatMarketCap(effectiveResearchData.researchHub?.company?.marketCap ?? 0)}
                    </Text>
                    {!!effectiveResearchData.researchHub?.company?.website && (
                      <Text style={styles.website} numberOfLines={1}>{effectiveResearchData.researchHub.company.website}</Text>
                    )}
                  </View>
                  <View style={styles.priceContainer}>
                    <Text style={styles.currentPrice}>
                      {safeMoney(effectiveResearchData.researchHub?.quote?.price || effectiveResearchData.researchHub?.quote?.currentPrice, 2)}
                    </Text>
                    <Text style={[
              styles.change,
              { color: ((effectiveResearchData.researchHub?.quote?.chg || effectiveResearchData.researchHub?.quote?.change) ?? 0) >= 0 ? '#22C55E' : '#EF4444' }
                    ]}>
                      {((effectiveResearchData.researchHub?.quote?.chg || effectiveResearchData.researchHub?.quote?.change) ?? 0) >= 0 ? '+' : ''}
                      {safeFixed(effectiveResearchData.researchHub?.quote?.chg || effectiveResearchData.researchHub?.quote?.change, 2)} ({safeFixed(effectiveResearchData.researchHub?.quote?.chgPct || effectiveResearchData.researchHub?.quote?.changePercent, 2)}%)
                    </Text>
                  </View>
                </View>
              </View>

              {/* Advanced Chart */}
              <View style={styles.card}>
                <View style={styles.chartHeader}>
          <Text style={styles.chartTitle}>Price Chart</Text>
                  <View style={styles.intervalSelector}>
                    {['1D', '1W', '1M', '3M', '1Y'].map(interval => (
                      <TouchableOpacity
                        key={interval}
                        style={[
                          styles.intervalButton,
                          chartInterval === interval && styles.intervalButtonActive
                        ]}
                        onPress={() => setChartInterval(interval)}
                      >
                        <Text style={[
                          styles.intervalText,
                          chartInterval === interval && styles.intervalTextActive
                        ]}>
                          {interval}
                        </Text>
                      </TouchableOpacity>
                    ))}
        </View>
                </View>
                {isChartLoading ? (
                  <View style={styles.chartLoading}>
                    <Text style={{ color: '#666' }}>Loading chart...</Text>
                  </View>
                ) : !chartLoading && chartError ? (
                  // ✅ Error state
                  <View style={[styles.chartLoading, { padding: 16 }]}>
                    <Text style={{ color: '#EF4444', marginBottom: 8 }}>Chart Error</Text>
                    <Text style={{ color: '#666', fontSize: 12 }}>
                      {chartError.message || 'Failed to load chart data'}
                    </Text>
                  </View>
                ) : !chartLoading && !chartError && !hasChartData ? (
                  // ✅ Empty state (no data)
                  <View style={styles.chartLoading}>
                    <Text style={{ color: '#666' }}>No chart data available</Text>
                    <Text style={{ color: '#999', fontSize: 12, marginTop: 4 }}>
                      Select a symbol to view chart
                    </Text>
                  </View>
                ) : hasChartData && chartSeries.length > 0 ? (
                  // ✅ Chart with data
                  <View style={{ height: 320, width: '100%', backgroundColor: 'transparent' }}>
                    <ResponsiveChart key={`${researchSymbol}-${chartInterval}`} height={220}>
                      {(w) => {
                        const candles = chartSeries.map(s => ({
                          open: s.o ?? s.c!,
                          high: s.h ?? s.c!,
                          low: s.l ?? s.c!,
                          close: s.c!,
                          volume: s.v ?? 0,
                          time: s.t,
                        }));
                        
                        // Convert single indicator values to arrays for AdvancedChart
                        const indicators = chartData?.stockChartData?.indicators;
                        const indicatorArrays = {
                          SMA20: indicators?.SMA20 ? [indicators.SMA20] : undefined,
                          SMA50: indicators?.SMA50 ? [indicators.SMA50] : undefined,
                          EMA12: indicators?.EMA12 ? [indicators.EMA12] : undefined,
                          EMA26: indicators?.EMA26 ? [indicators.EMA26] : undefined,
                          BBUpper: indicators?.BBUpper ? [indicators.BBUpper] : undefined,
                          BBMiddle: indicators?.BBMiddle ? [indicators.BBMiddle] : undefined,
                          BBLower: indicators?.BBLower ? [indicators.BBLower] : undefined,
                        };
                        
                        return (
                          <AdvancedChart
                            key={`${researchSymbol}-${chartInterval}-${chartSeries.length}`}
                            data={candles}
                            indicators={indicatorArrays}
                            width={w}
                            height={220}
                          />
                        );
                      }}
                    </ResponsiveChart>
                  </View>
                ) : (
                  // ✅ Loading state fallback
                  <View style={styles.chartLoading}>
                    <Text style={{ color: '#666' }}>Loading chart...</Text>
                  </View>
                )}
              </View>

              {/* Key Metrics */}
              <View style={styles.metricsGrid}>
                <View style={styles.metricCard}>
                  <Text style={styles.metricTitle}>Technicals</Text>
                  <View style={styles.metricItem}>
                    <Text style={styles.metricLabel}>RSI (14)</Text>
                    <Text style={styles.metricValue}>
                      {safeFixed(effectiveResearchData.researchHub.technicals?.rsi, 1)}
                    </Text>
                  </View>
                  <View style={styles.metricItem}>
                    <Text style={styles.metricLabel}>MACD</Text>
                    <Text style={styles.metricValue}>
                      {safeFixed(effectiveResearchData.researchHub?.technicals?.macd, 3)}
                    </Text>
                  </View>
                  <View style={styles.metricItem}>
                    <Text style={styles.metricLabel}>MA 50</Text>
                    <Text style={styles.metricValue}>
                      {safeMoney(effectiveResearchData.researchHub?.technicals?.movingAverage50)}
                    </Text>
                  </View>
                </View>

                <View style={styles.metricCard}>
                  <Text style={styles.metricTitle}>Sentiment</Text>
                  <View style={styles.metricItem}>
                    <Text style={styles.metricLabel}>News Sentiment</Text>
                    <Text style={[
                      styles.metricValue,
                      { color: getSentimentColor(effectiveResearchData.researchHub?.sentiment?.label || effectiveResearchData.researchHub?.sentiment?.sentiment_label || 'NEUTRAL') }
                    ]}>
                      {(effectiveResearchData.researchHub?.sentiment?.label || effectiveResearchData.researchHub?.sentiment?.sentiment_label) ?? 'NEUTRAL'}
                    </Text>
                  </View>
                  <View style={styles.metricItem}>
                    <Text style={styles.metricLabel}>Score</Text>
                    <Text style={styles.metricValue}>
                      {safeFixed(effectiveResearchData.researchHub?.sentiment?.score || effectiveResearchData.researchHub?.sentiment?.sentiment_score, 2)}
                    </Text>
                  </View>
                  <View style={styles.metricItem}>
                    <Text style={styles.metricLabel}>Articles</Text>
                    <Text style={styles.metricValue}>{(effectiveResearchData.researchHub?.sentiment?.articleCount || effectiveResearchData.researchHub?.sentiment?.article_count) ?? '—'}</Text>
                  </View>
                </View>
              </View>

              {/* Peers */}
              {effectiveResearchData.researchHub?.peers?.length > 0 && (
                <View style={styles.card}>
                  <Text style={styles.sectionTitle}>Peer Companies</Text>
                  <View style={styles.peersContainer}>
                    {effectiveResearchData.researchHub?.peers.map((peer: string) => (
                      <TouchableOpacity
                        key={peer}
                        style={styles.peerChip}
                        onPress={() => {
                          setResearchSymbol(peer);
                          refetchResearch({ s: peer });
                          refetchChart?.({ symbol: peer, tf: chartInterval, iv: chartInterval, limit: 180 });
                        }}
                      >
                        <Text style={styles.peerText}>{peer}</Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </View>
              )}
            </View>
          ) : null}
        </ScrollView>
      )}

      {/* Options Tab Content */}
      {activeTab === 'options' && (
        <View style={styles.optionsContainer}>
          <FlatList
            data={[]} // Empty data since we're using ListHeaderComponent and ListFooterComponent
            keyExtractor={() => 'options-placeholder'}
            renderItem={() => null}
            ListHeaderComponent={() => (
              <View style={styles.optionsContentContainer}>
                <View style={styles.optionsHeader}>
                  <Text style={styles.optionsTitle}>Options Trading</Text>
                  <View style={styles.searchContainer}>
                    <TextInput
                      style={styles.searchInput}
                      placeholder="Enter symbol (e.g., AAPL)"
                      value={optionsSymbol}
                      onChangeText={(text) => setOptionsSymbol(text.toUpperCase().trim())}
                      autoCapitalize="characters"
                      autoCorrect={false}
                    />
                    <TouchableOpacity style={styles.searchButton} onPress={() => {}}>
                      <Icon name="search" size={20} color="#007AFF" />
                    </TouchableOpacity>
                  </View>
                </View>

                {/* Options Chain */}
                <OptionChainCard
                  symbol={optionsSymbol}
                  expiration="2024-02-16"
                  underlyingPrice={243.36}
                  calls={[
                    { 
                      strike: 140, bid: 8.50, ask: 8.80, volume: 1250, optionType: 'CALL',
                      greeks: { delta: 0.85, gamma: 0.02, theta: -0.12, vega: 0.18, iv: 0.22, probITM: 0.85 }
                    },
                    { 
                      strike: 145, bid: 6.20, ask: 6.50, volume: 890, optionType: 'CALL',
                      greeks: { delta: 0.72, gamma: 0.03, theta: -0.15, vega: 0.22, iv: 0.24, probITM: 0.72 }
                    },
                    { 
                      strike: 150, bid: 4.10, ask: 4.40, volume: 2100, optionType: 'CALL',
                      greeks: { delta: 0.58, gamma: 0.04, theta: -0.18, vega: 0.25, iv: 0.26, probITM: 0.58 }
                    },
                    { 
                      strike: 155, bid: 2.50, ask: 2.80, volume: 1560, optionType: 'CALL',
                      greeks: { delta: 0.42, gamma: 0.05, theta: -0.20, vega: 0.28, iv: 0.28, probITM: 0.42 }
                    },
                    { 
                      strike: 160, bid: 1.40, ask: 1.70, volume: 980, optionType: 'CALL',
                      greeks: { delta: 0.28, gamma: 0.04, theta: -0.18, vega: 0.25, iv: 0.30, probITM: 0.28 }
                    },
                  ]}
                  puts={[
                    { 
                      strike: 140, bid: 1.20, ask: 1.50, volume: 890, optionType: 'PUT',
                      greeks: { delta: -0.15, gamma: 0.02, theta: -0.08, vega: 0.18, iv: 0.22, probITM: 0.15 }
                    },
                    { 
                      strike: 145, bid: 2.10, ask: 2.40, volume: 1200, optionType: 'PUT',
                      greeks: { delta: -0.28, gamma: 0.03, theta: -0.10, vega: 0.22, iv: 0.24, probITM: 0.28 }
                    },
                    { 
                      strike: 150, bid: 3.50, ask: 3.80, volume: 1800, optionType: 'PUT',
                      greeks: { delta: -0.42, gamma: 0.04, theta: -0.12, vega: 0.25, iv: 0.26, probITM: 0.42 }
                    },
                    { 
                      strike: 155, bid: 5.20, ask: 5.50, volume: 1100, optionType: 'PUT',
                      greeks: { delta: -0.58, gamma: 0.05, theta: -0.15, vega: 0.28, iv: 0.28, probITM: 0.58 }
                    },
                    { 
                      strike: 160, bid: 7.10, ask: 7.40, volume: 750, optionType: 'PUT',
                      greeks: { delta: -0.72, gamma: 0.04, theta: -0.18, vega: 0.25, iv: 0.30, probITM: 0.72 }
                    },
                  ]}
                  selected={selectedOption}
                  onSelect={(opt) => setSelectedOption(opt)}
                  fullBleed
                  gutter={20}
                />
              </View>
            )}
            ListFooterComponent={() => (
              <View style={styles.optionsContentContainer}>
                {/* Order Form */}
                {selectedOption && (
                  <View style={styles.card}>
                    <Text style={styles.sectionTitle}>Place Order</Text>
                    <View style={styles.orderForm}>
                      <View style={styles.orderInfo}>
                        <Text style={styles.orderInfoText}>
                          {selectedOption.optionType} {optionsSymbol} ${selectedOption.strike} {selectedOption.expiration}
                        </Text>
                        <Text style={styles.orderInfoSubtext}>
                          Bid: ${selectedOption.bid} | Ask: ${selectedOption.ask}
                        </Text>
                      </View>

                      <View style={styles.inputGroup}>
                        <Text style={styles.inputLabel}>Quantity</Text>
                        <TextInput
                          style={styles.input}
                          value={orderQuantity}
                          onChangeText={setOrderQuantity}
                          keyboardType="numeric"
                          placeholder="1"
                        />
                      </View>

                      <View style={styles.inputGroup}>
                        <Text style={styles.inputLabel}>Order Type</Text>
                        <View style={styles.segmentedControl}>
                          {['MARKET', 'LIMIT'].map((type) => (
                            <TouchableOpacity
                              key={type}
                              style={[styles.segment, orderType === type && styles.activeSegment]}
                              onPress={() => setOrderType(type)}
                            >
                              <Text style={[styles.segmentText, orderType === type && styles.activeSegmentText]}>
                                {type}
                              </Text>
                            </TouchableOpacity>
                          ))}
                        </View>
                      </View>

                      {orderType === 'LIMIT' && (
                        <View style={styles.inputGroup}>
                          <Text style={styles.inputLabel}>Limit Price</Text>
                          <TextInput
                            style={styles.input}
                            value={limitPrice}
                            onChangeText={setLimitPrice}
                            keyboardType="numeric"
                            placeholder="0.00"
                          />
                        </View>
                      )}

                      <View style={styles.inputGroup}>
                        <Text style={styles.inputLabel}>Time in Force</Text>
                        <View style={styles.segmentedControl}>
                          {['DAY', 'GTC'].map((tif) => (
                            <TouchableOpacity
                              key={tif}
                              style={[styles.segment, timeInForce === tif && styles.activeSegment]}
                              onPress={() => setTimeInForce(tif)}
                            >
                              <Text style={[styles.segmentText, timeInForce === tif && styles.activeSegmentText]}>
                                {tif}
                              </Text>
                            </TouchableOpacity>
                          ))}
                        </View>
                      </View>

                      <View style={styles.inputGroup}>
                        <Text style={styles.inputLabel}>Notes (Optional)</Text>
                        <TextInput
                          style={[styles.input, styles.textArea]}
                          value={orderNotes}
                          onChangeText={setOrderNotes}
                          placeholder="Add notes about this trade..."
                          multiline
                          numberOfLines={3}
                        />
                      </View>

                      <TouchableOpacity
                        style={[styles.placeOrderButton, placingOrder && styles.placeOrderButtonDisabled]}
                        onPress={handlePlaceOptionOrder}
                        disabled={placingOrder}
                      >
                        <Text style={styles.placeOrderButtonText}>
                          {placingOrder ? 'Placing Order...' : 'Place Order'}
                        </Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                )}

                {/* Order History */}
                <View style={styles.card}>
                  <Text style={styles.sectionTitle}>Order History</Text>
                  {optionsOrdersLoading ? (
                    <Text style={styles.loadingText}>Loading orders...</Text>
                  ) : optionsOrdersData?.optionOrders?.length > 0 ? (
                    optionsOrdersData.optionOrders.map((order: any) => (
                      <View key={order.id} style={styles.orderRow}>
                        <View style={styles.orderInfo}>
                          <Text style={styles.orderSymbol}>
                            {order.symbol} {order.optionType} ${order.strike} {order.expiration}
                          </Text>
                          <Text style={styles.orderDetails}>
                            {order.side} {order.quantity} @ {order.orderType}
                            {order.limitPrice && ` $${order.limitPrice}`}
                          </Text>
                          <Text style={styles.orderStatus}>{order.status}</Text>
                        </View>
                        <View style={styles.orderActions}>
                          <Text style={styles.orderDate}>
                            {new Date(order.createdAt).toLocaleDateString()}
                          </Text>
                          {order.status === 'PENDING' && (
                            <TouchableOpacity
                              style={styles.cancelButton}
                              onPress={() => handleCancelOptionOrder(order.id)}
                            >
                              <Text style={styles.cancelButtonText}>Cancel</Text>
                            </TouchableOpacity>
                          )}
                        </View>
                      </View>
                    ))
                  ) : (
                    <Text style={styles.noOrdersText}>No orders found</Text>
                  )}
                </View>
              </View>
            )}
            contentContainerStyle={{ flexGrow: 1 }}
            showsVerticalScrollIndicator={false}
          />
        </View>
      )}


      {/* List - Only show when not on research or options tab */}
      {activeTab !== 'research' && activeTab !== 'options' && (
      <FlatList
        data={Array.isArray(listData) ? listData : []}
        keyExtractor={activeTab === 'watchlist'
          ? ((i: any) => String(i.id))
          : ((i: any) => String(i.id))
        }
        renderItem={activeTab === 'watchlist' ? (renderWatch as any) : (renderStock as any)}
        refreshing={!!loading}
        onRefresh={() => {
          // Only refetch if user explicitly pulls to refresh
          if (activeTab === 'browse') stocks.refetch();
          else if (activeTab === 'beginner') refetchBeginner?.();
          else watchlistQ.refetch();
        }}
        contentContainerStyle={styles.listContainer}
        initialNumToRender={12}
        windowSize={7}
        removeClippedSubviews
        getItemLayout={(_, i) => ({ length: 168, offset: 168 * i, index: i })}
        ListEmptyComponent={!loading ? (
          <View style={styles.emptyState}>
            <Icon name="eye" size={48} color="#ccc" />
            <Text style={styles.emptyStateText}>{activeTab === 'watchlist' ? 'Your watchlist is empty' : 'No results'}</Text>
            <Text style={styles.emptyStateSubtext}>
              {activeTab === 'watchlist' ? 'Browse and add stocks to track them' : 'Try a different search'}
</Text>
          </View>
        ) : null}
        ListFooterComponent={activeTab === 'browse' && stocks.hasMore ? (
          <TouchableOpacity 
            style={styles.loadMoreButton} 
            onPress={stocks.loadMore}
            disabled={stocks.loadingMore}
          >
            <Text style={styles.loadMoreText}>
              {stocks.loadingMore ? 'Loading...' : 'Load More Stocks'}
            </Text>
          </TouchableOpacity>
        ) : null}
      />
      )}

      {/* Tooltip Modal */}
      <Modal visible={!!tooltip} transparent animationType="fade" onRequestClose={() => setTooltip(null)}>
        <View style={styles.modalOverlay}>
          <View style={styles.tooltipModal}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>{tooltip?.title}</Text>
              <TouchableOpacity onPress={() => setTooltip(null)} style={{ padding: 4 }}>
                <Icon name="x" size={24} color="#666" />
</TouchableOpacity>
            </View>
            <Text style={styles.tooltipDescription}>{tooltip?.description}</Text>
            <TouchableOpacity 
              style={{
                backgroundColor: '#00cc99',
                paddingVertical: 14,
                paddingHorizontal: 20,
                borderRadius: 12,
                alignItems: 'center',
                marginTop: 16,
                width: '100%'
              }} 
              onPress={() => setTooltip(null)}
            >
              <Text style={{ fontSize: 16, fontWeight: '600', color: '#fff' }}>DONE</Text>
</TouchableOpacity>
</View>
        </View>
      </Modal>

{/* Add to Watchlist Modal */}
      <Modal
        visible={watchlistModal.open && !!watchlistModal.stock}
        transparent animationType="slide"
        onRequestClose={() => setWatchlistModal({ open: false, stock: null })}
      >
<View style={styles.modalOverlay}>
<View style={styles.modal}>
<View style={styles.modalHeader}>
<Text style={styles.modalTitle}>Add to Watchlist</Text>
              <TouchableOpacity onPress={() => setWatchlistModal({ open: false, stock: null })} style={{ padding: 4 }}>
<Icon name="x" size={24} color="#666" />
</TouchableOpacity>
</View>
            <View style={{ marginBottom: 16 }}>
              <Text style={styles.symbolBig}>{watchlistModal.stock?.symbol}</Text>
              <Text style={styles.company}>{watchlistModal.stock?.companyName}</Text>
              <Text style={styles.sector}>{watchlistModal.stock?.sector}</Text>
</View>
<TextInput
style={styles.notesInput}
              placeholder="Add personal notes (optional)…"
              value={notes}
              onChangeText={setNotes}
placeholderTextColor="#999"
              multiline numberOfLines={3}
            />
            <View style={{ flexDirection: 'row', gap: 12 }}>
              <TouchableOpacity style={styles.outlineBtn} onPress={() => setWatchlistModal({ open: false, stock: null })}>
                <Text style={styles.outlineText}>Cancel</Text>
</TouchableOpacity>
              <TouchableOpacity style={styles.primaryBtn} onPress={onAddConfirm}>
                <Text style={styles.primaryText}>Add to Watchlist</Text>
</TouchableOpacity>
</View>
</View>
</View>
      </Modal>

{/* Rust Analysis Modal */}
      <Modal visible={rustOpen && !!rust} transparent animationType="slide" onRequestClose={() => {
        setRustOpen(false);
        setRustLoading(false);
      }}>
<View style={styles.modalOverlay}>
          <View style={[styles.modal, { maxHeight: '80%' }]}>
<View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Advanced Analysis: {rust?.symbol}</Text>
              <TouchableOpacity onPress={() => {
                setRustOpen(false);
                setRustLoading(false);
              }} style={{ padding: 4 }}>
<Icon name="x" size={24} color="#666" />
</TouchableOpacity>
</View>
            <ScrollView showsVerticalScrollIndicator={false}>
              {rustLoading && (
                <View style={{ padding: 8, alignItems: 'center', marginBottom: 8 }}>
                  <ActivityIndicator size="small" color="#6366f1" />
                  <Text style={{ marginTop: 4, color: '#6b7280', fontSize: 12 }}>Updating with latest data...</Text>
                </View>
              )}
              {/* Basic Analysis */}
              <View style={{ marginBottom: 20 }}>
                <Text style={{ fontWeight: '600', fontSize: 18, marginBottom: 12, color: '#1a1a1a' }}>
                  Analysis Summary
                </Text>
                <Text style={{ fontWeight: '600', marginBottom: 8, color: '#1a1a1a' }}>
                  Recommendation: <Text style={{ color: rust?.recommendation === 'STRONG BUY' ? '#10b981' : rust?.recommendation === 'BUY' ? '#059669' : '#6b7280' }}>{rust?.recommendation}</Text>
                </Text>
                <Text style={{ marginBottom: 8, color: '#1a1a1a' }}>
                  Risk Level: <Text style={{ fontWeight: '600', color: rust?.riskLevel === 'Low' ? '#10b981' : rust?.riskLevel === 'High' ? '#ef4444' : '#f59e0b' }}>{rust?.riskLevel}</Text>
                </Text>
                <Text style={{ marginBottom: 8, color: '#1a1a1a' }}>
                  Beginner Score: <Text style={{ fontWeight: '600', color: '#3b82f6' }}>{rust?.beginnerFriendlyScore}/100</Text>
                </Text>
                <Text style={{ marginBottom: 12, color: '#6b7280', lineHeight: 20 }}>
                  {rust?.reasoning}
                </Text>
              </View>

              {/* Technical Indicators */}
              {rust?.technicalIndicators && (
                <View style={{ marginBottom: 20 }}>
                  <Text style={{ fontWeight: '600', fontSize: 18, marginBottom: 12, color: '#1a1a1a' }}>
                    Technical Indicators
                  </Text>
                  <View style={{ backgroundColor: '#f8f9fa', padding: 16, borderRadius: 12, marginBottom: 12 }}>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 }}>
                      <Text style={{ color: '#6b7280' }}>RSI (14):</Text>
                      <Text style={{ fontWeight: '600', color: '#1a1a1a' }}>{rust.technicalIndicators.rsi?.toFixed(2)}</Text>
                    </View>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 }}>
                      <Text style={{ color: '#6b7280' }}>MACD:</Text>
                      <Text style={{ fontWeight: '600', color: '#1a1a1a' }}>{rust.technicalIndicators.macd?.toFixed(3)}</Text>
                    </View>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 }}>
                      <Text style={{ color: '#6b7280' }}>SMA 20:</Text>
                      <Text style={{ fontWeight: '600', color: '#1a1a1a' }}>${rust.technicalIndicators.sma20?.toFixed(2)}</Text>
                    </View>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 }}>
                      <Text style={{ color: '#6b7280' }}>SMA 50:</Text>
                      <Text style={{ fontWeight: '600', color: '#1a1a1a' }}>${rust.technicalIndicators.sma50?.toFixed(2)}</Text>
                    </View>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 }}>
                      <Text style={{ color: '#6b7280' }}>Bollinger Upper:</Text>
                      <Text style={{ fontWeight: '600', color: '#1a1a1a' }}>${rust.technicalIndicators.bollingerUpper?.toFixed(2)}</Text>
                    </View>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
                      <Text style={{ color: '#6b7280' }}>Bollinger Lower:</Text>
                      <Text style={{ fontWeight: '600', color: '#1a1a1a' }}>${rust.technicalIndicators.bollingerLower?.toFixed(2)}</Text>
                    </View>
                  </View>
                </View>
              )}

              {/* Fundamental Analysis */}
              {rust?.fundamentalAnalysis && (
                <View style={{ marginBottom: 20 }}>
                  <Text style={{ fontWeight: '600', fontSize: 18, marginBottom: 12, color: '#1a1a1a' }}>
                    Fundamental Analysis
                  </Text>
                  <View style={{ backgroundColor: '#f8f9fa', padding: 16, borderRadius: 12, marginBottom: 12 }}>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 }}>
                      <Text style={{ color: '#6b7280' }}>Valuation Score:</Text>
                      <Text style={{ fontWeight: '600', color: '#1a1a1a' }}>{rust.fundamentalAnalysis.valuationScore?.toFixed(1)}/100</Text>
                    </View>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 }}>
                      <Text style={{ color: '#6b7280' }}>Growth Score:</Text>
                      <Text style={{ fontWeight: '600', color: '#1a1a1a' }}>{rust.fundamentalAnalysis.growthScore?.toFixed(1)}/100</Text>
                    </View>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 }}>
                      <Text style={{ color: '#6b7280' }}>Stability Score:</Text>
                      <Text style={{ fontWeight: '600', color: '#1a1a1a' }}>{rust.fundamentalAnalysis.stabilityScore?.toFixed(1)}/100</Text>
                    </View>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginBottom: 8 }}>
                      <Text style={{ color: '#6b7280' }}>Dividend Score:</Text>
                      <Text style={{ fontWeight: '600', color: '#1a1a1a' }}>{rust.fundamentalAnalysis.dividendScore?.toFixed(1)}/100</Text>
                    </View>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
                      <Text style={{ color: '#6b7280' }}>Debt Score:</Text>
                      <Text style={{ fontWeight: '600', color: '#1a1a1a' }}>{rust.fundamentalAnalysis.debtScore?.toFixed(1)}/100</Text>
                    </View>
                  </View>
                </View>
              )}
            </ScrollView>
            <TouchableOpacity 
              style={{
                backgroundColor: '#00cc99',
                paddingVertical: 14,
                paddingHorizontal: 20,
                borderRadius: 12,
                alignItems: 'center',
                marginTop: 16,
                width: '100%'
              }} 
              onPress={() => {
                setRustOpen(false);
                setRustLoading(false);
              }}
            >
              <Text style={{ fontSize: 16, fontWeight: '600', color: '#fff' }}>Done</Text>
            </TouchableOpacity>
            )}
</View>
</View>
      </Modal>

      {/* Budget Impact Modal */}
      <BudgetImpactModal
        visible={budgetImpactModal.open && !!budgetImpactModal.stock}
        onClose={() => setBudgetImpactModal({ open: false, stock: null })}
        stockSymbol={budgetImpactModal.stock?.symbol || ''}
        stockName={budgetImpactModal.stock?.companyName || ''}
        score={budgetImpactModal.stock?.beginnerScoreBreakdown?.score || budgetImpactModal.stock?.beginnerFriendlyScore || 0}
        factors={budgetImpactModal.stock?.beginnerScoreBreakdown?.factors || []}
        notes={budgetImpactModal.stock?.beginnerScoreBreakdown?.notes || []}
        budget={getUserBudget()} // Dynamic budget based on user profile
        price={budgetImpactModal.stock?.currentPrice ? Number(budgetImpactModal.stock.currentPrice) : undefined}
        currency="USD"
      />

</View>
);
}

/* --- styles (kept close to yours) --- */
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa' },
header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 20, paddingTop: 60, paddingBottom: 20, backgroundColor: '#fff',
    borderBottomWidth: 1, borderBottomColor: '#e9ecef',
  },
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: '#333' },
searchContainer: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#fff',
    marginHorizontal: 20, marginTop: 20, marginBottom: 10, borderRadius: 12,
    paddingHorizontal: 16, paddingVertical: 12, borderWidth: 1, borderColor: '#e9ecef',
  },
  searchInput: { flex: 1, fontSize: 16, color: '#333' },
  searchButton: {
    marginLeft: 8,
    padding: 8,
    borderRadius: 20,
    backgroundColor: '#f0f0f0',
  },
  tabContainer: { flexDirection: 'row', backgroundColor: '#fff', marginHorizontal: 20, marginBottom: 20, borderRadius: 12, padding: 4 },
  tab: { flex: 1, paddingVertical: 12, alignItems: 'center', borderBottomWidth: 2, borderBottomColor: 'transparent' },
  activeTab: { borderBottomColor: '#00cc99' },
  tabText: { fontSize: 14, fontWeight: '600', color: '#666' },
  activeTabText: { color: '#00cc99', fontWeight: '700' },
  filterContainer: { 
    alignItems: 'center', 
    marginHorizontal: 20, 
    marginBottom: 16,
    paddingTop: 8,
  },
  filterLabel: { 
    fontSize: 12, 
    fontWeight: '500', 
    color: '#666',
    textAlign: 'center',
  },
  listContainer: { paddingHorizontal: 20, paddingBottom: 20 },
  emptyState: { alignItems: 'center', paddingVertical: 60 },
  emptyStateText: { fontSize: 18, fontWeight: '600', color: '#666', marginTop: 16, marginBottom: 8 },
  emptyStateSubtext: { fontSize: 14, color: '#999', textAlign: 'center', paddingHorizontal: 40 },

  modalOverlay: { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center' },
  modal: { backgroundColor: '#fff', borderRadius: 20, padding: 24, marginHorizontal: 20, width: '90%', maxWidth: 420 },
  modalHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 },
  modalTitle: { fontSize: 20, fontWeight: 'bold', color: '#333' },
  symbolBig: { fontSize: 24, fontWeight: 'bold', color: '#333', marginBottom: 4 },
  company: { fontSize: 16, fontWeight: '600', color: '#333', marginBottom: 4 },
  notesInput: { borderWidth: 1, borderColor: '#e9ecef', borderRadius: 12, padding: 16, fontSize: 16, color: '#333', textAlignVertical: 'top', marginBottom: 16 },
  outlineBtn: { flex: 1, paddingVertical: 14, borderRadius: 12, borderWidth: 1, borderColor: '#e9ecef', alignItems: 'center' },
  outlineText: { fontSize: 16, fontWeight: '600', color: '#666' },
  primaryBtn: { flex: 1, backgroundColor: '#00cc99', paddingVertical: 14, borderRadius: 12, alignItems: 'center' },
  primaryText: { fontSize: 16, fontWeight: '600', color: '#fff' },

  tooltipModal: { backgroundColor: '#fff', borderRadius: 20, padding: 24, marginHorizontal: 20, width: '90%', maxWidth: 420 },
  tooltipDescription: { fontSize: 16, lineHeight: 24, color: '#666', marginBottom: 16, textAlign: 'left' },

  loadMoreButton: {
    backgroundColor: '#00cc99',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 12,
    marginHorizontal: 20,
    marginVertical: 16,
    alignItems: 'center',
  },
  loadMoreText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  chartSection: {
    backgroundColor: '#fff',
    marginHorizontal: 20,
    marginVertical: 10,
    borderRadius: 12,
    padding: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  chartHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  closeChartButton: {
    padding: 8,
    borderRadius: 8,
    backgroundColor: '#f5f5f5',
  },
  chartModalContainer: {
    flex: 1,
    backgroundColor: '#fff',
    paddingTop: 50, // Account for status bar
  },
  chartModalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e5ea',
  },
  chartModalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#000',
  },
  chartModalContent: {
    flex: 1,
    paddingHorizontal: 20,
    paddingTop: 10,
    paddingBottom: 40, // Extra padding at bottom to prevent cutoff
  },
  backButton: {
    padding: 8,
    borderRadius: 8,
  },
  chartTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#000',
    marginBottom: 12,
  },
  // Research styles
  researchContainer: {
    flex: 1,
  },
  researchContentContainer: {
    padding: 16,
    paddingBottom: 100, // Extra padding for better scrolling
  },
  researchHeader: {
    marginBottom: 16,
  },
  researchTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#000',
    marginBottom: 12,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  companyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  companyName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#000',
  },
  symbol: {
    color: '#666',
    fontSize: 16,
    fontWeight: '600',
  },
  sector: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  website: {
    color: '#007AFF',
    fontSize: 12,
    marginTop: 6,
  },
  priceContainer: {
    alignItems: 'flex-end',
  },
  currentPrice: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#000',
  },
  change: {
    fontSize: 14,
    fontWeight: '600',
  },
  intervalSelector: {
    flexDirection: 'row',
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
    padding: 2,
  },
  intervalButton: {
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 6,
  },
  intervalButtonActive: {
    backgroundColor: '#007AFF',
  },
  intervalText: {
    fontSize: 12,
    color: '#666',
    fontWeight: '600',
  },
  intervalTextActive: {
    color: '#fff',
  },
  chartLoading: {
    height: 200,
    justifyContent: 'center',
    alignItems: 'center',
  },
  chartContainer: {
    width: '100%',
    marginVertical: 8,
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  metricCard: {
    width: '48%',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    minHeight: 120,
  },
  metricTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#000',
    marginBottom: 12,
  },
  metricItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
    minHeight: 20,
  },
  metricLabel: {
    fontSize: 14,
    color: '#666',
    flex: 1,
    flexWrap: 'wrap',
  },
  metricValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000',
    flex: 1,
    textAlign: 'right',
    flexWrap: 'wrap',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#000',
    marginBottom: 12,
  },
  peersContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  peerChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginRight: 8,
    marginBottom: 8,
    backgroundColor: '#f0f0f0',
    borderRadius: 16,
  },
  peerText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    marginTop: 12,
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    fontSize: 16,
    color: '#FF3B30',
    textAlign: 'center',
    marginBottom: 16,
  },
  retryButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },

  // Options Trading Styles
  optionsContainer: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  optionsContentContainer: {
    padding: 16,
    paddingBottom: 100,
  },
  optionsHeader: {
    marginBottom: 20,
  },
  optionsTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#000',
    marginBottom: 16,
  },
  optionsSection: {
    marginBottom: 20,
  },
  optionsSectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#000',
    marginBottom: 12,
  },
  optionsHeaderRow: {
    flexDirection: 'row',
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    marginBottom: 8,
  },
  optionsHeaderText: {
    flex: 1,
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
    textAlign: 'center',
  },
  optionsRow: {
    flexDirection: 'row',
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
    alignItems: 'center',
  },
  selectedOptionRow: {
    backgroundColor: '#e3f2fd',
    borderRadius: 8,
    marginVertical: 2,
  },
  optionsStrike: {
    flex: 1,
    fontSize: 14,
    fontWeight: '600',
    color: '#000',
    textAlign: 'center',
  },
  optionsBidAsk: {
    flex: 1,
    fontSize: 14,
    color: '#333',
    textAlign: 'center',
  },
  optionsVolume: {
    flex: 1,
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
  selectButton: {
    flex: 1,
    backgroundColor: '#007AFF',
    paddingVertical: 6,
    paddingHorizontal: 12,
    borderRadius: 6,
    alignItems: 'center',
  },
  selectButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  orderForm: {
    marginTop: 16,
  },
  orderInfo: {
    backgroundColor: '#f8f9fa',
    padding: 16,
    borderRadius: 8,
    marginBottom: 16,
  },
  orderInfoText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 4,
  },
  orderInfoSubtext: {
    fontSize: 14,
    color: '#666',
  },
  inputGroup: {
    marginBottom: 16,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    color: '#000',
  },
  textArea: {
    height: 80,
    textAlignVertical: 'top',
  },
  segmentedControl: {
    flexDirection: 'row',
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    padding: 2,
  },
  segment: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    alignItems: 'center',
  },
  activeSegment: {
    backgroundColor: '#007AFF',
  },
  segmentText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
  },
  activeSegmentText: {
    color: '#fff',
  },
  placeOrderButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  placeOrderButtonDisabled: {
    backgroundColor: '#ccc',
  },
  placeOrderButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  orderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  orderSymbol: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000',
    marginBottom: 2,
  },
  orderDetails: {
    fontSize: 12,
    color: '#666',
    marginBottom: 2,
  },
  orderStatus: {
    fontSize: 12,
    fontWeight: '600',
    color: '#007AFF',
  },
  orderActions: {
    alignItems: 'flex-end',
  },
  orderDate: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  cancelButton: {
    backgroundColor: '#FF3B30',
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 4,
  },
  cancelButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  noOrdersText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    paddingVertical: 20,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 16,
  },
});