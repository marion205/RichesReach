/**
 * AI Options Screen - Optimized Version
 * Uses GraphQL + FlatList virtualization for better performance
 */
import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  StatusBar,
  FlatList,
  InteractionManager,
} from 'react-native';
import Icon from 'react-native-vector-icons/MaterialIcons';
import { useQuery } from '@apollo/client';
import { gql } from '@apollo/client';

// GraphQL Query - Optimized to request only essential data
const GET_OPTIONS_ANALYSIS = gql`
  query GetOptionsAnalysis($symbol: String!) {
    optionsAnalysis(symbol: $symbol) {
      underlyingSymbol
      underlyingPrice
      putCallRatio
      impliedVolatilityRank
      skew
      sentimentScore
      sentimentDescription
      marketSentiment {
        sentiment
        sentimentDescription
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
      optionsChain {
        greeks {
          delta
          gamma
          theta
          vega
          rho
        }
        expirationDates
        calls {
          symbol
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
      }
    }
  }
`;

interface AIOptionsScreenProps {
  navigation: any;
}

// Memoized Option Row Component
const OptionRow = React.memo(function OptionRow({ option }: { option: any }) {
  const ivPct = useMemo(() => Math.round((option.impliedVolatility ?? 0) * 100), [option.impliedVolatility]);
  const delta = useMemo(() => option.delta?.toFixed?.(2) ?? '0.00', [option.delta]);
  
  return (
    <View style={styles.optionRow}>
      <Text style={styles.optionText}>
        {option.optionType} ${option.strike} • {ivPct}% IV • Δ {delta}
      </Text>
      <Text style={styles.optionSubtext}>
        Bid: ${option.bid} | Ask: ${option.ask} | Vol: {option.volume}
      </Text>
    </View>
  );
});

// Memoized Strategy Card Component
const StrategyCard = React.memo(function StrategyCard({ strategy, onPress }: { strategy: any; onPress: () => void }) {
  const profitLoss = useMemo(() => {
    const maxProfit = strategy.maxProfit || 0;
    const maxLoss = strategy.maxLoss || 0;
    return `Max Profit: $${maxProfit.toFixed(0)} | Max Loss: $${Math.abs(maxLoss).toFixed(0)}`;
  }, [strategy.maxProfit, strategy.maxLoss]);

  const probProfit = useMemo(() => 
    Math.round((strategy.probabilityOfProfit || 0) * 100), 
    [strategy.probabilityOfProfit]
  );

  return (
    <TouchableOpacity style={styles.strategyCard} onPress={onPress}>
      <View style={styles.strategyHeader}>
        <Text style={styles.strategyName}>{strategy.strategyName}</Text>
        <View style={[styles.strategyTypeBadge, { backgroundColor: getStrategyColor(strategy.strategyType) }]}>
          <Text style={styles.strategyTypeText}>{strategy.strategyType?.toUpperCase()}</Text>
        </View>
      </View>
      <Text style={styles.strategyDescription}>{strategy.description}</Text>
      <Text style={styles.profitLossText}>{profitLoss}</Text>
      <Text style={styles.probabilityText}>Probability of Profit: {probProfit}%</Text>
    </TouchableOpacity>
  );
});

// Helper function for strategy colors
const getStrategyColor = (type: string) => {
  switch (type) {
    case 'income': return '#34C759';
    case 'protection': return '#FF9500';
    case 'neutral': return '#007AFF';
    case 'volatility': return '#FF3B30';
    default: return '#8E8E93';
  }
};

const AIOptionsScreenOptimized: React.FC<AIOptionsScreenProps> = ({ navigation }) => {
  const [symbol, setSymbol] = useState('AAPL');
  const [ready, setReady] = useState(false);
  const [selectedStrategy, setSelectedStrategy] = useState<any>(null);

  // Defer heavy work until after UI settles
  useEffect(() => {
    const task = InteractionManager.runAfterInteractions(() => setReady(true));
    return () => task.cancel();
  }, []);

  // GraphQL Query with optimized fetch policy
  const { data, loading, error, refetch } = useQuery(GET_OPTIONS_ANALYSIS, {
    variables: { symbol },
    fetchPolicy: 'cache-first',
    notifyOnNetworkStatusChange: false,
    errorPolicy: 'all',
  });

  // Memoized data processing
  const optionsData = useMemo(() => {
    if (!data?.optionsAnalysis) return { calls: [], puts: [] };
    
    const chain = data.optionsAnalysis.optionsChain;
    return {
      calls: chain?.calls || [],
      puts: chain?.puts || [],
      strategies: data.optionsAnalysis.recommendedStrategies || [],
      marketData: {
        symbol: data.optionsAnalysis.underlyingSymbol,
        price: data.optionsAnalysis.underlyingPrice,
        sentiment: data.optionsAnalysis.marketSentiment,
        putCallRatio: data.optionsAnalysis.putCallRatio,
      }
    };
  }, [data]);

  // Memoized callbacks
  const handleSearch = useCallback(() => {
    refetch({ symbol });
  }, [symbol, refetch]);

  const handleStrategyPress = useCallback((strategy: any) => {
    setSelectedStrategy(strategy);
  }, []);

  const keyExtractor = useCallback((item: any) => item.symbol, []);
  const renderOptionItem = useCallback(({ item }: { item: any }) => <OptionRow option={item} />, []);
  const renderStrategyItem = useCallback(({ item }: { item: any }) => (
    <StrategyCard strategy={item} onPress={() => handleStrategyPress(item)} />
  ), [handleStrategyPress]);

  // Loading state
  if (loading && !data) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading AI Options Analysis...</Text>
      </View>
    );
  }

  // Error state
  if (error) {
    return (
      <View style={styles.errorContainer}>
        <Icon name="error" size={48} color="#FF3B30" />
        <Text style={styles.errorText}>Failed to load options data</Text>
        <Text style={styles.errorSubtext}>{error.message}</Text>
        <TouchableOpacity style={styles.retryButton} onPress={() => refetch()}>
          <Text style={styles.retryButtonText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#fff" />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={() => navigation.goBack()}>
          <Icon name="arrow-back" size={24} color="#000" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>AI Options</Text>
        <TouchableOpacity style={styles.refreshButton} onPress={handleSearch} disabled={loading}>
          <Icon name="refresh" size={24} color="#007AFF" />
        </TouchableOpacity>
      </View>

      {/* Search Input */}
      <View style={styles.inputSection}>
        <View style={styles.inputRow}>
          <TextInput
            style={styles.symbolInput}
            value={symbol}
            onChangeText={setSymbol}
            placeholder="Symbol (e.g., AAPL)"
            placeholderTextColor="#8E8E93"
            autoCapitalize="characters"
          />
          <TouchableOpacity
            style={[styles.searchButton, loading && styles.searchButtonDisabled]}
            onPress={handleSearch}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator size="small" color="#fff" />
            ) : (
              <Icon name="search" size={20} color="#fff" />
            )}
          </TouchableOpacity>
        </View>
      </View>

      {/* Market Overview */}
      {optionsData.marketData && (
        <View style={styles.marketCard}>
          <Text style={styles.marketTitle}>{optionsData.marketData.symbol}</Text>
          <Text style={styles.marketPrice}>${optionsData.marketData.price?.toFixed(2)}</Text>
          <Text style={styles.marketSentiment}>
            {optionsData.marketData.sentiment?.sentiment} • Put/Call: {optionsData.marketData.putCallRatio?.toFixed(2)}
          </Text>
        </View>
      )}

      {/* Strategies Section */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Recommended Strategies ({optionsData.strategies.length})</Text>
        <FlatList
          data={optionsData.strategies}
          keyExtractor={keyExtractor}
          renderItem={renderStrategyItem}
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.strategiesList}
          initialNumToRender={3}
          maxToRenderPerBatch={3}
          windowSize={5}
          removeClippedSubviews
        />
      </View>

      {/* Options Chain - Only render when ready */}
      {ready ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Options Chain</Text>
          <FlatList
            data={[...optionsData.calls, ...optionsData.puts]}
            keyExtractor={keyExtractor}
            renderItem={renderOptionItem}
            initialNumToRender={8}
            windowSize={5}
            maxToRenderPerBatch={8}
            removeClippedSubviews
            getItemLayout={(_, index) => ({ length: 64, offset: 64 * index, index })}
            contentContainerStyle={styles.optionsList}
          />
        </View>
      ) : (
        <View style={styles.skeletonContainer}>
          <ActivityIndicator size="small" color="#007AFF" />
          <Text style={styles.skeletonText}>Loading options chain...</Text>
        </View>
      )}

      {/* Strategy Detail Modal */}
      {selectedStrategy && (
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>{selectedStrategy.strategyName}</Text>
              <TouchableOpacity onPress={() => setSelectedStrategy(null)}>
                <Icon name="close" size={24} color="#8E8E93" />
              </TouchableOpacity>
            </View>
            <Text style={styles.modalDescription}>{selectedStrategy.description}</Text>
            <Text style={styles.modalRisk}>Risk Level: {selectedStrategy.riskLevel}</Text>
            <Text style={styles.modalOutlook}>Market Outlook: {selectedStrategy.marketOutlook}</Text>
          </View>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    paddingTop: 44,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    padding: 20,
  },
  errorText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FF3B30',
    marginTop: 16,
  },
  errorSubtext: {
    fontSize: 14,
    color: '#666',
    marginTop: 8,
    textAlign: 'center',
  },
  retryButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 8,
    marginTop: 16,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
  },
  refreshButton: {
    padding: 8,
  },
  inputSection: {
    backgroundColor: '#fff',
    padding: 16,
    marginBottom: 8,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  symbolInput: {
    flex: 1,
    height: 40,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    borderRadius: 8,
    paddingHorizontal: 12,
    fontSize: 16,
    marginRight: 12,
  },
  searchButton: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
  },
  searchButtonDisabled: {
    backgroundColor: '#8E8E93',
    opacity: 0.6,
  },
  marketCard: {
    backgroundColor: '#fff',
    padding: 16,
    marginBottom: 8,
    alignItems: 'center',
  },
  marketTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#000',
  },
  marketPrice: {
    fontSize: 24,
    fontWeight: '600',
    color: '#007AFF',
    marginTop: 4,
  },
  marketSentiment: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  section: {
    flex: 1,
    backgroundColor: '#fff',
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    padding: 16,
    paddingBottom: 8,
  },
  strategiesList: {
    paddingHorizontal: 16,
  },
  strategyCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 16,
    marginRight: 12,
    width: 280,
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  strategyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  strategyName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    flex: 1,
  },
  strategyTypeBadge: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  strategyTypeText: {
    fontSize: 10,
    fontWeight: '600',
    color: '#fff',
  },
  strategyDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  profitLossText: {
    fontSize: 12,
    color: '#007AFF',
    marginBottom: 4,
  },
  probabilityText: {
    fontSize: 12,
    color: '#34C759',
  },
  optionsList: {
    paddingHorizontal: 16,
  },
  optionRow: {
    height: 64,
    justifyContent: 'center',
    paddingHorizontal: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  optionText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#000',
  },
  optionSubtext: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  skeletonContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
    backgroundColor: '#fff',
  },
  skeletonText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#666',
  },
  modalOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    margin: 20,
    maxWidth: '90%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
    flex: 1,
  },
  modalDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 12,
  },
  modalRisk: {
    fontSize: 14,
    color: '#FF9500',
    marginBottom: 8,
  },
  modalOutlook: {
    fontSize: 14,
    color: '#007AFF',
  },
});

export default AIOptionsScreenOptimized;
