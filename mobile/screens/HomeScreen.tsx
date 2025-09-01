import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  Alert,
  Dimensions,
  SafeAreaView,
  FlatList,
  TextInput,
} from 'react-native';
import { useQuery, useApolloClient, useMutation } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

const { width: screenWidth } = Dimensions.get('window');

// GraphQL Queries
const GET_ME = gql`
  query GetMe {
    me {
      id
      email
      name
      profilePic
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

const ADD_TO_WATCHLIST = gql`
  mutation AddToWatchlist($stockSymbol: String!, $notes: String) {
    addToWatchlist(stockSymbol: $stockSymbol, notes: $notes) {
      success
      message
    }
  }
`;

// Types
interface User {
  id: string;
  name: string;
  email: string;
  profilePic?: string;
}

interface Stock {
  id: string;
  symbol: string;
  companyName: string;
  sector?: string;
  marketCap?: number;
  peRatio?: number;
  dividendYield?: number;
  debtRatio?: number;
  volatility?: number;
  beginnerFriendlyScore?: number;
}

interface WatchlistItem {
  id: string;
  stock: Stock;
  addedAt: string;
  notes?: string;
}

interface Watchlist {
  id: string;
  name: string;
  description?: string;
  is_public: boolean;
  is_shared: boolean;
  items: WatchlistItem[];
}

interface ChatMsg {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

export default function HomeScreen({ navigateTo }: { navigateTo: (screen: string, data?: any) => void }) {
  const client = useApolloClient();
  
  // State
  const [refreshing, setRefreshing] = useState(false);
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);

  // Chatbot state
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMsg[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatSending, setChatSending] = useState(false);
  const listRef = useRef<FlatList<ChatMsg>>(null);

  // Queries
  const { data: meData, loading: meLoading, error: meError } = useQuery(GET_ME);
  const { data: watchlistData, loading: watchlistLoading, error: watchlistError, refetch: refetchWatchlist } = useQuery(GET_MY_WATCHLIST);

  // Mutations
  const [addToWatchlist, { loading: addingToWatchlist }] = useMutation(ADD_TO_WATCHLIST);

  // Test function to add a stock to watchlist
  const testAddToWatchlist = async () => {
    try {
      console.log('🧪 Testing Add to Watchlist...');
      console.log('📤 Mutation Variables:', { stockSymbol: 'AAPL', notes: 'Test stock from HomeScreen' });
      
      const result = await addToWatchlist({
        variables: {
          stockSymbol: 'AAPL',
          notes: 'Test stock from HomeScreen'
        }
      });
      
      console.log('✅ Add to Watchlist Result:', result);
      console.log('📊 Result Data:', result.data);
      console.log('📊 Result Success:', result.data?.addToWatchlist?.success);
      console.log('📊 Result Message:', result.data?.addToWatchlist?.message);
      
      // Refresh the watchlist after adding
      console.log('🔄 Refreshing watchlist...');
      await refetchWatchlist();
      console.log('✅ Watchlist refreshed');
    } catch (error) {
      console.error('❌ Add to Watchlist Error:', error);
    }
  };

  // Debug logging
  useEffect(() => {
    console.log('🔍 HomeScreen Debug:', {
      meData,
      meLoading,
      meError,
      watchlistData,
      watchlistLoading,
      watchlistError
    });
  }, [meData, meLoading, meError, watchlistData, watchlistLoading, watchlistError]);

  const onRefresh = async () => {
    setRefreshing(true);
    try {
      await refetchWatchlist();
    } catch (error) {
      console.error('Error refreshing watchlist:', error);
    } finally {
      setRefreshing(false);
    }
  };

  const handleStockPress = (stock: Stock) => {
    setSelectedStock(stock);
    // Navigate to detailed stock view
    navigateTo('Stock', { stock });
  };

  const handleAddStock = () => {
    // Navigate to stock search/add screen
    navigateTo('Stock');
  };

  const formatCurrency = (value?: number) => {
    if (value === undefined || value === null) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatMarketCap = (value?: number) => {
    if (value === undefined || value === null) return 'N/A';
    if (value >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (value >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (value >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    return formatCurrency(value);
  };

  const formatPercentage = (value?: number) => {
    if (value === undefined || value === null) return 'N/A';
    return `${value.toFixed(2)}%`;
  };

  const renderStockCard = (watchlistItem: WatchlistItem) => {
    const { stock } = watchlistItem;
    
    return (
      <TouchableOpacity
        key={watchlistItem.id}
        style={styles.stockCard}
        onPress={() => handleStockPress(stock)}
      >
        <View style={styles.stockHeader}>
          <View style={styles.stockInfo}>
            <Text style={styles.stockSymbol}>{stock.symbol}</Text>
            <Text style={styles.companyName} numberOfLines={1}>
              {stock.companyName}
            </Text>
          </View>
        </View>
        
        {/* Notes */}
        {watchlistItem.notes && (
          <View style={styles.notesContainer}>
            <Text style={styles.notesLabel}>Notes:</Text>
            <Text style={styles.notesText} numberOfLines={2}>{watchlistItem.notes}</Text>
          </View>
        )}
      </TouchableOpacity>
    );
  };

  // -------- Chatbot --------
  const quickPrompts = [
    'What is an ETF?',
    'Roth vs Traditional IRA',
    'Explain 50/30/20 budgeting',
    'How do index funds work?',
    'What is an expense ratio?',
    'Index fund vs ETF',
    'Diversification basics',
    'Dollar-cost averaging',
    'How to analyze stocks?',
    'What is market cap?',
  ];

  const openChat = () => {
    setChatOpen(true);
    if (chatMessages.length === 0) {
      setChatMessages([
        {
          id: String(Date.now()),
          role: 'assistant',
          content:
            'Educational only — not financial advice.\nWhat do you need help with? Ask about ETFs, IRAs, fees, budgeting, or stock analysis.',
        },
      ]);
    }
    setTimeout(() => listRef.current?.scrollToEnd?.({ animated: false }), 0);
  };

  const closeChat = () => {
    setChatOpen(false);
    setChatInput('');
    setChatSending(false);
  };

  const clearChat = () => {
    setChatMessages([]);
    setChatInput('');
  };

  const sendMessage = async () => {
    if (!chatInput.trim() || chatSending) return;

    const userMessage: ChatMsg = {
      id: String(Date.now()),
      role: 'user',
      content: chatInput.trim(),
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatInput('');
    setChatSending(true);

    try {
      // Simulate AI response
      setTimeout(() => {
        const aiResponse: ChatMsg = {
          id: String(Date.now() + 1),
          role: 'assistant',
          content: `I understand you're asking about "${userMessage.content}". This is a great question about personal finance! While I can provide general educational information, remember that this is not financial advice. For personalized guidance, consider consulting with a qualified financial advisor.`,
        };
        setChatMessages(prev => [...prev, aiResponse]);
        setChatSending(false);
        setTimeout(() => listRef.current?.scrollToEnd?.({ animated: true }), 100);
      }, 1000);
    } catch (error) {
      console.error('Failed to send message:', error);
      setChatSending(false);
    }
  };

  const handleQuickPrompt = (prompt: string) => {
    // Don't set chatInput since we're auto-submitting
    // Create and send the message directly
    const userMessage: ChatMsg = {
      id: String(Date.now()),
      role: 'user',
      content: prompt,
    };

    setChatMessages(prev => [...prev, userMessage]);
    setChatSending(true);

    try {
      // Simulate AI response
      setTimeout(() => {
        const aiResponse: ChatMsg = {
          id: String(Date.now() + 1),
          role: 'assistant',
          content: `I understand you're asking about "${prompt}". This is a great question about personal finance! While I can provide general educational information, remember that this is not financial advice. For personalized guidance, consider consulting with a qualified financial advisor.`,
        };
        setChatMessages(prev => [...prev, aiResponse]);
        setChatSending(false);
        setTimeout(() => listRef.current?.scrollToEnd?.({ animated: true }), 100);
      }, 1000);
    } catch (error) {
      console.error('Failed to send message:', error);
      setChatSending(false);
    }
  };

  if (watchlistLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Stock Tracker</Text>
        </View>
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading your watchlist...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (meError || watchlistError) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Stock Tracker</Text>
        </View>
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>Error loading data. Please try again.</Text>
          <TouchableOpacity style={styles.retryButton} onPress={onRefresh}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  const user = meData?.me;
  const watchlistItems = watchlistData?.myWatchlist || [];
  const totalStocks = watchlistItems.length;
  
  // Debug logging
  console.log('🔍 HomeScreen Debug:', {
    meData: meData?.me ? { id: meData.me.id, name: meData.me.name } : null,
    watchlistData: watchlistData?.myWatchlist ? watchlistData.myWatchlist.length : 0,
    watchlistError,
    watchlistLoading,
    totalStocks,
    hasWatchlistItems: Boolean(watchlistItems && watchlistItems.length > 0)
  });

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Stock Tracker</Text>
        <View style={styles.headerButtons}>
          <TouchableOpacity style={styles.testButton} onPress={testAddToWatchlist}>
            <Text style={styles.testButtonText}>Test Add</Text>
          </TouchableOpacity>
          <TouchableOpacity style={styles.addButton} onPress={handleAddStock}>
            <Icon name="plus" size={24} color="#FFFFFF" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Summary Stats */}
      <View style={styles.summaryContainer}>
        <View style={styles.summaryItem}>
          <Text style={styles.summaryValue}>{totalStocks}</Text>
          <Text style={styles.summaryLabel}>Stocks</Text>
        </View>
        <View style={styles.summaryItem}>
          <Text style={styles.summaryValue}>
            {user?.name?.split(' ')[0] || 'User'}
          </Text>
          <Text style={styles.summaryLabel}>Welcome</Text>
        </View>
      </View>

      {/* Content */}
      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {watchlistLoading ? (
          <View style={styles.loadingContainer}>
            <Icon name="loader" size={32} color="#00cc99" />
            <Text style={styles.loadingText}>Loading your watchlist...</Text>
          </View>
        ) : !watchlistItems || watchlistItems.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Icon name="trending-up" size={64} color="#9CA3AF" />
            <Text style={styles.emptyTitle}>Welcome to Your Watchlist! 📈</Text>
            <Text style={styles.emptySubtitle}>
              You haven't added any stocks yet. Start building your investment portfolio by adding stocks you want to track.
            </Text>
            <View style={styles.emptyActions}>
              <TouchableOpacity style={styles.emptyButton} onPress={handleAddStock}>
                <Text style={styles.emptyButtonText}>Add Your First Stock</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.emptySecondaryButton} onPress={testAddToWatchlist}>
                <Text style={styles.emptySecondaryButtonText}>Try Demo Stock (AAPL)</Text>
              </TouchableOpacity>
            </View>
            <View style={styles.emptyTips}>
              <Text style={styles.emptyTipsTitle}>💡 Quick Tips:</Text>
              <Text style={styles.emptyTipsText}>• Start with companies you know and use</Text>
              <Text style={styles.emptyTipsText}>• Consider different sectors for diversity</Text>
              <Text style={styles.emptyTipsText}>• Use notes to track why you're interested</Text>
            </View>
          </View>
        ) : (
          <View>
            {watchlistItems.map(renderStockCard)}
          </View>
        )}
      </ScrollView>

      {/* Chatbot Floating Button */}
      <TouchableOpacity style={styles.chatButton} onPress={openChat}>
        <Icon name="message-circle" size={24} color="#fff" />
      </TouchableOpacity>

      {/* Chatbot Modal */}
      {chatOpen && (
        <View style={styles.chatModal}>
          <View style={styles.chatHeader}>
            <View style={styles.chatTitleContainer}>
              <Icon name="lightbulb" size={20} color="#00cc99" style={styles.chatTitleIcon} />
              <Text style={styles.chatTitle}>Financial Education Assistant</Text>
            </View>
            <View style={styles.chatHeaderActions}>
              <TouchableOpacity onPress={clearChat} style={styles.chatActionButton}>
                <Icon name="trash-2" size={16} color="#666" />
              </TouchableOpacity>
              <TouchableOpacity onPress={closeChat} style={styles.chatCloseButton}>
                <Icon name="x" size={20} color="#666" />
              </TouchableOpacity>
            </View>
          </View>

          {/* Quick Prompts */}
          <View style={styles.quickPromptsContainer}>
            <View style={styles.quickPromptsGrid}>
              {quickPrompts.map((prompt, index) => (
                <TouchableOpacity
                  key={index}
                  style={styles.quickPromptButton}
                  onPress={() => handleQuickPrompt(prompt)}
                >
                  <Text style={styles.quickPromptText}>{prompt}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Chat Messages */}
          <FlatList
            ref={listRef}
            data={chatMessages}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
              <View style={[
                styles.chatMessage,
                item.role === 'user' ? styles.userMessage : styles.assistantMessage
              ]}>
                <Text style={[
                  styles.chatMessageText,
                  item.role === 'user' ? styles.userMessageText : styles.assistantMessageText
                ]}>
                  {item.content}
                </Text>
              </View>
            )}
            style={styles.chatMessages}
            showsVerticalScrollIndicator={false}
          />

          {/* Chat Input */}
          <View style={styles.chatInputContainer}>
            <TextInput
              style={styles.chatInput}
              placeholder="Ask about personal finance..."
              value={chatInput}
              onChangeText={setChatInput}
              multiline
              maxLength={500}
            />
            <TouchableOpacity
              style={[styles.chatSendButton, !chatInput.trim() && styles.chatSendButtonDisabled]}
              onPress={sendMessage}
              disabled={!chatInput.trim() || chatSending}
            >
              <Icon 
                name={chatSending ? "loader" : "send"} 
                size={20} 
                color={chatInput.trim() ? "#fff" : "#ccc"} 
              />
            </TouchableOpacity>
          </View>
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },

  // Header
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 15,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
    paddingTop: 20,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  addButton: {
    backgroundColor: '#00cc99',
    padding: 8,
    borderRadius: 8,
  },
  headerButtons: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  testButton: {
    backgroundColor: '#4CAF50', // A different color for the test button
    paddingHorizontal: 15,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 10,
  },
  testButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },

  // Summary Stats
  summaryContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    backgroundColor: '#fff',
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
  },
  summaryItem: {
    alignItems: 'center',
  },
  summaryValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#00cc99',
  },
  summaryLabel: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },

  // Content
  content: {
    flex: 1,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
    backgroundColor: '#fff',
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
    marginTop: 20,
  },
  emptySubtitle: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    marginTop: 10,
    marginBottom: 30,
  },
  emptyButton: {
    backgroundColor: '#00cc99',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 25,
  },
  emptyButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  emptyActions: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 15,
    marginBottom: 30,
  },
  emptySecondaryButton: {
    backgroundColor: 'transparent',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#00cc99',
  },
  emptySecondaryButtonText: {
    color: '#00cc99',
    fontSize: 14,
    fontWeight: '500',
  },
  emptyTips: {
    backgroundColor: '#f8f9fa',
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#e2e8f0',
    width: '100%',
  },
  emptyTipsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 10,
  },
  emptyTipsText: {
    fontSize: 14,
    color: '#666',
    marginBottom: 5,
    lineHeight: 20,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
    backgroundColor: '#fff',
  },
  loadingText: {
    fontSize: 16,
    color: '#666',
    marginTop: 15,
  },

  // Watchlist Section
  watchlistSection: {
    backgroundColor: '#fff',
    marginHorizontal: 15,
    marginVertical: 10,
    borderRadius: 12,
    padding: 15,
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  watchlistHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  watchlistTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  stockCount: {
    fontSize: 14,
    color: '#666',
  },
  watchlistDescription: {
    fontSize: 14,
    color: '#555',
    marginBottom: 15,
  },

  // Stock Card
  stockCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: 12,
    padding: 15,
    marginBottom: 10,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  stockHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 10,
  },
  stockInfo: {
    flex: 1,
  },
  stockSymbol: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#00cc99',
  },
  companyName: {
    fontSize: 14,
    color: '#333',
    marginTop: 2,
  },
  sector: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  stockMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 10,
    marginBottom: 10,
  },
  metric: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#333',
  },
  notesContainer: {
    marginTop: 10,
    marginBottom: 10,
  },
  notesLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#333',
    marginBottom: 4,
  },
  notesText: {
    fontSize: 13,
    color: '#555',
    lineHeight: 18,
  },
  targetContainer: {
    marginTop: 10,
    marginBottom: 10,
  },
  targetLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#00cc99',
  },



  // Error
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
    backgroundColor: '#f8f9fa',
  },
  errorText: {
    fontSize: 18,
    color: '#666',
    textAlign: 'center',
    marginBottom: 20,
  },
  retryButton: {
    backgroundColor: '#00cc99',
    paddingHorizontal: 30,
    paddingVertical: 15,
    borderRadius: 25,
  },
  retryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },

  // Chatbot Styles
  chatButton: {
    position: 'absolute',
    bottom: 20,
    right: 20,
    backgroundColor: '#00cc99',
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  chatModal: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 20,
    maxHeight: '70%', // Adjust as needed
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.2,
    shadowRadius: 10,
    elevation: 10,
  },
  chatHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  chatTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  chatTitleIcon: {
    marginRight: 8,
  },
  chatTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  chatHeaderActions: {
    flexDirection: 'row',
  },
  chatActionButton: {
    marginLeft: 10,
  },
  chatCloseButton: {
    marginLeft: 10,
  },
  quickPromptsContainer: {
    marginBottom: 8,
  },
  quickPromptsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'flex-start',
    gap: 6,
  },
  quickPromptButton: {
    backgroundColor: '#e0e0e0',
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 15,
    marginBottom: 4,
  },
  quickPromptText: {
    fontSize: 12,
    color: '#333',
  },
  chatMessages: {
    flex: 1,
    marginBottom: 10,
  },
  chatMessage: {
    maxWidth: '80%',
    padding: 10,
    borderRadius: 10,
    marginBottom: 10,
  },
  userMessage: {
    alignSelf: 'flex-end',
    backgroundColor: '#00cc99',
    borderBottomRightRadius: 0,
  },
  assistantMessage: {
    alignSelf: 'flex-start',
    backgroundColor: '#f0f0f0',
    borderBottomLeftRadius: 0,
  },
  chatMessageText: {
    fontSize: 14,
    color: '#fff',
  },
  userMessageText: {
    color: '#fff',
  },
  assistantMessageText: {
    color: '#333',
  },
  chatInputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
  },
  chatInput: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 15,
    borderRadius: 20,
    backgroundColor: '#f0f0f0',
    fontSize: 14,
    color: '#333',
    marginRight: 10,
    minHeight: 40,
    maxHeight: 100,
  },
  chatSendButton: {
    backgroundColor: '#00cc99',
    padding: 10,
    borderRadius: 20,
  },
  chatSendButtonDisabled: {
    backgroundColor: '#ccc',
  },
});