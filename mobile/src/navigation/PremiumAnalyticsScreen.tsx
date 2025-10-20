import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
  Dimensions,
  SafeAreaView,
  TextInput,
  Modal,
  ActivityIndicator,
  RefreshControl,
} from 'react-native';
import { useQuery, useMutation, useApolloClient } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import RebalancingStorageService from '../features/portfolio/services/RebalancingStorageService';
import RebalancingResultsDisplay from '../features/portfolio/components/RebalancingResultsDisplay';
import TaxOptimizationScreen from '../screens/TaxOptimizationScreen';

// Custom Slider Component
const CustomSlider = ({ value, onValueChange, minimumValue = 0, maximumValue = 100, step = 1, style, ...props }) => {
  const [sliderWidth, setSliderWidth] = useState(0);
  
  const handleLayout = (event) => {
    setSliderWidth(event.nativeEvent.layout.width);
  };
  
  const handlePress = (event) => {
    if (sliderWidth > 0) {
      const newValue = minimumValue + (event.nativeEvent.locationX / sliderWidth) * (maximumValue - minimumValue);
      const steppedValue = Math.round(newValue / step) * step;
      const clampedValue = Math.max(minimumValue, Math.min(maximumValue, steppedValue));
      onValueChange(clampedValue);
    }
  };
  
  const thumbPosition = sliderWidth > 0 ? ((value - minimumValue) / (maximumValue - minimumValue)) * sliderWidth : 0;
  
  return (
    <View style={[{ height: 40, justifyContent: 'center' }, style]} onLayout={handleLayout}>
      <TouchableOpacity
        style={{ flex: 1, justifyContent: 'center' }}
        onPress={handlePress}
        activeOpacity={1}
      >
        <View style={styles.sliderTrack}>
          <View style={[styles.sliderFill, { width: thumbPosition }]} />
          <View style={[styles.sliderThumb, { left: Math.max(0, Math.min(thumbPosition - 10, sliderWidth - 20)) }]} />
        </View>
      </TouchableOpacity>
    </View>
  );
};

import { gql } from '@apollo/client';
const { width } = Dimensions.get('window');

// GraphQL Queries
const GET_PREMIUM_PORTFOLIO_METRICS = gql`
  query GetPremiumPortfolioMetrics {
    portfolioMetrics {
      totalValue
      totalCost
      totalReturn
      totalReturnPercent
      dayChange
      dayChangePercent
      volatility
      sharpeRatio
      maxDrawdown
      beta
      alpha
      sectorAllocation
      riskMetrics
      holdings {
        symbol
        companyName
        shares
        currentPrice
        totalValue
        costBasis
        returnAmount
        returnPercent
        sector
      }
    }
  }
`;

const GET_AI_RECOMMENDATIONS = gql`
  query GetAIRecommendations($riskTolerance: String) {
    aiRecommendations(riskTolerance: $riskTolerance) {
      portfolioAnalysis {
        totalValue
        numHoldings
        sectorBreakdown
        riskScore
        diversificationScore
      }
      buyRecommendations {
        symbol
        companyName
        recommendation
        confidence
        reasoning
        targetPrice
        currentPrice
        expectedReturn
      }
      sellRecommendations {
        symbol
        reasoning
      }
      rebalanceSuggestions {
        action
        currentAllocation
        suggestedAllocation
        reasoning
        priority
      }
      riskAssessment {
        overallRisk
        volatilityEstimate
        recommendations
      }
      marketOutlook {
        overallSentiment
        confidence
        keyFactors
      }
    }
  }
`;

const AI_REBALANCE_PORTFOLIO = gql`
  mutation AIRebalancePortfolio($portfolioName: String, $riskTolerance: String, $maxRebalancePercentage: Float, $dryRun: Boolean) {
    aiRebalancePortfolio(portfolioName: $portfolioName, riskTolerance: $riskTolerance, maxRebalancePercentage: $maxRebalancePercentage, dryRun: $dryRun) {
      success
      message
      changesMade
      stockTrades {
        symbol
        companyName
        action
        shares
        price
        totalValue
        reason
      }
      newPortfolioValue
      rebalanceCost
      estimatedImprovement
    }
  }
`;

const GET_OPTIONS_ANALYSIS = gql`
  query GetOptionsAnalysis($symbol: String!) {
    optionsAnalysis(symbol: $symbol) {
      underlyingSymbol
      underlyingPrice
      marketSentiment {
        sentiment
        sentimentDescription
      }
      putCallRatio
      impliedVolatilityRank
      skew
      sentimentScore
      sentimentDescription
      unusualFlow {
        symbol
        totalVolume
        unusualVolume
        unusualVolumePercent
        topTrades {
          symbol
          contractSymbol
          optionType
          strike
          expirationDate
          volume
          openInterest
          premium
          impliedVolatility
          unusualActivityScore
          activityType
          type
        }
        sweepTrades
        blockTrades
        lastUpdated
      }
      recommendedStrategies {
        strategyName
        strategyType
        description
        riskLevel
        marketOutlook
        maxProfit
        maxLoss
        breakevenPoints
        probabilityOfProfit
        riskRewardRatio
        daysToExpiration
        totalCost
        totalCredit
      }
    }
  }
`;

const GET_STOCK_SCREENING = gql`
  query GetStockScreening($sector: String, $minMlScore: Int, $limit: Int) {
    advancedStockScreening(sector: $sector, minBeginnerScore: $minMlScore, limit: $limit) {
      symbol
      companyName
      sector
      marketCap
      peRatio
      beginnerFriendlyScore
      currentPrice
      mlScore
    }
  }
`;

// Fallback test query (no auth required)
const GET_OPTIONS_ANALYSIS_TEST = gql`
  query TestOptionsAnalysis($symbol: String!) {
    testOptionsAnalysis(symbol: $symbol) {
      underlyingSymbol
      underlyingPrice
      marketSentiment {
        sentiment
        sentimentDescription
      }
      putCallRatio
      impliedVolatilityRank
      skew
      sentimentScore
      recommendedStrategies {
        strategyName
        strategyType
        marketOutlook
        riskLevel
        maxProfit
        maxLoss
        probabilityOfProfit
        riskRewardRatio
        description
        setup
        breakevenPoints
        timeDecay
        volatilityImpact
      }
    }
  }
`;

// Mock data for when backend returns null
const mockMetrics = {
  totalValue: 125000.0,
  totalCost: 100000.0,
  totalReturn: 25000.0,
  totalReturnPercent: 25.0,
  dayChange: 1250.0,
  dayChangePercent: 1.0,
  volatility: 0.15,
  sharpeRatio: 1.2,
  maxDrawdown: -0.08,
  beta: 1.0,
  alpha: 0.05,
  sectorAllocation: JSON.stringify({
    "Technology": 40,
    "Healthcare": 25,
    "Finance": 20,
    "Consumer": 15
  }),
  riskMetrics: JSON.stringify({
    "riskScore": 0.65,
    "diversificationScore": 0.78
  }),
  holdings: [
    {
      symbol: "AAPL",
      companyName: "Apple Inc.",
      shares: 100,
      currentPrice: 150.25,
      totalValue: 15025.0,
      costBasis: 14000.0,
      returnAmount: 1025.0,
      returnPercent: 7.32,
      sector: "Technology"
    },
    {
      symbol: "MSFT",
      companyName: "Microsoft Corporation",
      shares: 50,
      currentPrice: 330.15,
      totalValue: 16507.5,
      costBasis: 15000.0,
      returnAmount: 1507.5,
      returnPercent: 10.05,
      sector: "Technology"
    }
  ]
};

const mockOptionsData = {
  underlyingSymbol: 'AAPL',
  underlyingPrice: 175.50,
  marketSentiment: {
    sentiment: 'Bullish',
    sentimentDescription: 'Strong earnings growth and positive analyst sentiment'
  },
  putCallRatio: 0.65,
  impliedVolatilityRank: 0.45,
  skew: 0.12,
  sentimentScore: 0.75,
  recommendedStrategies: [
    {
      strategyName: 'Covered Call',
      strategyType: 'Income',
      marketOutlook: 'Bullish',
      riskLevel: 'Low',
      maxProfit: 850.00,
      maxLoss: -1750.00,
      probabilityOfProfit: 0.68,
      riskRewardRatio: 0.49,
      description: 'Generate income by selling call options on stocks you own',
      setup: 'Sell 1 call option for every 100 shares owned',
      breakevenPoints: [175.50],
      timeDecay: 'Positive',
      volatilityImpact: 'Negative'
    },
    {
      strategyName: 'Protective Put',
      strategyType: 'Protective',
      marketOutlook: 'Bearish',
      riskLevel: 'Low',
      maxProfit: Infinity,
      maxLoss: -250.00,
      probabilityOfProfit: 0.45,
      riskRewardRatio: Infinity,
      description: 'Hedge downside risk by buying put options',
      setup: 'Buy 1 put option for every 100 shares owned',
      breakevenPoints: [173.00],
      timeDecay: 'Negative',
      volatilityImpact: 'Positive'
    },
    {
      strategyName: 'Iron Condor',
      strategyType: 'Neutral',
      marketOutlook: 'Neutral',
      riskLevel: 'Medium',
      maxProfit: 400.00,
      maxLoss: -600.00,
      probabilityOfProfit: 0.55,
      riskRewardRatio: 0.67,
      description: 'Profit from range-bound markets with limited risk',
      setup: 'Sell call spread + sell put spread',
      breakevenPoints: [170.00, 180.00],
      timeDecay: 'Positive',
      volatilityImpact: 'Negative'
    },
    {
      strategyName: 'Bull Put Spread',
      strategyType: 'Bullish',
      marketOutlook: 'Bullish',
      riskLevel: 'Medium',
      maxProfit: 300.00,
      maxLoss: -700.00,
      probabilityOfProfit: 0.62,
      riskRewardRatio: 0.43,
      description: 'Bullish strategy with limited risk and reward',
      setup: 'Sell put + buy lower strike put',
      breakevenPoints: [172.00],
      timeDecay: 'Positive',
      volatilityImpact: 'Negative'
    }
  ]
};

const PremiumAnalyticsScreen = ({ navigateTo }) => {
  const [activeTab, setActiveTab] = useState('metrics');
  const [refreshing, setRefreshing] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
  const [searchSymbol, setSearchSymbol] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [marketOutlook, setMarketOutlook] = useState('Neutral');
  
  // Apollo Client for manual queries
  const client = useApolloClient();
  
  // Stock Screening state
  const [screeningFilters, setScreeningFilters] = useState({
    sector: null,
    marketCap: null,
    minPERatio: 0,
    maxPERatio: 50,
    minMLScore: 0,
    riskLevel: null,
    sortBy: 'ML Score'
  });
  const [screeningResults, setScreeningResults] = useState([]);
  const [screeningLoading, setScreeningLoading] = useState(false);
  
  // Options Chain state
  const [showFullChain, setShowFullChain] = useState(false);
  const [selectedExpiration, setSelectedExpiration] = useState<number | null>(null);
  
  // Tooltip state
  const [showTooltip, setShowTooltip] = useState<string | null>(null);
  
  // Stock details modal state
  const [selectedStockDetails, setSelectedStockDetails] = useState(null);
  const [showStockDetailsModal, setShowStockDetailsModal] = useState(false);
  
  // Rebalancing state
  const [rebalancingPerformed, setRebalancingPerformed] = useState(false);
  const [lastRebalancingResult, setLastRebalancingResult] = useState(null);
  const [showRebalancingResults, setShowRebalancingResults] = useState(false);
  
  // Safety features state
  const [isDryRunMode, setIsDryRunMode] = useState(false);
  const [dryRunResults, setDryRunResults] = useState(null);
  const [showDryRunModal, setShowDryRunModal] = useState(false);
  
  // Queries
  const { data: metricsData, loading: metricsLoading, refetch: refetchMetrics } = useQuery(
    GET_PREMIUM_PORTFOLIO_METRICS,
    {
      errorPolicy: 'all',
      onCompleted: (data) => {
        console.log('🔍 Portfolio metrics loaded:', data);
      },
      onError: (error) => {
        console.error('❌ PremiumAnalyticsScreen: Metrics query error:', error);
      }
    }
  );

  const {
    data: recommendationsData,
    loading: recommendationsLoading,
    error: recommendationsError,
    refetch: refetchRecommendations,
  } = useQuery(
    GET_AI_RECOMMENDATIONS,
    {
      variables: { riskTolerance: 'medium' },
      errorPolicy: 'all',
      fetchPolicy: 'network-only',
      onCompleted: (data) => {
        console.log('🔍 AI recommendations loaded:', data);
      },
      onError: (error) => {
        console.error('❌ PremiumAnalyticsScreen: AI Recommendations query error:', error);
      },
    },
  );

  const [aiRebalancePortfolio, { loading: rebalanceLoading }] = useMutation(AI_REBALANCE_PORTFOLIO, {
    onCompleted: async (data) => {
      if (data.aiRebalancePortfolio.success) {
        const result = data.aiRebalancePortfolio;
        
        if (isDryRunMode) {
          setDryRunResults(result);
          setShowDryRunModal(true);
          setIsDryRunMode(false);
          return;
        }
        
        setLastRebalancingResult(result);
        setRebalancingPerformed(true);

        Alert.alert(
          'Rebalancing Complete!',
          result.message,
          [
            { text: 'View Updated Recommendations', onPress: () => {
              // State is already set above
            }}
          ]
        );
      } else {
        Alert.alert('Rebalancing Failed', data.aiRebalancePortfolio.message);
      }
    },
    onError: (error) => {
      const err = error as Error;
      Alert.alert('Error', `Rebalancing failed: ${err?.message || 'Unknown error'}`);
    }
  });

  const { data: optionsData, loading: optionsLoading, error: optionsError, refetch: refetchOptions } = useQuery(
    GET_OPTIONS_ANALYSIS,
    {
      variables: { symbol: selectedSymbol },
      errorPolicy: 'all',
      onCompleted: (data) => {
        console.log('🔍 Options analysis loaded:', data);
      },
      onError: (error) => {
        console.error('❌ PremiumAnalyticsScreen: Options Analysis Error:', error);
      }
    }
  );

  // Options data - accessible throughout component
  const options = optionsData?.optionsAnalysis || mockOptionsData;
  const isUsingMockOptionsData = !optionsData?.optionsAnalysis;
  
  // Debug logging
  console.log('🔍 Options Debug:', {
    optionsData: optionsData?.optionsAnalysis,
    mockOptionsData: mockOptionsData,
    finalOptions: options,
    isUsingMockOptionsData,
    hasStrategies: options?.recommendedStrategies?.length
  });

  // Use mock data if backend returns null
  const displayMetrics = metricsData?.portfolioMetrics || mockMetrics;
  const isUsingMockData = !metricsData?.portfolioMetrics;

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await Promise.all([
        refetchMetrics(),
        refetchRecommendations(),
        refetchOptions()
      ]);
    } catch (error) {
      console.error('Error refreshing data:', error);
    } finally {
      setRefreshing(false);
    }
  }, [refetchMetrics, refetchRecommendations, refetchOptions]);

  const handleSearch = useCallback(() => {
    if (searchSymbol.trim()) {
      const next = searchSymbol.trim().toUpperCase();
      setIsSearching(true);
      setSelectedSymbol(next);
      setSearchSymbol('');
      refetchOptions({ symbol: next });
      setTimeout(() => setIsSearching(false), 1000);
    }
  }, [searchSymbol, refetchOptions]);

  const handleQuickSelect = useCallback((symbol: string) => {
    setIsSearching(true);
    setSelectedSymbol(symbol);
    refetchOptions({ symbol });
    setTimeout(() => setIsSearching(false), 1000);
  }, [refetchOptions]);

  // Stock Screening Functions
  const handleScreeningSearch = useCallback(async () => {
    setScreeningLoading(true);
    try {
      const variables = {
        sector: screeningFilters.sector,
        minMlScore: screeningFilters.minMLScore,
        limit: 50
      };
      
      const result = await client.query({
        query: GET_STOCK_SCREENING,
        variables: variables,
        errorPolicy: 'all',
        fetchPolicy: 'cache-first'
      });
      
      if (result.data && result.data.advancedStockScreening) {
        setScreeningResults(result.data.advancedStockScreening);
      } else {
        setScreeningResults([]);
      }
    } catch (error) {
      console.error('Screening search error:', error);
      setScreeningResults([]);
    } finally {
      setScreeningLoading(false);
    }
  }, [client, screeningFilters]);

  // Function to filter strategies based on market outlook
  const getFilteredStrategies = (strategies: any[]) => {
    if (!strategies) return [];
    
    // If no specific outlook is selected, show all strategies
    if (marketOutlook === 'Neutral') {
      return strategies;
    }
    
    const filtered = strategies.filter(strategy => {
      const outlook = strategy.marketOutlook?.toLowerCase() || '';
      const strategyType = strategy.strategyType?.toLowerCase() || '';
      
      switch (marketOutlook) {
        case 'Bullish':
          return outlook.includes('bullish') || 
                 outlook.includes('income') || 
                 strategyType.includes('income') ||
                 strategy.strategyName?.toLowerCase().includes('covered call');
        case 'Bearish':
          return outlook.includes('bearish') || 
                 outlook.includes('protective') || 
                 strategyType.includes('protective') ||
                 strategy.strategyName?.toLowerCase().includes('put');
        default:
          return true;
      }
    });
    
    return filtered;
  };

  const renderMetricsTab = () => {
    if (metricsLoading) {
      return (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading advanced metrics...</Text>
        </View>
      );
    }

    return (
      <ScrollView 
        style={styles.tabContent} 
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor="#007AFF"
            title="Pull to refresh metrics"
          />
        }
      >
        {/* Performance Overview */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Performance Overview</Text>
            {isUsingMockData && (
              <View style={styles.mockDataIndicator}>
                <Text style={styles.mockDataText}>Demo Data</Text>
              </View>
            )}
          </View>
          
          <View style={styles.metricsGrid}>
            <View style={styles.metricCard}>
              <View style={styles.metricHeader}>
                <Icon name="dollar-sign" size={20} color="#007AFF" />
                <Text style={styles.metricLabel}>Total Value</Text>
              </View>
              <Text style={styles.metricValue}>
                ${displayMetrics.totalValue?.toLocaleString() || '0.00'}
              </Text>
            </View>
            
            <View style={styles.metricCard}>
              <View style={styles.metricHeader}>
                <Icon name="trending-up" size={20} color="#34C759" />
                <Text style={styles.metricLabel}>Weighted APY</Text>
              </View>
              <Text style={[styles.metricValue, { color: '#34C759' }]}>
                {displayMetrics.totalReturnPercent?.toFixed(2) || '0.00'}%
              </Text>
            </View>
            
            <View style={styles.metricCard}>
              <View style={styles.metricHeader}>
                <Icon name="activity" size={20} color="#FF9500" />
                <Text style={styles.metricLabel}>Portfolio Risk</Text>
              </View>
              <Text style={styles.metricValue}>
                {displayMetrics.volatility != null ? `${(displayMetrics.volatility * 100).toFixed(1)}%` : 'N/A'}
              </Text>
            </View>
            
            <View style={styles.metricCard}>
              <View style={styles.metricHeader}>
                <Icon name="layers" size={20} color="#007AFF" />
                <Text style={styles.metricLabel}>Diversification</Text>
              </View>
              <Text style={styles.metricValue}>
                {displayMetrics.riskMetrics ? JSON.parse(displayMetrics.riskMetrics).diversificationScore ? `${(JSON.parse(displayMetrics.riskMetrics).diversificationScore * 100).toFixed(0)}%` : 'N/A' : 'N/A'}
              </Text>
            </View>
          </View>
        </View>

        {/* Returns Overview */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Returns Overview</Text>
          <View style={styles.returnsContainer}>
            <View style={styles.returnItem}>
              <Text style={styles.returnLabel}>1 Day</Text>
              <Text style={[styles.returnValue, { color: displayMetrics.dayChange >= 0 ? '#34C759' : '#ef4444' }]}>
                ${displayMetrics.dayChange?.toLocaleString() || '0'}
              </Text>
            </View>
            <View style={styles.returnItem}>
              <Text style={styles.returnLabel}>7 Days</Text>
              <Text style={[styles.returnValue, { color: displayMetrics.totalReturn >= 0 ? '#34C759' : '#ef4444' }]}>
                ${displayMetrics.totalReturn?.toLocaleString() || '0'}
              </Text>
            </View>
            <View style={styles.returnItem}>
              <Text style={styles.returnLabel}>30 Days</Text>
              <Text style={[styles.returnValue, { color: displayMetrics.totalReturn >= 0 ? '#34C759' : '#ef4444' }]}>
                ${displayMetrics.totalReturn?.toLocaleString() || '0'}
              </Text>
            </View>
          </View>
        </View>

        {/* Portfolio Summary */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Portfolio Summary</Text>
          <View style={styles.summaryCard}>
            <View style={styles.summaryItem}>
              <Text style={styles.summaryLabel}>Active Positions</Text>
              <Text style={styles.summaryValue}>{displayMetrics.holdings?.length || 0}</Text>
            </View>
            <View style={styles.summaryItem}>
              <Text style={styles.summaryLabel}>Protocols</Text>
              <Text style={styles.summaryValue}>{displayMetrics.holdings?.length || 0}</Text>
            </View>
            <View style={styles.summaryItem}>
              <Text style={styles.summaryLabel}>Last Updated</Text>
              <Text style={styles.summaryValue}>
                {displayMetrics.createdAt ? new Date(displayMetrics.createdAt).toLocaleDateString() : 'N/A'}
              </Text>
            </View>
          </View>
        </View>
      </ScrollView>
    );
  };

  const renderRecommendationsTab = () => {
    if (recommendationsLoading) {
      return (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading AI recommendations...</Text>
        </View>
      );
    }

    const recommendations = recommendationsData?.aiRecommendations;

    if (!recommendations) {
      return (
        <View style={styles.errorContainer}>
          <Icon name="cpu" size={48} color="#007AFF" />
          <Text style={styles.errorText}>Unable to load AI recommendations</Text>
          {recommendationsError && (
            <Text style={styles.errorDetails}>
              Error: {recommendationsError.message}
            </Text>
          )}
        </View>
      );
    }

    return (
      <ScrollView 
        style={styles.tabContent} 
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor="#007AFF"
            title="Pull to refresh recommendations"
          />
        }
      >
        {/* Portfolio Analysis */}
        {recommendations.portfolioAnalysis && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>
              Portfolio Analysis {rebalancingPerformed && <Text style={styles.updatedLabel}>(Updated)</Text>}
            </Text>
            <View style={styles.analysisCard}>
              <View style={styles.analysisItem}>
                <Text style={styles.analysisLabel}>Total Value</Text>
                <Text style={styles.analysisValue}>
                  ${recommendations.portfolioAnalysis.totalValue?.toFixed(2) || 'N/A'}
                </Text>
              </View>
              <View style={styles.analysisItem}>
                <Text style={styles.analysisLabel}>Number of Holdings</Text>
                <Text style={styles.analysisValue}>
                  {recommendations.portfolioAnalysis.numHoldings || 'N/A'}
                </Text>
              </View>
              <View style={styles.analysisItem}>
                <Text style={styles.analysisLabel}>Risk Score</Text>
                <Text style={styles.analysisValue}>
                  {recommendations.portfolioAnalysis.riskScore || 'N/A'}
                </Text>
              </View>
              <View style={styles.analysisItem}>
                <Text style={styles.analysisLabel}>Diversification Score</Text>
                <Text style={styles.analysisValue}>
                  {recommendations.portfolioAnalysis.diversificationScore || 'N/A'}
                </Text>
              </View>
            </View>
          </View>
        )}

        {/* Buy Recommendations */}
        {recommendations.buyRecommendations && recommendations.buyRecommendations.length > 0 && (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Buy Recommendations</Text>
              <TouchableOpacity 
                style={styles.refreshButton}
                onPress={onRefresh}
                disabled={refreshing}
              >
                <Icon name={refreshing ? "loader" : "refresh-cw"} size={20} color="#007AFF" />
                <Text style={styles.refreshButtonText}>
                  {refreshing ? 'Refreshing...' : 'Refresh'}
                </Text>
              </TouchableOpacity>
            </View>
            {recommendations.buyRecommendations.map((rec: any, index: number) => (
              <View key={index} style={styles.recommendationCard}>
                <View style={styles.recommendationHeader}>
                  <Text style={styles.recommendationSymbol}>{rec.symbol}</Text>
                  <View style={styles.recommendationBadge}>
                    <Text style={styles.recommendationText}>{rec.recommendation}</Text>
                  </View>
                </View>
                <Text style={styles.recommendationName}>{rec.companyName}</Text>
                <Text style={styles.recommendationReasoning}>{rec.reasoning}</Text>
                <View style={styles.recommendationMetrics}>
                  <Text style={styles.recommendationMetric}>
                    Confidence: {rec?.confidence != null ? Math.round(rec.confidence * 100) : 0}%
                  </Text>
                  <Text style={styles.recommendationMetric}>
                    Expected Return: {rec?.expectedReturn != null ? rec.expectedReturn.toFixed(1) : 'N/A'}%
                  </Text>
                  <Text style={styles.recommendationMetric}>
                    Current: ${rec?.currentPrice != null ? rec.currentPrice.toFixed(2) : 'N/A'}
                  </Text>
                  <Text style={styles.recommendationMetric}>
                    Target: ${rec?.targetPrice != null ? rec.targetPrice.toFixed(2) : 'N/A'}
                  </Text>
                </View>
              </View>
            ))}
          </View>
        )}

        {/* Rebalancing Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Portfolio Rebalancing</Text>
            <View style={styles.rebalanceButtons}>
              {recommendations.rebalanceSuggestions && recommendations.rebalanceSuggestions.length > 0 ? (
                <TouchableOpacity
                  style={[styles.rebalanceButton, rebalanceLoading && styles.rebalanceButtonDisabled]}
                  onPress={() => {
                    Alert.alert(
                      'AI Portfolio Rebalancing',
                      'This will automatically rebalance your portfolio based on AI recommendations.\n\nContinue with rebalancing?',
                      [
                        { text: 'Cancel', style: 'cancel' },
                        { 
                          text: 'Preview Changes', 
                          onPress: () => {
                            setIsDryRunMode(true);
                            aiRebalancePortfolio({
                              variables: {
                                riskTolerance: 'medium',
                                maxRebalancePercentage: 20.0,
                                dryRun: true
                              }
                            });
                          },
                          style: 'default'
                        },
                        { 
                          text: 'Execute Rebalancing', 
                          onPress: () => aiRebalancePortfolio({
                            variables: {
                              riskTolerance: 'medium',
                              maxRebalancePercentage: 20.0
                            }
                          }),
                          style: 'destructive'
                        }
                      ]
                    );
                  }}
                  disabled={rebalanceLoading}
                >
                  <Icon name={rebalanceLoading ? "loader" : "refresh-cw"} size={16} color="#fff" />
                  <Text style={styles.rebalanceButtonText}>
                    {rebalanceLoading ? 'Analyzing & Rebalancing...' : 'AI Rebalance'}
                  </Text>
                </TouchableOpacity>
              ) : (
                <TouchableOpacity
                  style={[styles.rebalanceButton, styles.rebalanceButtonDisabled]}
                  disabled={true}
                >
                  <Icon name="refresh-cw" size={16} color="#8E8E93" />
                  <Text style={[styles.rebalanceButtonText, { color: '#8E8E93' }]}>
                    No Rebalancing Needed
                  </Text>
                </TouchableOpacity>
              )}
              <TouchableOpacity
                style={styles.viewResultsButton}
                onPress={() => setShowRebalancingResults(true)}
              >
                <Icon name="clock" size={16} color="#007AFF" />
                <Text style={styles.viewResultsButtonText}>View Results</Text>
              </TouchableOpacity>
            </View>
          </View>
          {recommendations.rebalanceSuggestions && recommendations.rebalanceSuggestions.length > 0 ? (
            recommendations.rebalanceSuggestions.map((suggestion: any, index: number) => (
              <View key={index} style={styles.rebalanceCard}>
                <View style={styles.rebalanceHeader}>
                  <Text style={styles.rebalanceAction}>{suggestion.action}</Text>
                  <View style={[
                    styles.priorityBadge,
                    { backgroundColor: suggestion.priority === 'High' ? '#ef4444' : suggestion.priority === 'Medium' ? '#FF9500' : '#34C759' }
                  ]}>
                    <Text style={styles.priorityText}>{suggestion.priority}</Text>
                  </View>
                </View>
                <Text style={styles.rebalanceReasoning}>{suggestion.reasoning}</Text>
                <View style={styles.rebalanceAllocation}>
                  <Text style={styles.allocationLabel}>Current: {suggestion.currentAllocation}%</Text>
                  <Text style={styles.allocationArrow}>→</Text>
                  <Text style={styles.allocationLabel}>Suggested: {suggestion.suggestedAllocation}%</Text>
                </View>
              </View>
            ))
          ) : (
            <View style={styles.noSuggestionsCard}>
              <Icon name="check-circle" size={24} color="#34C759" />
              <Text style={styles.noSuggestionsTitle}>Portfolio is Well Balanced</Text>
              <Text style={styles.noSuggestionsText}>
                No rebalancing suggestions at this time. Your portfolio appears to be well diversified.
              </Text>
            </View>
          )}
        </View>
      </ScrollView>
    );
  };

  const renderScreeningTab = () => {
    return (
      <ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false}>
        {/* Screening Filters */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Screening Filters</Text>
          
          {/* Sector Filter */}
          <View style={styles.filterGroup}>
            <Text style={styles.filterLabel}>Sector</Text>
            <View style={styles.filterRow}>
              {['All', 'Technology', 'Healthcare', 'Financial Services', 'Consumer Cyclical', 'Consumer Defensive'].map((sector) => (
                <TouchableOpacity
                  key={sector}
                  style={[
                    styles.filterChip,
                    screeningFilters.sector === sector && styles.filterChipActive
                  ]}
                  onPress={() => setScreeningFilters({...screeningFilters, sector: sector === 'All' ? null : sector})}
                >
                  <Text style={[
                    styles.filterChipText,
                    screeningFilters.sector === sector && styles.filterChipTextActive
                  ]}>
                    {sector}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* ML Score Filter */}
          <View style={styles.filterGroup}>
            <Text style={styles.filterLabel}>ML Score (Minimum)</Text>
            <View style={styles.rangeContainer}>
              <Text style={styles.rangeLabel}>{screeningFilters.minMLScore || 0}</Text>
              <CustomSlider
                style={styles.slider}
                minimumValue={0}
                maximumValue={100}
                value={screeningFilters.minMLScore || 0}
                onValueChange={(value) => setScreeningFilters({...screeningFilters, minMLScore: Math.round(value)})}
              />
            </View>
          </View>

          {/* Search Button */}
          <TouchableOpacity 
            style={[styles.searchButton, screeningLoading && styles.searchButtonDisabled]}
            onPress={handleScreeningSearch}
            disabled={screeningLoading}
          >
            {screeningLoading ? (
              <View style={styles.loadingButtonContent}>
                <ActivityIndicator size="small" color="#FFFFFF" style={{ marginRight: 8 }} />
                <Text style={styles.searchButtonText}>Searching...</Text>
              </View>
            ) : (
              <Text style={styles.searchButtonText}>Search Stocks</Text>
            )}
          </TouchableOpacity>
        </View>

        {/* Search Results */}
        {screeningLoading && (
          <View style={styles.loadingResultsContainer}>
            <ActivityIndicator size="small" color="#007AFF" />
            <Text style={styles.loadingResultsText}>Searching stocks...</Text>
          </View>
        )}

        {screeningResults && screeningResults.length > 0 && !screeningLoading && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>
              Search Results ({screeningResults.length} stocks found)
            </Text>
            {screeningResults.map((stock, index) => (
              <View key={index} style={styles.stockCard}>
                <View style={styles.stockHeader}>
                  <View style={styles.stockInfo}>
                    <Text style={styles.stockSymbol}>{stock.symbol}</Text>
                    <Text style={styles.stockName}>{stock.companyName}</Text>
                    <Text style={styles.stockSector}>{stock.sector}</Text>
                  </View>
                  <View style={styles.stockMetrics}>
                    <Text style={styles.stockPrice}>${stock.currentPrice?.toFixed(2) || 'N/A'}</Text>
                    <Text style={styles.stockMLScore}>ML: {stock.mlScore?.toFixed(1) || 'N/A'}</Text>
                  </View>
                </View>
                <View style={styles.stockDetails}>
                  <View style={styles.stockDetailItem}>
                    <Text style={styles.stockDetailLabel}>Market Cap</Text>
                    <Text style={styles.stockDetailValue}>
                      ${(stock.marketCap / 1000000000).toFixed(1)}B
                    </Text>
                  </View>
                  <View style={styles.stockDetailItem}>
                    <Text style={styles.stockDetailLabel}>P/E Ratio</Text>
                    <Text style={styles.stockDetailValue}>
                      {stock.peRatio?.toFixed(1) || 'N/A'}
                    </Text>
                  </View>
                  <View style={styles.stockDetailItem}>
                    <Text style={styles.stockDetailLabel}>Risk Level</Text>
                    <Text style={[styles.stockDetailValue, { color: '#FF9500' }]}>
                      Medium
                    </Text>
                  </View>
                  <View style={styles.stockDetailItem}>
                    <Text style={styles.stockDetailLabel}>Growth</Text>
                    <Text style={styles.stockDetailValue}>
                      Moderate
                    </Text>
                  </View>
                </View>
                <View style={styles.stockActions}>
                  <TouchableOpacity 
                    style={styles.actionButton}
                    onPress={() => {
                      setSelectedStockDetails(stock);
                      setShowStockDetailsModal(true);
                    }}
                  >
                    <Text style={styles.actionButtonText}>View Details</Text>
                  </TouchableOpacity>
                  <TouchableOpacity 
                    style={[styles.actionButton, styles.addButton]}
                    onPress={async () => {
                      try {
                        const result = await client.mutate({
                          mutation: gql`
                            mutation AddToWatchlist($symbol: String!, $notes: String) {
                              addToWatchlist(symbol: $symbol, notes: $notes) {
                                success
                                message
                              }
                            }
                          `,
                          variables: {
                            symbol: stock.symbol,
                            notes: `Added from screening - ML Score: ${stock.mlScore?.toFixed(1) || 'N/A'}`
                          }
                        });
                        if (result.data?.addToWatchlist?.success) {
                          Alert.alert(
                            'Success',
                            `${stock.symbol} has been added to your watchlist!`,
                            [{ text: 'OK' }]
                          );
                        } else {
                          Alert.alert(
                            'Error',
                            result.data?.addToWatchlist?.message || 'Failed to add to watchlist',
                            [{ text: 'OK' }]
                          );
                        }
                      } catch (error) {
                        console.error('Error adding to watchlist:', error);
                        Alert.alert(
                          'Error',
                          'Failed to add to watchlist. Please try again.',
                          [{ text: 'OK' }]
                        );
                      }
                    }}
                  >
                    <Text style={[styles.actionButtonText, styles.addButtonText]}>Add to Watchlist</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ))}
          </View>
        )}

        {/* No Results */}
        {screeningResults && screeningResults.length === 0 && !screeningLoading && (
          <View style={styles.noResultsContainer}>
            <Icon name="search" size={48} color="#8E8E93" />
            <Text style={styles.noResultsText}>No stocks found matching your criteria</Text>
            <Text style={styles.noResultsSubtext}>Try adjusting your filters and search again</Text>
          </View>
        )}
      </ScrollView>
    );
  };

  const renderOptionsTab = () => {
    // Use the global options variable that includes mock data fallback

    return (
      <ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false}>
        {/* Stock Search and Selector */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Search Any Stock for Options Analysis</Text>
          
          {/* Search Input */}
          <View style={styles.optionsSearchContainer}>
            <Icon name="search" size={20} color="#8E8E93" style={styles.searchIcon} />
            <TextInput
              style={styles.searchInput}
              placeholder="Enter stock symbol (e.g., NFLX, AMD, SPY)"
              placeholderTextColor="#8E8E93"
              value={searchSymbol}
              onChangeText={setSearchSymbol}
              autoCapitalize="characters"
              autoCorrect={false}
              returnKeyType="search"
              onSubmitEditing={handleSearch}
              maxLength={10}
            />
            {searchSymbol.length > 0 && (
              <TouchableOpacity
                style={styles.clearButton}
                onPress={() => setSearchSymbol('')}
              >
                <Icon name="x" size={16} color="#8E8E93" />
              </TouchableOpacity>
            )}
            <TouchableOpacity
              style={[
                styles.optionsSearchButton, 
                (isSearching || !searchSymbol.trim()) && styles.optionsSearchButtonDisabled
              ]}
              onPress={handleSearch}
              disabled={isSearching || !searchSymbol.trim()}
            >
              <Icon 
                name={isSearching ? "loader" : "arrow-right"} 
                size={18} 
                color={isSearching || !searchSymbol.trim() ? "#8E8E93" : "#fff"} 
              />
            </TouchableOpacity>
          </View>

          {/* Quick Select Buttons */}
          <Text style={styles.quickSelectLabel}>Popular Stocks:</Text>
          <View style={styles.stockSelector}>
            {['AAPL', 'TSLA', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'NFLX', 'AMD', 'SPY'].map((symbol) => (
              <TouchableOpacity
                key={symbol}
                style={[
                  styles.stockButton,
                  selectedSymbol === symbol && styles.selectedStockButton
                ]}
                onPress={() => handleQuickSelect(symbol)}
              >
                <Text style={[
                  styles.stockButtonText,
                  selectedSymbol === symbol && styles.selectedStockButtonText
                ]}>
                  {symbol}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <View style={styles.stockInfoContainer}>
            {(isSearching || optionsLoading) ? (
              <View style={styles.loadingContainer}>
                <Icon name="loader" size={16} color="#007AFF" />
                <Text style={styles.loadingText}>
                  {isSearching ? `Searching for ${searchSymbol}...` : 'Loading options data...'}
                </Text>
              </View>
            ) : (
              <Text style={styles.stockInfoText}>
                Analyzing options strategies for {selectedSymbol}
              </Text>
            )}
          </View>
        </View>

        {/* Market Sentiment */}
        {options?.marketSentiment && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Market Sentiment</Text>
            <View style={styles.metricsGrid}>
              <View style={styles.metricCard}>
                <View style={styles.metricHeader}>
                  <Text style={styles.metricLabel}>Put/Call Ratio</Text>
                  <TouchableOpacity 
                    style={styles.tooltipButton}
                    onPress={() => setShowTooltip(showTooltip === 'putCallRatio' ? null : 'putCallRatio')}
                  >
                    <Icon name="help-circle" size={16} color="#8E8E93" />
                  </TouchableOpacity>
                </View>
                <Text style={styles.metricValue}>
                  {options?.putCallRatio?.toFixed(2) || 'N/A'}
                </Text>
                <Text style={styles.metricExplanation}>
                  {options?.putCallRatio ? 
                    (options.putCallRatio > 0.8 ? 'Bearish sentiment - more puts' :
                      options.putCallRatio < 0.6 ? 'Bullish sentiment - more calls' :
                      'Neutral sentiment') : 'N/A'}
                </Text>
              </View>
              <View style={styles.metricCard}>
                <View style={styles.metricHeader}>
                  <Text style={styles.metricLabel}>IV Rank</Text>
                  <TouchableOpacity 
                    style={styles.tooltipButton}
                    onPress={() => setShowTooltip(showTooltip === 'ivRank' ? null : 'ivRank')}
                  >
                    <Icon name="help-circle" size={16} color="#8E8E93" />
                  </TouchableOpacity>
                </View>
                <Text style={styles.metricValue}>
                  {options?.impliedVolatilityRank?.toFixed(1) || 'N/A'}%
                </Text>
                <Text style={styles.metricExplanation}>
                  {options?.impliedVolatilityRank ? 
                    (options.impliedVolatilityRank > 70 ? 'High volatility - expensive options' :
                      options.impliedVolatilityRank < 30 ? 'Low volatility - cheap options' :
                      'Moderate volatility') : 'N/A'}
                </Text>
              </View>
              <View style={styles.metricCard}>
                <View style={styles.metricHeader}>
                  <Text style={styles.metricLabel}>Sentiment</Text>
                  <TouchableOpacity 
                    style={styles.tooltipButton}
                    onPress={() => setShowTooltip(showTooltip === 'sentiment' ? null : 'sentiment')}
                  >
                    <Icon name="help-circle" size={16} color="#8E8E93" />
                  </TouchableOpacity>
                </View>
                <Text 
                  style={[
                    styles.metricValue,
                    { color: (options?.sentimentScore || 50) > 50 ? '#34C759' : '#ef4444' }
                  ]}
                  numberOfLines={2}
                  ellipsizeMode="tail"
                >
                  {options?.sentimentDescription || 'Neutral'}
                </Text>
                <Text style={styles.metricExplanation}>
                  {options?.sentimentScore ? 
                    `Score: ${options.sentimentScore.toFixed(0)}/100` : 'N/A'}
                </Text>
              </View>
            </View>
          </View>
        )}

        {/* AI Options Recommendations */}
        <View style={styles.section}>
          <TouchableOpacity
            style={styles.aiOptionsButton}
            onPress={() => navigateTo('ai-options')}
          >
            <View style={styles.aiOptionsContent}>
              <View style={styles.aiOptionsHeader}>
                <Icon name="cpu" size={24} color="#007AFF" />
                <Text style={styles.aiOptionsTitle}>AI Options Recommendations</Text>
              </View>
              <Text style={styles.aiOptionsDescription}>
                Get hedge fund-level options strategy recommendations powered by advanced AI and machine learning
              </Text>
              <View style={styles.aiOptionsFeatures}>
                <View style={styles.featureItem}>
                  <Icon name="check" size={16} color="#34C759" />
                  <Text style={styles.featureText}>Smart Strategy Selection</Text>
                </View>
                <View style={styles.featureItem}>
                  <Icon name="check" size={16} color="#34C759" />
                  <Text style={styles.featureText}>Risk-Adjusted Returns</Text>
                </View>
                <View style={styles.featureItem}>
                  <Icon name="check" size={16} color="#34C759" />
                  <Text style={styles.featureText}>Real-time Market Analysis</Text>
                </View>
              </View>
              <View style={styles.aiOptionsFooter}>
                <Text style={styles.aiOptionsAction}>Tap to Access AI Options</Text>
                <Icon name="arrow-right" size={20} color="#007AFF" />
              </View>
            </View>
          </TouchableOpacity>
        </View>

        {/* Market Outlook Selector */}
        {options?.recommendedStrategies && options.recommendedStrategies.length > 0 && (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Market Outlook Filter</Text>
              {isUsingMockOptionsData && (
                <View style={styles.mockDataIndicator}>
                  <Text style={styles.mockDataText}>Demo Data</Text>
                </View>
              )}
            </View>
            <View style={styles.outlookSelector}>
              {['Bullish', 'Neutral', 'Bearish'].map((outlook) => (
                <TouchableOpacity
                  key={outlook}
                  style={[
                    styles.outlookButton,
                    marketOutlook === outlook && styles.outlookButtonActive
                  ]}
                  onPress={() => setMarketOutlook(outlook)}
                >
                  <Text style={[
                    styles.outlookButtonText,
                    marketOutlook === outlook && styles.outlookButtonTextActive
                  ]}>
                    {outlook}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        )}

        {/* Recommended Strategies */}
        {options?.recommendedStrategies && options.recommendedStrategies.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>
              Recommended Strategies
              {optionsLoading && (
                <Icon name="loader" size={16} color="#007AFF" style={{ marginLeft: 8 }} />
              )}
            </Text>
            {(getFilteredStrategies(options?.recommendedStrategies || []) || options?.recommendedStrategies || []).map((strategy, index) => (
              <View key={index} style={styles.strategyCard}>
                <View style={styles.strategyHeader}>
                  <Text style={styles.strategyName}>{strategy.strategyName}</Text>
                  <View style={styles.strategyBadges}>
                    <View style={[styles.riskBadge, { 
                      backgroundColor: strategy.riskLevel === 'Low' ? '#E8F5E8' : 
                        strategy.riskLevel === 'Medium' ? '#FFF3CD' : '#F8D7DA'
                    }]}>
                      <Text style={[styles.riskBadgeText, { 
                        color: strategy.riskLevel === 'Low' ? '#155724' : 
                          strategy.riskLevel === 'Medium' ? '#856404' : '#721C24'
                      }]}>
                        {strategy.riskLevel}
                      </Text>
                    </View>
                    <Text style={styles.strategyType}>{strategy.strategyType}</Text>
                  </View>
                </View>
                <Text style={styles.strategyDescription}>{strategy.description}</Text>
                <View style={styles.strategyMetrics}>
                  <View style={styles.strategyMetric}>
                    <Text style={styles.strategyMetricLabel}>Max Profit</Text>
                    <Text style={[styles.strategyMetricValue, { color: '#34C759' }]}>
                      {strategy.maxProfit === Infinity ? '∞' : `$${strategy.maxProfit?.toFixed(2) || '0.00'}`}
                    </Text>
                  </View>
                  <View style={styles.strategyMetric}>
                    <Text style={styles.strategyMetricLabel}>Max Loss</Text>
                    <Text style={[styles.strategyMetricValue, { color: '#ef4444' }]}>
                      {strategy.maxLoss === Infinity ? '∞' : `$${strategy.maxLoss?.toFixed(2) || '0.00'}`}
                    </Text>
                  </View>
                  <View style={styles.strategyMetric}>
                    <Text style={styles.strategyMetricLabel}>Win Rate</Text>
                    <Text style={styles.strategyMetricValue}>
                      {(strategy.probabilityOfProfit * 100)?.toFixed(0) || '0'}%
                    </Text>
                  </View>
                  <View style={styles.strategyMetric}>
                    <Text style={styles.strategyMetricLabel}>Risk/Reward</Text>
                    <Text style={styles.strategyMetricValue}>
                      {strategy.riskRewardRatio === Infinity ? '∞' : strategy.riskRewardRatio?.toFixed(2) || '0.00'}
                    </Text>
                  </View>
                </View>
              </View>
            ))}
          </View>
        )}

        {/* Error Message */}
        {!options && !optionsLoading && (
          <View style={styles.errorContainer}>
            <Icon name="alert-circle" size={48} color="#ef4444" />
            <Text style={styles.errorText}>Unable to load options data</Text>
            {optionsError && (
              <Text style={styles.errorDetails}>
                Error: {optionsError.message}
              </Text>
            )}
          </View>
        )}
      </ScrollView>
    );
  };

  const renderTaxTab = () => {
    return (
      <View style={styles.tabContent}>
        <TaxOptimizationScreen />
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigateTo('portfolio')}>
          <Icon name="arrow-left" size={24} color="#1f2937" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Premium Analytics</Text>
        <TouchableOpacity onPress={() => navigateTo('subscription')}>
          <Icon name="star" size={24} color="#FFD700" />
        </TouchableOpacity>
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabNavigation}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'metrics' && styles.activeTab]}
          onPress={() => setActiveTab('metrics')}
        >
          <Text style={[styles.tabText, activeTab === 'metrics' && styles.activeTabText]}>
            Metrics
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'recommendations' && styles.activeTab]}
          onPress={() => setActiveTab('recommendations')}
        >
          <Text style={[styles.tabText, activeTab === 'recommendations' && styles.activeTabText]}>
            AI Insights
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'screening' && styles.activeTab]}
          onPress={() => setActiveTab('screening')}
        >
          <Text style={[styles.tabText, activeTab === 'screening' && styles.activeTabText]}>
            Screening
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'options' && styles.activeTab]}
          onPress={() => setActiveTab('options')}
        >
          <Text style={[styles.tabText, activeTab === 'options' && styles.activeTabText]}>
            Options
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'tax' && styles.activeTab]}
          onPress={() => setActiveTab('tax')}
        >
          <Text style={[styles.tabText, activeTab === 'tax' && styles.activeTabText]}>
            Tax
          </Text>
        </TouchableOpacity>
      </View>

      {/* Tab Content */}
      <View style={styles.tabContentContainer}>
        {activeTab === 'metrics' && renderMetricsTab()}
        {activeTab === 'recommendations' && renderRecommendationsTab()}
        {activeTab === 'screening' && renderScreeningTab()}
        {activeTab === 'options' && renderOptionsTab()}
        {activeTab === 'tax' && renderTaxTab()}
      </View>

      {/* Tooltip Modal */}
      <Modal
        visible={showTooltip !== null}
        transparent={true}
        animationType="fade"
        onRequestClose={() => setShowTooltip(null)}
      >
        <TouchableOpacity 
          style={styles.tooltipOverlay}
          activeOpacity={1}
          onPress={() => setShowTooltip(null)}
        >
          <View style={styles.tooltipContent}>
            <View style={styles.tooltipHeader}>
              <Text style={styles.tooltipTitle}>
                {showTooltip === 'putCallRatio' && 'Put/Call Ratio'}
                {showTooltip === 'ivRank' && 'Implied Volatility Rank'}
                {showTooltip === 'sentiment' && 'Market Sentiment'}
              </Text>
              <TouchableOpacity 
                style={styles.tooltipCloseButton}
                onPress={() => setShowTooltip(null)}
              >
                <Icon name="x" size={20} color="#8E8E93" />
              </TouchableOpacity>
            </View>
            <Text style={styles.tooltipText}>
              {showTooltip === 'putCallRatio' && 
                'The Put/Call Ratio shows the ratio of put options to call options being traded. ' +
                'A high ratio (>0.8) indicates bearish sentiment (more puts), while a low ratio (<0.6) ' +
                'indicates bullish sentiment (more calls). This is a contrarian indicator - extreme ' +
                'ratios often signal potential reversals.'
              }
              {showTooltip === 'ivRank' && 
                'IV Rank shows where current implied volatility stands relative to its 52-week range. ' +
                'High IV Rank (>70%) means options are expensive relative to historical levels, ' +
                'while low IV Rank (<30%) means options are cheap. This helps determine the best ' +
                'time to buy or sell options.'
              }
              {showTooltip === 'sentiment' && 
                'Market Sentiment combines multiple factors to gauge overall market mood for this stock. ' +
                'The score ranges from 0-100, where 70+ is bullish, 30-70 is neutral, and below 30 is bearish. ' +
                'This helps you understand the general market perception and potential contrarian opportunities.'
              }
            </Text>
          </View>
        </TouchableOpacity>
      </Modal>

      {/* Stock Details Modal */}
      <Modal
        visible={showStockDetailsModal}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setShowStockDetailsModal(false)}
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>
              {selectedStockDetails?.symbol} - Stock Details
            </Text>
            <TouchableOpacity
              style={styles.closeButton}
              onPress={() => setShowStockDetailsModal(false)}
            >
              <Icon name="x" size={24} color="#8E8E93" />
            </TouchableOpacity>
          </View>
          <ScrollView style={styles.modalContent}>
            {selectedStockDetails && (
              <>
                {/* Stock Header */}
                <View style={styles.stockDetailsHeader}>
                  <View style={styles.stockInfo}>
                    <Text style={styles.stockSymbol}>{selectedStockDetails.symbol}</Text>
                    <Text style={styles.stockName}>{selectedStockDetails.companyName}</Text>
                    <Text style={styles.stockSector}>{selectedStockDetails.sector}</Text>
                  </View>
                  <View style={styles.stockMetrics}>
                    <Text style={styles.stockPrice}>
                      ${selectedStockDetails.currentPrice?.toFixed(2) || 'N/A'}
                    </Text>
                    <Text style={styles.stockMLScore}>
                      ML Score: {selectedStockDetails.mlScore?.toFixed(1) || 'N/A'}
                    </Text>
                  </View>
                </View>
                {/* Detailed Metrics */}
                <View style={styles.detailedMetrics}>
                  <Text style={styles.sectionTitle}>Financial Metrics</Text>
                  <View style={styles.metricsGrid}>
                    <View style={styles.metricCard}>
                      <Text style={styles.metricLabel}>Market Cap</Text>
                      <Text style={styles.metricValue}>
                        ${(selectedStockDetails.marketCap / 1000000000).toFixed(1)}B
                      </Text>
                    </View>
                    <View style={styles.metricCard}>
                      <Text style={styles.metricLabel}>P/E Ratio</Text>
                      <Text style={styles.metricValue}>
                        {selectedStockDetails.peRatio?.toFixed(1) || 'N/A'}
                      </Text>
                    </View>
                    <View style={styles.metricCard}>
                      <Text style={styles.metricLabel}>Risk Level</Text>
                      <Text style={[styles.metricValue, { color: '#FF9500' }]}>
                        Medium
                      </Text>
                    </View>
                    <View style={styles.metricCard}>
                      <Text style={styles.metricLabel}>Growth Potential</Text>
                      <Text style={styles.metricValue}>
                        Moderate
                      </Text>
                    </View>
                  </View>
                </View>
                {/* Actions */}
                <View style={styles.modalActions}>
                  <TouchableOpacity 
                    style={[styles.modalActionButton, styles.primaryButton]}
                    onPress={async () => {
                      try {
                        const result = await client.mutate({
                          mutation: gql`
                            mutation AddToWatchlist($symbol: String!, $notes: String) {
                              addToWatchlist(symbol: $symbol, notes: $notes) {
                                success
                                message
                              }
                            }
                          `,
                          variables: {
                            symbol: selectedStockDetails.symbol,
                            notes: `Added from screening - ML Score: ${selectedStockDetails.mlScore?.toFixed(1) || 'N/A'}`
                          }
                        });
                        if (result.data?.addToWatchlist?.success) {
                          Alert.alert(
                            'Success',
                            `${selectedStockDetails.symbol} has been added to your watchlist!`,
                            [{ text: 'OK' }]
                          );
                          setShowStockDetailsModal(false);
                        } else {
                          Alert.alert(
                            'Error',
                            result.data?.addToWatchlist?.message || 'Failed to add to watchlist',
                            [{ text: 'OK' }]
                          );
                        }
                      } catch (error) {
                        console.error('Error adding to watchlist:', error);
                        Alert.alert(
                          'Error',
                          'Failed to add to watchlist. Please try again.',
                          [{ text: 'OK' }]
                        );
                      }
                    }}
                  >
                    <Icon name="plus" size={20} color="#fff" />
                    <Text style={styles.primaryButtonText}>Add to Watchlist</Text>
                  </TouchableOpacity>
                  <TouchableOpacity 
                    style={[styles.modalActionButton, styles.secondaryButton]}
                    onPress={() => {
                      setShowStockDetailsModal(false);
                      navigateTo('stock');
                    }}
                  >
                    <Icon name="search" size={20} color="#007AFF" />
                    <Text style={styles.secondaryButtonText}>View Full Analysis</Text>
                  </TouchableOpacity>
                </View>
              </>
            )}
          </ScrollView>
        </SafeAreaView>
      </Modal>

      {/* Rebalancing Results Modal */}
      <Modal
        visible={showRebalancingResults}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <RebalancingResultsDisplay
          onClose={() => setShowRebalancingResults(false)}
          showCloseButton={true}
        />
      </Modal>

      {/* Dry Run Results Modal */}
      <Modal
        visible={showDryRunModal}
        animationType="slide"
        presentationStyle="pageSheet"
      >
        <SafeAreaView style={styles.container}>
          <View style={styles.header}>
            <TouchableOpacity onPress={() => setShowDryRunModal(false)}>
              <Icon name="x" size={24} color="#007AFF" />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>Preview Rebalancing</Text>
            <View style={{ width: 24 }} />
          </View>
          <ScrollView style={styles.modalContent}>
            {dryRunResults && (
              <View>
                <View style={styles.previewHeader}>
                  <Icon name="eye" size={24} color="#007AFF" />
                  <Text style={styles.previewTitle}>This is a preview - no trades will be executed</Text>
                </View>
                <View style={styles.previewSection}>
                  <Text style={styles.sectionTitle}>Sector Changes</Text>
                  {dryRunResults.changesMade && dryRunResults.changesMade.length > 0 ? (
                    dryRunResults.changesMade.map((change, index) => (
                      <Text key={index} style={styles.previewItem}>• {change}</Text>
                    ))
                  ) : (
                    <Text style={styles.previewItem}>No sector changes</Text>
                  )}
                </View>
                <View style={styles.previewSection}>
                  <Text style={styles.sectionTitle}>Stock Trades</Text>
                  {dryRunResults.stockTrades && dryRunResults.stockTrades.length > 0 ? (
                    dryRunResults.stockTrades.map((trade, index) => (
                      <View key={index} style={styles.tradeItem}>
                        <Text style={styles.tradeAction}>
                          {trade.action} {trade.shares} shares of {trade.symbol}
                        </Text>
                        <Text style={styles.tradeDetails}>
                          {trade.companyName} @ ${trade.price.toFixed(2)} = ${trade.totalValue.toFixed(2)}
                        </Text>
                      </View>
                    ))
                  ) : (
                    <Text style={styles.previewItem}>No stock trades</Text>
                  )}
                </View>
                <View style={styles.previewSection}>
                  <Text style={styles.sectionTitle}>Cost Summary</Text>
                  <Text style={styles.previewItem}>Transaction Cost: ${dryRunResults.rebalanceCost?.toFixed(2) || '0.00'}</Text>
                  <Text style={styles.previewItem}>New Portfolio Value: ${dryRunResults.newPortfolioValue?.toFixed(2) || '0.00'}</Text>
                </View>
                {dryRunResults.estimatedImprovement && (
                  <View style={styles.previewSection}>
                    <Text style={styles.sectionTitle}>Expected Improvement</Text>
                    <Text style={styles.previewItem}>{dryRunResults.estimatedImprovement}</Text>
                  </View>
                )}
                <View style={styles.previewActions}>
                  <TouchableOpacity
                    style={[styles.actionButton, styles.cancelButton]}
                    onPress={() => setShowDryRunModal(false)}
                  >
                    <Text style={styles.cancelButtonText}>Close Preview</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.actionButton, styles.executeButton]}
                    onPress={() => {
                      setShowDryRunModal(false);
                      aiRebalancePortfolio({
                        variables: {
                          riskTolerance: 'medium',
                          maxRebalancePercentage: 20.0
                        }
                      });
                    }}
                  >
                    <Text style={styles.executeButtonText}>Execute Rebalancing</Text>
                  </TouchableOpacity>
                </View>
              </View>
            )}
          </ScrollView>
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1f2937',
  },
  tabNavigation: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  tab: {
    flex: 1,
    paddingVertical: 14,
    alignItems: 'center',
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  activeTab: {
    borderBottomColor: '#007AFF',
  },
  tabText: {
    fontSize: 14,
    color: '#6b7280',
    fontWeight: '500',
  },
  activeTabText: {
    color: '#007AFF',
    fontWeight: '600',
  },
  tabContentContainer: {
    flex: 1,
  },
  tabContent: {
    flex: 1,
    padding: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 40,
  },
  loadingText: {
    fontSize: 16,
    color: '#6b7280',
    marginTop: 16,
    fontWeight: '500',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 40,
  },
  errorText: {
    fontSize: 16,
    color: '#ef4444',
    marginTop: 16,
    textAlign: 'center',
    fontWeight: '500',
  },
  errorDetails: {
    fontSize: 12,
    color: '#dc2626',
    textAlign: 'center',
    marginTop: 8,
    paddingHorizontal: 20,
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1f2937',
    marginBottom: 16,
  },
  mockDataIndicator: {
    backgroundColor: '#fef3c7',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#f59e0b',
  },
  mockDataText: {
    fontSize: 12,
    color: '#92400e',
    fontWeight: '600',
  },
  updatedLabel: {
    fontSize: 14,
    color: '#34C759',
    fontWeight: '600',
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  metricCard: {
    width: (width - 64) / 2,
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  metricHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  metricLabel: {
    fontSize: 14,
    color: '#6b7280',
    marginLeft: 8,
    fontWeight: '500',
  },
  metricValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1f2937',
  },
  returnsContainer: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  returnItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  returnLabel: {
    fontSize: 16,
    color: '#6b7280',
    fontWeight: '500',
  },
  returnValue: {
    fontSize: 16,
    fontWeight: '600',
  },
  summaryCard: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  summaryItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  summaryLabel: {
    fontSize: 16,
    color: '#6b7280',
    fontWeight: '500',
  },
  summaryValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
  },
  analysisCard: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  analysisItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  analysisLabel: {
    fontSize: 16,
    color: '#6b7280',
    fontWeight: '500',
  },
  analysisValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
  },
  refreshButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f3f4f6',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
  },
  refreshButtonText: {
    fontSize: 14,
    color: '#007AFF',
    marginLeft: 8,
    fontWeight: '500',
  },
  recommendationCard: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  recommendationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  recommendationSymbol: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1f2937',
  },
  recommendationBadge: {
    backgroundColor: '#34C759',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  recommendationText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#fff',
  },
  recommendationName: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 8,
    fontWeight: '500',
  },
  recommendationReasoning: {
    fontSize: 14,
    color: '#1f2937',
    marginBottom: 12,
    lineHeight: 20,
  },
  recommendationMetrics: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  recommendationMetric: {
    fontSize: 12,
    color: '#6b7280',
    flex: 1,
    minWidth: '45%',
    marginBottom: 4,
  },
  rebalanceButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  rebalanceButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#007AFF',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    flex: 1,
  },
  rebalanceButtonDisabled: {
    backgroundColor: '#e5e7eb',
  },
  rebalanceButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 8,
  },
  viewResultsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f3f4f6',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  viewResultsButtonText: {
    color: '#007AFF',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 8,
  },
  rebalanceCard: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  rebalanceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  rebalanceAction: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
  },
  priorityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  priorityText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#fff',
  },
  rebalanceReasoning: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 12,
    lineHeight: 20,
  },
  rebalanceAllocation: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  allocationLabel: {
    fontSize: 14,
    color: '#6b7280',
    fontWeight: '500',
  },
  allocationArrow: {
    fontSize: 16,
    color: '#007AFF',
    marginHorizontal: 12,
    fontWeight: '600',
  },
  noSuggestionsCard: {
    backgroundColor: '#f0fdf4',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#bbf7d0',
  },
  noSuggestionsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
    marginTop: 8,
    marginBottom: 4,
  },
  noSuggestionsText: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    lineHeight: 20,
  },
  // Stock Screening Styles
  filterGroup: {
    marginBottom: 20,
  },
  filterLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 12,
  },
  filterRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  filterChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#f3f4f6',
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  filterChipActive: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  filterChipText: {
    fontSize: 14,
    color: '#6b7280',
    fontWeight: '500',
  },
  filterChipTextActive: {
    color: '#fff',
  },
  rangeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  rangeLabel: {
    fontSize: 14,
    color: '#6b7280',
    minWidth: 60,
    fontWeight: '500',
  },
  slider: {
    flex: 1,
    height: 40,
  },
  sliderTrack: {
    height: 4,
    backgroundColor: '#e5e7eb',
    borderRadius: 2,
    position: 'relative',
  },
  sliderFill: {
    height: 4,
    backgroundColor: '#007AFF',
    borderRadius: 2,
    position: 'absolute',
    top: 0,
    left: 0,
  },
  sliderThumb: {
    position: 'absolute',
    top: -8,
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: '#007AFF',
  },
  searchButton: {
    backgroundColor: '#007AFF',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 20,
  },
  searchButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  searchButtonDisabled: {
    backgroundColor: '#e5e7eb',
  },
  loadingButtonContent: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingResultsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
    paddingHorizontal: 16,
  },
  loadingResultsText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#6b7280',
  },
  stockCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  stockHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  stockInfo: {
    flex: 1,
  },
  stockSymbol: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1f2937',
  },
  stockName: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
    fontWeight: '500',
  },
  stockSector: {
    fontSize: 12,
    color: '#007AFF',
    marginTop: 4,
    fontWeight: '500',
  },
  stockMetrics: {
    alignItems: 'flex-end',
  },
  stockPrice: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1f2937',
  },
  stockMLScore: {
    fontSize: 12,
    color: '#34C759',
    marginTop: 2,
    fontWeight: '500',
  },
  stockDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  stockDetailItem: {
    flex: 1,
    alignItems: 'center',
  },
  stockDetailLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 4,
    fontWeight: '500',
  },
  stockDetailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1f2937',
  },
  stockActions: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    alignItems: 'center',
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6b7280',
  },
  addButton: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  addButtonText: {
    color: '#fff',
  },
  noResultsContainer: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  noResultsText: {
    fontSize: 16,
    color: '#6b7280',
    marginTop: 16,
    textAlign: 'center',
    fontWeight: '500',
  },
  noResultsSubtext: {
    fontSize: 14,
    color: '#9ca3af',
    marginTop: 8,
    textAlign: 'center',
  },
  // Options Analysis Styles
  optionsSearchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  searchIcon: {
    marginRight: 12,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: '#1f2937',
    paddingVertical: 4,
  },
  clearButton: {
    padding: 4,
    marginRight: 8,
  },
  optionsSearchButton: {
    padding: 8,
    marginLeft: 8,
    backgroundColor: '#007AFF',
    borderRadius: 8,
  },
  optionsSearchButtonDisabled: {
    opacity: 0.5,
    backgroundColor: '#e5e7eb',
  },
  quickSelectLabel: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 8,
    fontWeight: '500',
  },
  stockSelector: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 16,
  },
  stockButton: {
    backgroundColor: '#f3f4f6',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  selectedStockButton: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
    shadowColor: '#007AFF',
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 3,
  },
  stockButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6b7280',
  },
  selectedStockButtonText: {
    color: '#fff',
    fontWeight: '700',
  },
  stockInfoContainer: {
    marginBottom: 20,
  },
  stockInfoText: {
    fontSize: 14,
    color: '#6b7280',
    fontStyle: 'italic',
    textAlign: 'center',
  },
  tooltipButton: {
    padding: 2,
    marginLeft: 4,
  },
  metricExplanation: {
    fontSize: 12,
    color: '#9ca3af',
    textAlign: 'center',
    lineHeight: 14,
    marginTop: 4,
  },
  // Tooltip Styles
  tooltipOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  tooltipContent: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    maxWidth: '90%',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 4,
    },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 8,
  },
  tooltipHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  tooltipTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1f2937',
    flex: 1,
  },
  tooltipCloseButton: {
    padding: 4,
  },
  tooltipText: {
    fontSize: 16,
    color: '#374151',
    lineHeight: 24,
  },
  outlookSelector: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 16,
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    padding: 4,
  },
  outlookButton: {
    flex: 1,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 6,
    alignItems: 'center',
    marginHorizontal: 2,
  },
  outlookButtonActive: {
    backgroundColor: '#007AFF',
  },
  outlookButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#6b7280',
  },
  outlookButtonTextActive: {
    color: '#fff',
    fontWeight: '600',
  },
  aiOptionsButton: {
    backgroundColor: '#f8f9fa',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  aiOptionsContent: {
    alignItems: 'center',
  },
  aiOptionsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  aiOptionsTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1f2937',
    marginLeft: 8,
  },
  aiOptionsDescription: {
    fontSize: 14,
    color: '#6b7280',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 16,
  },
  aiOptionsFeatures: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    marginBottom: 16,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: 8,
    marginVertical: 4,
  },
  featureText: {
    fontSize: 12,
    color: '#374151',
    marginLeft: 4,
    fontWeight: '500',
  },
  aiOptionsFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
  },
  aiOptionsAction: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
    marginRight: 8,
  },
  strategyCard: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  strategyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  strategyName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
  },
  strategyBadges: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  riskBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  riskBadgeText: {
    fontSize: 12,
    fontWeight: '600',
  },
  strategyType: {
    fontSize: 12,
    color: '#6b7280',
    backgroundColor: '#f3f4f6',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  strategyDescription: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 8,
    lineHeight: 20,
  },
  strategyMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  strategyMetric: {
    alignItems: 'center',
  },
  strategyMetricLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 4,
    fontWeight: '500',
  },
  strategyMetricValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
  },
  // Modal Styles
  modalContainer: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1f2937',
    flex: 1,
  },
  closeButton: {
    padding: 8,
  },
  modalContent: {
    flex: 1,
    padding: 16,
  },
  stockDetailsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 20,
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  detailedMetrics: {
    marginBottom: 20,
  },
  modalActions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 20,
  },
  modalActionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    paddingHorizontal: 20,
    borderRadius: 12,
  },
  primaryButton: {
    backgroundColor: '#007AFF',
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  secondaryButton: {
    backgroundColor: '#f3f4f6',
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  secondaryButtonText: {
    color: '#007AFF',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  // Preview Modal Styles
  previewHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#eff6ff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: '#bfdbfe',
  },
  previewTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1e40af',
    marginLeft: 12,
  },
  previewSection: {
    marginBottom: 20,
  },
  previewItem: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 4,
    lineHeight: 20,
  },
  tradeItem: {
    backgroundColor: '#f8f9fa',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
  },
  tradeAction: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1f2937',
  },
  tradeDetails: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 4,
  },
  previewActions: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 20,
  },
  cancelButton: {
    backgroundColor: '#f3f4f6',
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  cancelButtonText: {
    color: '#6b7280',
    fontSize: 16,
    fontWeight: '600',
  },
  executeButton: {
    backgroundColor: '#ef4444',
  },
  executeButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});

export default PremiumAnalyticsScreen;
