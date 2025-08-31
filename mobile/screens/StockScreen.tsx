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
import { useQuery, useMutation, gql, useApolloClient } from '@apollo/client';
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

// Rust Engine Queries
const GET_RUST_STOCK_ANALYSIS = gql`
  query GetRustStockAnalysis($symbol: String!) {
    rustStockAnalysis(symbol: $symbol) {
      symbol
      beginnerFriendlyScore
      riskLevel
      recommendation
      technicalIndicators {
        rsi
        macd
        macdSignal
        macdHistogram
        sma20
        sma50
        ema12
        ema26
        bollingerUpper
        bollingerLower
        bollingerMiddle
      }
      fundamentalAnalysis {
        valuationScore
        growthScore
        stabilityScore
        dividendScore
        debtScore
      }
      reasoning
    }
  }
`;

const GET_RUST_RECOMMENDATIONS = gql`
  query GetRustRecommendations {
    rustRecommendations {
      symbol
      reason
      riskLevel
      beginnerScore
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
  marketCap?: number | string | null;
  peRatio?: number | null;
  dividendYield?: number | null;
  beginnerFriendlyScore: number;
}

interface WatchlistItem {
  id: string;
  stock: Stock;
  addedAt: string;
  notes?: string;
}

// Rust Analysis Interfaces
interface TechnicalIndicators {
  rsi?: number | null;
  macd?: number | null;
  macdSignal?: number | null;
  macdHistogram?: number | null;
  sma20?: number | null;
  sma50?: number | null;
  ema12?: number | null;
  ema26?: number | null;
  bollingerUpper?: number | null;
  bollingerLower?: number | null;
  bollingerMiddle?: number | null;
}

interface FundamentalAnalysis {
  valuationScore: number;
  growthScore: number;
  stabilityScore: number;
  dividendScore: number;
  debtScore: number;
}

interface RustStockAnalysis {
  symbol: string;
  beginnerFriendlyScore: number;
  riskLevel: string;
  recommendation: string;
  technicalIndicators: TechnicalIndicators;
  fundamentalAnalysis: FundamentalAnalysis;
  reasoning: string[];
}

interface RustRecommendation {
  symbol: string;
  reason: string;
  riskLevel: string;
  beginnerScore: number;
}

export default function StockScreen({ navigateTo }) {
  const [activeTab, setActiveTab] = useState<'browse' | 'beginner' | 'watchlist'>('browse');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
  const [showAddToWatchlist, setShowAddToWatchlist] = useState(false);
  const [watchlistNotes, setWatchlistNotes] = useState('');
  const [showTooltip, setShowTooltip] = useState(false);
  const [tooltipContent, setTooltipContent] = useState({ title: '', description: '' });
  
  // Rust Analysis State
  const [rustAnalysis, setRustAnalysis] = useState<RustStockAnalysis | null>(null);
  const [showRustAnalysis, setShowRustAnalysis] = useState(false);

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


  
  // Apollo Client
  const client = useApolloClient();

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

  const handleRustAnalysis = async (symbol: string) => {
    try {
      // Use Apollo client to fetch Rust analysis
      const { data } = await client.query({
        query: GET_RUST_STOCK_ANALYSIS,
        variables: { symbol },
        fetchPolicy: 'network-only',
      });
      
      if (data?.rustStockAnalysis) {
        setRustAnalysis(data.rustStockAnalysis);
        setShowRustAnalysis(true);
      } else {
        Alert.alert('Analysis Unavailable', 'Rust analysis is not available for this stock at the moment.');
      }
    } catch (error) {
      console.error('Rust analysis error:', error);
      Alert.alert('Analysis Error', 'Failed to get advanced analysis. Please try again.');
    }
  };

  const formatMarketCap = (marketCap: number | string | null | undefined) => {
    if (!marketCap) return 'N/A';
    
    // Convert string to number if needed
    const numValue = typeof marketCap === 'string' ? parseInt(marketCap, 10) : marketCap;
    
    if (numValue >= 1e12) return `$${(numValue / 1e12).toFixed(1)}T`;
    if (numValue >= 1e9) return `$${(numValue / 1e9).toFixed(1)}B`;
    if (numValue >= 1e6) return `$${(numValue / 1e6).toFixed(1)}M`;
    return `$${numValue.toLocaleString()}`;
  };

  const showMetricTooltip = (metric: 'marketCap' | 'peRatio' | 'dividendYield') => {
    const tooltips = {
      marketCap: {
        title: 'Market Cap',
        description: 'The total value of a company\'s shares. Large companies (over $10B) are generally more stable and suitable for beginners.'
      },
      peRatio: {
        title: 'P/E Ratio',
        description: 'Price-to-Earnings ratio shows how expensive a stock is relative to its earnings. Lower ratios (under 25) are often better for beginners.'
      },
      dividendYield: {
        title: 'Dividend Yield',
        description: 'Annual dividend payments as a percentage of stock price. Higher yields (2-5%) provide regular income and indicate stable companies.'
      }
    };
    
    setTooltipContent(tooltips[metric]);
    setShowTooltip(true);
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
          <View style={styles.recommendationContainer}>
            <View style={[styles.scoreBadge, { backgroundColor: getScoreColor(item.beginnerFriendlyScore) }]}>
              <Text style={styles.scoreText}>{item.beginnerFriendlyScore}</Text>
            </View>
            <View style={[styles.recommendationBadge, { 
              backgroundColor: getBuyRecommendation(item).backgroundColor,
              borderColor: getBuyRecommendation(item).color 
            }]}>
              <Text style={[styles.recommendationText, { color: getBuyRecommendation(item).color }]}>
                {getBuyRecommendation(item).text}
              </Text>
            </View>
          </View>
        </View>
        <Text style={styles.companyName}>{item.companyName}</Text>
        <Text style={styles.sectorText}>{item.sector}</Text>
      </View>
      
      <View style={styles.stockMetrics}>
        {item.marketCap != null && (
          <TouchableOpacity 
            style={styles.metric} 
            onPress={() => showMetricTooltip('marketCap')}
            activeOpacity={0.7}
          >
            <Text style={styles.metricLabel}>Market Cap</Text>
            <Text style={styles.metricValue}>{formatMarketCap(item.marketCap)}</Text>
            <Icon name="info" size={16} color="#00cc99" style={styles.infoIcon} />
          </TouchableOpacity>
        )}
        {item.peRatio != null && (
          <TouchableOpacity 
            style={styles.metric} 
            onPress={() => showMetricTooltip('peRatio')}
            activeOpacity={0.7}
          >
            <Text style={styles.metricLabel}>P/E Ratio</Text>
            <Text style={styles.metricValue}>{Number(item.peRatio).toFixed(1)}</Text>
            <Icon name="info" size={16} color="#00cc99" style={styles.infoIcon} />
          </TouchableOpacity>
        )}
        {item.dividendYield != null && (
          <TouchableOpacity 
            style={styles.metric} 
            onPress={() => showMetricTooltip('dividendYield')}
            activeOpacity={0.7}
          >
            <Text style={styles.metricLabel}>Dividend</Text>
            <Text style={styles.metricValue}>{Number(item.dividendYield).toFixed(1)}%</Text>
            <Icon name="info" size={16} color="#00cc99" style={styles.infoIcon} />
          </TouchableOpacity>
        )}
      </View>
      
      {/* Advanced Analysis Button */}
      <TouchableOpacity
        style={styles.rustAnalysisButton}
        onPress={() => handleRustAnalysis(item.symbol)}
        activeOpacity={0.7}
      >
        <Icon name="bar-chart-2" size={16} color="#ffffff" style={styles.rustIcon} />
        <Text style={styles.rustAnalysisText}>Advanced Analysis</Text>
      </TouchableOpacity>
    </TouchableOpacity>
  );

  const renderWatchlistItem = ({ item }: { item: WatchlistItem }) => (
    <View style={styles.watchlistCard}>
      <View style={styles.watchlistHeader}>
        <View style={styles.stockSymbol}>
          <Text style={styles.symbolText}>{item.stock.symbol}</Text>
          <View style={styles.recommendationContainer}>
            <View style={[styles.scoreBadge, { backgroundColor: getScoreColor(item.stock.beginnerFriendlyScore) }]}>
              <Text style={styles.scoreText}>{item.stock.beginnerFriendlyScore}</Text>
            </View>
            <View style={[styles.recommendationBadge, { 
              backgroundColor: getBuyRecommendation(item.stock).backgroundColor,
              borderColor: getBuyRecommendation(item.stock).color 
            }]}>
              <Text style={[styles.recommendationText, { color: getBuyRecommendation(item.stock).color }]}>
                {getBuyRecommendation(item.stock).text}
              </Text>
            </View>
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

  const getBuyRecommendation = (stock: Stock) => {
    const score = stock.beginnerFriendlyScore;
    
    // Strong buy: 90+ score
    if (score >= 90) {
      return { text: 'STRONG BUY', color: '#4CAF50', backgroundColor: '#E8F5E8' };
    }
    // Buy: 80-89 score
    if (score >= 80) {
      return { text: 'BUY', color: '#8BC34A', backgroundColor: '#F1F8E9' };
    }
    // Hold: 70-79 score
    if (score >= 70) {
      return { text: 'HOLD', color: '#FFC107', backgroundColor: '#FFF8E1' };
    }
    // Avoid: Below 70
    return { text: 'AVOID', color: '#FF5722', backgroundColor: '#FFEBEE' };
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

      {/* Educational Tooltip Modal */}
      {showTooltip && (
        <View style={styles.modalOverlay}>
          <View style={styles.tooltipModal}>
            <View style={styles.tooltipHeader}>
              <Text style={styles.tooltipTitle}>{tooltipContent.title}</Text>
              <TouchableOpacity
                style={styles.closeButton}
                onPress={() => setShowTooltip(false)}
              >
                <Icon name="x" size={24} color="#666" />
              </TouchableOpacity>
            </View>
            
            <Text style={styles.tooltipDescription}>{tooltipContent.description}</Text>
            
            <TouchableOpacity
              style={styles.tooltipCloseButton}
              onPress={() => setShowTooltip(false)}
            >
              <Text style={styles.tooltipCloseButtonText}>Got it!</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Rust Analysis Modal */}
      {showRustAnalysis && rustAnalysis && (
        <View style={styles.modalOverlay}>
          <View style={styles.rustAnalysisModal}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Advanced Analysis: {rustAnalysis.symbol}</Text>
              <TouchableOpacity
                style={styles.closeButton}
                onPress={() => setShowRustAnalysis(false)}
              >
                <Icon name="x" size={24} color="#666" />
              </TouchableOpacity>
            </View>
            
            <ScrollView style={styles.rustAnalysisContent} showsVerticalScrollIndicator={false}>
              {/* Beginner Score & Recommendation */}
              <View style={styles.rustAnalysisSection}>
                <View style={styles.rustScoreContainer}>
                  <View style={[styles.rustScoreBadge, { backgroundColor: getScoreColor(rustAnalysis.beginnerFriendlyScore) }]}>
                    <Text style={styles.rustScoreText}>{rustAnalysis.beginnerFriendlyScore}</Text>
                  </View>
                  <View style={styles.rustScoreInfo}>
                    <Text style={styles.rustScoreLabel}>Beginner Score</Text>
                    <Text style={styles.rustScoreDescription}>Out of 100</Text>
                  </View>
                </View>
                
                <View style={styles.rustRecommendationContainer}>
                  <Text style={styles.rustRecommendationLabel}>Recommendation</Text>
                  <View style={[styles.rustRecommendationBadge, { 
                    backgroundColor: rustAnalysis.recommendation === 'Buy' ? '#00cc99' : 
                                   rustAnalysis.recommendation === 'Hold' ? '#ffaa00' : '#ff4444'
                  }]}>
                    <Text style={styles.rustRecommendationText}>{rustAnalysis.recommendation}</Text>
                  </View>
                </View>
              </View>

              {/* Risk Level */}
              <View style={styles.rustAnalysisSection}>
                <Text style={styles.rustSectionTitle}>Risk Assessment</Text>
                <View style={[styles.rustRiskBadge, { 
                  backgroundColor: rustAnalysis.riskLevel === 'Low' ? '#00cc99' : 
                                 rustAnalysis.riskLevel === 'Medium' ? '#ffaa00' : '#ff4444'
                }]}>
                  <Text style={styles.rustRiskText}>{rustAnalysis.riskLevel} Risk</Text>
                </View>
              </View>

              {/* Fundamental Analysis */}
              <View style={styles.rustAnalysisSection}>
                <Text style={styles.rustSectionTitle}>Fundamental Analysis</Text>
                <View style={styles.rustFundamentalGrid}>
                  <View style={styles.rustFundamentalItem}>
                    <Text style={styles.rustFundamentalLabel}>Valuation</Text>
                    <Text style={styles.rustFundamentalValue}>{rustAnalysis.fundamentalAnalysis.valuationScore}/100</Text>
                  </View>
                  <View style={styles.rustFundamentalItem}>
                    <Text style={styles.rustFundamentalLabel}>Growth</Text>
                    <Text style={styles.rustFundamentalValue}>{rustAnalysis.fundamentalAnalysis.growthScore}/100</Text>
                  </View>
                  <View style={styles.rustFundamentalItem}>
                    <Text style={styles.rustFundamentalLabel}>Stability</Text>
                    <Text style={styles.rustFundamentalValue}>{rustAnalysis.fundamentalAnalysis.stabilityScore}/100</Text>
                  </View>
                  <View style={styles.rustFundamentalItem}>
                    <Text style={styles.rustFundamentalLabel}>Dividend</Text>
                    <Text style={styles.rustFundamentalValue}>{rustAnalysis.fundamentalAnalysis.dividendScore}/100</Text>
                  </View>
                  <View style={styles.rustFundamentalItem}>
                    <Text style={styles.rustFundamentalLabel}>Debt</Text>
                    <Text style={styles.rustFundamentalValue}>{rustAnalysis.fundamentalAnalysis.debtScore}/100</Text>
                  </View>
                </View>
              </View>

              {/* Technical Indicators */}
              <View style={styles.rustAnalysisSection}>
                <Text style={styles.rustSectionTitle}>Technical Indicators</Text>
                <View style={styles.rustTechnicalGrid}>
                  <View style={styles.rustTechnicalItem}>
                    <Text style={styles.rustTechnicalLabel}>RSI</Text>
                    <Text style={styles.rustTechnicalValue}>{rustAnalysis.technicalIndicators.rsi?.toFixed(2) || 'N/A'}</Text>
                  </View>
                  <View style={styles.rustTechnicalItem}>
                    <Text style={styles.rustTechnicalLabel}>MACD</Text>
                    <Text style={styles.rustTechnicalValue}>{rustAnalysis.technicalIndicators.macd?.toFixed(2) || 'N/A'}</Text>
                  </View>
                  <View style={styles.rustTechnicalItem}>
                    <Text style={styles.rustTechnicalLabel}>SMA 20</Text>
                    <Text style={styles.rustTechnicalValue}>{rustAnalysis.technicalIndicators.sma20?.toFixed(2) || 'N/A'}</Text>
                  </View>
                  <View style={styles.rustTechnicalItem}>
                    <Text style={styles.rustTechnicalLabel}>SMA 50</Text>
                    <Text style={styles.rustTechnicalValue}>{rustAnalysis.technicalIndicators.sma50?.toFixed(2) || 'N/A'}</Text>
                  </View>
                </View>
              </View>

              {/* Reasoning */}
              <View style={styles.rustAnalysisSection}>
                <Text style={styles.rustSectionTitle}>Analysis Reasoning</Text>
                {rustAnalysis.reasoning.map((reason, index) => (
                  <View key={index} style={styles.rustReasoningItem}>
                    <Text style={styles.rustReasoningText}>• {reason}</Text>
                  </View>
                ))}
              </View>
            </ScrollView>
            
            <TouchableOpacity
              style={styles.rustAnalysisCloseButton}
              onPress={() => setShowRustAnalysis(false)}
            >
              <Text style={styles.rustAnalysisCloseButtonText}>Close Analysis</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}

      {/* Bottom Tab Navigation */}
      <View style={styles.bottomTabBar}>
        <TouchableOpacity 
          style={styles.tabItem} 
          onPress={() => navigateTo('Home')}
        >
          <Icon name="home" size={24} color="#999" />
          <Text style={styles.tabLabel}>Home</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={[styles.tabItem, styles.activeTabItem]} 
          onPress={() => navigateTo('Stocks')}
        >
          <Icon name="trending-up" size={24} color="#00cc99" />
          <Text style={styles.tabLabel}>Stocks</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.tabItem} 
          onPress={() => navigateTo('DiscoverUsers')}
        >
          <Icon name="users" size={24} color="#999" />
          <Text style={styles.tabLabel}>Discover</Text>
        </TouchableOpacity>

        <TouchableOpacity 
          style={styles.tabItem} 
          onPress={() => navigateTo('Profile')}
        >
          <Icon name="user" size={24} color="#999" />
          <Text style={styles.tabLabel}>Profile</Text>
        </TouchableOpacity>
      </View>
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
  recommendationContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  recommendationBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
    minWidth: 60,
    alignItems: 'center',
  },
  recommendationText: {
    fontSize: 10,
    fontWeight: 'bold',
    textAlign: 'center',
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
  infoIcon: {
    marginLeft: 8,
  },
  tooltipModal: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 24,
    marginHorizontal: 20,
    width: '90%',
    maxWidth: 400,
  },
  tooltipHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  tooltipTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  tooltipDescription: {
    fontSize: 16,
    lineHeight: 24,
    color: '#666',
    marginBottom: 24,
    textAlign: 'left',
  },
  tooltipCloseButton: {
    backgroundColor: '#00cc99',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  tooltipCloseButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },
  bottomTabBar: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e9ecef',
    paddingBottom: 20,
    paddingTop: 10,
  },
  tabItem: {
    flex: 1,
    alignItems: 'center',
    paddingVertical: 8,
  },
  activeTabItem: {
    // Active tab styling is handled by icon color
  },
  tabLabel: {
    fontSize: 12,
    color: '#999',
    marginTop: 4,
    fontWeight: '500',
  },
  // Rust Analysis Button Styles
  rustAnalysisButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#6366f1',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 12,
    marginTop: 16,
    shadowColor: '#6366f1',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 3,
  },
  rustIcon: {
    marginRight: 8,
  },
  rustAnalysisText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ffffff',
  },
  // Rust Analysis Modal Styles
  rustAnalysisModal: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 24,
    marginHorizontal: 20,
    width: '90%',
    maxWidth: 400,
    maxHeight: '80%',
  },
  rustAnalysisContent: {
    maxHeight: 400,
  },
  rustAnalysisSection: {
    marginBottom: 24,
  },
  rustScoreContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  rustScoreBadge: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 16,
    marginRight: 16,
    minWidth: 48,
    alignItems: 'center',
  },
  rustScoreText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#fff',
  },
  rustScoreInfo: {
    flex: 1,
  },
  rustScoreLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  rustScoreDescription: {
    fontSize: 14,
    color: '#666',
  },
  rustRecommendationContainer: {
    alignItems: 'center',
  },
  rustRecommendationLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 8,
  },
  rustRecommendationBadge: {
    paddingHorizontal: 20,
    paddingVertical: 8,
    borderRadius: 16,
    minWidth: 80,
    alignItems: 'center',
  },
  rustRecommendationText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  rustSectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 16,
  },
  rustRiskBadge: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 16,
    alignItems: 'center',
    minWidth: 100,
  },
  rustRiskText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  rustFundamentalGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  rustFundamentalItem: {
    width: '48%',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 8,
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    marginBottom: 8,
  },
  rustFundamentalLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  rustFundamentalValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  rustTechnicalGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  rustTechnicalItem: {
    width: '48%',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 8,
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    marginBottom: 8,
  },
  rustTechnicalLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  rustTechnicalValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  rustReasoningItem: {
    marginBottom: 8,
    paddingLeft: 8,
  },
  rustReasoningText: {
    fontSize: 14,
    lineHeight: 20,
    color: '#333',
  },
  rustAnalysisCloseButton: {
    backgroundColor: '#6366f1',
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 16,
  },
  rustAnalysisCloseButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#fff',
  },

});
