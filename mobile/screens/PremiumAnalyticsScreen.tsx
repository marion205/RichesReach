import React, { useState, useEffect } from 'react';
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
import RebalancingStorageService from '../services/RebalancingStorageService';
import RebalancingResultsDisplay from '../components/RebalancingResultsDisplay';
// Custom Slider Component (replacing @react-native-community/slider)
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
// GraphQL Queries - Using premium queries for authenticated users
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
// Options Analysis Queries - Using premium query for authenticated users
const GET_OPTIONS_ANALYSIS = gql`
  query GetOptionsAnalysis($symbol: String!) {
    optionsAnalysis(symbol: $symbol) {
      underlyingSymbol
      underlyingPrice
      optionsChain {
        expirationDates
        calls {
          symbol
          contractSymbol
          strike
          expirationDate
          optionType
          bid
          ask
          lastPrice
          volume
          openInterest
          impliedVolatility
          delta
          gamma
          theta
          vega
          rho
          intrinsicValue
          timeValue
          daysToExpiration
        }
        puts {
          symbol
          contractSymbol
          strike
          expirationDate
          optionType
          bid
          ask
          lastPrice
          volume
          openInterest
          impliedVolatility
          delta
          gamma
          theta
          vega
          rho
          intrinsicValue
          timeValue
          daysToExpiration
        }
        greeks {
          delta
          gamma
          theta
          vega
          rho
        }
      }
      unusualFlow {
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
      marketSentiment {
        putCallRatio
        impliedVolatilityRank
        skew
        sentimentScore
        sentimentDescription
      }
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
        sentimentDescription
        sentimentScore
        putCallRatio
        impliedVolatilityRank
      }
      unusualFlow {
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
// Stock Screening Query
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
riskLevel
growthPotential
}
}
`;
// Props interface removed - using PropTypes or JSDoc instead
// Helper functions for sector analysis
const getSectorInfo = (sector: string) => {
const sectorData = {
'Technology': {
description: 'Software, hardware, and tech services',
riskLevel: 'Medium',
riskColor: '#FF9500',
color: '#007AFF'
},
'Communication Services': {
description: 'Media, telecom, and social platforms',
riskLevel: 'High',
riskColor: '#FF3B30',
color: '#FF2D92'
},
'Healthcare': {
description: 'Pharmaceuticals and medical devices',
riskLevel: 'Low',
riskColor: '#34C759',
color: '#30D158'
},
'Financial Services': {
description: 'Banks, insurance, and financial tech',
riskLevel: 'Medium',
riskColor: '#FF9500',
color: '#FF9F0A'
},
'Consumer Cyclical': {
description: 'Retail, automotive, and discretionary spending',
riskLevel: 'High',
riskColor: '#FF3B30',
color: '#FF6B6B'
},
'Consumer Defensive': {
description: 'Food, beverages, and household products',
riskLevel: 'Low',
riskColor: '#34C759',
color: '#32D74B'
},
'Energy': {
description: 'Oil, gas, and renewable energy',
riskLevel: 'High',
riskColor: '#FF3B30',
color: '#FF453A'
},
'Industrials': {
description: 'Manufacturing, aerospace, and infrastructure',
riskLevel: 'Medium',
riskColor: '#FF9500',
color: '#FFCC02'
},
'Materials': {
description: 'Chemicals, metals, and mining',
riskLevel: 'High',
riskColor: '#FF3B30',
color: '#FF6B35'
},
'Utilities': {
description: 'Electric, gas, and water utilities',
riskLevel: 'Low',
riskColor: '#34C759',
color: '#64D2FF'
},
'Real Estate': {
description: 'REITs and real estate companies',
riskLevel: 'Medium',
riskColor: '#FF9500',
color: '#BF5AF2'
}
};
return sectorData[sector] || {
description: 'Other industries',
riskLevel: 'Medium',
riskColor: '#8E8E93',
color: '#8E8E93'
};
};
const getSectorInsight = (sector: string, percentage: number) => {
if (isNaN(percentage)) return 'No data available';
const insights = {
'Technology': percentage > 40 ? 
'High tech exposure - great for growth but increases volatility' :
percentage > 20 ?
'Moderate tech allocation - balanced growth potential' :
'Low tech exposure - consider adding for growth',
'Communication Services': percentage > 30 ?
'High communication exposure - watch for regulatory risks' :
'Moderate communication allocation - good for diversification',
'Healthcare': percentage > 25 ?
'Strong healthcare allocation - defensive and stable' :
'Consider adding healthcare for stability',
'Financial Services': percentage > 30 ?
'High financial exposure - sensitive to interest rates' :
'Moderate financial allocation - good for dividends',
'Consumer Cyclical': percentage > 25 ?
'High consumer cyclical - economic sensitivity' :
'Moderate consumer exposure - balanced approach',
'Consumer Defensive': percentage > 20 ?
'Good defensive allocation - recession resistant' :
'Consider adding consumer staples for stability'
};
return insights[sector] || `Allocated ${percentage.toFixed(1)}% to ${sector}`;
};
const getPortfolioRecommendations = (sectorAllocation: any, riskMetrics: any) => {
const recommendations = [];
const sectors = Object.keys(sectorAllocation);
const totalSectors = sectors.length;
// Diversification recommendations
if (totalSectors < 3) {
recommendations.push('Consider diversifying across more sectors (aim for 5-7 sectors)');
}
// Concentration risk
const maxAllocation = Math.max(...Object.values(sectorAllocation).map(Number));
if (maxAllocation > 50) {
recommendations.push('High concentration in one sector - consider rebalancing');
}
// Specific sector recommendations
if (sectorAllocation['Technology'] > 40) {
recommendations.push('High tech concentration - consider adding defensive sectors');
}
if (!sectorAllocation['Healthcare'] || sectorAllocation['Healthcare'] < 10) {
recommendations.push('Consider adding healthcare for defensive exposure');
}
if (!sectorAllocation['Consumer Defensive'] || sectorAllocation['Consumer Defensive'] < 10) {
recommendations.push('Add consumer staples for recession protection');
}
// Risk assessment
if (riskMetrics?.diversification_score < 50) {
recommendations.push('Low diversification score - spread risk across more sectors');
}
return recommendations.length > 0 ? recommendations : ['Portfolio is well balanced across sectors'];
};
const PremiumAnalyticsScreen = ({ navigateTo }) => {
const [activeTab, setActiveTab] = useState('metrics');
const [refreshing, setRefreshing] = useState(false);
const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
const [searchSymbol, setSearchSymbol] = useState('');
const [isSearching, setIsSearching] = useState(false);
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
const [tradeLimits, setTradeLimits] = useState({
maxTradeValue: 10000, // $10,000 max per trade
maxDailyTrades: 10, // 10 trades per day
maxRebalanceAmount: 50000, // $50,000 max rebalance amount
dailyTradeCount: 0,
dailyTradeValue: 0
});
// Market outlook state
const [marketOutlook, setMarketOutlook] = useState('Neutral');

// Track active tab changes
useEffect(() => {
}, [activeTab]);

// Safety check functions
const checkTradeLimits = (trades) => {
const totalTradeValue = trades.reduce((sum, trade) => sum + (trade.totalValue || 0), 0);
const tradeCount = trades.length;

// Include today's running tallies
const projectedCount = tradeLimits.dailyTradeCount + tradeCount;
const projectedValue = tradeLimits.dailyTradeValue + totalTradeValue;

// Check individual trade limits
const exceedsTradeValue = trades.some(trade => (trade.totalValue || 0) > tradeLimits.maxTradeValue);
if (exceedsTradeValue) {
return {
allowed: false,
reason: `Individual trade exceeds $${tradeLimits.maxTradeValue.toLocaleString()} limit`
};
}
// Check daily trade count
if (projectedCount > tradeLimits.maxDailyTrades) {
return {
allowed: false,
reason: `Exceeds daily trade limit of ${tradeLimits.maxDailyTrades} trades`
};
}
// Check total rebalance amount
if (projectedValue > tradeLimits.maxRebalanceAmount) {
return {
allowed: false,
reason: `Total rebalance amount ($${projectedValue.toLocaleString()}) exceeds $${tradeLimits.maxRebalanceAmount.toLocaleString()} limit`
};
}
return { allowed: true };
};
const performDryRun = async () => {
setIsDryRunMode(true);
try {
await aiRebalancePortfolio({
variables: {
riskTolerance: 'medium',
maxRebalancePercentage: 20.0,
dryRun: true
}
});
} catch (error) {
console.error('Dry run failed:', error);
const err = error as Error;
Alert.alert('Dry Run Failed', `Failed to simulate rebalancing: ${err?.message || 'Unknown error'}`);
}
};
// Function to cycle through market outlook options
const toggleMarketOutlook = () => {
const outlooks: ('Bullish' | 'Bearish' | 'Neutral')[] = ['Bullish', 'Bearish', 'Neutral'];
const currentIndex = outlooks.indexOf(marketOutlook);
const nextIndex = (currentIndex + 1) % outlooks.length;
setMarketOutlook(outlooks[nextIndex]);
};
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
outlook.includes('hedge') || 
outlook.includes('protection') ||
strategyType.includes('hedge') ||
strategy.strategyName?.toLowerCase().includes('protective put');
default:
return true;
}
});
// Filtered strategies ready
return filtered;
};
// Queries
const { data: metricsData, loading: metricsLoading, refetch: refetchMetrics } = useQuery(
GET_PREMIUM_PORTFOLIO_METRICS,
{
errorPolicy: 'all',
onCompleted: (data) => {
          // Portfolio metrics data loaded
        },
onError: (error) => {
console.error('❌ PremiumAnalyticsScreen: Metrics query error:', error);
const err = error as Error;
console.error('❌ Error details:', {
message: err?.message,
graphQLErrors: error.graphQLErrors,
networkError: error.networkError,
stack: err?.stack
});
if (err?.message?.includes('Premium subscription required')) {
Alert.alert(
'Premium Required',
'This feature requires a premium subscription. Upgrade now to access advanced analytics.',
[
{ text: 'Cancel', style: 'cancel' },
{ text: 'Upgrade', onPress: () => navigateTo('subscription') }
]
);
}
}
});

const {
  data: recommendationsData,
  loading: recommendationsLoading,
  error: recommendationsError,
  refetch: refetchRecommendations,
} = useQuery(
  GET_AI_RECOMMENDATIONS,
  {
    variables: { riskTolerance: 'medium' },
    errorPolicy: 'all', // 'ignore' hides partial data; 'all' is usually better
    fetchPolicy: 'network-only', // Always fetch fresh data, bypass cache
    onCompleted: () => {
      // AI recommendations data loaded
    },
    onError: (error) => {
      console.error('❌ PremiumAnalyticsScreen: AI Recommendations query error:', error);
      const err = error as Error;
      console.error('❌ Recommendations error details:', {
        message: err?.message,
        // `any` casts avoid TS complaining when these are undefined
        graphQLErrors: (error as any).graphQLErrors,
        networkError: (error as any).networkError,
        stack: err?.stack,
      });

      if (err?.message?.includes('Premium subscription required')) {
        Alert.alert(
          'Premium Required',
          'This feature requires a premium subscription. Upgrade now to access AI recommendations.',
          [
            { text: 'Cancel', style: 'cancel' },
            { text: 'Upgrade', onPress: () => navigateTo('subscription') },
          ],
        );
      }
    },
  },
);

const [aiRebalancePortfolio, { loading: rebalanceLoading }] = useMutation(AI_REBALANCE_PORTFOLIO, {
onCompleted: async (data) => {
if (data.aiRebalancePortfolio.success) {
const result = data.aiRebalancePortfolio;
// If this is a dry run, show results without executing
if (isDryRunMode) {
setDryRunResults(result);
setShowDryRunModal(true);
setIsDryRunMode(false);
return;
}
// Safety checks for actual execution
if (result.stockTrades && result.stockTrades.length > 0) {
const safetyCheck = checkTradeLimits(result.stockTrades);
if (!safetyCheck.allowed) {
Alert.alert(
' Trade Limit Exceeded',
`Cannot execute rebalancing: ${safetyCheck.reason}\n\nPlease adjust your rebalancing parameters or contact support.`,
[{ text: 'OK' }]
);
return;
}
}
const changesText = Array.isArray(result.changesMade) && result.changesMade.length > 0 
? `\n\nSector Changes:\n${result.changesMade.map(change => `• ${change}`).join('\n')}`
: '\n\nNo sector changes were made (all suggestions exceeded the 20% rebalance limit).';
const tradesText = Array.isArray(result.stockTrades) && result.stockTrades.length > 0
? `\n\nStock Trades Executed:\n${result.stockTrades.map(trade => 
`• ${trade.action} ${trade.shares} shares of ${trade.symbol} (${trade.companyName}) at $${trade.price.toFixed(2)} = $${trade.totalValue.toFixed(2)}`
).join('\n')}`
: '\n\nNo stock trades were executed.';
const costText = result.rebalanceCost > 0 && Array.isArray(result.stockTrades)
? `\n\nTransaction Costs (0.1% per trade):\n${result.stockTrades.map(trade => 
`• ${trade.symbol}: $${(trade.totalValue * 0.001).toFixed(2)}`
).join('\n')}\n\nTotal Transaction Cost: $${result.rebalanceCost.toFixed(2)}`
: '';
const improvementText = result.estimatedImprovement 
? `\n\n${result.estimatedImprovement}`
: '';
// Store the rebalancing result
setLastRebalancingResult(result);
setRebalancingPerformed(true);

// Update daily counters if executed (not dry run)
if (result.stockTrades?.length) {
const addedValue = (result.stockTrades || []).reduce((s, t) => s + (t.totalValue || 0), 0);
setTradeLimits(prev => ({
...prev,
dailyTradeCount: prev.dailyTradeCount + (result.stockTrades?.length || 0),
dailyTradeValue: prev.dailyTradeValue + addedValue
}));
}

// Save to persistent storage
try {
const storageService = RebalancingStorageService.getInstance();
await storageService.saveRebalancingResult({
success: result.success,
message: result.message,
changesMade: result.changesMade || [],
stockTrades: result.stockTrades || [],
newPortfolioValue: result.newPortfolioValue || 0,
rebalanceCost: result.rebalanceCost || 0,
estimatedImprovement: result.estimatedImprovement || '',
riskTolerance: 'medium', // You might want to pass this from the mutation
maxRebalancePercentage: 20.0, // You might want to pass this from the mutation
});
} catch (error) {
console.error(' Error saving rebalancing result to storage:', error);
}
// Refresh recommendations to get updated rebalancing suggestions
try {
await refetchRecommendations();
} catch (error) {
console.error(' Error refreshing recommendations:', error);
}
Alert.alert(
' Rebalancing Complete!',
`${result.message}${changesText}${tradesText}${costText}${improvementText}`,
[
{ text: 'View Updated Recommendations', onPress: () => {
// The state is already set above, this just confirms the user wants to see updates
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
// Options Analysis Query - Try premium first, fallback to test
const { data: optionsData, loading: optionsLoading, error: optionsError, refetch: refetchOptions } = useQuery(
GET_OPTIONS_ANALYSIS,
{
variables: { symbol: selectedSymbol },
errorPolicy: 'all',
onCompleted: (data) => {
          // Options analysis data loaded
        },
onError: (error) => {
console.error('❌ PremiumAnalyticsScreen: Options Analysis Error:', error);
const err = error as Error;
console.error('❌ Options error details:', {
message: err?.message,
graphQLErrors: error.graphQLErrors,
networkError: error.networkError,
stack: err?.stack
});
if (err?.message?.includes('Premium subscription required')) {
Alert.alert(
'Premium Required',
'This feature requires a premium subscription. Upgrade now to access options analysis.',
[
{ text: 'Cancel', style: 'cancel' },
{ text: 'Upgrade', onPress: () => navigateTo('subscription') }
]
);
}
}
});
// Fallback test query if premium fails
const { data: testOptionsData, loading: testOptionsLoading, error: testOptionsError } = useQuery(
GET_OPTIONS_ANALYSIS_TEST,
{
variables: { symbol: selectedSymbol },
errorPolicy: 'all',
skip: !optionsError, // Only run if premium query fails
onCompleted: (data) => {
          // Test options analysis data loaded
        },
onError: (error) => {
console.error('❌ PremiumAnalyticsScreen: Test Options Analysis Error:', error);
const err = error as Error;
console.error('❌ Test options error details:', {
message: err?.message,
graphQLErrors: error.graphQLErrors,
networkError: error.networkError,
stack: error.stack
});
}
});
// Options data - accessible throughout component
const options = optionsData?.optionsAnalysis || testOptionsData?.testOptionsAnalysis;

// Track metrics loading state
useEffect(() => {
  // Track loading state changes
}, [metricsLoading, metricsData]);
const onRefresh = async () => {
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
};
const handleSearch = () => {
if (searchSymbol.trim()) {
const next = searchSymbol.trim().toUpperCase();
setIsSearching(true);
setSelectedSymbol(next);
setSearchSymbol('');
// Refetch options data with new symbol
refetchOptions({ symbol: next });
setTimeout(() => setIsSearching(false), 1000);
}
};
const handleQuickSelect = (symbol: string) => {
setIsSearching(true);
setSelectedSymbol(symbol);
refetchOptions({ symbol });
setTimeout(() => setIsSearching(false), 1000);
};
// Stock Screening Functions
const handleScreeningSearch = async () => {
setScreeningLoading(true);
try {
// Convert filters to GraphQL variables
const variables = {
sector: screeningFilters.sector,
minMlScore: screeningFilters.minMLScore,
limit: 50
};
// Call GraphQL query
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
};
const renderMetricsTab = () => {

if (metricsLoading) {
return (
<View style={styles.loadingContainer}>
<Text style={styles.loadingText}>Loading advanced metrics...</Text>
</View>
);
}
const metrics = metricsData?.portfolioMetrics;
console.log('🔍 METRICS DATA:', metrics);
console.log('🔍 HOLDINGS COUNT:', metrics?.holdings?.length);
if (!metrics) {
return (
<View style={styles.errorContainer}>
<Icon name="alert-circle" size={48} color="#FF3B30" />
<Text style={styles.errorText}>Unable to load portfolio metrics</Text>
</View>
);
}
// Parse sector allocation JSON string if it exists
let parsedSectorAllocation = {};
if (metrics.sectorAllocation) {
try {
parsedSectorAllocation = typeof metrics.sectorAllocation === 'string' 
? JSON.parse(metrics.sectorAllocation) 
: metrics.sectorAllocation;
} catch (error) {
console.error('Error parsing sector allocation:', error);
parsedSectorAllocation = {};
}
}
// Parse risk metrics JSON string if it exists
let parsedRiskMetrics = {};
if (metrics.riskMetrics) {
try {
parsedRiskMetrics = typeof metrics.riskMetrics === 'string' 
? JSON.parse(metrics.riskMetrics) 
: metrics.riskMetrics;
} catch (error) {
console.error(' Error parsing risk metrics:', error);
parsedRiskMetrics = {};
}
} else {
}
// Create updated metrics object with parsed data
const updatedMetrics = {
...metrics,
sectorAllocation: parsedSectorAllocation,
riskMetrics: parsedRiskMetrics
};
// Debug: Log the parsed risk metrics
return (
<ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false}>
{/* Performance Overview */}
<View style={styles.section}>
<Text style={styles.sectionTitle}>Performance Overview</Text>
<View style={styles.metricsGrid}>
<View style={styles.metricCard}>
<Text style={styles.metricLabel}>Total Value</Text>
<Text style={styles.metricValue}>
${metrics.totalValue?.toLocaleString() || '0.00'}
</Text>
</View>
<View style={styles.metricCard}>
<Text style={styles.metricLabel}>Total Return</Text>
<Text style={[
styles.metricValue,
{ color: metrics.totalReturn >= 0 ? '#34C759' : '#FF3B30' }
]}>
{metrics.totalReturnPercent?.toFixed(2) || '0.00'}%
</Text>
</View>
<View style={styles.metricCard}>
<Text style={styles.metricLabel}>Volatility</Text>
<Text style={styles.metricValue}>
{metrics.volatility != null && !isNaN(Number(metrics.volatility)) ? `${Number(metrics.volatility).toFixed(1)}%` : 'N/A'}
</Text>
</View>
<View style={styles.metricCard}>
<Text style={styles.metricLabel}>Sharpe Ratio</Text>
<Text style={styles.metricValue}>
{metrics.sharpeRatio != null && !isNaN(Number(metrics.sharpeRatio)) ? Number(metrics.sharpeRatio).toFixed(2) : 'N/A'}
</Text>
</View>
</View>
</View>
{/* Risk Metrics */}
<View style={styles.section}>
<Text style={styles.sectionTitle}>Risk Analysis</Text>
<View style={styles.riskContainer}>
<View style={styles.riskItem}>
<Text style={styles.riskLabel}>Max Drawdown</Text>
<Text style={styles.riskValue}>
{metrics.maxDrawdown != null && !isNaN(Number(metrics.maxDrawdown)) ? `${Number(metrics.maxDrawdown).toFixed(1)}%` : 'N/A'}
</Text>
</View>
<View style={styles.riskItem}>
<Text style={styles.riskLabel}>Beta</Text>
<Text style={styles.riskValue}>
{metrics.beta != null && !isNaN(Number(metrics.beta)) ? Number(metrics.beta).toFixed(2) : 'N/A'}
</Text>
</View>
<View style={styles.riskItem}>
<Text style={styles.riskLabel}>Alpha</Text>
<Text style={styles.riskValue}>
{metrics.alpha != null && !isNaN(Number(metrics.alpha)) ? Number(metrics.alpha).toFixed(2) : 'N/A'}
</Text>
</View>
</View>
</View>
{/* Sector Allocation */}
{updatedMetrics.sectorAllocation && Object.keys(updatedMetrics.sectorAllocation).length > 0 && (
<View style={styles.section}>
<Text style={styles.sectionTitle}>Sector Allocation</Text>
<Text style={styles.sectionDescription}>
How your portfolio is distributed across different industry sectors. 
Diversification helps reduce risk by spreading investments across various industries.
</Text>
{/* Diversification Score */}
<View style={styles.diversificationCard}>
<View style={styles.diversificationHeader}>
<Text style={styles.diversificationTitle}>Diversification Score</Text>
<Text style={styles.diversificationScore}>
{(() => {
const score = updatedMetrics.riskMetrics?.diversification_score;
// Score processing
if (score != null && !isNaN(Number(score))) {
return `${Math.round(Number(score))}/100`;
} else {
return 'N/A';
}
})()}
</Text>
</View>
<Text style={styles.diversificationDescription}>
{(() => {
const score = updatedMetrics.riskMetrics?.diversification_score;
if (score == null || isNaN(Number(score))) {
return 'Unable to calculate diversification score';
}
const numScore = Number(score);
if (numScore > 70) {
return 'Well diversified across sectors';
} else if (numScore > 40) {
return 'Moderately diversified - consider adding more sectors';
} else {
return 'Low diversification - high concentration risk';
}
})()}
</Text>
</View>
<View style={styles.sectorContainer}>
{Object.entries(updatedMetrics.sectorAllocation).map(([sector, percentage]) => {
const numPercentage = Number(percentage);
const isValidPercentage = !isNaN(numPercentage) && isFinite(numPercentage);
const sectorInfo = getSectorInfo(sector);
return (
<View key={sector} style={styles.sectorItem}>
<View style={styles.sectorHeader}>
<View style={styles.sectorNameContainer}>
<Text style={styles.sectorName}>{sector}</Text>
<Text style={styles.sectorDescription}>{sectorInfo.description}</Text>
</View>
<View style={styles.sectorMetrics}>
<Text style={styles.sectorPercentage}>
{isValidPercentage ? `${numPercentage.toFixed(1)}%` : 'N/A'}
</Text>
<Text style={[styles.sectorRisk, { color: sectorInfo.riskColor }]}>
{sectorInfo.riskLevel}
</Text>
</View>
</View>
<View style={styles.progressBar}>
<View 
style={[
styles.progressFill, 
{ 
width: isValidPercentage ? `${Math.max(0, Math.min(100, numPercentage))}%` : '0%',
backgroundColor: sectorInfo.color
}
]} 
/>
</View>
<Text style={styles.sectorInsight}>
{getSectorInsight(sector, numPercentage)}
</Text>
</View>
);
})}
</View>
{/* Sector Recommendations */}
<View style={styles.recommendationsCard}>
<Text style={styles.recommendationsTitle}> Portfolio Insights</Text>
{getPortfolioRecommendations(updatedMetrics.sectorAllocation, updatedMetrics.riskMetrics).map((rec, index) => (
<Text key={index} style={styles.recommendationItem}>• {rec}</Text>
))}
</View>
</View>
)}
{/* Holdings Details */}
{metrics.holdings && metrics.holdings.length > 0 && (
<View style={styles.section}>
<Text style={styles.sectionTitle}>Holdings Analysis</Text>
{metrics.holdings.map((holding: any, index: number) => (
<View key={index} style={styles.holdingCard}>
<View style={styles.holdingHeader}>
<Text style={styles.holdingSymbol}>{holding.symbol}</Text>
<Text style={[
styles.holdingReturn,
{ color: holding.returnPercent >= 0 ? '#34C759' : '#FF3B30' }
]}>
{holding.returnPercent?.toFixed(2)}%
</Text>
</View>
<Text style={styles.holdingName}>{holding.companyName}</Text>
<View style={styles.holdingDetails}>
<Text style={styles.holdingDetail}>
{holding.shares} shares @ ${holding.currentPrice?.toFixed(2)}
</Text>
<Text style={styles.holdingDetail}>
Value: ${holding.totalValue?.toLocaleString()}
</Text>
</View>
</View>
))}
</View>
)}
</ScrollView>
);
};
// Calculate updated portfolio values after rebalancing
const getUpdatedPortfolioAnalysis = (portfolioAnalysis: any) => {
if (!rebalancingPerformed || !lastRebalancingResult || !portfolioAnalysis) {
return portfolioAnalysis;
}
const original = portfolioAnalysis;
const trades = lastRebalancingResult.stockTrades || [];
// Calculate new total value (add trade values)
const totalTradeValue = trades.reduce((sum, trade) => sum + (trade.totalValue || 0), 0);
const newTotalValue = (original.totalValue || 0) + totalTradeValue;
// Calculate new number of holdings (add new stocks)
const newStocks = trades.filter(trade => trade.action === 'BUY').length;
const newNumHoldings = (original.numHoldings || 0) + newStocks;
// Update diversification score based on rebalancing result
// Handle both string format "0.08 → 0.12" and number format 0.08
let newDiversificationScore = original.diversificationScore;
if (lastRebalancingResult.estimatedImprovement) {
  if (typeof lastRebalancingResult.estimatedImprovement === 'string') {
    const improvementMatch = lastRebalancingResult.estimatedImprovement.match(/(\d+\.?\d*) → (\d+\.?\d*)/);
    newDiversificationScore = improvementMatch ? parseFloat(improvementMatch[2]) : original.diversificationScore;
  } else if (typeof lastRebalancingResult.estimatedImprovement === 'number') {
    // If it's a number, assume it's the improvement percentage and add it to current score
    newDiversificationScore = Math.min(10, (original.diversificationScore || 0) + (lastRebalancingResult.estimatedImprovement * 10));
  }
}
// Reduce risk score slightly due to better diversification
const newRiskScore = Math.max(1, (original.riskScore || 0) - 1);

return {
...original,
totalValue: newTotalValue,
numHoldings: newNumHoldings,
diversificationScore: newDiversificationScore,
riskScore: newRiskScore
};
};
const renderRecommendationsTab = () => {
if (recommendationsLoading) {
return (
<View style={styles.loadingContainer}>
<Text style={styles.loadingText}>Loading AI recommendations...</Text>
</View>
);
}
const recommendations = recommendationsData?.aiRecommendations;
// Parse sector breakdown JSON string if it exists
let parsedSectorBreakdown = {};
if (recommendations?.portfolioAnalysis?.sectorBreakdown) {
try {
parsedSectorBreakdown = typeof recommendations.portfolioAnalysis.sectorBreakdown === 'string' 
? JSON.parse(recommendations.portfolioAnalysis.sectorBreakdown) 
: recommendations.portfolioAnalysis.sectorBreakdown;
} catch (error) {
console.error('Error parsing sector breakdown:', error);
parsedSectorBreakdown = {};
}
}
// Debug logging
// AI recommendations data ready
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
{(() => {
const portfolioAnalysis = getUpdatedPortfolioAnalysis(recommendations?.portfolioAnalysis);
return (
<>
<View style={styles.analysisItem}>
<Text style={styles.analysisLabel}>Total Value</Text>
<Text style={styles.analysisValue}>
${portfolioAnalysis.totalValue?.toFixed(2) || 'N/A'}
{rebalancingPerformed && portfolioAnalysis.totalValue > recommendations?.portfolioAnalysis?.totalValue && (
<Text style={styles.improvementText}> ↗</Text>
)}
</Text>
</View>
<View style={styles.analysisItem}>
<Text style={styles.analysisLabel}>Number of Holdings</Text>
<Text style={styles.analysisValue}>
{portfolioAnalysis.numHoldings || 'N/A'}
{rebalancingPerformed && portfolioAnalysis.numHoldings > recommendations?.portfolioAnalysis?.numHoldings && (
<Text style={styles.improvementText}> ↗</Text>
)}
</Text>
</View>
<View style={styles.analysisItem}>
<Text style={styles.analysisLabel}>Risk Score</Text>
<Text style={styles.analysisValue}>
{portfolioAnalysis.riskScore || 'N/A'}
{rebalancingPerformed && portfolioAnalysis.riskScore < recommendations?.portfolioAnalysis?.riskScore && (
<Text style={styles.improvementText}> ↘</Text>
)}
</Text>
</View>
<View style={styles.analysisItem}>
<Text style={styles.analysisLabel}>Diversification Score</Text>
<Text style={styles.analysisValue}>
{portfolioAnalysis.diversificationScore || 'N/A'}
{rebalancingPerformed && portfolioAnalysis.diversificationScore > recommendations?.portfolioAnalysis?.diversificationScore && (
<Text style={styles.improvementText}> ↗</Text>
)}
</Text>
</View>
</>
);
})()}
</View>
{/* Sector Breakdown */}
{Object.keys(parsedSectorBreakdown).length > 0 && (
<View style={styles.sectorBreakdownCard}>
<Text style={styles.sectorBreakdownTitle}>Current Sector Allocation</Text>
{Object.entries(parsedSectorBreakdown).map(([sector, value]) => (
<View key={sector} style={styles.sectorBreakdownItem}>
<Text style={styles.sectorBreakdownSector}>{sector}</Text>
<Text style={styles.sectorBreakdownValue}>${Number(value).toFixed(2)}</Text>
</View>
))}
</View>
)}
</View>
)}
{/* Market Outlook */}
{recommendations.marketOutlook && (
<View style={styles.section}>
<Text style={styles.sectionTitle}>Market Outlook</Text>
<View style={styles.outlookCard}>
<View style={styles.outlookHeader}>
<Text style={styles.outlookSentiment}>
{recommendations.marketOutlook.overallSentiment}
</Text>
<Text style={styles.outlookConfidence}>
{recommendations?.marketOutlook?.confidence != null ? Math.round(recommendations.marketOutlook.confidence * 100) : 0}% confidence
</Text>
</View>
<View style={styles.factorsContainer}>
<Text style={styles.factorsTitle}>Key Factors:</Text>
{recommendations.marketOutlook.keyFactors?.map((factor: string, index: number) => (
<Text key={index} style={styles.factorItem}>• {factor}</Text>
))}
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
onPress={async () => {
const suggestionCount = recommendations.rebalanceSuggestions?.length || 0;
// Check if this rebalancing would be the same as the last one
try {
const storageService = RebalancingStorageService.getInstance();
const lastResult = await storageService.getLatestRebalancingResult();
if (lastResult) {
const currentSuggestions = recommendations.rebalanceSuggestions?.map(s => ({
action: s.action,
currentAllocation: s.currentAllocation,
suggestedAllocation: s.suggestedAllocation
})) || [];
const lastSuggestions = Array.isArray(lastResult.changesMade) ? lastResult.changesMade : [];
// Check if the suggestions are essentially the same
const isSameRebalancing = currentSuggestions.length > 0 && 
Array.isArray(lastSuggestions) && lastSuggestions.length > 0 &&
currentSuggestions.every(current => 
lastSuggestions.some(last => 
typeof last === 'string' && last.includes(current.action.split(':')[0]) && 
Math.abs(parseFloat(last.split('→')[0].split(':')[1].trim().replace('%', '')) - current.currentAllocation) < 1 &&
Math.abs(parseFloat(last.split('→')[1].trim().replace('%', '')) - current.suggestedAllocation) < 1
)
);
if (isSameRebalancing) {
Alert.alert(
' Same Rebalancing Detected',
'The current rebalancing suggestions are the same as your last rebalancing operation. No changes will be made.\n\nWould you like to proceed anyway?',
[
{ text: 'Cancel', style: 'cancel' },
{ 
text: 'Proceed Anyway', 
onPress: () => performRebalancing()
}
]
);
return;
}
}
// Proceed with normal rebalancing
performRebalancing();
} catch (error) {
console.error('Error checking last rebalancing result:', error);
// If there's an error checking, proceed with normal rebalancing
performRebalancing();
}
function performRebalancing() {
Alert.alert(
' AI Portfolio Rebalancing',
`This will automatically rebalance your portfolio based on ${suggestionCount} AI recommendations.\n\n• Maximum rebalance: 20% per change\n• Transaction costs: ~0.1% per trade\n• Changes will be applied to improve diversification\n• Trade limits: $${tradeLimits.maxTradeValue.toLocaleString()} max per trade\n• Daily limit: ${tradeLimits.maxDailyTrades} trades\n\nContinue with rebalancing?`,
[
{ text: 'Cancel', style: 'cancel' },
{ 
text: 'Preview Changes', 
onPress: () => performDryRun(),
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
}
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
{ backgroundColor: suggestion.priority === 'High' ? '#FF3B30' : suggestion.priority === 'Medium' ? '#FF9500' : '#34C759' }
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
{/* Risk Assessment */}
{recommendations.riskAssessment && (
<View style={styles.section}>
<Text style={styles.sectionTitle}>Risk Assessment</Text>
<View style={styles.riskAssessmentCard}>
<View style={styles.riskAssessmentItem}>
<Text style={styles.riskAssessmentLabel}>Overall Risk</Text>
<Text style={styles.riskAssessmentValue}>
{recommendations.riskAssessment.overallRisk}
</Text>
</View>
<View style={styles.riskAssessmentItem}>
<Text style={styles.riskAssessmentLabel}>Volatility Estimate</Text>
<Text style={styles.riskAssessmentValue}>
{recommendations.riskAssessment.volatilityEstimate ? 
`${recommendations.riskAssessment.volatilityEstimate}%` : 
'N/A'
}
</Text>
</View>
{recommendations.riskAssessment.recommendations && (
<View style={styles.recommendationsContainer}>
<Text style={styles.recommendationsTitle}>Recommendations:</Text>
{recommendations.riskAssessment.recommendations.map((rec: string, index: number) => (
<Text key={index} style={styles.recommendationItem}>• {rec}</Text>
))}
</View>
)}
</View>
</View>
)}
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
{['All', 'Technology', 'Healthcare', 'Financial Services', 'Consumer Cyclical', 'Consumer Defensive', 'Communication Services', 'Energy', 'Industrials', 'Materials', 'Utilities', 'Real Estate'].map((sector) => (
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
{/* Market Cap Filter */}
<View style={styles.filterGroup}>
<Text style={styles.filterLabel}>Market Cap</Text>
<View style={styles.filterRow}>
{['All', 'Large Cap', 'Mid Cap', 'Small Cap', 'Micro Cap'].map((cap) => (
<TouchableOpacity 
key={cap}
style={[
styles.filterChip,
screeningFilters.marketCap === cap && styles.filterChipActive
]}
onPress={() => setScreeningFilters({...screeningFilters, marketCap: cap === 'All' ? null : cap})}
>
<Text style={[
styles.filterChipText,
screeningFilters.marketCap === cap && styles.filterChipTextActive
]}>
{cap}
</Text>
</TouchableOpacity>
))}
</View>
</View>
{/* P/E Ratio Filter */}
<View style={styles.filterGroup}>
<Text style={styles.filterLabel}>P/E Ratio</Text>
<View style={styles.rangeContainer}>
<Text style={styles.rangeLabel}>Min: {screeningFilters.minPERatio || 0}</Text>
<CustomSlider
style={styles.slider}
minimumValue={0}
maximumValue={50}
value={screeningFilters.minPERatio || 0}
onValueChange={(value) => setScreeningFilters({...screeningFilters, minPERatio: Math.round(value)})}
/>
<Text style={styles.rangeLabel}>Max: {screeningFilters.maxPERatio || 50}</Text>
<CustomSlider
style={styles.slider}
minimumValue={0}
maximumValue={50}
value={screeningFilters.maxPERatio || 50}
onValueChange={(value) => setScreeningFilters({...screeningFilters, maxPERatio: Math.round(value)})}
/>
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
{/* Risk Level Filter */}
<View style={styles.filterGroup}>
<Text style={styles.filterLabel}>Risk Level</Text>
<View style={styles.filterRow}>
{['All', 'Low', 'Medium', 'High'].map((risk) => (
<TouchableOpacity
key={risk}
style={[
styles.filterChip,
screeningFilters.riskLevel === risk && styles.filterChipActive
]}
onPress={() => setScreeningFilters({...screeningFilters, riskLevel: risk === 'All' ? null : risk})}
>
<Text style={[
styles.filterChipText,
screeningFilters.riskLevel === risk && styles.filterChipTextActive
]}>
{risk}
</Text>
</TouchableOpacity>
))}
</View>
</View>
{/* Sort By Filter */}
<View style={styles.filterGroup}>
<Text style={styles.filterLabel}>Sort By</Text>
<View style={styles.filterRow}>
{['ML Score', 'Market Cap', 'P/E Ratio', 'Symbol'].map((sort) => (
<TouchableOpacity
key={sort}
style={[
styles.filterChip,
screeningFilters.sortBy === sort && styles.filterChipActive
]}
onPress={() => setScreeningFilters({...screeningFilters, sortBy: sort})}
>
<Text style={[
styles.filterChipText,
screeningFilters.sortBy === sort && styles.filterChipTextActive
]}>
{sort}
</Text>
</TouchableOpacity>
))}
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
<Text style={[
styles.stockDetailValue,
{ color: stock.riskLevel === 'Low' ? '#34C759' : stock.riskLevel === 'Medium' ? '#FF9500' : '#FF3B30' }
]}>
{stock.riskLevel}
</Text>
</View>
<View style={styles.stockDetailItem}>
<Text style={styles.stockDetailLabel}>Growth</Text>
<Text style={styles.stockDetailValue}>
{stock.growthPotential}
</Text>
</View>
</View>
<View style={styles.stockActions}>
<TouchableOpacity 
style={styles.actionButton}
onPress={() => {
// Show stock details in modal
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
// Add to watchlist functionality
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
// Options analysis data ready
// Don't return early on loading - show content with loading indicator
// Always show the same UI structure to prevent flashing
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
{(isSearching || optionsLoading || testOptionsLoading) ? (
<View style={styles.loadingContainer}>
<Icon name="loader" size={16} color="#007AFF" />
<Text style={styles.loadingText}>
{isSearching ? `Searching for ${searchSymbol}...` : 'Loading options data...'}
</Text>
</View>
) : (
<Text style={styles.stockInfo}>
Analyzing options strategies for {selectedSymbol}
</Text>
)}
</View>
</View>
{/* Options Education Section */}
<View style={styles.section}>
<Text style={styles.sectionTitle}>Options Trading Education</Text>
<View style={styles.educationCard}>
<View style={styles.educationHeader}>
<Icon name="book-open" size={20} color="#007AFF" />
<Text style={styles.educationTitle}>What are Options?</Text>
</View>
<Text style={styles.educationText}>
Options give you the right (but not obligation) to buy or sell a stock at a specific price by a certain date. 
They're powerful tools for income generation, hedging, and speculation.
</Text>
</View>
<View style={styles.educationCard}>
<View style={styles.educationHeader}>
<Icon name="trending-up" size={20} color="#34C759" />
<Text style={styles.educationTitle}>Key Strategies</Text>
</View>
<View style={styles.strategyList}>
<View style={styles.strategyItem}>
<Text style={styles.strategyName}>Covered Calls</Text>
<Text style={styles.strategyDesc}>Generate income by selling call options on stocks you own</Text>
</View>
<View style={styles.strategyItem}>
<Text style={styles.strategyName}>Protective Puts</Text>
<Text style={styles.strategyDesc}>Hedge downside risk by buying put options</Text>
</View>
<View style={styles.strategyItem}>
<Text style={styles.strategyName}>Iron Condors</Text>
<Text style={styles.strategyDesc}>Profit from range-bound markets with limited risk</Text>
</View>
</View>
</View>
<View style={styles.educationCard}>
<View style={styles.educationHeader}>
<Icon name="alert-triangle" size={20} color="#FF9500" />
<Text style={styles.educationTitle}>Risk Management</Text>
</View>
<Text style={styles.educationText}>
• Never risk more than you can afford to lose{'\n'}
• Understand the Greeks (Delta, Gamma, Theta, Vega){'\n'}
• Start with paper trading to practice{'\n'}
• Consider your risk tolerance and investment goals
</Text>
</View>
<View style={styles.educationCard}>
<View style={styles.educationHeader}>
<Icon name="info" size={20} color="#8E8E93" />
<Text style={styles.educationTitle}>Important Terms</Text>
</View>
<View style={styles.termsList}>
<View style={styles.termItem}>
<Text style={styles.termName}>Strike Price:</Text>
<Text style={styles.termDesc}>The price at which you can buy/sell the stock</Text>
</View>
<View style={styles.termItem}>
<Text style={styles.termName}>Expiration:</Text>
<Text style={styles.termDesc}>The date when the option expires</Text>
</View>
<View style={styles.termItem}>
<Text style={styles.termName}>Premium:</Text>
<Text style={styles.termDesc}>The cost to buy the option</Text>
</View>
<View style={styles.termItem}>
<Text style={styles.termName}>IV (Implied Volatility):</Text>
<Text style={styles.termDesc}>Market's expectation of future price movement</Text>
</View>
</View>
</View>
</View>
{/* AI Options Button */}
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
{/* Market Sentiment */}
{options?.marketSentiment && (
<View style={styles.section}>
<Text style={styles.sectionTitle}>
Market Sentiment
{(optionsLoading || testOptionsLoading) && (
<Icon name="loader" size={16} color="#007AFF" style={{ marginLeft: 8 }} />
)}
</Text>
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
{options?.marketSentiment?.putCallRatio?.toFixed(2) || 'N/A'}
</Text>
<Text style={styles.metricExplanation}>
{options?.marketSentiment?.putCallRatio ? 
(options.marketSentiment.putCallRatio > 0.8 ? 'Bearish sentiment - more puts' :
options.marketSentiment.putCallRatio < 0.6 ? 'Bullish sentiment - more calls' :
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
{options?.marketSentiment?.impliedVolatilityRank?.toFixed(1) || 'N/A'}%
</Text>
<Text style={styles.metricExplanation}>
{options?.marketSentiment?.impliedVolatilityRank ? 
(options.marketSentiment.impliedVolatilityRank > 70 ? 'High volatility - expensive options' :
options.marketSentiment.impliedVolatilityRank < 30 ? 'Low volatility - cheap options' :
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
{ color: (options?.marketSentiment?.sentimentScore || 50) > 50 ? '#34C759' : '#FF3B30' }
]}
numberOfLines={2}
ellipsizeMode="tail"
>
{options?.marketSentiment?.sentimentDescription || 'Neutral'}
</Text>
<Text style={styles.metricExplanation}>
{options?.marketSentiment?.sentimentScore ? 
`Score: ${options.marketSentiment.sentimentScore.toFixed(0)}/100` : 'N/A'}
</Text>
</View>
</View>
</View>
)}
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
{/* Unusual Options Flow */}
{options?.unusualFlow && options.unusualFlow.length > 0 && (
<View style={styles.section}>
<Text style={styles.sectionTitle}>
Unusual Options Activity
{(optionsLoading || testOptionsLoading) && (
<Icon name="loader" size={16} color="#007AFF" style={{ marginLeft: 8 }} />
)}
</Text>
{options?.unusualFlow?.slice(0, 3).map((flow, index) => (
<View key={index} style={styles.flowCard}>
<View style={styles.flowHeader}>
<Text style={styles.flowSymbol}>{flow.symbol}</Text>
<Text style={styles.flowType}>{flow.activityType}</Text>
</View>
<View style={styles.flowDetails}>
<Text style={styles.flowStrike}>Strike: ${flow.strike}</Text>
<Text style={styles.flowVolume}>Volume: {(flow?.volume ?? 0).toLocaleString()}</Text>
<Text style={styles.flowScore}>Score: {Math.round((flow?.unusualActivityScore ?? 0) * 100)}%</Text>
</View>
</View>
))}
</View>
)}
{/* Market Outlook Toggle */}
<View style={styles.section}>
<View style={styles.marketOutlookToggle}>
<Text style={styles.marketOutlookLabel}>Market Outlook:</Text>
<TouchableOpacity 
style={styles.marketOutlookButton}
onPress={toggleMarketOutlook}
activeOpacity={0.7}
>
<View style={[
styles.marketOutlookDot,
{ 
backgroundColor: marketOutlook === 'Bullish' ? '#34C759' : 
marketOutlook === 'Bearish' ? '#FF3B30' : '#007AFF'
}
]} />
<Text style={styles.marketOutlookText}>{marketOutlook}</Text>
</TouchableOpacity>
</View>
</View>
{/* Recommended Strategies */}
{options?.recommendedStrategies && options.recommendedStrategies.length > 0 && (
<View style={styles.section}>
<Text style={styles.sectionTitle}>
Recommended Strategies
{(optionsLoading || testOptionsLoading) && (
<Icon name="loader" size={16} color="#007AFF" style={{ marginLeft: 8 }} />
)}
</Text>
{(getFilteredStrategies(options?.recommendedStrategies || []) || options?.recommendedStrategies || [])?.map((strategy, index) => (
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
<View style={styles.strategyOutlook}>
<Text style={styles.outlookLabel}>Market Outlook:</Text>
<Text style={styles.outlookValue}>{strategy.marketOutlook}</Text>
</View>
<View style={styles.strategyMetrics}>
<View style={styles.strategyMetric}>
<Text style={styles.strategyMetricLabel}>Max Profit</Text>
<Text style={[styles.strategyMetricValue, { color: '#34C759' }]}>
{strategy.maxProfit === Infinity ? '∞' : `$${strategy.maxProfit?.toFixed(2) || '0.00'}`}
</Text>
</View>
<View style={styles.strategyMetric}>
<Text style={styles.strategyMetricLabel}>Max Loss</Text>
<Text style={[styles.strategyMetricValue, { color: '#FF3B30' }]}>
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
{/* Expiration Timeframe */}
<View style={styles.expirationSection}>
<View style={styles.expirationItem}>
<Text style={styles.expirationLabel}>Expiration:</Text>
<Text style={styles.expirationValue}>
{strategy.daysToExpiration} days
</Text>
</View>
<View style={styles.expirationItem}>
<Text style={styles.expirationLabel}>Strategy Type:</Text>
<Text style={styles.expirationValue}>
{strategy.strategyType}
</Text>
</View>
</View>
{strategy.breakevenPoints && strategy.breakevenPoints.length > 0 && (
<View style={styles.breakevenSection}>
<Text style={styles.breakevenLabel}>Breakeven Points:</Text>
<Text style={styles.breakevenValue}>
${strategy.breakevenPoints.map(p => p.toFixed(2)).join(', $')}
</Text>
</View>
)}
</View>
))}
</View>
)}
{/* View Full Chain Button */}
{options?.optionsChain && (
<View style={styles.section}>
<TouchableOpacity 
style={styles.viewFullChainButton}
onPress={() => {
setShowFullChain(true);
setSelectedExpiration(0); // Select first expiration by default
}}
>
<Text style={styles.viewFullChainButtonText}>View Full Chain</Text>
</TouchableOpacity>
</View>
)}
{/* Error Message - Only show if no data and not loading */}
{!options && !optionsLoading && !testOptionsLoading && (
<View style={styles.errorContainer}>
<Icon name="alert-circle" size={48} color="#FF3B30" />
<Text style={styles.errorText}>Unable to load options data</Text>
<Text style={styles.errorText}>Premium Error: {optionsError?.message || 'None'}</Text>
<Text style={styles.errorText}>Test Error: {testOptionsError?.message || 'None'}</Text>
</View>
)}
</ScrollView>
);
};
return (
<SafeAreaView style={styles.container}>
{/* Header */}
<View style={styles.header}>
<TouchableOpacity onPress={() => {
try {
navigateTo('portfolio');
} catch (error) {
console.error('Navigation error:', error);
// Fallback - try other common routes
try {
navigateTo('home');
} catch (fallbackError) {
console.error('Fallback navigation error:', fallbackError);
}
}
}}>
<Icon name="arrow-left" size={24} color="#000" />
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
</View>
{/* Tab Content */}
<View style={styles.tabContentContainer}>
{activeTab === 'metrics' && renderMetricsTab()}
{activeTab === 'recommendations' && renderRecommendationsTab()}
{activeTab === 'screening' && renderScreeningTab()}
{activeTab === 'options' && renderOptionsTab()}
</View>
{/* Full Options Chain Modal */}
<Modal
visible={showFullChain}
animationType="slide"
presentationStyle="pageSheet"
onRequestClose={() => setShowFullChain(false)}
>
<SafeAreaView style={styles.modalContainer}>
<View style={styles.modalHeader}>
<Text style={styles.modalTitle}>Full Options Chain - {selectedSymbol}</Text>
<TouchableOpacity
style={styles.closeButton}
onPress={() => setShowFullChain(false)}
>
<Icon name="x" size={24} color="#000" />
</TouchableOpacity>
</View>
<ScrollView style={styles.modalContent}>
{options?.optionsChain ? (
<>
{/* Expiration Date Selector */}
<View style={styles.expirationSelector}>
<Text style={styles.selectorLabel}>Select Expiration:</Text>
<ScrollView horizontal showsHorizontalScrollIndicator={false}>
{options.optionsChain.expirationDates?.map((date, index) => (
<TouchableOpacity
key={index}
style={[
styles.expirationButton,
selectedExpiration === index && styles.selectedExpirationButton
]}
onPress={() => setSelectedExpiration(index)}
>
<Text style={[
styles.expirationButtonText,
selectedExpiration === index && styles.selectedExpirationButtonText
]}>
{date}
</Text>
</TouchableOpacity>
))}
</ScrollView>
</View>
{/* Options Chain Table */}
{selectedExpiration !== null && (
<View style={styles.optionsTable}>
<Text style={styles.tableTitle}>
Options Chain - {options.optionsChain.expirationDates?.[selectedExpiration || 0]}
</Text>
<Text style={styles.tableSubtitle}>
{(() => {
const selectedDate = options.optionsChain.expirationDates?.[selectedExpiration || 0];
const callCount = options.optionsChain.calls?.filter(call => 
call.expirationDate === selectedDate
).length || 0;
const putCount = options.optionsChain.puts?.filter(put => 
put.expirationDate === selectedDate
).length || 0;
return `${callCount} calls, ${putCount} puts available`;
})()}
</Text>
{/* Table Header */}
<View style={styles.tableHeader}>
<Text style={styles.tableHeaderText}>Calls</Text>
<Text style={styles.tableHeaderText}>Strike</Text>
<Text style={styles.tableHeaderText}>Puts</Text>
</View>
{/* Options Rows */}
{(() => {
// Filter options by selected expiration date
const selectedDate = options.optionsChain.expirationDates?.[selectedExpiration || 0];
const filteredCalls = options.optionsChain.calls?.filter(call => 
call.expirationDate === selectedDate
) || [];
const filteredPuts = options.optionsChain.puts?.filter(put => 
put.expirationDate === selectedDate
) || [];
// Map by strike price for proper alignment
const byStrike = new Map();
for (const call of filteredCalls) byStrike.set(call.strike, { call });
for (const put of filteredPuts) byStrike.set(put.strike, { ...(byStrike.get(put.strike) || {}), put });

return [...byStrike.keys()].sort((a, b) => a - b).slice(0, 50).map((strike, index) => {
const { call, put } = byStrike.get(strike);
return (
<View key={index} style={styles.optionsRow}>
{/* Call Option */}
<View style={styles.optionCell}>
<Text style={styles.optionPrice}>
{call?.lastPrice != null ? `$${call.lastPrice.toFixed(2)}` : 'N/A'}
</Text>
<Text style={styles.optionVolume}>
Vol: {call?.volume || 0}
</Text>
<Text style={styles.optionOI}>
OI: {call?.openInterest || 0}
</Text>
</View>
{/* Strike Price */}
<View style={styles.strikeCell}>
<Text style={styles.strikePrice}>
{call?.strike != null ? `$${call.strike.toFixed(0)}` : 'N/A'}
</Text>
</View>
{/* Put Option */}
<View style={styles.optionCell}>
<Text style={styles.optionPrice}>
${put?.lastPrice?.toFixed(2) || 'N/A'}
</Text>
<Text style={styles.optionVolume}>
Vol: {put?.volume || 0}
</Text>
<Text style={styles.optionOI}>
OI: {put?.openInterest || 0}
</Text>
</View>
</View>
);
});
})()}
</View>
)}
{/* Greeks Information */}
<View style={styles.greeksSection}>
<Text style={styles.greeksTitle}>Greeks Information</Text>
<View style={styles.greeksGrid}>
<View style={styles.greekCard}>
<Text style={styles.greekLabel}>Delta</Text>
<Text style={styles.greekValue}>
{options.optionsChain.greeks?.delta?.toFixed(3) || 'N/A'}
</Text>
</View>
<View style={styles.greekCard}>
<Text style={styles.greekLabel}>Gamma</Text>
<Text style={styles.greekValue}>
{options.optionsChain.greeks?.gamma?.toFixed(3) || 'N/A'}
</Text>
</View>
<View style={styles.greekCard}>
<Text style={styles.greekLabel}>Theta</Text>
<Text style={styles.greekValue}>
{options.optionsChain.greeks?.theta?.toFixed(3) || 'N/A'}
</Text>
</View>
<View style={styles.greekCard}>
<Text style={styles.greekLabel}>Vega</Text>
<Text style={styles.greekValue}>
{options.optionsChain.greeks?.vega?.toFixed(3) || 'N/A'}
</Text>
</View>
</View>
</View>
</>
) : (
<View style={styles.noDataContainer}>
<Text style={styles.noDataText}>No options data available</Text>
<Text style={styles.noDataSubtext}>
Try searching for a different stock symbol
</Text>
</View>
)}
</ScrollView>
</SafeAreaView>
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
<Text style={[
styles.metricValue,
{ color: selectedStockDetails.riskLevel === 'Low' ? '#34C759' : 
selectedStockDetails.riskLevel === 'Medium' ? '#FF9500' : '#FF3B30' }
]}>
{selectedStockDetails.riskLevel}
</Text>
</View>
<View style={styles.metricCard}>
<Text style={styles.metricLabel}>Growth Potential</Text>
<Text style={styles.metricValue}>
{selectedStockDetails.growthPotential}
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
<Text style={styles.sectionTitle}> Sector Changes</Text>
{dryRunResults.changesMade && dryRunResults.changesMade.length > 0 ? (
dryRunResults.changesMade.map((change, index) => (
<Text key={index} style={styles.previewItem}>• {change}</Text>
))
) : (
<Text style={styles.previewItem}>No sector changes</Text>
)}
</View>
<View style={styles.previewSection}>
<Text style={styles.sectionTitle}> Stock Trades</Text>
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
<Text style={styles.sectionTitle}> Cost Summary</Text>
<Text style={styles.previewItem}>Transaction Cost: ${dryRunResults.rebalanceCost?.toFixed(2) || '0.00'}</Text>
<Text style={styles.previewItem}>New Portfolio Value: ${dryRunResults.newPortfolioValue?.toFixed(2) || '0.00'}</Text>
</View>
{dryRunResults.estimatedImprovement && (
<View style={styles.previewSection}>
<Text style={styles.sectionTitle}> Expected Improvement</Text>
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
// Execute the actual rebalancing
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
backgroundColor: '#F2F2F7',
},
header: {
flexDirection: 'row',
alignItems: 'center',
justifyContent: 'space-between',
paddingHorizontal: 20,
paddingVertical: 16,
backgroundColor: '#fff',
borderBottomWidth: 1,
borderBottomColor: '#E5E5EA',
},
headerTitle: {
fontSize: 18,
fontWeight: '600',
color: '#000',
},
tabNavigation: {
flexDirection: 'row',
backgroundColor: '#fff',
paddingHorizontal: 20,
borderBottomWidth: 1,
borderBottomColor: '#E5E5EA',
},
tab: {
flex: 1,
paddingVertical: 16,
alignItems: 'center',
borderBottomWidth: 2,
borderBottomColor: 'transparent',
},
activeTab: {
borderBottomColor: '#007AFF',
},
tabText: {
fontSize: 16,
color: '#8E8E93',
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
padding: 20,
},
loadingContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
},
loadingText: {
fontSize: 16,
color: '#8E8E93',
marginTop: 16,
},
errorContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
},
errorText: {
fontSize: 16,
color: '#8E8E93',
marginTop: 16,
textAlign: 'center',
},
errorDetails: {
fontSize: 12,
color: '#FF3B30',
textAlign: 'center',
marginTop: 8,
paddingHorizontal: 20,
},
section: {
marginBottom: 24,
},
sectionTitle: {
fontSize: 20,
fontWeight: '600',
color: '#000',
marginBottom: 16,
},
metricsGrid: {
flexDirection: 'row',
flexWrap: 'wrap',
justifyContent: 'space-between',
},
metricCard: {
width: (width - 60) / 2,
backgroundColor: '#fff',
padding: 16,
borderRadius: 12,
marginBottom: 12,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 4,
elevation: 3,
},
metricLabel: {
fontSize: 14,
color: '#8E8E93',
marginBottom: 4,
},
metricValue: {
fontSize: 18,
fontWeight: '600',
color: '#000',
},
metricHeader: {
flexDirection: 'row',
alignItems: 'center',
marginBottom: 4,
},
tooltipButton: {
padding: 2,
marginLeft: 4,
},
metricExplanation: {
fontSize: 11,
color: '#8E8E93',
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
color: '#000',
flex: 1,
},
tooltipCloseButton: {
padding: 4,
},
tooltipText: {
fontSize: 16,
color: '#333',
lineHeight: 24,
},
riskContainer: {
backgroundColor: '#fff',
padding: 16,
borderRadius: 12,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 4,
elevation: 3,
},
riskItem: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
paddingVertical: 8,
borderBottomWidth: 1,
borderBottomColor: '#F2F2F7',
},
riskLabel: {
fontSize: 16,
color: '#000',
},
riskValue: {
fontSize: 16,
fontWeight: '600',
color: '#007AFF',
},
sectorContainer: {
backgroundColor: '#fff',
padding: 16,
borderRadius: 12,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 4,
elevation: 3,
},
sectorItem: {
marginBottom: 16,
},
sectorHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
marginBottom: 8,
},
sectorName: {
fontSize: 16,
color: '#000',
fontWeight: '500',
},
sectorPercentage: {
fontSize: 16,
fontWeight: '600',
color: '#007AFF',
},
progressBar: {
height: 8,
backgroundColor: '#F2F2F7',
borderRadius: 4,
overflow: 'hidden',
},
progressFill: {
height: '100%',
backgroundColor: '#007AFF',
borderRadius: 4,
},
holdingCard: {
backgroundColor: '#fff',
padding: 16,
borderRadius: 12,
marginBottom: 12,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 4,
elevation: 3,
},
holdingHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
marginBottom: 4,
},
holdingSymbol: {
fontSize: 18,
fontWeight: '600',
color: '#000',
},
holdingReturn: {
fontSize: 16,
fontWeight: '600',
},
holdingName: {
fontSize: 14,
color: '#8E8E93',
marginBottom: 8,
},
holdingDetails: {
flexDirection: 'row',
justifyContent: 'space-between',
},
holdingDetail: {
fontSize: 14,
color: '#8E8E93',
},
outlookCard: {
backgroundColor: '#fff',
padding: 16,
borderRadius: 12,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 4,
elevation: 3,
},
outlookHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
marginBottom: 16,
},
outlookSentiment: {
fontSize: 20,
fontWeight: '600',
color: '#34C759',
},
outlookConfidence: {
fontSize: 14,
color: '#8E8E93',
},
factorsContainer: {
marginTop: 8,
},
factorsTitle: {
fontSize: 16,
fontWeight: '600',
color: '#000',
marginBottom: 8,
},
factorItem: {
fontSize: 14,
color: '#8E8E93',
marginBottom: 4,
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
elevation: 3,
},
recommendationHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
marginBottom: 4,
},
recommendationSymbol: {
fontSize: 18,
fontWeight: '600',
color: '#000',
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
color: '#8E8E93',
marginBottom: 8,
},
recommendationReasoning: {
fontSize: 14,
color: '#000',
marginBottom: 12,
lineHeight: 20,
},
recommendationMetrics: {
flexDirection: 'row',
justifyContent: 'space-between',
},
recommendationMetric: {
fontSize: 12,
color: '#8E8E93',
},
riskAssessmentCard: {
backgroundColor: '#fff',
padding: 16,
borderRadius: 12,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 4,
elevation: 3,
},
riskAssessmentItem: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
paddingVertical: 8,
borderBottomWidth: 1,
borderBottomColor: '#F2F2F7',
},
riskAssessmentLabel: {
fontSize: 16,
color: '#000',
},
riskAssessmentValue: {
fontSize: 16,
fontWeight: '600',
color: '#FF3B30',
},
recommendationsContainer: {
marginTop: 16,
},
recommendationsTitle: {
fontSize: 16,
fontWeight: '600',
color: '#000',
marginBottom: 8,
},
recommendationItem: {
fontSize: 14,
color: '#8E8E93',
marginBottom: 4,
},
comingSoonContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
paddingHorizontal: 40,
},
comingSoonTitle: {
fontSize: 24,
fontWeight: '600',
color: '#000',
marginTop: 16,
marginBottom: 8,
textAlign: 'center',
},
comingSoonText: {
fontSize: 16,
color: '#8E8E93',
textAlign: 'center',
lineHeight: 24,
marginBottom: 32,
},
comingSoonButton: {
backgroundColor: '#007AFF',
paddingHorizontal: 32,
paddingVertical: 12,
borderRadius: 8,
},
comingSoonButtonText: {
fontSize: 16,
fontWeight: '600',
color: '#fff',
},
// Options Analysis Styles
flowCard: {
backgroundColor: '#fff',
padding: 16,
borderRadius: 12,
marginBottom: 12,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 4,
elevation: 3,
},
flowHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
marginBottom: 8,
},
flowSymbol: {
fontSize: 18,
fontWeight: '600',
color: '#000',
},
flowType: {
fontSize: 12,
color: '#007AFF',
backgroundColor: '#E3F2FD',
paddingHorizontal: 8,
paddingVertical: 4,
borderRadius: 12,
},
flowDetails: {
flexDirection: 'row',
justifyContent: 'space-between',
},
flowStrike: {
fontSize: 14,
color: '#8E8E93',
},
flowVolume: {
fontSize: 14,
color: '#8E8E93',
},
flowScore: {
fontSize: 14,
fontWeight: '600',
color: '#FF9500',
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
elevation: 3,
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
color: '#000',
},
strategyType: {
fontSize: 12,
color: '#8E8E93',
backgroundColor: '#F2F2F7',
paddingHorizontal: 8,
paddingVertical: 4,
borderRadius: 12,
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
color: '#8E8E93',
marginBottom: 4,
},
strategyMetricValue: {
fontSize: 16,
fontWeight: '600',
color: '#000',
},
chainPreview: {
backgroundColor: '#F2F2F7',
padding: 16,
borderRadius: 12,
marginBottom: 12,
},
chainText: {
fontSize: 14,
color: '#8E8E93',
marginBottom: 4,
},
viewFullChainButton: {
backgroundColor: '#007AFF',
paddingVertical: 12,
paddingHorizontal: 24,
borderRadius: 8,
alignItems: 'center',
},
viewFullChainButtonText: {
fontSize: 16,
fontWeight: '600',
color: '#fff',
},
// Enhanced Strategy Styles
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
strategyDescription: {
fontSize: 14,
color: '#8E8E93',
marginBottom: 8,
lineHeight: 20,
},
strategyOutlook: {
flexDirection: 'row',
alignItems: 'center',
marginBottom: 12,
},
outlookLabel: {
fontSize: 12,
color: '#8E8E93',
marginRight: 8,
},
outlookValue: {
fontSize: 12,
fontWeight: '600',
color: '#007AFF',
backgroundColor: '#E3F2FD',
paddingHorizontal: 8,
paddingVertical: 4,
borderRadius: 8,
},
breakevenSection: {
marginTop: 8,
paddingTop: 8,
borderTopWidth: 1,
borderTopColor: '#F2F2F7',
},
marketOutlookToggle: {
flexDirection: 'row',
alignItems: 'center',
justifyContent: 'space-between',
backgroundColor: '#fff',
padding: 16,
borderRadius: 12,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 4,
elevation: 3,
},
marketOutlookLabel: {
fontSize: 16,
fontWeight: '600',
color: '#000',
},
marketOutlookButton: {
flexDirection: 'row',
alignItems: 'center',
backgroundColor: '#F2F2F7',
paddingHorizontal: 12,
paddingVertical: 8,
borderRadius: 20,
},
marketOutlookDot: {
width: 12,
height: 12,
borderRadius: 6,
marginRight: 8,
},
marketOutlookText: {
fontSize: 14,
fontWeight: '600',
color: '#000',
},
breakevenLabel: {
fontSize: 12,
color: '#8E8E93',
marginBottom: 4,
},
breakevenValue: {
fontSize: 14,
fontWeight: '600',
color: '#000',
},
// Expiration Styles
expirationSection: {
marginTop: 12,
paddingTop: 12,
borderTopWidth: 1,
borderTopColor: '#F2F2F7',
},
expirationItem: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
marginBottom: 4,
},
expirationLabel: {
fontSize: 12,
color: '#8E8E93',
fontWeight: '500',
},
expirationValue: {
fontSize: 12,
fontWeight: '600',
color: '#007AFF',
},
// Stock Selector Styles
stockSelector: {
flexDirection: 'row',
flexWrap: 'wrap',
gap: 8,
marginBottom: 12,
},
stockButton: {
backgroundColor: '#F2F2F7',
paddingHorizontal: 16,
paddingVertical: 8,
borderRadius: 20,
borderWidth: 1,
borderColor: '#E5E5EA',
},
selectedStockButton: {
backgroundColor: '#007AFF',
borderColor: '#007AFF',
},
stockButtonText: {
fontSize: 14,
fontWeight: '600',
color: '#8E8E93',
},
selectedStockButtonText: {
color: '#fff',
},
stockInfo: {
fontSize: 14,
color: '#8E8E93',
fontStyle: 'italic',
},
// Options Search Styles
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
elevation: 3,
},
searchInput: {
flex: 1,
fontSize: 16,
color: '#000',
paddingVertical: 4,
},
optionsSearchButton: {
padding: 8,
marginLeft: 8,
},
optionsSearchButtonDisabled: {
opacity: 0.5,
},
quickSelectLabel: {
fontSize: 14,
color: '#8E8E93',
marginBottom: 8,
fontWeight: '500',
},
// Enhanced Sector Allocation Styles
sectionDescription: {
fontSize: 14,
color: '#8E8E93',
lineHeight: 20,
marginBottom: 16,
},
diversificationCard: {
backgroundColor: '#F8F9FA',
padding: 16,
borderRadius: 12,
marginBottom: 16,
borderLeftWidth: 4,
borderLeftColor: '#007AFF',
},
diversificationHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
marginBottom: 8,
},
diversificationTitle: {
fontSize: 16,
fontWeight: '600',
color: '#000',
},
diversificationScore: {
fontSize: 18,
fontWeight: '700',
color: '#007AFF',
},
diversificationDescription: {
fontSize: 14,
color: '#8E8E93',
lineHeight: 18,
},
sectorNameContainer: {
flex: 1,
},
sectorDescription: {
fontSize: 12,
color: '#8E8E93',
marginTop: 2,
},
sectorMetrics: {
alignItems: 'flex-end',
},
sectorRisk: {
fontSize: 12,
fontWeight: '600',
marginTop: 2,
},
sectorInsight: {
fontSize: 12,
color: '#8E8E93',
fontStyle: 'italic',
marginTop: 8,
lineHeight: 16,
},
recommendationsCard: {
backgroundColor: '#E8F5E8',
padding: 16,
borderRadius: 12,
marginTop: 16,
borderLeftWidth: 4,
borderLeftColor: '#34C759',
},
recommendationsTitle: {
fontSize: 16,
fontWeight: '600',
color: '#000',
marginBottom: 12,
},
recommendationItem: {
fontSize: 14,
color: '#000',
lineHeight: 20,
marginBottom: 6,
},
// Stock Screening Styles
filterGroup: {
marginBottom: 20,
},
filterLabel: {
fontSize: 16,
fontWeight: '600',
color: '#000',
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
backgroundColor: '#F2F2F7',
borderWidth: 1,
borderColor: '#E5E5EA',
},
filterChipActive: {
backgroundColor: '#007AFF',
borderColor: '#007AFF',
},
filterChipText: {
fontSize: 14,
color: '#8E8E93',
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
color: '#8E8E93',
minWidth: 60,
},
slider: {
flex: 1,
height: 40,
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
backgroundColor: '#E5E5EA',
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
color: '#8E8E93',
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
elevation: 3,
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
color: '#000',
},
stockName: {
fontSize: 14,
color: '#8E8E93',
marginTop: 2,
},
stockSector: {
fontSize: 12,
color: '#007AFF',
marginTop: 4,
},
stockMetrics: {
alignItems: 'flex-end',
},
stockPrice: {
fontSize: 18,
fontWeight: '700',
color: '#000',
},
stockMLScore: {
fontSize: 12,
color: '#34C759',
marginTop: 2,
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
color: '#8E8E93',
marginBottom: 4,
},
stockDetailValue: {
fontSize: 14,
fontWeight: '600',
color: '#000',
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
borderColor: '#E5E5EA',
alignItems: 'center',
},
actionButtonText: {
fontSize: 14,
fontWeight: '600',
color: '#8E8E93',
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
color: '#8E8E93',
marginTop: 16,
textAlign: 'center',
},
noResultsSubtext: {
fontSize: 14,
color: '#8E8E93',
marginTop: 8,
textAlign: 'center',
},
// Custom Slider Styles
sliderTrack: {
height: 4,
backgroundColor: '#E5E5EA',
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
// Full Options Chain Modal Styles
modalContainer: {
flex: 1,
backgroundColor: '#F2F2F7',
},
modalHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
paddingHorizontal: 20,
paddingVertical: 16,
backgroundColor: '#fff',
borderBottomWidth: 1,
borderBottomColor: '#E5E5EA',
},
modalTitle: {
fontSize: 18,
fontWeight: '600',
color: '#000',
flex: 1,
},
closeButton: {
padding: 8,
},
modalContent: {
flex: 1,
padding: 20,
},
expirationSelector: {
marginBottom: 20,
},
selectorLabel: {
fontSize: 16,
fontWeight: '600',
color: '#000',
marginBottom: 12,
},
expirationButton: {
paddingHorizontal: 16,
paddingVertical: 8,
marginRight: 8,
backgroundColor: '#E5E5EA',
borderRadius: 20,
},
selectedExpirationButton: {
backgroundColor: '#007AFF',
},
expirationButtonText: {
fontSize: 14,
color: '#8E8E93',
},
selectedExpirationButtonText: {
color: '#fff',
fontWeight: '600',
},
optionsTable: {
backgroundColor: '#fff',
borderRadius: 12,
padding: 16,
marginBottom: 20,
},
tableTitle: {
fontSize: 16,
fontWeight: '600',
color: '#000',
marginBottom: 8,
textAlign: 'center',
},
tableSubtitle: {
fontSize: 14,
color: '#8E8E93',
marginBottom: 16,
textAlign: 'center',
},
tableHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
paddingBottom: 12,
borderBottomWidth: 1,
borderBottomColor: '#E5E5EA',
marginBottom: 12,
},
tableHeaderText: {
fontSize: 14,
fontWeight: '600',
color: '#8E8E93',
flex: 1,
textAlign: 'center',
},
optionsRow: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
paddingVertical: 8,
borderBottomWidth: 1,
borderBottomColor: '#F2F2F7',
},
optionCell: {
flex: 1,
alignItems: 'center',
},
optionPrice: {
fontSize: 14,
fontWeight: '600',
color: '#000',
},
optionVolume: {
fontSize: 12,
color: '#8E8E93',
marginTop: 2,
},
optionOI: {
fontSize: 12,
color: '#8E8E93',
},
strikeCell: {
flex: 1,
alignItems: 'center',
},
strikePrice: {
fontSize: 16,
fontWeight: '700',
color: '#007AFF',
},
greeksSection: {
backgroundColor: '#fff',
borderRadius: 12,
padding: 16,
},
greeksTitle: {
fontSize: 16,
fontWeight: '600',
color: '#000',
marginBottom: 16,
},
greeksGrid: {
flexDirection: 'row',
flexWrap: 'wrap',
justifyContent: 'space-between',
},
greekCard: {
width: '48%',
backgroundColor: '#F8F9FA',
borderRadius: 8,
padding: 12,
marginBottom: 8,
alignItems: 'center',
},
greekLabel: {
fontSize: 12,
color: '#8E8E93',
marginBottom: 4,
},
greekValue: {
fontSize: 16,
fontWeight: '600',
color: '#000',
},
noDataContainer: {
flex: 1,
justifyContent: 'center',
alignItems: 'center',
paddingVertical: 40,
},
noDataText: {
fontSize: 18,
fontWeight: '600',
color: '#8E8E93',
marginBottom: 8,
},
noDataSubtext: {
fontSize: 14,
color: '#8E8E93',
textAlign: 'center',
},
// Search Styles
searchContainer: {
flexDirection: 'row',
alignItems: 'center',
backgroundColor: '#fff',
borderRadius: 12,
paddingHorizontal: 16,
paddingVertical: 12,
marginBottom: 16,
shadowColor: '#000',
shadowOffset: {
width: 0,
height: 2,
},
shadowOpacity: 0.1,
shadowRadius: 4,
elevation: 3,
},
searchIcon: {
marginRight: 12,
},
searchInput: {
flex: 1,
fontSize: 16,
color: '#000',
paddingVertical: 4,
},
clearButton: {
padding: 4,
marginRight: 8,
},
searchButton: {
backgroundColor: '#007AFF',
borderRadius: 8,
padding: 10,
minWidth: 44,
alignItems: 'center',
justifyContent: 'center',
},
searchButtonDisabled: {
backgroundColor: '#E5E5EA',
},
// Quick Select Styles
quickSelectLabel: {
fontSize: 16,
fontWeight: '600',
color: '#000',
marginBottom: 12,
},
stockSelector: {
flexDirection: 'row',
flexWrap: 'wrap',
gap: 8,
marginBottom: 16,
},
stockButton: {
backgroundColor: '#fff',
borderRadius: 20,
paddingHorizontal: 16,
paddingVertical: 10,
borderWidth: 1.5,
borderColor: '#E5E5EA',
shadowColor: '#000',
shadowOffset: {
width: 0,
height: 1,
},
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
color: '#8E8E93',
},
selectedStockButtonText: {
color: '#fff',
fontWeight: '700',
},
stockInfoContainer: {
marginBottom: 20,
},
stockInfo: {
fontSize: 16,
fontWeight: '500',
color: '#007AFF',
textAlign: 'center',
},
loadingContainer: {
flexDirection: 'row',
alignItems: 'center',
justifyContent: 'center',
gap: 8,
},
loadingText: {
fontSize: 16,
fontWeight: '500',
color: '#007AFF',
},
// Stock Details Modal Styles
stockDetailsHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
marginBottom: 24,
paddingBottom: 16,
borderBottomWidth: 1,
borderBottomColor: '#E5E5EA',
},
detailedMetrics: {
marginBottom: 24,
},
metricsGrid: {
flexDirection: 'row',
flexWrap: 'wrap',
justifyContent: 'space-between',
gap: 12,
},
metricCard: {
backgroundColor: '#F2F2F7',
borderRadius: 12,
padding: 16,
width: '48%',
alignItems: 'center',
},
metricLabel: {
fontSize: 14,
color: '#8E8E93',
marginBottom: 8,
textAlign: 'center',
},
metricValue: {
fontSize: 18,
fontWeight: '600',
color: '#000',
textAlign: 'center',
flexWrap: 'wrap',
},
modalActions: {
flexDirection: 'row',
gap: 12,
marginTop: 24,
},
modalActionButton: {
flex: 1,
flexDirection: 'row',
alignItems: 'center',
justifyContent: 'center',
paddingVertical: 16,
borderRadius: 12,
gap: 8,
},
primaryButton: {
backgroundColor: '#34C759',
},
secondaryButton: {
backgroundColor: '#F2F2F7',
borderWidth: 1,
borderColor: '#007AFF',
},
primaryButtonText: {
color: '#fff',
fontSize: 16,
fontWeight: '600',
},
secondaryButtonText: {
color: '#007AFF',
fontSize: 16,
fontWeight: '600',
},
// AI Insights Styles
analysisCard: {
backgroundColor: '#F2F2F7',
borderRadius: 12,
padding: 16,
marginBottom: 16,
},
analysisItem: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
paddingVertical: 8,
},
analysisLabel: {
fontSize: 16,
color: '#8E8E93',
},
analysisValue: {
fontSize: 16,
fontWeight: '600',
color: '#000',
},
sectorBreakdownCard: {
backgroundColor: '#fff',
borderRadius: 12,
padding: 16,
borderWidth: 1,
borderColor: '#E5E5EA',
},
sectorBreakdownTitle: {
fontSize: 16,
fontWeight: '600',
color: '#000',
marginBottom: 12,
},
sectorBreakdownItem: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
paddingVertical: 6,
},
sectorBreakdownSector: {
fontSize: 14,
color: '#8E8E93',
},
sectorBreakdownValue: {
fontSize: 14,
fontWeight: '600',
color: '#000',
},
rebalanceCard: {
backgroundColor: '#fff',
borderRadius: 12,
padding: 16,
marginBottom: 12,
borderWidth: 1,
borderColor: '#E5E5EA',
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
color: '#000',
flex: 1,
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
color: '#8E8E93',
marginBottom: 12,
lineHeight: 20,
},
rebalanceAllocation: {
flexDirection: 'row',
alignItems: 'center',
justifyContent: 'center',
gap: 8,
},
allocationLabel: {
fontSize: 14,
color: '#8E8E93',
},
allocationArrow: {
fontSize: 16,
color: '#007AFF',
fontWeight: '600',
},
// Rebalancing Button Styles
sectionHeader: {
flexDirection: 'row',
justifyContent: 'space-between',
alignItems: 'center',
marginBottom: 16,
gap: 12,
},
rebalanceButton: {
flexDirection: 'row',
alignItems: 'center',
backgroundColor: '#007AFF',
paddingHorizontal: 10,
paddingVertical: 6,
borderRadius: 6,
gap: 4,
},
rebalanceButtonDisabled: {
backgroundColor: '#8E8E93',
},
rebalanceButtonText: {
color: '#fff',
fontSize: 12,
fontWeight: '600',
},
rebalanceButtons: {
flexDirection: 'column',
gap: 6,
},
viewResultsButton: {
flexDirection: 'row',
alignItems: 'center',
backgroundColor: '#F2F2F7',
paddingHorizontal: 10,
paddingVertical: 6,
borderRadius: 6,
borderWidth: 1,
borderColor: '#007AFF',
gap: 4,
},
viewResultsButtonText: {
color: '#007AFF',
fontSize: 12,
fontWeight: '600',
},
// Dry run modal styles
previewHeader: {
flexDirection: 'row',
alignItems: 'center',
backgroundColor: '#E3F2FD',
padding: 16,
borderRadius: 12,
marginBottom: 20,
},
previewTitle: {
fontSize: 16,
fontWeight: '600',
color: '#1976D2',
marginLeft: 8,
},
previewSection: {
backgroundColor: '#fff',
padding: 16,
borderRadius: 12,
marginBottom: 16,
borderWidth: 1,
borderColor: '#E5E5EA',
},
sectionTitle: {
fontSize: 18,
fontWeight: '700',
color: '#1C1C1E',
marginBottom: 12,
},
previewItem: {
fontSize: 16,
color: '#3C3C43',
marginBottom: 8,
lineHeight: 22,
},
tradeItem: {
backgroundColor: '#F8F9FA',
padding: 12,
borderRadius: 8,
marginBottom: 8,
},
tradeAction: {
fontSize: 16,
fontWeight: '600',
color: '#1C1C1E',
marginBottom: 4,
},
tradeDetails: {
fontSize: 14,
color: '#6D6D70',
},
previewActions: {
flexDirection: 'row',
justifyContent: 'space-between',
marginTop: 20,
gap: 12,
},
actionButton: {
flex: 1,
paddingVertical: 16,
paddingHorizontal: 24,
borderRadius: 12,
alignItems: 'center',
},
cancelButton: {
backgroundColor: '#F2F2F7',
borderWidth: 1,
borderColor: '#C7C7CC',
},
cancelButtonText: {
fontSize: 16,
fontWeight: '600',
color: '#8E8E93',
},
executeButton: {
backgroundColor: '#FF3B30',
},
executeButtonText: {
fontSize: 16,
fontWeight: '600',
color: '#fff',
},
noSuggestionsCard: {
backgroundColor: '#F8F9FA',
borderRadius: 12,
padding: 20,
alignItems: 'center',
borderWidth: 1,
borderColor: '#E5E5EA',
marginTop: 12,
},
noSuggestionsTitle: {
fontSize: 16,
fontWeight: '600',
color: '#1C1C1E',
marginTop: 8,
marginBottom: 4,
},
noSuggestionsText: {
fontSize: 14,
color: '#8E8E93',
textAlign: 'center',
lineHeight: 20,
},
updatedLabel: {
color: '#34C759',
fontSize: 14,
fontWeight: '600',
},
improvementText: {
color: '#34C759',
fontSize: 16,
fontWeight: 'bold',
},
// Education Section Styles
educationCard: {
backgroundColor: '#fff',
borderRadius: 12,
padding: 16,
marginBottom: 12,
shadowColor: '#000',
shadowOffset: { width: 0, height: 2 },
shadowOpacity: 0.1,
shadowRadius: 4,
elevation: 3,
},
educationHeader: {
flexDirection: 'row',
alignItems: 'center',
marginBottom: 8,
},
educationTitle: {
fontSize: 16,
fontWeight: '600',
color: '#000',
marginLeft: 8,
},
educationText: {
fontSize: 14,
color: '#666',
lineHeight: 20,
},
strategyList: {
marginTop: 8,
},
strategyItem: {
marginBottom: 8,
},
strategyName: {
fontSize: 14,
fontWeight: '600',
color: '#000',
marginBottom: 2,
},
strategyDesc: {
fontSize: 13,
color: '#666',
lineHeight: 18,
},
termsList: {
marginTop: 8,
},
termItem: {
marginBottom: 6,
},
termName: {
fontSize: 13,
fontWeight: '600',
color: '#007AFF',
},
termDesc: {
fontSize: 12,
color: '#666',
marginTop: 2,
lineHeight: 16,
},
// AI Options Button Styles
aiOptionsButton: {
backgroundColor: '#fff',
borderRadius: 16,
padding: 20,
marginBottom: 12,
shadowColor: '#000',
shadowOffset: { width: 0, height: 4 },
shadowOpacity: 0.15,
shadowRadius: 8,
elevation: 6,
borderWidth: 1,
borderColor: '#e8f4fd',
},
// Refresh Button Styles
refreshButton: {
flexDirection: 'row',
alignItems: 'center',
backgroundColor: '#F2F2F7',
paddingHorizontal: 12,
paddingVertical: 8,
borderRadius: 8,
borderWidth: 1,
borderColor: '#007AFF',
},
refreshButtonText: {
color: '#007AFF',
fontSize: 14,
fontWeight: '600',
marginLeft: 4,
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
color: '#000',
marginLeft: 12,
},
aiOptionsDescription: {
fontSize: 14,
color: '#666',
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
color: '#34C759',
marginLeft: 4,
fontWeight: '500',
},
aiOptionsFooter: {
flexDirection: 'row',
alignItems: 'center',
backgroundColor: '#f0f8ff',
paddingHorizontal: 16,
paddingVertical: 8,
borderRadius: 20,
},
aiOptionsAction: {
fontSize: 14,
color: '#007AFF',
fontWeight: '600',
marginRight: 8,
},
});
export default PremiumAnalyticsScreen;
