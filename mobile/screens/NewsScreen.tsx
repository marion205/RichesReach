import React, { useState, useEffect } from 'react';
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
  Image,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import NewsCard from '../components/NewsCard';
import NewsCategories from '../components/NewsCategories';
import NewsPreferences from '../components/NewsPreferences';
import NewsAlerts from '../components/NewsAlerts';
import SavedArticles from '../components/SavedArticles';
import newsService, { NewsCategory, NewsArticle, NEWS_CATEGORIES } from '../services/newsService';

const NewsScreen: React.FC = () => {
  const [refreshing, setRefreshing] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<NewsCategory>(NEWS_CATEGORIES.ALL);
  const [articles, setArticles] = useState<NewsArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showPreferences, setShowPreferences] = useState(false);
  const [showAlerts, setShowAlerts] = useState(false);
  const [showSavedArticles, setShowSavedArticles] = useState(false);
  const [isPersonalized, setIsPersonalized] = useState(false);
  const [categories, setCategories] = useState<Array<{
    category: NewsCategory;
    count: number;
    label: string;
  }>>([]);

  // Helper function to get category label
  const getCategoryLabel = (category: NewsCategory): string => {
    const categoryLabels: Record<NewsCategory, string> = {
      [NEWS_CATEGORIES.ALL]: 'All',
      [NEWS_CATEGORIES.MARKETS]: 'Markets',
      [NEWS_CATEGORIES.TECHNOLOGY]: 'Technology',
      [NEWS_CATEGORIES.CRYPTO]: 'Crypto',
      [NEWS_CATEGORIES.ECONOMY]: 'Economy',
      [NEWS_CATEGORIES.PERSONAL_FINANCE]: 'Personal Finance',
      [NEWS_CATEGORIES.INVESTING]: 'Investing',
      [NEWS_CATEGORIES.REAL_ESTATE]: 'Real Estate',
    };
    return categoryLabels[category] || 'All';
  };

  // Load articles and categories when component mounts or category changes
  useEffect(() => {
    loadArticles();
    loadCategories();
  }, [selectedCategory, isPersonalized]);

  const loadArticles = async () => {
    try {
      setLoading(true);
      const fetchedArticles = await newsService.getNews(selectedCategory, isPersonalized);
      setArticles(fetchedArticles);
    } catch (error) {
      console.error('Error loading articles:', error);
      Alert.alert('Error', 'Failed to load news articles');
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const fetchedCategories = await newsService.getNewsCategories();
      setCategories(fetchedCategories);
    } catch (error) {
      console.error('Error loading categories:', error);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await Promise.all([loadArticles(), loadCategories()]);
    setRefreshing(false);
  };

  const handleCategoryChange = (category: NewsCategory) => {
    setSelectedCategory(category);
  };

  const handleArticlePress = (article: NewsArticle) => {
    // In a real app, you would open the article URL or navigate to a detail screen
    Alert.alert(
      article.title,
      `Published: ${new Date(article.publishedAt).toLocaleDateString()}\n\n${article.description}`,
      [
        { text: 'Close', style: 'cancel' },
        { text: 'Read Full Article', onPress: () => console.log('Open article:', article.url) }
      ]
    );
  };

  const handleSaveArticle = async (article: NewsArticle) => {
    try {
      await newsService.saveArticle(article);
      Alert.alert('Saved', 'Article saved to your reading list');
    } catch (error) {
      Alert.alert('Error', 'Failed to save article');
    }
  };

  const handleShareArticle = (article: NewsArticle) => {
    // In a real app, you would use the Share API
    Alert.alert('Share', `Share: ${article.title}`);
  };

  const filteredArticles = articles.filter(article =>
    article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    article.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const renderArticle = ({ item }: { item: NewsArticle }) => (
    <NewsCard
      news={item}
      onSave={() => handleSaveArticle(item)}
      onUnsave={() => newsService.unsaveArticle(item.id)}
      showSaveButton={true}
    />
  );

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Icon name="globe" size={24} color="#34C759" />
          <Text style={styles.headerTitle}>Financial News</Text>
        </View>
        <View style={styles.headerRight}>
          <TouchableOpacity 
            style={styles.headerButton}
            onPress={() => setShowSavedArticles(true)}
          >
            <Icon name="bookmark" size={20} color="#5856D6" />
          </TouchableOpacity>
          <TouchableOpacity 
            style={styles.headerButton}
            onPress={() => setShowAlerts(true)}
          >
            <Icon name="bell" size={20} color="#FF9500" />
          </TouchableOpacity>
          <TouchableOpacity 
            style={styles.headerButton}
            onPress={() => setShowPreferences(true)}
          >
            <Icon name="settings" size={20} color="#8E8E93" />
          </TouchableOpacity>
        </View>
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <View style={styles.searchBar}>
          <Icon name="search" size={20} color="#8E8E93" />
          <TextInput
            style={styles.searchInput}
            placeholder="Search news..."
            value={searchQuery}
            onChangeText={setSearchQuery}
            placeholderTextColor="#8E8E93"
          />
          {searchQuery.length > 0 && (
            <TouchableOpacity onPress={() => setSearchQuery('')}>
              <Icon name="x" size={20} color="#8E8E93" />
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Personalization Toggle */}
      <View style={styles.personalizationContainer}>
        <TouchableOpacity 
          style={styles.personalizationButton}
          onPress={() => setIsPersonalized(!isPersonalized)}
        >
          <Icon 
            name={isPersonalized ? "user-check" : "user"} 
            size={16} 
            color={isPersonalized ? "#34C759" : "#8E8E93"} 
          />
          <Text style={[
            styles.personalizationText,
            { color: isPersonalized ? "#34C759" : "#8E8E93" }
          ]}>
            {isPersonalized ? "Personalized" : "General"}
          </Text>
        </TouchableOpacity>
        <Text style={styles.personalizationDescription}>
          {isPersonalized 
            ? "Showing news tailored to your interests" 
            : "Showing general financial news"
          }
        </Text>
      </View>

      {/* Categories */}
      <NewsCategories
        categories={categories}
        selectedCategory={selectedCategory}
        onCategorySelect={handleCategoryChange}
      />

      {/* Articles */}
      <View style={styles.articlesContainer}>
        <View style={styles.articlesHeader}>
          <Text style={styles.articlesTitle}>
            {getCategoryLabel(selectedCategory)} News
          </Text>
          <Text style={styles.articlesCount}>
            {filteredArticles.length} articles
          </Text>
        </View>

        {loading ? (
          <View style={styles.loadingContainer}>
            <Icon name="loader" size={24} color="#8E8E93" />
            <Text style={styles.loadingText}>Loading articles...</Text>
          </View>
        ) : (
          <FlatList
            data={filteredArticles}
            renderItem={renderArticle}
            keyExtractor={(item) => item.id}
            showsVerticalScrollIndicator={false}
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={handleRefresh}
                colors={['#34C759']}
                tintColor="#34C759"
              />
            }
            ListEmptyComponent={
              <View style={styles.emptyContainer}>
                <Icon name="newspaper" size={48} color="#E5E5EA" />
                <Text style={styles.emptyTitle}>No articles found</Text>
                <Text style={styles.emptyDescription}>
                  {searchQuery 
                    ? "Try adjusting your search terms"
                    : "Pull down to refresh or try a different category"
                  }
                </Text>
              </View>
            }
            contentContainerStyle={styles.articlesList}
          />
        )}
      </View>

      {/* Modals */}
      <NewsPreferences
        visible={showPreferences}
        onClose={() => setShowPreferences(false)}
        onPreferencesUpdated={() => {
          // Reload articles when preferences are updated
          loadArticles();
        }}
      />

      <NewsAlerts
        visible={showAlerts}
        onClose={() => setShowAlerts(false)}
      />

      <SavedArticles
        visible={showSavedArticles}
        onClose={() => setShowSavedArticles(false)}
      />
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
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 10,
    paddingBottom: 20,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  headerRight: {
    flexDirection: 'row',
    gap: 16,
  },
  headerButton: {
    padding: 8,
  },
  searchContainer: {
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
  },
  searchBar: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    gap: 12,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: '#1C1C1E',
  },
  personalizationContainer: {
    paddingHorizontal: 20,
    paddingBottom: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  personalizationButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 4,
  },
  personalizationText: {
    fontSize: 16,
    fontWeight: '600',
  },
  personalizationDescription: {
    fontSize: 14,
    color: '#8E8E93',
  },
  articlesContainer: {
    flex: 1,
    paddingHorizontal: 20,
  },
  articlesHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
  },
  articlesTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  articlesCount: {
    fontSize: 14,
    color: '#8E8E93',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
  },
  loadingText: {
    fontSize: 16,
    color: '#8E8E93',
  },
  articlesList: {
    paddingBottom: 20,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
    gap: 16,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  emptyDescription: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 20,
  },
});

export default NewsScreen;
