import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  TextInput,
  Image,
  Alert,
  ScrollView,
} from 'react-native';
import { useQuery, useMutation, gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

// GraphQL Queries
const GET_STOCKS = gql`
  query GetStocks($search: String) {
    stocks(search: $search) {
      id
      symbol
      companyName
      sector
      marketCap
      peRatio
      dividendYield
      beginnerFriendlyScore
    }
  }
`;

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
    }
  }
`;

const GET_MY_WATCHLIST = gql`
  query GetMyWatchlist {
    myWatchlist {
      id
      stock {
        id
        symbol
        companyName
        sector
        beginnerFriendlyScore
      }
      addedAt
      notes
    }
  }
`;

// GraphQL Mutations
const ADD_TO_WATCHLIST = gql`
  mutation AddToWatchlist($stockSymbol: String!, $notes: String) {
    addToWatchlist(stockSymbol: $stockSymbol, notes: $notes) {
      success
      message
    }
  }
`;

const REMOVE_FROM_WATCHLIST = gql`
  mutation RemoveFromWatchlist($stockSymbol: String!) {
    removeFromWatchlist(stockSymbol: $stockSymbol) {
      success
      message
    }
  }
`;

interface Stock {
  id: string;
  symbol: string;
  companyName: string;
  sector: string;
  marketCap?: number;
  peRatio?: number;
  dividendYield?: number;
  beginnerFriendlyScore: number;
}

interface WatchlistItem {
  id: string;
  stock: Stock;
  addedAt: string;
  notes?: string;
}

export default function StockScreen({ navigateTo }) {
  const [activeTab, setActiveTab] = useState<'browse' | 'beginner' | 'watchlist'>('browse');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
  const [showAddToWatchlist, setShowAddToWatchlist] = useState(false);
  const [watchlistNotes, setWatchlistNotes] = useState('');

  // Queries
  const { data: stocksData, loading: stocksLoading, refetch: refetchStocks } = useQuery(GET_STOCKS, {
    variables: { search: searchQuery || undefined },
    fetchPolicy: 'cache-and-network',
  });

  const { data: beginnerStocksData, loading: beginnerLoading } = useQuery(GET_BEGINNER_FRIENDLY_STOCKS, {
    fetchPolicy: 'cache-and-network',
  });

  const { data: watchlistData, loading: watchlistLoading, refetch: refetchWatchlist } = useQuery(GET_MY_WATCHLIST, {
    fetchPolicy: 'cache-and-network',
  });

  // Mutations
  const [addToWatchlist] = useMutation(ADD_TO_WATCHLIST, {
    onCompleted: (data) => {
      if (data.addToWatchlist.success) {
        Alert.alert('Success', data.addToWatchlist.message);
        setShowAddToWatchlist(false);
        setSelectedStock(null);
        setWatchlistNotes('');
        refetchWatchlist();
      }
    },
    onError: (error) => {
      Alert.alert('Error', 'Failed to add stock to watchlist. Please try again.');
    },
  });

  const [removeFromWatchlist] = useMutation(REMOVE_FROM_WATCHLIST, {
    onCompleted: (data) => {
      if (data.removeFromWatchlist.success) {
        Alert.alert('Success', data.removeFromWatchlist.message);
        refetchWatchlist();
      }
    },
    onError: (error) => {
      Alert.alert('Error', 'Failed to remove stock from watchlist. Please try again.');
    },
  });

  const handleAddToWatchlist = () => {
    if (selectedStock) {
      addToWatchlist({
        variables: {
          stockSymbol: selectedStock.symbol,
          notes: watchlistNotes,
        },
      });
    }
  };

  const handleRemoveFromWatchlist = (symbol: string) => {
    Alert.alert(
      'Remove from Watchlist',
      'Are you sure you want to remove this stock from your watchlist?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: () => removeFromWatchlist({ variables: { stockSymbol: symbol } }),
        },
      ]
    );
  };

  const formatMarketCap = (marketCap: number) => {
    if (marketCap >= 1e12) return `$${(marketCap / 1e12).toFixed(1)}T`;
    if (marketCap >= 1e9) return `$${(marketCap / 1e9).toFixed(1)}B`;
    if (marketCap >= 1e6) return `$${(marketCap / 1e6).toFixed(1)}M`;
    return `$${marketCap.toLocaleString()}`;
  };

  const renderStockCard = ({ item }: { item: Stock }) => (
    <TouchableOpacity
      style={styles.stockCard}
      onPress={() => {
        setSelectedStock(item);
        setShowAddToWatchlist(true);
      }}
    >
      <View style={styles.stockHeader}>
        <View style={styles.stockSymbol}>
          <Text style={styles.symbolText}>{item.symbol}</Text>
          <View style={[styles.scoreBadge, { backgroundColor: getScoreColor(item.beginnerFriendlyScore) }]}>
            <Text style={styles.scoreText}>{item.beginnerFriendlyScore}</Text>
          </View>
        </View>
        <Text style={styles.companyName}>{item.companyName}</Text>
        <Text style={styles.sectorText}>{item.sector}</Text>
      </View>
      
      <View style={styles.stockMetrics}>
        {item.marketCap && (
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>Market Cap</Text>
            <Text style={styles.metricValue}>{formatMarketCap(item.marketCap)}</Text>
          </View>
        )}
        {item.peRatio && (
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>P/E Ratio</Text>
            <Text style={styles.metricValue}>{item.peRatio.toFixed(1)}</Text>
          </View>
        )}
        {item.dividendYield && (
          <View style={styles.metric}>
            <Text style={styles.metricLabel}>Dividend</Text>
            <Text style={styles.metricValue}>{item.dividendYield.toFixed(1)}%</Text>
          </View>
        )}
      </View>
    </TouchableOpacity>
  );

  const renderWatchlistItem = ({ item }: { item: WatchlistItem }) => (
    <View style={styles.watchlistCard}>
      <View style={styles.watchlistHeader}>
        <View style={styles.stockSymbol}>
          <Text style={styles.symbolText}>{item.stock.symbol}</Text>
          <View style={[styles.scoreBadge, { backgroundColor: getScoreColor(item.stock.beginnerFriendlyScore) }]}>
            <Text style={styles.scoreText}>{item.stock.beginnerFriendlyScore}</Text>
          </View>
        </View>
        <TouchableOpacity
          style={styles.removeButton}
          onPress={() => handleRemoveFromWatchlist(item.stock.symbol)}
        >
          <Icon name="x" size={20} color="#ff4444" />
        </TouchableOpacity>
      </View>
      
      <Text style={styles.companyName}>{item.stock.companyName}</Text>
      <Text style={styles.sectorText}>{item.stock.sector}</Text>
      
      {item.notes && (
        <View style={styles.notesContainer}>
          <Text style={styles.notesLabel}>Notes:</Text>
          <Text style={styles.notesText}>{item.notes}</Text>
        </View>
      )}
      
      <Text style={styles.addedDate}>
        Added: {new Date(item.addedAt).toLocaleDateString()}
      </Text>
    </View>
  );

  const getScoreColor = (score: number) => {
    if (score >= 90) return '#4CAF50'; // Green
    if (score >= 80) return '#8BC34A'; // Light Green
    if (score >= 70) return '#FFC107'; // Yellow
    return '#FF5722'; // Red
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'browse':
        return (
          <FlatList
            data={stocksData?.stocks || []}
            renderItem={renderStockCard}
            keyExtractor={(item) => item.id}
            refreshing={stocksLoading}
            onRefresh={refetchStocks}
            contentContainerStyle={styles.listContainer}
          />
        );
      
      case 'beginner':
        return (
          <FlatList
            data={beginnerStocksData?.beginnerFriendlyStocks || []}
            renderItem={renderStockCard}
            keyExtractor={(item) => item.id}
            refreshing={beginnerLoading}
            onRefresh={() => {}} // No refetch needed for this query
            contentContainerStyle={styles.listContainer}
          />
        );
      
      case 'watchlist':
        return (
          <FlatList
            data={watchlistData?.myWatchlist || []}
            renderItem={renderWatchlistItem}
            keyExtractor={(item) => item.id}
            refreshing={watchlistLoading}
            onRefresh={refetchWatchlist}
            contentContainerStyle={styles.listContainer}
            ListEmptyComponent={
              <View style={styles.emptyState}>
                <Icon name="eye" size={48} color="#ccc" />
                <Text style={styles.emptyStateText}>Your watchlist is empty</Text>
                <Text style={styles.emptyStateSubtext}>
                  Browse stocks and add them to your watchlist to track them
                </Text>
              </View>
            }
          />
        );
      
      default:
        return null;
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigateTo('Home')}
        >
          <Icon name="arrow-left" size={24} color="#00cc99" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Stocks & Investing</Text>
        <View style={styles.headerRight} />
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <Icon name="search" size={20} color="#666" style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search stocks by symbol or company name..."
          value={searchQuery}
          onChangeText={setSearchQuery}
          placeholderTextColor="#999"
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity
            style={styles.clearButton}
            onPress={() => setSearchQuery('')}
          >
            <Icon name="x" size={20} color="#666" />
          </TouchableOpacity>
        )}
      </View>

      {/* Tab Navigation */}
      <View style={styles.tabContainer}>
        <TouchableOpacity
          style={[styles.tab, activeTab === 'browse' && styles.activeTab]}
          onPress={() => setActiveTab('browse')}
        >
          <Text style={[styles.tabText, activeTab === 'browse' && styles.activeTabText]}>
            Browse All
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.tab, activeTab === 'beginner' && styles.activeTab]}
          onPress={() => setActiveTab('beginner')}
        >
          <Text style={[styles.tabText, activeTab === 'beginner' && styles.activeTabText]}>
            Beginner Friendly
          </Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={[styles.tab, activeTab === 'watchlist' && styles.activeTab]}
          onPress={() => setActiveTab('watchlist')}
        >
          <Text style={[styles.tabText, activeTab === 'watchlist' && styles.activeTabText]}>
            My Watchlist
          </Text>
        </TouchableOpacity>
      </View>

      {/* Content */}
      {renderContent()}

      {/* Add to Watchlist Modal */}
      {showAddToWatchlist && selectedStock && (
        <View style={styles.modalOverlay}>
          <View style={styles.modal}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Add to Watchlist</Text>
              <TouchableOpacity
                style={styles.closeButton}
                onPress={() => {
                  setShowAddToWatchlist(false);
                  setSelectedStock(null);
                  setWatchlistNotes('');
                }}
              >
                <Icon name="x" size={24} color="#666" />
              </TouchableOpacity>
            </View>
            
            <View style={styles.stockInfo}>
              <Text style={styles.modalSymbol}>{selectedStock.symbol}</Text>
              <Text style={styles.modalCompanyName}>{selectedStock.companyName}</Text>
              <Text style={styles.modalSector}>{selectedStock.sector}</Text>
            </View>
            
            <TextInput
              style={styles.notesInput}
              placeholder="Add personal notes (optional)..."
              value={watchlistNotes}
              onChangeText={setWatchlistNotes}
              multiline
              numberOfLines={3}
              placeholderTextColor="#999"
            />
            
            <View style={styles.modalActions}>
              <TouchableOpacity
                style={styles.cancelButton}
                onPress={() => {
                  setShowAddToWatchlist(false);
                  setSelectedStock(null);
                  setWatchlistNotes('');
                }}
              >
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              
              <TouchableOpacity
                style={styles.addButton}
                onPress={handleAddToWatchlist}
              >
                <Text style={styles.addButtonText}>Add to Watchlist</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 60,
    paddingBottom: 20,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e9ecef',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  headerRight: {
    width: 40,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    marginHorizontal: 20,
    marginTop: 20,
    marginBottom: 10,
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: '#e9ecef',
  },
  searchIcon: {
    marginRight: 12,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: '#333',
  },
  clearButton: {
    padding: 4,
  },
  tabContainer: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    marginHorizontal: 20,
    marginBottom: 20,
    borderRadius: 12,
    padding: 4,
  },
  tab: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    borderRadius: 8,
  },
  activeTab: {
    backgroundColor: '#00cc99',
  },
  tabText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#666',
  },
  activeTabText: {
    color: '#fff',
  },
  listContainer: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  stockCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  stockHeader: {
    marginBottom: 16,
  },
  stockSymbol: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  symbolText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginRight: 12,
  },
  scoreBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    minWidth: 32,
    alignItems: 'center',
  },
  scoreText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#fff',
  },
  companyName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  sectorText: {
    fontSize: 14,
    color: '#666',
  },
  stockMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  metric: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#999',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#333',
  },
  watchlistCard: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  watchlistHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  removeButton: {
    padding: 8,
  },
  notesContainer: {
    marginTop: 12,
    padding: 12,
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
  },
  notesLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
    marginBottom: 4,
  },
  notesText: {
    fontSize: 14,
    color: '#333',
  },
  addedDate: {
    fontSize: 12,
    color: '#999',
    marginTop: 12,
    textAlign: 'right',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyStateText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#666',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
    paddingHorizontal: 40,
  },
  modalOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  modal: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 24,
    marginHorizontal: 20,
    width: '90%',
    maxWidth: 400,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  closeButton: {
    padding: 4,
  },
  stockInfo: {
    marginBottom: 20,
  },
  modalSymbol: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 4,
  },
  modalCompanyName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  modalSector: {
    fontSize: 14,
    color: '#666',
  },
  notesInput: {
    borderWidth: 1,
    borderColor: '#e9ecef',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: '#333',
    textAlignVertical: 'top',
    marginBottom: 24,
  },
  modalActions: {
    flexDirection: 'row',
    gap: 12,
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e9ecef',
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#666',
  },
  addButton: {
    flex: 1,
    backgroundColor: '#00cc99',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  addButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
});
