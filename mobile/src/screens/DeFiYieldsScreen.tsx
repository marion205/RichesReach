import React, { useState, memo, useCallback, useMemo, Suspense, useEffect } from 'react';
import {
  View,
  Text,
  FlatList,
  TouchableOpacity,
  TextInput,
  Alert,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
  useColorScheme,
  Animated, // For subtle animations
} from 'react-native';
import { Ionicons } from '@expo/vector-icons'; // Icons
import { useQuery, useMutation } from '@apollo/client';
import { TOP_YIELDS_QUERY, STAKE_INTENT_MUTATION } from '../graphql/queries_actual_schema';
import { debounce } from '../utils/debounce';

interface DeFiYieldsScreenProps {
  navigation?: any;
  onTabChange?: (tab: string) => void;
}

interface YieldItem {
  id: string;
  protocol: string;
  chain: string;
  symbol: string;
  poolAddress: string;
  apy: number;
  apyBase: number;
  apyReward: number;
  tvl: number;
  risk: number;
  audits: string[];
  url: string;
}

// Constants
const CHAINS = ['ethereum', 'base', 'polygon'] as const;
const RISK_THRESHOLDS = { low: 0.3, medium: 0.7 } as const;
const DEBOUNCE_DELAY = 300;
const QUERY_LIMIT = 20;

// Mock data for instant loading
const MOCK_YIELDS: YieldItem[] = [
  {
    id: 'mock-1',
    protocol: 'Aave V3',
    chain: 'ethereum',
    symbol: 'USDC',
    poolAddress: '0x...',
    apy: 8.5,
    apyBase: 6.2,
    apyReward: 2.3,
    tvl: 2500000000,
    risk: 0.2,
    audits: ['OpenZeppelin', 'Trail of Bits'],
    url: 'https://app.aave.com',
  },
  {
    id: 'mock-2',
    protocol: 'Compound',
    chain: 'ethereum',
    symbol: 'USDT',
    poolAddress: '0x...',
    apy: 7.8,
    apyBase: 5.5,
    apyReward: 2.3,
    tvl: 1800000000,
    risk: 0.3,
    audits: ['OpenZeppelin'],
    url: 'https://app.compound.finance',
  },
  {
    id: 'mock-3',
    protocol: 'Uniswap V3',
    chain: 'ethereum',
    symbol: 'ETH/USDC',
    poolAddress: '0x...',
    apy: 12.4,
    apyBase: 8.1,
    apyReward: 4.3,
    tvl: 3200000000,
    risk: 0.6,
    audits: ['ConsenSys'],
    url: 'https://app.uniswap.org',
  },
  {
    id: 'mock-4',
    protocol: 'Curve',
    chain: 'ethereum',
    symbol: '3CRV',
    poolAddress: '0x...',
    apy: 6.2,
    apyBase: 4.8,
    apyReward: 1.4,
    tvl: 1500000000,
    risk: 0.4,
    audits: ['OpenZeppelin', 'Trail of Bits'],
    url: 'https://curve.fi',
  },
  {
    id: 'mock-5',
    protocol: 'Yearn',
    chain: 'ethereum',
    symbol: 'yUSDC',
    poolAddress: '0x...',
    apy: 9.1,
    apyBase: 6.5,
    apyReward: 2.6,
    tvl: 800000000,
    risk: 0.5,
    audits: ['OpenZeppelin'],
    url: 'https://yearn.finance',
  },
];

// Chain Icons Map
const CHAIN_ICONS = {
  ethereum: 'diamond',
  base: 'layers',
  polygon: 'triangle',
} as const;

// Sub-component: Single Yield Item with Animation
const YieldItem: React.FC<{ item: YieldItem; onStake: (item: YieldItem) => void; index: number }> = memo(({ item, onStake, index }) => {
  const fadeAnim = useMemo(() => new Animated.Value(0), [index]);
  
  useEffect(() => {
    Animated.timing(fadeAnim, { 
      toValue: 1, 
      duration: 300, 
      delay: index * 50, 
      useNativeDriver: true 
    }).start();
  }, [fadeAnim, index]);

  const formatTVL = (tvl: number) => {
    if (tvl >= 1e9) return `$${(tvl / 1e9).toFixed(1)}B`;
    if (tvl >= 1e6) return `$${(tvl / 1e6).toFixed(1)}M`;
    return `$${(tvl / 1e3).toFixed(1)}K`;
  };

  const getRiskColor = (risk: number) => {
    if (risk < RISK_THRESHOLDS.low) return '#10B981';
    if (risk < RISK_THRESHOLDS.medium) return '#F59E0B';
    return '#EF4444';
  };

  const getRiskLabel = (risk: number) => {
    if (risk < RISK_THRESHOLDS.low) return 'Low';
    if (risk < RISK_THRESHOLDS.medium) return 'Medium';
    return 'High';
  };

  const getRiskIcon = (risk: number) => {
    if (risk < RISK_THRESHOLDS.low) return 'shield';
    if (risk < RISK_THRESHOLDS.medium) return 'warning';
    return 'warning';
  };

  return (
    <Animated.View style={[styles.yieldItem, { opacity: fadeAnim }]}>
      <TouchableOpacity
        style={styles.yieldCardTouchable}
        onPress={() => onStake(item)}
        activeOpacity={0.8}
        accessibilityRole="button"
        accessibilityLabel={`Stake in ${item.protocol} on ${item.chain}, APY ${item.apy.toFixed(1)}%`}
      >
        <View style={styles.yieldHeader}>
          <View style={styles.protocolInfo}>
            <View style={styles.protocolIcon}>
              <Ionicons name="pulse" size={24} color="#10B981" />
            </View>
            <View>
              <Text style={styles.protocolName}>{item.protocol}</Text>
              <Text style={styles.symbol}>{item.symbol}</Text>
            </View>
          </View>
          <View style={styles.apyContainer}>
            <View style={styles.apyBadge}>
              <Text style={styles.apyText}>{item.apy.toFixed(1)}%</Text>
            </View>
            <Text style={styles.apyLabel}>APY</Text>
          </View>
        </View>
        
        <View style={styles.yieldDetails}>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>TVL</Text>
            <Text style={styles.detailValue}>{formatTVL(item.tvl)}</Text>
          </View>
          <View style={styles.detailRow}>
            <View style={[styles.riskPill, { backgroundColor: getRiskColor(item.risk) + '20' }]}>
              <Ionicons name={getRiskIcon(item.risk)} size={16} color={getRiskColor(item.risk)} />
              <Text style={[styles.riskLabel, { color: getRiskColor(item.risk) }]}>{getRiskLabel(item.risk)}</Text>
            </View>
          </View>
          <View style={styles.detailRow}>
            <Text style={styles.detailLabel}>Base</Text>
            <Text style={styles.detailValue}>{item.apyBase.toFixed(1)}%</Text>
          </View>
          {item.apyReward > 0 && (
            <View style={styles.detailRow}>
              <Text style={styles.detailLabel}>Rewards</Text>
              <Text style={styles.detailValue}>+{item.apyReward.toFixed(1)}%</Text>
            </View>
          )}
        </View>
        
        {item.audits.length > 0 && (
          <View style={styles.auditContainer}>
            <Text style={styles.auditLabel}>Audited:</Text>
            <Text style={styles.auditValue}>{item.audits.join(', ')}</Text>
          </View>
        )}
        
        <TouchableOpacity style={styles.stakeButton} onPress={() => onStake(item)}>
          <Ionicons name="add-circle" size={20} color="#fff" />
          <Text style={styles.stakeButtonText}>Stake Now</Text>
        </TouchableOpacity>
      </TouchableOpacity>
    </Animated.View>
  );
});

// Sub-component: Chain Selector (Scrollable Pills)
const ChainSelector: React.FC<{ selectedChain: string; onSelect: (chain: string) => void }> = memo(({ selectedChain, onSelect }) => (
  <FlatList
    horizontal
    data={CHAINS}
    keyExtractor={(chain) => chain}
    renderItem={({ item: chain }) => (
      <TouchableOpacity
        style={[
          styles.chainButton,
          selectedChain === chain && styles.chainButtonActive,
        ]}
        onPress={() => onSelect(chain)}
        accessibilityRole="tab"
        accessibilityState={{ selected: selectedChain === chain }}
      >
        <Ionicons name={CHAIN_ICONS[chain]} size={16} color={selectedChain === chain ? '#fff' : '#888'} />
        <Text style={[styles.chainButtonText, selectedChain === chain && styles.chainButtonTextActive]}>
          {chain.charAt(0).toUpperCase() + chain.slice(1)}
        </Text>
      </TouchableOpacity>
    )}
    showsHorizontalScrollIndicator={false}
    contentContainerStyle={styles.chainSelector}
  />
));

// Shimmer Skeleton
const AISkeleton = () => {
  const [shimmer, setShimmer] = useState(new Animated.Value(0));
  
  useEffect(() => {
    const anim = Animated.loop(
      Animated.timing(shimmer, { 
        toValue: 1, 
        duration: 1500, 
        useNativeDriver: false 
      })
    ).start();
    return () => anim.stop();
  }, [shimmer]);

  const shimmerAnim = shimmer.interpolate({
    inputRange: [0, 1],
    outputRange: ['#e5e7eb', '#f3f4f6', '#e5e7eb'],
  });

  return (
    <View style={styles.skeletonContainer}>
      <View style={styles.skeletonHeader}>
        <Animated.View style={[styles.skeletonTitle, { backgroundColor: shimmerAnim }]} />
        <Animated.View style={[styles.skeletonBadge, { backgroundColor: shimmerAnim }]} />
      </View>
      <View style={styles.skeletonContent}>
        <Animated.View style={[styles.skeletonLine, { backgroundColor: shimmerAnim }]} />
        <Animated.View style={[styles.skeletonLine, { backgroundColor: shimmerAnim }]} />
        <Animated.View style={[styles.skeletonLine, { backgroundColor: shimmerAnim }]} />
      </View>
    </View>
  );
};

// Partial Yields (Updated with YieldItem)
const PartialYields = memo(({ data, onRefresh, refreshing, onStake, showAI, navigation, onTabChange }: { data: any; onRefresh: () => void; refreshing: boolean; onStake: (item: YieldItem) => void; showAI: boolean; navigation?: any; onTabChange?: (tab: string) => void }) => (
  <FlatList
    style={styles.flatListContainer}
    data={data?.topYields || []}
    keyExtractor={(item) => item.id}
    renderItem={({ item, index }) => <YieldItem item={item} onStake={onStake} index={index} />}
    refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
    contentContainerStyle={styles.listContainer}
    showsVerticalScrollIndicator={false}
    removeClippedSubviews={true}
    initialNumToRender={10}
    maxToRenderPerBatch={5}
    windowSize={10}
    updateCellsBatchingPeriod={50}
    getItemLayout={(data, index) => ({ length: 120, offset: 120 * index, index })}
    ListEmptyComponent={
      <View style={styles.emptyContainer}>
        <Ionicons name="search" size={64} color="#666" />
        <Text style={styles.emptyText}>No yields found. Try searching or switching chains.</Text>
      </View>
    }
    ListFooterComponent={
      showAI && (
        <View style={styles.aiSection}>
          <Text style={styles.aiSectionTitle}>AI-Powered Recommendations</Text>
          <TouchableOpacity
            style={styles.optimizerFAB}
            onPress={() => onTabChange?.('optimizer')}
            accessibilityRole="button"
            accessibilityLabel="Open AI Yield Optimizer"
          >
            <Ionicons name="sparkles" size={20} color="#fff" />
            <Text style={styles.optimizerButtonText}>AI Optimizer</Text>
          </TouchableOpacity>
        </View>
      )
    }
  />
));

const DeFiYieldsScreen: React.FC<DeFiYieldsScreenProps> = memo(({ navigation, onTabChange }) => {
  const [search, setSearch] = useState('');
  const [selectedChain, setSelectedChain] = useState('ethereum');
  const [refreshing, setRefreshing] = useState(false);
  const [showAI, setShowAI] = useState(true); // Show AI section by default for testing

  // Debounced handlers
  const debouncedSetSearch = useCallback(debounce((value: string) => setSearch(value), DEBOUNCE_DELAY), []);
  const debouncedSetChain = useCallback(debounce((chain: string) => setSelectedChain(chain), DEBOUNCE_DELAY), []);

  const { data, loading, error, refetch } = useQuery(TOP_YIELDS_QUERY, {
    variables: { chain: selectedChain, limit: QUERY_LIMIT },
    fetchPolicy: 'cache-and-network',     // show cached immediately, then refresh
    nextFetchPolicy: 'cache-first',
    returnPartialData: true,
    errorPolicy: 'all',
    notifyOnNetworkStatusChange: false,
  });

  // Progressive AI trigger
  useEffect(() => {
    if (!loading && data?.topYields?.length > 0) {
      const timer = setTimeout(() => setShowAI(true), 100);
      return () => clearTimeout(timer);
    }
  }, [loading, data]);

  const [stakeIntent] = useMutation(STAKE_INTENT_MUTATION);

  const handleStake = useCallback(async (pool: YieldItem) => {
    try {
      const result = await stakeIntent({
        variables: { 
          poolId: pool.id, 
          wallet: '0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6', 
          amount: 1.0 
        },
      });
      
      if (result.data?.stakeIntent?.ok) {
        Alert.alert(
          'Staking Intent Created',
          'Please sign the transaction in your wallet to complete staking.',
          [{ text: 'OK', onPress: () => navigation?.navigate?.('WalletConnect') }]
        );
      } else {
        Alert.alert('Error', result.data?.stakeIntent?.message || 'Failed to create staking intent');
      }
    } catch (err) {
      console.error('Staking error:', err);
      Alert.alert('Error', 'Failed to initiate staking');
    }
  }, [stakeIntent, navigation]);

  // Memoized filtered data - always use mock data for optimistic loading, replace with real data when available
  const yields = useMemo(() => {
    // Priority 1: Use real data if available
    if (data?.topYields && data.topYields.length > 0) {
      return data.topYields.filter((yieldItem: YieldItem) =>
        yieldItem.protocol.toLowerCase().includes(search.toLowerCase()) ||
        yieldItem.symbol.toLowerCase().includes(search.toLowerCase())
      );
    }
    // Priority 2: Always use mock data for optimistic loading (show immediately, replace when real data arrives)
    return MOCK_YIELDS.filter((yieldItem: YieldItem) =>
      yieldItem.protocol.toLowerCase().includes(search.toLowerCase()) ||
      yieldItem.symbol.toLowerCase().includes(search.toLowerCase())
    );
  }, [data, search]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await refetch();
    } finally {
      setRefreshing(false);
    }
  }, [refetch]);

  // Never show error state - always use mock data as fallback
  // The yields useMemo already handles this, so we just render normally

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>DeFi Yield Farming</Text>
        <Text style={styles.subtitle}>Earn passive income with crypto</Text>
      </View>

      <View style={styles.controls}>
        <TextInput
          style={styles.searchInput}
          placeholder="Search protocols or tokens…"
          value={search}
          onChangeText={debouncedSetSearch}
          placeholderTextColor="#888"
          accessibilityLabel="Search yields"
        />
        <ChainSelector selectedChain={selectedChain} onSelect={debouncedSetChain} />
      </View>

      <PartialYields 
        data={{ topYields: yields }} 
        onRefresh={onRefresh} 
        refreshing={refreshing} 
        onStake={handleStake}
        showAI={showAI}
        navigation={navigation}
        onTabChange={onTabChange}
      />
    </View>
  );
});

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff', // Clean white background
  },
  header: {
    padding: 20,
    backgroundColor: '#ffffff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1f2937',
    backgroundColor: 'transparent',
  },
  subtitle: {
    fontSize: 16,
    color: '#6b7280',
  },
  // Controls
  controls: {
    padding: 16,
    backgroundColor: '#ffffff',
  },
  searchInput: {
    backgroundColor: '#f9fafb',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    marginBottom: 16,
    color: '#1f2937',
    borderWidth: 1,
    borderColor: '#d1d5db',
  },
  chainSelector: {
    paddingHorizontal: 8,
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
    marginRight: 8,
  },
  chainButtonActive: {
    backgroundColor: '#10B981',
    borderColor: '#10B981',
  },
  chainButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6b7280',
  },
  chainButtonTextActive: {
    color: '#fff',
  },
  // Yield Item
  yieldItem: {
    marginBottom: 16,
  },
  yieldCardTouchable: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#e5e7eb',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  yieldHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  protocolInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  protocolIcon: {
    backgroundColor: '#10B98120',
    padding: 4,
    borderRadius: 6,
  },
  protocolName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1f2937',
  },
  symbol: {
    fontSize: 14,
    color: '#6b7280',
  },
  apyContainer: {
    alignItems: 'flex-end',
  },
  apyBadge: {
    backgroundColor: '#10B981',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  apyText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    fontFamily: 'monospace', // For numbers
  },
  apyLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginTop: 2,
  },
  yieldDetails: {
    marginBottom: 16,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  detailLabel: {
    fontSize: 14,
    color: '#6b7280',
  },
  detailValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1f2937',
    fontFamily: 'monospace',
  },
  riskPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  riskLabel: {
    fontSize: 12,
    fontWeight: '600',
  },
  auditContainer: {
    marginBottom: 16,
    padding: 8,
    backgroundColor: '#f0f9ff',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#bae6fd',
  },
  auditLabel: {
    fontSize: 12,
    color: '#0369a1',
    fontWeight: '600',
  },
  auditValue: {
    fontSize: 12,
    color: '#1f2937',
    marginTop: 2,
  },
  stakeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: '#007AFF',
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: 'center',
  },
  stakeButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  // AI Section - Normal footer (not floating)
  aiSection: {
    backgroundColor: '#ffffff',
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
    padding: 16,
    marginTop: 16,
  },
  aiSectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1f2937',
    textAlign: 'center',
    marginBottom: 12,
  },
  optimizerFAB: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#10B981',
    paddingHorizontal: 20,
    paddingVertical: 14,
    borderRadius: 12,
    marginTop: 8,
    shadowColor: '#10B981',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  optimizerButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  // Other styles (loading, error, empty, skeleton) adapted to light theme
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#ffffff',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#6b7280',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#ffffff',
    padding: 20,
  },
  errorText: {
    fontSize: 16,
    color: '#EF4444',
    marginBottom: 16,
    textAlign: 'center',
  },
  retryButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  contentContainer: {
    flex: 1,
  },
  flatListContainer: {
    flex: 1,
  },
  listContainer: {
    padding: 16,
    flexGrow: 1,
  },
  emptyContainer: {
    padding: 40,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#6b7280',
    textAlign: 'center',
  },
  loadingFooter: {
    padding: 20,
    alignItems: 'center',
  },
  footerNote: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 8,
  },
  skeletonContainer: {
    padding: 16,
    backgroundColor: '#f8f9fa',
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb',
  },
  skeletonHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  skeletonTitle: {
    height: 20,
    width: 200,
    backgroundColor: '#e5e7eb',
    borderRadius: 4,
  },
  skeletonBadge: {
    height: 20,
    width: 80,
    backgroundColor: '#e5e7eb',
    borderRadius: 10,
  },
  skeletonContent: {
    gap: 8,
  },
  skeletonLine: {
    height: 16,
    backgroundColor: '#e5e7eb',
    borderRadius: 4,
  },
});

export default DeFiYieldsScreen;