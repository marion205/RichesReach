import React, { useCallback, useMemo, useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, FlatList, TextInput, Alert, Modal, ScrollView, Dimensions,
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
import { useWatchlist } from '../../../shared/hooks/useWatchlist';
import { UI } from '../../../shared/constants';

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

const formatMarketCap = (cap: number) => {
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

export default function StockScreen({ navigateTo }: { navigateTo: (s: string, d?: any) => void }) {
const [activeTab, setActiveTab] = useState<'browse' | 'beginner' | 'watchlist' | 'research' | 'options'>('browse');
const [searchQuery, setSearchQuery] = useState('');
  const [tooltip, setTooltip] = useState<{ title: string; description: string } | null>(null);
  const [watchlistModal, setWatchlistModal] = useState<{ open: boolean; stock: Stock | null }>({ open: false, stock: null });
  const [notes, setNotes] = useState('');
  const [rust, setRust] = useState<any | null>(null);
  const [rustOpen, setRustOpen] = useState(false);
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
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
  
  // Watchlist mutations
  const [addToWatchlistMutation] = useMutation(ADD_TO_WATCHLIST);
  const [removeFromWatchlistMutation] = useMutation(REMOVE_FROM_WATCHLIST);
  const { data: beginnerData, loading: beginnerLoading, refetch: refetchBeginner, error: beginnerError } =
    useQuery(GET_BEGINNER_FRIENDLY_STOCKS_ALT, { 
      fetchPolicy: 'network-only', 
      errorPolicy: 'all',
      notifyOnNetworkStatusChange: true,
      skip: activeTab !== 'beginner' // Only run when beginner tab is active
    });

  // Research queries
  const { data: researchData, loading: researchLoading, error: researchError, refetch: refetchResearch } = useQuery(RESEARCH_QUERY, {
    variables: { s: researchSymbol },
    skip: activeTab !== 'research' || !researchSymbol,
  });

  const { data: chartData, loading: chartLoading, error: chartError, refetch: refetchChart } = useQuery(CHART_QUERY, {
    variables: {
      symbol: researchSymbol,
      tf: chartInterval,
      iv: chartInterval,
      limit: 180,
      inds: ["SMA20","SMA50","EMA12","EMA26","RSI","MACD","MACDHist","BB"],
    },
    skip: activeTab !== 'research' || !researchSymbol,
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
    skip: activeTab !== 'options',
    fetchPolicy: 'cache-and-network',
    });

  // Debug query state changes
  React.useEffect(() => {
    console.log('=== Query State Debug ===');
    console.log('stocks.loading:', stocks.loading);
    console.log('stocks.data:', stocks.data);
    console.log('stocks.error:', stocks.error);
    console.log('activeTab:', activeTab);
    console.log('searchQuery:', searchQuery);
  }, [stocks.loading, stocks.data, stocks.error, activeTab, searchQuery]);

  const { list: watchlistQ, addToWatchlist, removeFromWatchlist } = useWatchlist();

  // Note: Removed automatic refetch on tab change to prevent infinite loop
  // Data will be refetched when user manually switches tabs via handleTabChange
  
  const handleTabChange = useCallback((tab: 'browse' | 'beginner' | 'watchlist' | 'research' | 'options') => {
    console.log('Switching to tab:', tab);
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
    
    try {
      const { data } = await addToWatchlistMutation({
        variables: {
          symbol: watchlistModal.stock.symbol,
          companyName: watchlistModal.stock.companyName,
          notes: notes
        }
      });
      
      if (data?.addToWatchlist?.success) {
        Alert.alert('Success', data.addToWatchlist.message);
        setWatchlistModal({ open: false, stock: null });
        setNotes('');
        // Refresh watchlist data
        if (watchlistQ?.refetch) {
          watchlistQ.refetch();
        }
      } else {
        Alert.alert('Error', data?.addToWatchlist?.message || 'Failed to add to watchlist');
      }
    } catch (error) {
      console.error('Error adding to watchlist:', error);
      Alert.alert('Error', 'Failed to add to watchlist. Please try again.');
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
          console.error('Error removing from watchlist:', error);
          Alert.alert('Error', 'Failed to remove from watchlist. Please try again.');
        }
      }},
    ]);
  }, [removeFromWatchlistMutation, watchlistQ]);

  const handleRustAnalysis = useCallback(async (symbol: string) => {
    console.log('🔍 Starting Advanced Analysis for:', symbol);
    try {
      console.log('📡 Making GraphQL query...');
      const { data } = await client.query({ query: GET_RUST_STOCK_ANALYSIS, variables: { symbol }, fetchPolicy: 'network-only' });
      console.log('📊 Received data:', data);
      
      if (data?.rustStockAnalysis) {
        console.log('✅ Setting rust data and opening modal');
        setRust(data.rustStockAnalysis);
        setRustOpen(true);
      } else {
        console.log('❌ No analysis data received');
        Alert.alert('Analysis Unavailable', 'No analysis for this symbol right now.');
      }
    } catch (error) {
      console.log('❌ Error getting analysis:', error);
      Alert.alert('Analysis Error', 'Failed to get advanced analysis.');
    }
  }, [client]);

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
      onPressAdd={() => onPressAdd(item)}
      onPressAnalysis={() => handleRustAnalysis(item.symbol)}
      onPressMetric={showMetricTooltip}
      onPressBudgetImpact={() => setBudgetImpactModal({ open: true, stock: item })}
      onPress={() => setSelectedStock(selectedStock?.symbol === item.symbol ? null : item)}
      isSelected={selectedStock?.symbol === item.symbol}
    />
  ), [onPressAdd, handleRustAnalysis, showMetricTooltip, selectedStock]);

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
      console.error('Error placing options order:', error);
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
      console.error('Error cancelling options order:', error);
      Alert.alert('Error', 'Failed to cancel options order');
    }
  }, [cancelOptionOrder, refetchOptionsOrders]);

  // Mock data for development/screenshots
  const mockStocks = [
    {
      id: "1",
      symbol: "AAPL",
      companyName: "Apple Inc.",
      sector: "Technology",
      marketCap: 3000000000000,
      peRatio: 28.5,
      dividendYield: 0.44,
      beginnerFriendlyScore: 0.85,
      currentPrice: 150.25,
      beginnerScoreBreakdown: {
        score: 0.85,
        factors: [
          { name: "Stability", weight: 0.3, value: 0.9, contrib: 0.27, detail: "Large cap, stable business" },
          { name: "Growth", weight: 0.25, value: 0.8, contrib: 0.2, detail: "Consistent revenue growth" },
          { name: "Dividend", weight: 0.2, value: 0.7, contrib: 0.14, detail: "Regular dividend payments" },
          { name: "Volatility", weight: 0.25, value: 0.8, contrib: 0.2, detail: "Moderate price volatility" }
        ],
        notes: "Excellent choice for beginners due to strong fundamentals and market position"
      },
      __typename: "Stock"
    },
    {
      id: "2",
      symbol: "MSFT",
      companyName: "Microsoft Corporation",
      sector: "Technology",
      marketCap: 2800000000000,
      peRatio: 32.1,
      dividendYield: 0.68,
      beginnerFriendlyScore: 0.82,
      currentPrice: 350.75,
      beginnerScoreBreakdown: {
        score: 0.82,
        factors: [
          { name: "Stability", weight: 0.3, value: 0.85, contrib: 0.255, detail: "Dominant market position" },
          { name: "Growth", weight: 0.25, value: 0.75, contrib: 0.1875, detail: "Cloud business growth" },
          { name: "Dividend", weight: 0.2, value: 0.8, contrib: 0.16, detail: "Growing dividend yield" },
          { name: "Volatility", weight: 0.25, value: 0.8, contrib: 0.2, detail: "Stable price movement" }
        ],
        notes: "Strong cloud business and enterprise focus make it beginner-friendly"
      },
      __typename: "Stock"
    },
    {
      id: "3",
      symbol: "GOOGL",
      companyName: "Alphabet Inc.",
      sector: "Technology",
      marketCap: 1800000000000,
      peRatio: 25.8,
      dividendYield: 0.0,
      beginnerFriendlyScore: 0.78,
      currentPrice: 142.50,
      beginnerScoreBreakdown: {
        score: 0.78,
        factors: [
          { name: "Stability", weight: 0.3, value: 0.8, contrib: 0.24, detail: "Search dominance" },
          { name: "Growth", weight: 0.25, value: 0.85, contrib: 0.2125, detail: "Strong revenue growth" },
          { name: "Dividend", weight: 0.2, value: 0.0, contrib: 0.0, detail: "No dividend" },
          { name: "Volatility", weight: 0.25, value: 0.7, contrib: 0.175, detail: "Higher volatility" }
        ],
        notes: "Growth stock with no dividend, suitable for growth-focused investors"
      },
      __typename: "Stock"
    },
    {
      id: "4",
      symbol: "TSLA",
      companyName: "Tesla Inc.",
      sector: "Consumer Discretionary",
      marketCap: 800000000000,
      peRatio: 45.2,
      dividendYield: 0.0,
      beginnerFriendlyScore: 0.65,
      currentPrice: 250.80,
      beginnerScoreBreakdown: {
        score: 0.65,
        factors: [
          { name: "Stability", weight: 0.3, value: 0.6, contrib: 0.18, detail: "Volatile stock" },
          { name: "Growth", weight: 0.25, value: 0.9, contrib: 0.225, detail: "High growth potential" },
          { name: "Dividend", weight: 0.2, value: 0.0, contrib: 0.0, detail: "No dividend" },
          { name: "Volatility", weight: 0.25, value: 0.5, contrib: 0.125, detail: "High volatility" }
        ],
        notes: "High-risk, high-reward growth stock"
      },
      __typename: "Stock"
    },
    {
      id: "5",
      symbol: "AMZN",
      companyName: "Amazon.com Inc.",
      sector: "Consumer Discretionary",
      marketCap: 1600000000000,
      peRatio: 52.3,
      dividendYield: 0.0,
      beginnerFriendlyScore: 0.72,
      currentPrice: 155.40,
      beginnerScoreBreakdown: {
        score: 0.72,
        factors: [
          { name: "Stability", weight: 0.3, value: 0.75, contrib: 0.225, detail: "E-commerce leader" },
          { name: "Growth", weight: 0.25, value: 0.8, contrib: 0.2, detail: "Cloud and retail growth" },
          { name: "Dividend", weight: 0.2, value: 0.0, contrib: 0.0, detail: "No dividend" },
          { name: "Volatility", weight: 0.25, value: 0.7, contrib: 0.175, detail: "Moderate volatility" }
        ],
        notes: "Diversified business model with strong growth prospects"
      },
      __typename: "Stock"
    }
  ];

  const listData = useMemo(() => {
    console.log('=== listData useMemo called ===');
    console.log('activeTab:', activeTab);
    console.log('stocks.data:', stocks.data);
    console.log('beginnerData:', beginnerData);
    
    if (activeTab === 'browse') {
      // Use mock data if GraphQL data is empty or failed
      const hasValidData = stocks.data?.stocks && stocks.data.stocks.length > 0;
      const data = hasValidData ? stocks.data.stocks : mockStocks;
      console.log('Browse All data:', data);
      console.log('Browse All first item:', data[0]);
      console.log('Browse All data length:', data.length);
      return data;
    }
    if (activeTab === 'beginner') {
      // Use mock data if GraphQL data is empty or failed
      const hasValidData = beginnerData?.beginnerFriendlyStocks && beginnerData.beginnerFriendlyStocks.length > 0;
      const data = hasValidData ? beginnerData.beginnerFriendlyStocks : mockStocks;
      console.log('Beginner Friendly data:', data);
      console.log('Beginner Friendly first item:', data[0]);
      console.log('Beginner Friendly data length:', data.length);
      return data;
    }
    const data = (watchlistQ.data as any)?.myWatchlist ?? [];
    console.log('Watchlist data:', data);
    return data;
  }, [activeTab, stocks.data, beginnerData, watchlistQ.data]);

  const loading = (activeTab === 'browse' && stocks.loading)
               || (activeTab === 'beginner' && beginnerLoading)
               || (activeTab === 'watchlist' && watchlistQ.loading);

  // Log errors for debugging
  if (stocks.error) console.warn('Stocks error:', stocks.error);
  if (beginnerError) console.warn('Beginner error:', beginnerError);
  if (watchlistQ.error) console.warn('Watchlist error:', watchlistQ.error);
  
  // Debug current tab and data
  console.log('Current tab:', activeTab);
  console.log('Stocks loading:', stocks.loading, 'Beginner loading:', beginnerLoading);

return (
<View style={styles.container}>
{/* Header */}
<View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => navigateTo('Home')}>
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

          {researchLoading || chartLoading ? (
            <View style={styles.loadingContainer}>
              <Text style={styles.loadingText}>Loading research data...</Text>
            </View>
          ) : researchError ? (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>Error loading research: {researchError.message}</Text>
              <TouchableOpacity onPress={() => refetchResearch()} style={styles.retryButton}>
                <Text style={styles.retryButtonText}>Retry</Text>
              </TouchableOpacity>
            </View>
          ) : researchData?.researchHub ? (
            <View>
              {/* Company Header */}
              <View style={styles.card}>
                <View style={styles.companyHeader}>
                  <View style={{ flex: 1, paddingRight: 12 }}>
                    <Text style={styles.companyName}>
                      {researchData.researchHub.company?.name ?? 'N/A'} <Text style={styles.symbol}>({researchData.researchHub.symbol ?? 'N/A'})</Text>
                    </Text>
                    <Text style={styles.sector}>
                      {researchData.researchHub.company?.sector ?? 'N/A'} • {formatMarketCap(researchData.researchHub.company?.marketCap ?? 0)}
                    </Text>
                    {!!researchData.researchHub.company?.website && (
                      <Text style={styles.website} numberOfLines={1}>{researchData.researchHub.company.website}</Text>
                    )}
                  </View>
                  <View style={styles.priceContainer}>
                    <Text style={styles.currentPrice}>
                      {safeMoney(researchData.researchHub.quote?.currentPrice, 2)}
                    </Text>
                    <Text style={[
                      styles.change,
                      { color: (researchData.researchHub.quote?.change ?? 0) >= 0 ? '#22C55E' : '#EF4444' }
                    ]}>
                      {(researchData.researchHub.quote?.change ?? 0) >= 0 ? '+' : ''}
                      {safeFixed(researchData.researchHub.quote?.change, 2)} ({safeFixed(researchData.researchHub.quote?.changePercent, 2)}%)
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
                {chartLoading ? (
                  <View style={styles.chartLoading}>
                    <Text style={{ color: '#666' }}>Loading chart...</Text>
                  </View>
                ) : chartData?.stockChartData?.data?.length ? (
                  <ResponsiveChart height={220}>
                    {(w) => (
                      <AdvancedChart
                        key={`${researchSymbol}-${chartInterval}-${chartData.stockChartData.data.length}`}
                        data={chartData.stockChartData.data}
                        indicators={chartData.stockChartData.indicators || {}}
                        width={w}
                        height={220}
                      />
                    )}
                  </ResponsiveChart>
                ) : (
                  <View style={styles.chartLoading}>
                    <Text style={{ color: '#666' }}>No chart data</Text>
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
                      {safeFixed(researchData.researchHub.technicals?.rsi, 1)}
                    </Text>
                  </View>
                  <View style={styles.metricItem}>
                    <Text style={styles.metricLabel}>MACD</Text>
                    <Text style={styles.metricValue}>
                      {safeFixed(researchData.researchHub.technicals?.macd, 3)}
                    </Text>
                  </View>
                  <View style={styles.metricItem}>
                    <Text style={styles.metricLabel}>MA 50</Text>
                    <Text style={styles.metricValue}>
                      {safeMoney(researchData.researchHub.technicals?.movingAverage50)}
                    </Text>
                  </View>
                </View>

                <View style={styles.metricCard}>
                  <Text style={styles.metricTitle}>Sentiment</Text>
                  <View style={styles.metricItem}>
                    <Text style={styles.metricLabel}>News Sentiment</Text>
                    <Text style={[
                      styles.metricValue,
                      { color: getSentimentColor(researchData.researchHub.sentiment?.sentiment_label || 'NEUTRAL') }
                    ]}>
                      {researchData.researchHub.sentiment?.sentiment_label ?? 'NEUTRAL'}
                    </Text>
                  </View>
                  <View style={styles.metricItem}>
                    <Text style={styles.metricLabel}>Score</Text>
                    <Text style={styles.metricValue}>
                      {safeFixed(researchData.researchHub.sentiment?.sentiment_score, 2)}
                    </Text>
                  </View>
                  <View style={styles.metricItem}>
                    <Text style={styles.metricLabel}>Articles</Text>
                    <Text style={styles.metricValue}>{researchData.researchHub.sentiment?.article_count ?? '—'}</Text>
                  </View>
                </View>
              </View>

              {/* Peers */}
              {researchData.researchHub.peers?.length > 0 && (
                <View style={styles.card}>
                  <Text style={styles.sectionTitle}>Peer Companies</Text>
                  <View style={styles.peersContainer}>
                    {researchData.researchHub.peers.map((peer: string) => (
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

      {/* Chart Modal - Show for selected stock (only on non-research/options tabs) */}
      {activeTab !== 'research' && activeTab !== 'options' && selectedStock && (
        <Modal
          visible={!!selectedStock}
          animationType="slide"
          presentationStyle="fullScreen"
          onRequestClose={() => setSelectedStock(null)}
        >
          <View style={styles.chartModalContainer}>
            <View style={styles.chartModalHeader}>
              <TouchableOpacity 
                onPress={() => setSelectedStock(null)}
                style={styles.backButton}
              >
                <Icon name="arrow-left" size={24} color="#007AFF" />
              </TouchableOpacity>
              <Text style={styles.chartModalTitle}>Price Chart - {selectedStock.symbol}</Text>
              <View style={{ width: 24 }} />
            </View>
            <View style={styles.chartModalContent}>
              <ResponsiveChart height={500}>
                {(w) => (
                  <StockChart
                    symbol={selectedStock.symbol}
                    embedded
                    width={w}
                    height={500}
                    key={`${selectedStock.symbol}-${w}`}
                  />
                )}
              </ResponsiveChart>
            </View>
          </View>
        </Modal>
      )}

      {/* List - Only show when not on research or options tab */}
      {activeTab !== 'research' && activeTab !== 'options' && (
      <FlatList
        key={`${activeTab}-${listData.length}`} // Force re-render when tab or data changes
        data={Array.isArray(listData) ? listData : []}
        keyExtractor={activeTab === 'watchlist'
          ? ((i: any) => String(i.id))
          : ((i: any) => String(i.id))
        }
        renderItem={activeTab === 'watchlist' ? (renderWatch as any) : (renderStock as any)}
        refreshing={!!loading}
        onRefresh={() => {
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
      <Modal visible={rustOpen && !!rust} transparent animationType="slide" onRequestClose={() => setRustOpen(false)}>
<View style={styles.modalOverlay}>
          <View style={[styles.modal, { maxHeight: '80%' }]}>
<View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Advanced Analysis: {rust?.symbol}</Text>
              <TouchableOpacity onPress={() => setRustOpen(false)} style={{ padding: 4 }}>
<Icon name="x" size={24} color="#666" />
</TouchableOpacity>
</View>
            <ScrollView showsVerticalScrollIndicator={false}>
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
              onPress={() => setRustOpen(false)}
            >
              <Text style={{ fontSize: 16, fontWeight: '600', color: '#fff' }}>Done</Text>
            </TouchableOpacity>
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
        budget={1000} // Default budget - could be made dynamic from user profile
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
    marginBottom: 8,
  },
  metricLabel: {
    fontSize: 14,
    color: '#666',
  },
  metricValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000',
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