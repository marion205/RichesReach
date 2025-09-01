import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  SafeAreaView,
  FlatList,
  TextInput,
  Alert,
} from 'react-native';
import { useApolloClient } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import NewsCard from '../components/NewsCard';
import NewsCategories from '../components/NewsCategories';
import NewsPreferences from '../components/NewsPreferences';
import NewsAlerts from '../components/NewsAlerts';
import SavedArticles from '../components/SavedArticles';
import newsService, { NewsCategory, NewsArticle, NEWS_CATEGORIES } from '../services/newsService';






// Types
interface ChatMsg {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

export default function HomeScreen({ navigateTo }: { navigateTo: (screen: string, data?: any) => void }) {
  const client = useApolloClient();
  
  // State
  const [refreshing, setRefreshing] = useState(false);

  // News state
  const [newsArticles, setNewsArticles] = useState<NewsArticle[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<NewsCategory>(NEWS_CATEGORIES.ALL);
  const [newsCategories, setNewsCategories] = useState<Array<{ category: NewsCategory; count: number; label: string }>>([]);
  const [showPreferences, setShowPreferences] = useState(false);
  const [showAlerts, setShowAlerts] = useState(false);
  const [showSavedArticles, setShowSavedArticles] = useState(false);
  const [isPersonalized, setIsPersonalized] = useState(false);

  // Chatbot state
  const [chatOpen, setChatOpen] = useState(false);
  const [chatMessages, setChatMessages] = useState<ChatMsg[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatSending, setChatSending] = useState(false);
  const listRef = useRef<FlatList<ChatMsg>>(null);

  // Load news on component mount
  useEffect(() => {
    loadNews();
    loadNewsCategories();
  }, [selectedCategory, isPersonalized]);

  const loadNews = async () => {
    try {
      let news;
      if (isPersonalized) {
        news = await newsService.getPersonalizedNews();
      } else {
        news = await newsService.getRealTimeNews(selectedCategory);
      }
      setNewsArticles(news);
    } catch (error) {
      console.error('Error loading news:', error);
    }
  };

  const loadNewsCategories = async () => {
    try {
      const categories = await newsService.getNewsCategories();
      setNewsCategories(categories);
    } catch (error) {
      console.error('Error loading news categories:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadNews();
    setRefreshing(false);
  };

  // -------- Chatbot --------



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

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Icon name="home" size={24} color="#34C759" />
        <Text style={styles.headerTitle}>Financial News</Text>
      </View>

      {/* Content */}
      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Welcome Message */}
        <View style={styles.welcomeContainer}>
          <Icon name="home" size={48} color="#34C759" />
          <Text style={styles.welcomeTitle}>Welcome to RichesReach! 📰</Text>
          <Text style={styles.welcomeSubtitle}>
            Stay informed with the latest financial news and get personalized financial education.
          </Text>
        </View>

        {/* News Section */}
        <View style={styles.newsSection}>
          <View style={styles.newsHeader}>
            <View style={styles.newsHeaderLeft}>
              <Icon name="rss" size={20} color="#34C759" />
              <Text style={styles.newsTitle}>Financial News</Text>
            </View>
            <View style={styles.newsHeaderRight}>
              <TouchableOpacity 
                style={styles.savedButton}
                onPress={() => setShowSavedArticles(true)}
              >
                <Icon name="bookmark" size={16} color="#5856D6" />
              </TouchableOpacity>
              <TouchableOpacity 
                style={styles.alertsButton}
                onPress={() => setShowAlerts(true)}
              >
                <Icon name="bell" size={16} color="#FF9500" />
              </TouchableOpacity>
              <TouchableOpacity 
                style={styles.personalizeButton}
                onPress={() => setIsPersonalized(!isPersonalized)}
              >
                <Icon 
                  name={isPersonalized ? "user-check" : "user"} 
                  size={16} 
                  color={isPersonalized ? "#34C759" : "#8E8E93"} 
                />
                <Text style={[
                  styles.personalizeText,
                  isPersonalized && styles.personalizeTextActive
                ]}>
                  {isPersonalized ? 'Personal' : 'All'}
                </Text>
              </TouchableOpacity>
              <TouchableOpacity 
                style={styles.preferencesButton}
                onPress={() => setShowPreferences(true)}
              >
                <Icon name="settings" size={16} color="#8E8E93" />
              </TouchableOpacity>
            </View>
          </View>

          {/* News Categories */}
          {newsCategories.length > 0 && (
            <NewsCategories
              selectedCategory={selectedCategory}
              onCategorySelect={setSelectedCategory}
              categories={newsCategories}
            />
          )}

          <FlatList
            data={newsArticles}
            keyExtractor={(item) => item.id}
            renderItem={({ item }) => (
              <NewsCard 
                news={item} 
                onSave={newsService.saveArticle}
                onUnsave={newsService.unsaveArticle}
                showSaveButton={true}
              />
            )}
            horizontal={false}
            showsVerticalScrollIndicator={false}
            scrollEnabled={false}
          />
        </View>

        {/* News Preferences Modal */}
        <NewsPreferences
          visible={showPreferences}
          onClose={() => setShowPreferences(false)}
          onPreferencesUpdated={() => {
            loadNews();
            loadNewsCategories();
          }}
        />

        {/* News Alerts Modal */}
        <NewsAlerts
          visible={showAlerts}
          onClose={() => setShowAlerts(false)}
        />

        {/* Saved Articles Modal */}
        <SavedArticles
          visible={showSavedArticles}
          onClose={() => setShowSavedArticles(false)}
        />
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
                name={chatSending ? "refresh-cw" : "send"} 
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
    alignItems: 'center',
    gap: 12,
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
  },

  // Welcome Section
  welcomeContainer: {
    alignItems: 'center',
    padding: 40,
    backgroundColor: '#FFFFFF',
    marginHorizontal: 16,
    marginVertical: 12,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  welcomeTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
    marginTop: 16,
    marginBottom: 8,
    textAlign: 'center',
  },
  welcomeSubtitle: {
    fontSize: 16,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 22,
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

  // News Section
  newsSection: {
    marginTop: 24,
    marginBottom: 16,
  },
  newsHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
    paddingHorizontal: 16,
  },
  newsHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  newsHeaderRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  newsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  personalizeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#F2F2F7',
  },
  personalizeText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E93',
  },
  personalizeTextActive: {
    color: '#34C759',
  },
  savedButton: {
    padding: 8,
    borderRadius: 16,
    backgroundColor: '#F2F2F7',
  },
  alertsButton: {
    padding: 8,
    borderRadius: 16,
    backgroundColor: '#F2F2F7',
  },
  preferencesButton: {
    padding: 8,
    borderRadius: 16,
    backgroundColor: '#F2F2F7',
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