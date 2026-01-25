import React, { useState, useMemo, memo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  FlatList,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import Slider from '@react-native-community/slider';
import { PieChart } from 'react-native-chart-kit';
import { Ionicons } from '@expo/vector-icons'; // Icons
import { useQuery } from '@apollo/client';
import { AI_YIELD_OPTIMIZER_QUERY } from '../graphql/queries_actual_schema';

const screenWidth = Dimensions.get('window').width - 32;

interface YieldOptimizerScreenProps {
  navigation?: any;
}

interface OptimizedPool {
  id: string;
  protocol: string;
  apy: number;
  tvl: number;
  risk: number;
  symbol: string;
  chain: string;
  weight: number;
}

interface OptimizerResult {
  expectedApy: number;
  totalRisk: number;
  explanation: string;
  allocations: OptimizedPool[];
  optimizationStatus: string;
  riskMetrics: any;
}

const YieldOptimizerScreen: React.FC<YieldOptimizerScreenProps> = memo(({ navigation }) => {
  const [riskTolerance, setRiskTolerance] = useState(0.5);
  const [selectedChain, setSelectedChain] = useState('ethereum');

  const { data, loading, refetch } = useQuery(AI_YIELD_OPTIMIZER_QUERY, {
    variables: {
      userRiskTolerance: riskTolerance,
      chain: selectedChain,
      limit: 8,
    },
    fetchPolicy: 'cache-first',
    errorPolicy: 'all',
    notifyOnNetworkStatusChange: false,
  });

  // Mock data for testing
  const mockResult: OptimizerResult = {
    expectedApy: 12.5,
    totalRisk: 0.65,
    explanation: "Based on your risk tolerance and current market conditions, this portfolio balances high-yield opportunities with risk management. The allocation focuses on established protocols with strong TVL and proven track records.",
    optimizationStatus: "OPTIMIZED",
    riskMetrics: {
      sharpeRatio: 1.8,
      maxDrawdown: 0.15,
      volatility: 0.22
    },
    allocations: [
      {
        id: 'aave-v3-eth',
        protocol: 'Aave V3',
        apy: 8.5,
        tvl: 1200000000,
        risk: 0.3,
        symbol: 'ETH',
        chain: 'ethereum',
        weight: 0.4
      },
      {
        id: 'compound-v3-usdc',
        protocol: 'Compound V3',
        apy: 6.2,
        tvl: 800000000,
        risk: 0.25,
        symbol: 'USDC',
        chain: 'ethereum',
        weight: 0.3
      },
      {
        id: 'uniswap-v3-eth-usdc',
        protocol: 'Uniswap V3',
        apy: 15.8,
        tvl: 500000000,
        risk: 0.7,
        symbol: 'ETH/USDC',
        chain: 'ethereum',
        weight: 0.2
      },
      {
        id: 'curve-3pool',
        protocol: 'Curve',
        apy: 4.1,
        tvl: 300000000,
        risk: 0.2,
        symbol: '3Pool',
        chain: 'ethereum',
        weight: 0.1
      }
    ]
  };

  const result: OptimizerResult = data?.aiYieldOptimizer || mockResult;

  const chartData = useMemo(() => {
    if (!result?.allocations) return [];
    
    return result.allocations.map((pool) => ({
      name: pool.protocol,
      population: Math.round(pool.weight * 100),
      color: getColorForProtocol(pool.protocol),
      legendFontColor: '#7c3aed',
      legendFontSize: 12,
    }));
  }, [result?.allocations]);

  const handleOptimize = () => {
    refetch();
  };

  const handleStakePool = (pool: OptimizedPool) => {
    Alert.alert(
      'Stake in Pool',
      `Stake in ${pool.protocol} (${pool.symbol})?\n\nExpected APY: ${pool.apy.toFixed(1)}%\nAllocation: ${Math.round(pool.weight * 100)}%`,
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Stake', onPress: () => navigation?.navigate('DeFiStake', { poolId: pool.id }) },
      ]
    );
  };

  const getRiskLevel = (risk: number) => {
    if (risk <= 0.3) return { label: 'Conservative', color: '#10B981', icon: 'shield-checkmark' as const };
    if (risk <= 0.7) return { label: 'Balanced', color: '#F59E0B', icon: 'scale' as const };
    return { label: 'Aggressive', color: '#EF4444', icon: 'flame' as const };
  };

  const riskLevel = getRiskLevel(riskTolerance);

  if (loading && !data) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Optimizing your portfolio...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Ionicons name="sparkles-outline" size={32} color="#007AFF" />
        <View style={styles.headerText}>
          <Text style={styles.title}>AI Yield Optimizer</Text>
          <Text style={styles.subtitle}>Maximize APY while managing risk</Text>
        </View>
      </View>

      {/* All Content - Scrollable */}
      <ScrollView style={styles.scrollContainer} showsVerticalScrollIndicator={false}>
        
        {/* Controls Card - Now scrollable */}
        <View style={styles.controlsCard}>
          <View style={styles.riskSection}>
            <View style={styles.riskHeader}>
              <View style={styles.riskIconContainer}>
                <Ionicons name={riskLevel.icon} size={16} color={riskLevel.color} />
                <Text style={styles.riskLabel}>Risk Tolerance</Text>
              </View>
              <View style={[styles.riskBadge, { backgroundColor: `${riskLevel.color}20` }]}>
                <Ionicons name={riskLevel.icon} size={12} color={riskLevel.color} />
                <Text style={[styles.riskBadgeText, { color: riskLevel.color }]}>{riskLevel.label}</Text>
              </View>
            </View>
            <Text style={styles.riskValue}>{Math.round(riskTolerance * 100)}%</Text>
            <Slider
              style={styles.slider}
              minimumValue={0}
              maximumValue={1}
              value={riskTolerance}
              onSlidingComplete={setRiskTolerance}
              minimumTrackTintColor={riskLevel.color}
              maximumTrackTintColor="#e5e7eb"
              thumbTintColor="#fff"
            />
            <View style={styles.riskLabels}>
              <Text style={styles.riskLabelText}>Conservative</Text>
              <Text style={styles.riskLabelText}>Aggressive</Text>
            </View>
          </View>

          <View style={styles.chainSelector}>
            {['ethereum', 'base', 'polygon'].map((chain) => (
              <TouchableOpacity
                key={chain}
                style={[
                  styles.chainButton,
                  selectedChain === chain && styles.chainButtonActive,
                ]}
                onPress={() => setSelectedChain(chain)}
                activeOpacity={0.7}
              >
                <Ionicons name="earth" size={14} color={selectedChain === chain ? '#fff' : '#6b7280'} />
                <Text
                  style={[
                    styles.chainButtonText,
                    selectedChain === chain && styles.chainButtonTextActive,
                  ]}
                >
                  {chain.charAt(0).toUpperCase() + chain.slice(1)}
                </Text>
              </TouchableOpacity>
            ))}
          </View>

          <TouchableOpacity style={styles.optimizeButton} onPress={handleOptimize} disabled={loading} activeOpacity={0.8}>
            <Ionicons name="refresh" size={18} color="#fff" />
            <Text style={styles.optimizeButtonText}>
              {loading ? 'Optimizing...' : 'Optimize Portfolio'}
            </Text>
          </TouchableOpacity>
        </View>

        {result?.allocations?.length === 0 ? (
          <View style={styles.noResultsContainer}>
            <Ionicons name="search-circle-outline" size={64} color="#d1d5db" />
            <Text style={styles.noResultsText}>
              No eligible pools for this risk level. Try increasing risk or changing chain.
            </Text>
          </View>
        ) : result?.allocations ? (
          <>
            {/* Results Header Card */}
            <View style={styles.card}>
              <View style={styles.resultsHeader}>
                <View style={styles.metricContainer}>
                  <Ionicons name="trending-up" size={24} color="#10B981" />
                  <Text style={styles.apyLabel}>Expected APY</Text>
                  <Text style={styles.apyValue}>{result.expectedApy?.toFixed(1)}%</Text>
                </View>
                <View style={styles.metricContainer}>
                  <Ionicons name={riskLevel.icon} size={24} color={riskLevel.color} />
                  <Text style={styles.riskLabel}>Portfolio Risk</Text>
                  <Text style={[styles.riskValue, { color: riskLevel.color }]}>
                    {result.totalRisk?.toFixed(2)}
                  </Text>
                </View>
              </View>
            </View>

            {/* Explanation Card */}
            <View style={styles.card}>
              <Ionicons name="bulb-outline" size={24} color="#7c3aed" style={styles.explanationIcon} />
              <Text style={styles.explanation}>{result.explanation}</Text>
            </View>

            {/* Chart Card */}
            {chartData.length > 0 && (
              <View style={styles.chartCard}>
                <Text style={styles.chartTitle}>Portfolio Allocation</Text>
                <PieChart
                  data={chartData}
                  width={screenWidth}
                  height={220}
                  chartConfig={{
                    backgroundColor: '#fff',
                    backgroundGradientFrom: '#fff',
                    backgroundGradientTo: '#fff',
                    decimalPlaces: 0,
                    color: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                    labelColor: (opacity = 1) => `rgba(0, 0, 0, ${opacity})`,
                    style: { borderRadius: 16 },
                    propsForDots: { r: '6', strokeWidth: '2', stroke: '#007AFF' },
                  }}
                  accessor="population"
                  backgroundColor="transparent"
                  paddingLeft="15"
                  absolute
                  hasLegend={false}
                />
                {/* Simple Legend */}
                <View style={styles.legendContainer}>
                  {chartData.map((entry, index) => (
                    <View key={index} style={styles.legendItem}>
                      <View style={[styles.legendColor, { backgroundColor: entry.color }]} />
                      <Text style={styles.legendText}>{entry.name} ({entry.population}%)</Text>
                    </View>
                  ))}
                </View>
              </View>
            )}

            {/* Allocations Card */}
            <View style={styles.allocationsCard}>
              <View style={styles.allocationsHeader}>
                <Ionicons name="pie-chart-outline" size={24} color="#10B981" />
                <Text style={styles.allocationsTitle}>Recommended Allocations</Text>
              </View>
              <View style={styles.allocationsList}>
                {result.allocations.map((item) => (
                  <TouchableOpacity
                    key={item.id}
                    style={styles.allocationItem}
                    onPress={() => handleStakePool(item)}
                    activeOpacity={0.7}
                  >
                    <View style={styles.allocationHeader}>
                      <View style={styles.protocolInfo}>
                        <Ionicons name={getProtocolIcon(item.protocol)} size={20} color="#007AFF" />
                        <View>
                          <Text style={styles.protocolName}>{item.protocol}</Text>
                          <Text style={styles.symbol}>{item.symbol}</Text>
                        </View>
                      </View>
                      <View style={styles.allocationInfo}>
                        <Text style={styles.allocationWeight}>
                          {Math.round(item.weight * 100)}%
                        </Text>
                        <Text style={styles.allocationApy}>
                          {item.apy.toFixed(1)}% APY
                        </Text>
                      </View>
                    </View>
                    <View style={styles.allocationDetails}>
                      <View style={styles.detailRow}>
                        <Text style={styles.detailLabel}>TVL</Text>
                        <Text style={styles.detailValue}>${(item.tvl / 1e6).toFixed(1)}M</Text>
                      </View>
                      <View style={styles.detailRow}>
                        <Text style={styles.detailLabel}>Risk</Text>
                        <Text style={[styles.detailValue, { color: getRiskLevel(item.risk).color }]}>
                          {getRiskLevel(item.risk).label}
                        </Text>
                      </View>
                    </View>
                    <TouchableOpacity style={styles.stakeMiniButton}>
                      <Text style={styles.stakeMiniButtonText}>Stake</Text>
                    </TouchableOpacity>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
          </>
        ) : null}
      </ScrollView>
    </View>
  );
});

// Helper function for protocol colors
const getColorForProtocol = (protocol: string): string => {
  const colors: { [key: string]: string } = {
    'Aave V3': '#B6509E',
    'Compound V3': '#00D395',
    'Uniswap V3': '#FF007A',
    'Curve': '#3465A4',
    'Yearn': '#006AE3',
    'Balancer': '#1E1E1E',
    'SushiSwap': '#F3BA2F',
    '1inch': '#1F2937',
  };
  return colors[protocol] || '#6B7280';
};

// Helper function for protocol icons
const getProtocolIcon = (protocol: string): any => {
  const icons: { [key: string]: any } = {
    'Aave V3': 'shield',
    'Compound V3': 'library',
    'Uniswap V3': 'swap-horizontal',
    'Curve': 'trending-up',
    'Yearn': 'rocket',
    'Balancer': 'scale',
    'SushiSwap': 'restaurant',
    '1inch': 'flash',
  };
  return icons[protocol] || 'diamond';
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  scrollContainer: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8f9fa',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  header: {
    padding: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 12,
  },
  headerText: {
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  subtitle: {
    fontSize: 16,
    color: '#6b7280',
    textAlign: 'center',
    marginTop: 4,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    margin: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  controlsCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 16,
    margin: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  riskSection: {
    marginBottom: 16,
  },
  riskHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  riskIconContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  riskLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
  },
  riskBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  riskBadgeText: {
    fontSize: 12,
    fontWeight: '600',
  },
  riskValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#007AFF',
    textAlign: 'center',
    marginBottom: 12,
  },
  slider: {
    width: '100%',
    height: 40,
  },
  sliderTrack: {
    height: 4,
    borderRadius: 2,
  },
  sliderThumb: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 3,
    width: 24,
    height: 24,
  },
  riskLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 12,
  },
  riskLabelText: {
    fontSize: 12,
    color: '#6b7280',
    fontWeight: '500',
  },
  chainSelector: {
    flexDirection: 'row',
    gap: 8,
    justifyContent: 'center',
    marginBottom: 16,
  },
  chainButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: '#f3f4f6',
    borderWidth: 1,
    borderColor: '#d1d5db',
  },
  chainButtonActive: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  chainButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#6b7280',
  },
  chainButtonTextActive: {
    color: '#fff',
  },
  optimizeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#007AFF',
    paddingVertical: 12,
    borderRadius: 12,
    justifyContent: 'center',
  },
  optimizeButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  noResultsContainer: {
    margin: 32,
    alignItems: 'center',
  },
  noResultsText: {
    fontSize: 16,
    color: '#6b7280',
    textAlign: 'center',
    marginTop: 12,
  },
  resultsHeader: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: 20,
  },
  metricContainer: {
    alignItems: 'center',
    gap: 4,
  },
  apyLabel: {
    fontSize: 14,
    color: '#6b7280',
  },
  apyValue: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#10B981',
  },
  explanationIcon: {
    position: 'absolute',
    top: 16,
    left: 16,
  },
  explanation: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 22,
    padding: 20,
    paddingLeft: 56,
  },
  chartCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    margin: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    alignItems: 'center',
  },
  chartTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
    marginBottom: 16,
  },
  legendContainer: {
    marginTop: 12,
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    gap: 12,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  legendColor: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  legendText: {
    fontSize: 12,
    color: '#6b7280',
    fontWeight: '500',
  },
  allocationsCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    margin: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    borderWidth: 1,
    borderColor: '#e5e7eb',
  },
  allocationsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  allocationsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
  },
  allocationsList: {
    paddingBottom: 20,
  },
  allocationItem: {
    padding: 16,
    marginHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  allocationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  protocolInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  protocolName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1f2937',
  },
  symbol: {
    fontSize: 14,
    color: '#6b7280',
  },
  allocationInfo: {
    alignItems: 'flex-end',
    gap: 2,
  },
  allocationWeight: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  allocationApy: {
    fontSize: 12,
    color: '#10B981',
    fontWeight: '500',
  },
  allocationDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  detailRow: {
    flexDirection: 'row',
    gap: 4,
  },
  detailLabel: {
    fontSize: 12,
    color: '#6b7280',
  },
  detailValue: {
    fontSize: 12,
    fontWeight: '500',
    color: '#1f2937',
  },
  stakeMiniButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    alignSelf: 'flex-end',
  },
  stakeMiniButtonText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
});

export default YieldOptimizerScreen;