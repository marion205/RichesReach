import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  FlatList,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useLazyQuery, useQuery } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import { SEARCH_STOCKS, TOP_STOCKS, RESEARCH_HUB } from '../../../graphql/queries_actual_schema';
import StockTradingModal from '../../../components/forms/StockTradingModal';
import logger from '../../../utils/logger';

const RECENTS_KEY = 'research_recent_symbols';

// Map regime types to simple labels
function getRegimeLabel(regime: string): string {
  const normalized = regime?.toLowerCase() || '';
  if (normalized.includes('bull') || normalized.includes('calm')) return 'Calm';
  if (normalized.includes('bear') || normalized.includes('storm')) return 'Storm';
  if (normalized.includes('sideways') || normalized.includes('choppy') || normalized.includes('volatile')) return 'Choppy';
  return 'Choppy'; // Default
}

// Debounce hook for search
const useDebounce = (value: string, ms = 300) => {
  const [debouncedValue, setDebouncedValue] = useState(value);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => setDebouncedValue(value), ms);
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [value, ms]);

  return debouncedValue;
};

// Helper functions
const safeNum = (n?: number) => (n && n > 0 ? n.toFixed(2) : 'N/A');
const safePct = (n?: number) => (n ? `${n.toFixed(2)}%` : 'N/A');
const safeMoney = (n?: number) => (n ? `$${n.toFixed(2)}` : 'N/A');

export default function ResearchScreen() {
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
  const [searchQuery, setSearchQuery] = useState('');
  const debouncedQuery = useDebounce(searchQuery, 250);
  const [recents, setRecents] = useState<string[]>([]);
  const [tradingModalVisible, setTradingModalVisible] = useState(false);
  const [selectedStock, setSelectedStock] = useState<any>(null);

  // Load/save recent symbols
  useEffect(() => {
    const loadRecents = async () => {
      try {
        const raw = await AsyncStorage.getItem(RECENTS_KEY);
        setRecents(raw ? JSON.parse(raw) : []);
      } catch (error) {
        logger.error('Error loading recent symbols:', error);
      }
    };
    loadRecents();
  }, []);

  const pushRecent = async (symbol: string) => {
    try {
      const next = [symbol, ...recents.filter(x => x !== symbol)].slice(0, 8);
      setRecents(next);
      await AsyncStorage.setItem(RECENTS_KEY, JSON.stringify(next));
    } catch (error) {
        logger.error('Error saving recent symbol:', error);
    }
  };

  // Search functionality
  const [runSearch, { data: searchData, loading: searching }] = useLazyQuery(SEARCH_STOCKS, { 
    fetchPolicy: 'network-only' 
  });

  useEffect(() => {
    const term = debouncedQuery.trim();
    if (term.length >= 2) {
      runSearch({ variables: { term, limit: 10 } });
    }
  }, [debouncedQuery, runSearch]);

  // Top stocks for initial display
  const { data: topStocksData, loading: topStocksLoading } = useQuery(TOP_STOCKS, {
    variables: { limit: 10 },
    skip: !!searchQuery
  });

  // Research data for selected symbol
  const { data: researchData, loading: researchLoading, error: researchError, refetch } = useQuery(RESEARCH_HUB, {
    variables: { symbol: selectedSymbol },
    fetchPolicy: 'network-only',
    nextFetchPolicy: 'cache-first',
  });

  // Timeout handling for research loading
  const [researchLoadingTimeout, setResearchLoadingTimeout] = useState(false);
  useEffect(() => {
    if (researchLoading && !researchData) {
      const timer = setTimeout(() => {
        setResearchLoadingTimeout(true);
      }, 3000); // 3 second timeout
      return () => clearTimeout(timer);
    } else {
      setResearchLoadingTimeout(false);
    }
  }, [researchLoading, researchData]);

  // Generate mock research data for demo
  const getMockResearchData = () => {
    const symbol = selectedSymbol;
    const basePrice = symbol === 'AAPL' ? 175.50 : symbol === 'MSFT' ? 380.25 : 150.00;
    const change = basePrice * 0.02; // 2% change
    
    return {
      researchHub: {
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
        peers: symbol === 'AAPL' ? ['MSFT', 'GOOGL', 'META', 'AMZN'] : ['AAPL', 'GOOGL', 'META'],
      },
    };
  };

  // Use mock data immediately if loading, or if timeout/error occurs
  // This provides instant content while real data loads
  const effectiveResearchData = useMemo(() => {
    // Prioritize real data if available
    if (researchData?.researchHub) {
      return researchData;
    }
    // Show mock data immediately while loading, on timeout, or on error
    if (researchLoading || researchLoadingTimeout || researchError) {
      return getMockResearchData();
    }
    return null;
  }, [researchData, researchLoadingTimeout, researchError, researchLoading, selectedSymbol]);
  
  // Don't show loading spinner - always show mock data immediately while loading
  const effectiveResearchLoading = false;

  // Change symbol handler
  const openSymbol = (symbol: string) => {
    const upperSymbol = symbol.toUpperCase();
    setSelectedSymbol(upperSymbol);
    setSearchQuery('');
    pushRecent(upperSymbol);
    refetch({ symbol: upperSymbol });
  };

  // Open trading modal
  const openTradingModal = (stock: any) => {
    setSelectedStock(stock);
    setTradingModalVisible(true);
  };

  const searchResults = searchData?.searchStocks ?? [];
  const topStocks = topStocksData?.topStocks ?? [];
  const displayStocks = searchQuery ? searchResults : topStocks;

  const renderStockItem = ({ item }: { item: any }) => (
    <View style={styles.stockItem}>
      <TouchableOpacity 
        style={styles.stockItemContent} 
        onPress={() => openSymbol(item.symbol)}
      >
        <View style={styles.stockInfo}>
          <Text style={styles.symbol}>{item.symbol}</Text>
          <Text style={styles.company} numberOfLines={1}>{item.companyName}</Text>
        </View>
        <View style={styles.stockMetrics}>
          <Text style={styles.price}>{safeMoney(item.currentPrice)}</Text>
          <Text style={[
            styles.change, 
            { color: (item.changePercent || 0) >= 0 ? '#10B981' : '#EF4444' }
          ]}>
            {safePct(item.changePercent)}
          </Text>
        </View>
      </TouchableOpacity>
      <TouchableOpacity
        style={styles.tradeButton}
        onPress={() => openTradingModal(item)}
      >
        <Icon name="trending-up" size={16} color="white" />
        <Text style={styles.tradeButtonText}>Trade</Text>
      </TouchableOpacity>
    </View>
  );

  const renderRecentChip = (symbol: string) => (
    <TouchableOpacity
      key={symbol}
      style={styles.recentChip}
      onPress={() => openSymbol(symbol)}
    >
      <Text style={styles.recentChipText}>{symbol}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Research Explorer</Text>
        <Text style={styles.subtitle}>Discover and analyze any stock</Text>
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <Icon name="search" size={20} color="#6B7280" style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search any stock (e.g., AMZN, GOOGL, META)..."
          value={searchQuery}
          onChangeText={setSearchQuery}
          autoCapitalize="characters"
          placeholderTextColor="#9CA3AF"
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => setSearchQuery('')} style={styles.clearButton}>
            <Icon name="x" size={20} color="#6B7280" />
          </TouchableOpacity>
        )}
      </View>

      {/* Recent Symbols */}
      {!searchQuery && recents.length > 0 && (
        <View style={styles.recentsContainer}>
          <Text style={styles.recentsTitle}>Recent</Text>
          <View style={styles.recentsList}>
            {recents.map(renderRecentChip)}
          </View>
        </View>
      )}

      {/* Stocks List */}
      <View style={styles.listContainer}>
        <Text style={styles.sectionTitle}>
          {searchQuery ? `Search Results (${searchResults.length})` : 'Top Movers'}
        </Text>
        
        {searching || topStocksLoading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="small" color="#3B82F6" />
            <Text style={styles.loadingText}>Loading stocks...</Text>
          </View>
        ) : (
          <FlatList
            data={displayStocks}
            keyExtractor={(item) => item.symbol}
            renderItem={renderStockItem}
            style={styles.list}
            showsVerticalScrollIndicator={false}
            ListEmptyComponent={
              <View style={styles.emptyContainer}>
                <Icon name="search" size={48} color="#D1D5DB" />
                <Text style={styles.emptyTitle}>No stocks found</Text>
                <Text style={styles.emptySubtitle}>
                  {searchQuery ? 'Try a different search term' : 'Unable to load top stocks'}
                </Text>
              </View>
            }
          />
        )}
      </View>

      {/* Divider */}
      <View style={styles.divider} />

      {/* Selected Stock Research Detail */}
      <View style={styles.detailContainer}>
        <View style={styles.detailHeader}>
          <Text style={styles.detailTitle}>Research: {selectedSymbol}</Text>
          <TouchableOpacity onPress={() => refetch()} style={styles.refreshButton}>
            <Icon name="refresh-cw" size={16} color="#3B82F6" />
          </TouchableOpacity>
        </View>

        {effectiveResearchLoading ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="small" color="#3B82F6" />
            <Text style={styles.loadingText}>Loading research data...</Text>
          </View>
        ) : !effectiveResearchData?.researchHub ? (
          <View style={styles.errorContainer}>
            <Icon name="search" size={24} color="#6B7280" />
            <Text style={styles.errorText}>Symbol not found</Text>
            <Text style={styles.errorSubtext}>Try another ticker or check the spelling.</Text>
          </View>
        ) : (
          <ResearchBody data={effectiveResearchData.researchHub} />
        )}
      </View>

      {/* Trading Modal */}
      {selectedStock && (
        <StockTradingModal
          visible={tradingModalVisible}
          onClose={() => setTradingModalVisible(false)}
          symbol={selectedStock.symbol}
          currentPrice={selectedStock.currentPrice || 0}
          companyName={selectedStock.companyName || selectedStock.symbol}
        />
      )}
    </View>
  );
}

function ResearchBody({ data }: { data: any }) {
  const quote = data.quote;
  const technical = data.technical;
  const sentiment = data.sentiment;
  const macro = data.macro;
  const marketRegime = data.marketRegime;

  return (
    <ScrollView style={styles.researchBody} showsVerticalScrollIndicator={false}>
      {/* Price Overview */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Price Overview</Text>
        <View style={styles.priceContainer}>
          <Text style={styles.priceLarge}>{safeMoney(quote?.price)}</Text>
          <View style={styles.changeContainer}>
            <Text style={[
              styles.change, 
              { color: (quote?.chg || 0) >= 0 ? '#10B981' : '#EF4444' }
            ]}>
              {quote?.chg ? `${quote.chg >= 0 ? '+' : ''}${safeMoney(quote.chg)}` : '—'}
            </Text>
            <Text style={[
              styles.changePercent, 
              { color: (quote?.chg || 0) >= 0 ? '#10B981' : '#EF4444' }
            ]}>
              {safePct(quote?.chgPct)}
            </Text>
          </View>
        </View>
        <View style={styles.priceDetails}>
          <Text style={styles.priceDetail}>High: {safeMoney(quote?.high)}</Text>
          <Text style={styles.priceDetail}>Low: {safeMoney(quote?.low)}</Text>
          <Text style={styles.priceDetail}>Volume: {quote?.volume ? quote.volume.toLocaleString() : '—'}</Text>
        </View>
      </View>

      {/* Technical Analysis */}
      {technical && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Technical Analysis</Text>
          <View style={styles.metricsGrid}>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>RSI (14)</Text>
              <Text style={styles.metricValue}>{safeNum(technical.rsi)}</Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>MACD</Text>
              <Text style={styles.metricValue}>{safeNum(technical.macd)}</Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>MA 50</Text>
              <Text style={styles.metricValue}>{safeMoney(technical.movingAverage50)}</Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>MA 200</Text>
              <Text style={styles.metricValue}>{safeMoney(technical.movingAverage200)}</Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Support</Text>
              <Text style={styles.metricValue}>{safeMoney(technical.supportLevel)}</Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Resistance</Text>
              <Text style={styles.metricValue}>{safeMoney(technical.resistanceLevel)}</Text>
            </View>
          </View>
        </View>
      )}

      {/* Sentiment Analysis */}
      {sentiment && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Sentiment Analysis</Text>
          <View style={styles.sentimentContainer}>
            <View style={[
              styles.sentimentBadge, 
              { backgroundColor: sentiment.label === 'BULLISH' ? '#DCFCE7' : 
                                sentiment.label === 'BEARISH' ? '#FEE2E2' : '#F3F4F6' }
            ]}>
              <Text style={[
                styles.sentimentLabel,
                { color: sentiment.label === 'BULLISH' ? '#166534' : 
                         sentiment.label === 'BEARISH' ? '#991B1B' : '#374151' }
              ]}>
                {sentiment.label || 'NEUTRAL'}
              </Text>
            </View>
            <View style={styles.sentimentMetrics}>
              <Text style={styles.sentimentMetric}>Score: {safeNum(sentiment.score)}</Text>
              <Text style={styles.sentimentMetric}>Articles: {sentiment.articleCount || '—'}</Text>
              <Text style={styles.sentimentMetric}>Confidence: {safePct(sentiment.confidence)}</Text>
            </View>
          </View>
        </View>
      )}

      {/* Market Context */}
      {macro && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Market Context</Text>
          <View style={styles.metricsGrid}>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>VIX</Text>
              <Text style={styles.metricValue}>{safeNum(macro.vix)}</Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Market Sentiment</Text>
              <Text style={styles.metricValue}>{macro.marketSentiment || '—'}</Text>
            </View>
            <View style={styles.metricItem}>
              <Text style={styles.metricLabel}>Risk Appetite</Text>
              <Text style={styles.metricValue}>{safePct(macro.riskAppetite)}</Text>
            </View>
          </View>
        </View>
      )}

      {/* Today's Conditions */}
      {marketRegime && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Today's Conditions</Text>
          <View style={styles.regimeContainer}>
            <Text style={styles.regimeText}>{getRegimeLabel(marketRegime.market_regime || '—')}</Text>
            <Text style={styles.regimeText}>Confidence: {safePct(marketRegime.confidence)}</Text>
            <Text style={styles.regimeText}>Strategy: {marketRegime.recommended_strategy || '—'}</Text>
          </View>
        </View>
      )}

      {/* Peers */}
      {data.peers && data.peers.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Peer Companies</Text>
          <View style={styles.peersContainer}>
            {data.peers.map((peer: string, index: number) => (
              <TouchableOpacity key={index} style={styles.peerChip}>
                <Text style={styles.peerText}>{peer}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
  },
  subtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    margin: 16,
    paddingHorizontal: 12,
    paddingVertical: 8,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  searchIcon: {
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: '#111827',
  },
  clearButton: {
    padding: 4,
  },
  recentsContainer: {
    marginHorizontal: 16,
    marginBottom: 16,
  },
  recentsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  recentsList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  recentChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#E5E7EB',
    borderRadius: 16,
  },
  recentChipText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },
  listContainer: {
    flex: 1,
    marginHorizontal: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 12,
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  loadingText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#6B7280',
  },
  list: {
    flex: 1,
  },
  stockItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  stockItemContent: {
    flex: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  stockInfo: {
    flex: 1,
  },
  symbol: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  company: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 2,
  },
  stockMetrics: {
    alignItems: 'flex-end',
  },
  price: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  change: {
    fontSize: 14,
    fontWeight: '500',
    marginTop: 2,
  },
  emptyContainer: {
    alignItems: 'center',
    padding: 40,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
    marginTop: 12,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#9CA3AF',
    marginTop: 4,
    textAlign: 'center',
  },
  divider: {
    height: 1,
    backgroundColor: '#E5E7EB',
    marginHorizontal: 16,
  },
  detailContainer: {
    flex: 1,
    padding: 16,
  },
  detailHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  detailTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
  },
  refreshButton: {
    padding: 8,
  },
  errorContainer: {
    alignItems: 'center',
    padding: 20,
  },
  errorText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#EF4444',
    marginTop: 8,
  },
  errorSubtext: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
    textAlign: 'center',
  },
  researchBody: {
    flex: 1,
  },
  section: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  priceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  priceLarge: {
    fontSize: 28,
    fontWeight: '700',
    color: '#111827',
    marginRight: 16,
  },
  changeContainer: {
    alignItems: 'flex-end',
  },
  changePercent: {
    fontSize: 16,
    fontWeight: '600',
    marginTop: 2,
  },
  priceDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  priceDetail: {
    fontSize: 14,
    color: '#6B7280',
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  metricItem: {
    width: '48%',
    padding: 12,
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  metricLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  sentimentContainer: {
    alignItems: 'center',
  },
  sentimentBadge: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginBottom: 12,
  },
  sentimentLabel: {
    fontSize: 16,
    fontWeight: '600',
  },
  sentimentMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    width: '100%',
  },
  sentimentMetric: {
    fontSize: 14,
    color: '#6B7280',
  },
  regimeContainer: {
    gap: 8,
  },
  regimeText: {
    fontSize: 14,
    color: '#374151',
  },
  peersContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  peerChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#E5E7EB',
    borderRadius: 16,
  },
  peerText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
  },
  tradeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#3B82F6',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    marginLeft: 12,
  },
  tradeButtonText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
    marginLeft: 4,
  },
});