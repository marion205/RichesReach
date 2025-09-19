import React, { useCallback, useMemo, useState } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity, FlatList, TextInput, Alert, Modal, ScrollView,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useApolloClient, gql, useQuery } from '@apollo/client';

import StockCard from '../src/components/StockCard';
import WatchlistCard, { WatchlistItem } from '../src/components/WatchlistCard';
import { useStockSearch } from '../src/hooks/useStockSearch';
import { useWatchlist } from '../src/hooks/useWatchlist';

type Stock = {
  id: string; symbol: string; companyName: string; sector: string;
  marketCap?: number | string | null; peRatio?: number | null;
  dividendYield?: number | null; beginnerFriendlyScore: number;
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

export default function StockScreen({ navigateTo }: { navigateTo: (s: string, d?: any) => void }) {
const [activeTab, setActiveTab] = useState<'browse' | 'beginner' | 'watchlist'>('browse');
const [searchQuery, setSearchQuery] = useState('');
  const [tooltip, setTooltip] = useState<{ title: string; description: string } | null>(null);
  const [watchlistModal, setWatchlistModal] = useState<{ open: boolean; stock: Stock | null }>({ open: false, stock: null });
  const [notes, setNotes] = useState('');
  const [rust, setRust] = useState<any | null>(null);
  const [rustOpen, setRustOpen] = useState(false);
  const client = useApolloClient();
  const { stocks, screening } = useStockSearch(searchQuery, false); // Always run the query
  const { data: beginnerData, loading: beginnerLoading, refetch: refetchBeginner, error: beginnerError } =
    useQuery(GET_BEGINNER_FRIENDLY_STOCKS_ALT, { 
      fetchPolicy: 'network-only', 
      errorPolicy: 'all',
      notifyOnNetworkStatusChange: true,
      skip: activeTab !== 'beginner' // Only run when beginner tab is active
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
  
  const handleTabChange = useCallback((tab: 'browse' | 'beginner' | 'watchlist') => {
    console.log('Switching to tab:', tab);
    setActiveTab(tab);
    
    // Clear Apollo cache for the current tab to ensure fresh data
    client.cache.evict({ fieldName: tab === 'browse' ? 'stocks' : tab === 'beginner' ? 'beginnerFriendlyStocks' : 'myWatchlist' });
    client.cache.gc();
    
    // Refetch data when switching tabs to ensure fresh data
    if (tab === 'browse') {
      stocks.refetch();
    } else if (tab === 'beginner') {
      refetchBeginner?.();
    } else if (tab === 'watchlist') {
      watchlistQ.refetch();
    }
  }, [stocks, refetchBeginner, watchlistQ, client]);

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
    await addToWatchlist(watchlistModal.stock.symbol, notes);
    setWatchlistModal({ open: false, stock: null });
    setNotes('');
  }, [watchlistModal, notes, addToWatchlist]);

  const onRemoveWatchlist = useCallback((symbol: string) => {
    Alert.alert('Remove from Watchlist', 'Are you sure?', [
{ text: 'Cancel', style: 'cancel' },
      { text: 'Remove', style: 'destructive', onPress: () => removeFromWatchlist(symbol) },
    ]);
  }, [removeFromWatchlist]);

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
      onPressAdd={() => onPressAdd(item)}
      onPressAnalysis={() => handleRustAnalysis(item.symbol)}
      onPressMetric={showMetricTooltip}
    />
  ), [onPressAdd, handleRustAnalysis, showMetricTooltip]);

  const renderWatch = useCallback(({ item }: { item: WatchlistItem }) => (
    <WatchlistCard item={item} onRemove={onRemoveWatchlist} />
  ), [onRemoveWatchlist]);

  const keyStock = useCallback((i: Stock) => i.id, []);
  const keyWatch = useCallback((i: WatchlistItem) => i.id, []);

  const listData = useMemo(() => {
    console.log('=== listData useMemo called ===');
    console.log('activeTab:', activeTab);
    console.log('stocks.data:', stocks.data);
    console.log('beginnerData:', beginnerData);
    
    if (activeTab === 'browse') {
      const data = stocks.data?.stocks ?? [];
      console.log('Browse All data:', data);
      console.log('Browse All first item:', data[0]);
      console.log('Browse All data length:', data.length);
      return data;
    }
    if (activeTab === 'beginner') {
      const data = beginnerData?.beginnerFriendlyStocks ?? [];
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
        {(['browse','beginner','watchlist'] as const).map(tab => (
          <TouchableOpacity key={tab}
            style={[styles.tab, activeTab === tab && styles.activeTab]}
            onPress={() => handleTabChange(tab)}
          >
            <Text style={[styles.tabText, activeTab === tab && styles.activeTabText]}>
              {tab === 'browse' ? 'Browse All' : tab === 'beginner' ? 'Beginner Friendly' : 'My Watchlist'}
</Text>
</TouchableOpacity>
        ))}
      </View>

      {/* List */}
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
  backButton: { padding: 8 },
  headerTitle: { fontSize: 20, fontWeight: 'bold', color: '#333' },
searchContainer: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#fff',
    marginHorizontal: 20, marginTop: 20, marginBottom: 10, borderRadius: 12,
    paddingHorizontal: 16, paddingVertical: 12, borderWidth: 1, borderColor: '#e9ecef',
  },
  searchInput: { flex: 1, fontSize: 16, color: '#333' },
  tabContainer: { flexDirection: 'row', backgroundColor: '#fff', marginHorizontal: 20, marginBottom: 20, borderRadius: 12, padding: 4 },
  tab: { flex: 1, paddingVertical: 12, alignItems: 'center', borderRadius: 8 },
  activeTab: { backgroundColor: '#00cc99' },
  tabText: { fontSize: 14, fontWeight: '600', color: '#666' },
  activeTabText: { color: '#fff' },
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
  sector: { fontSize: 14, color: '#666' },
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
});