import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Modal,
  FlatList,
  Alert,
  TextInput,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { NewsArticle } from '../services/newsService';
import newsService from '../services/newsService';
import NewsCard from './NewsCard';

interface SavedArticlesProps {
  visible: boolean;
  onClose: () => void;
}

const SavedArticles: React.FC<SavedArticlesProps> = ({ visible, onClose }) => {
  const [savedArticles, setSavedArticles] = useState<NewsArticle[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState<string | null>(null);

  useEffect(() => {
    if (visible) {
      loadSavedArticles();
    }
  }, [visible]);

  const loadSavedArticles = async () => {
    try {
      const articles = await newsService.getSavedArticles();
      setSavedArticles(articles);
    } catch (error) {
      console.error('Error loading saved articles:', error);
    }
  };

  const handleUnsave = async (articleId: string) => {
    try {
      await newsService.unsaveArticle(articleId);
      await loadSavedArticles();
    } catch (error) {
      console.error('Error unsaving article:', error);
    }
  };

  const clearAllSaved = () => {
    Alert.alert(
      'Clear All Saved Articles',
      'Are you sure you want to remove all saved articles? This action cannot be undone.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Clear All',
          style: 'destructive',
          onPress: async () => {
            try {
              // Remove all saved articles one by one
              for (const article of savedArticles) {
                await newsService.unsaveArticle(article.id);
              }
              await loadSavedArticles();
            } catch (error) {
              console.error('Error clearing saved articles:', error);
            }
          },
        },
      ]
    );
  };

  const getFilteredArticles = () => {
    let filtered = savedArticles;

    // Filter by search query
    if (searchQuery.trim()) {
      filtered = filtered.filter(article =>
        article?.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        article?.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        article?.source?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Filter by category
    if (filterCategory) {
      filtered = filtered.filter(article => article?.category === filterCategory);
    }

    return filtered;
  };

  const getCategories = () => {
    const categories = [...new Set(savedArticles.map(article => article.category))];
    return categories.sort();
  };

  const getCategoryCount = (category: string) => {
    return savedArticles.filter(article => article.category === category).length;
  };

  const filteredArticles = getFilteredArticles();
  const categories = getCategories();

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
    >
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <Icon name="bookmark" size={24} color="#34C759" />
            <Text style={styles.headerTitle}>Saved Articles</Text>
            {savedArticles.length > 0 && (
              <View style={styles.countBadge}>
                <Text style={styles.countText}>{savedArticles.length}</Text>
              </View>
            )}
          </View>
          <View style={styles.headerRight}>
            {savedArticles.length > 0 && (
              <TouchableOpacity 
                style={styles.clearButton}
                onPress={clearAllSaved}
              >
                <Icon name="trash-2" size={20} color="#FF3B30" />
              </TouchableOpacity>
            )}
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Icon name="x" size={24} color="#8E8E93" />
            </TouchableOpacity>
          </View>
        </View>

        {/* Search and Filters */}
        {savedArticles.length > 0 && (
          <View style={styles.filtersContainer}>
            {/* Search Bar */}
            <View style={styles.searchContainer}>
              <Icon name="search" size={16} color="#8E8E93" />
              <TextInput
                style={styles.searchInput}
                placeholder="Search saved articles..."
                value={searchQuery}
                onChangeText={setSearchQuery}
                placeholderTextColor="#8E8E93"
              />
              {searchQuery.length > 0 && (
                <TouchableOpacity onPress={() => setSearchQuery('')}>
                  <Icon name="x" size={16} color="#8E8E93" />
                </TouchableOpacity>
              )}
            </View>

            {/* Category Filters */}
            <ScrollView 
              horizontal 
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.categoriesContainer}
            >
              <TouchableOpacity
                style={[
                  styles.categoryFilter,
                  filterCategory === null && styles.categoryFilterActive,
                ]}
                onPress={() => setFilterCategory(null)}
              >
                <Text style={[
                  styles.categoryFilterText,
                  filterCategory === null && styles.categoryFilterTextActive,
                ]}>
                  All ({savedArticles.length})
                </Text>
              </TouchableOpacity>
              
              {categories.map((category) => (
                <TouchableOpacity
                  key={category}
                  style={[
                    styles.categoryFilter,
                    filterCategory === category && styles.categoryFilterActive,
                  ]}
                  onPress={() => setFilterCategory(category)}
                >
                  <Text style={[
                    styles.categoryFilterText,
                    filterCategory === category && styles.categoryFilterTextActive,
                  ]}>
                    {category.replace('-', ' ')} ({getCategoryCount(category)})
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}

        {/* Content */}
        <View style={styles.content}>
          {savedArticles.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Icon name="bookmark" size={48} color="#C7C7CC" />
              <Text style={styles.emptyTitle}>No Saved Articles</Text>
              <Text style={styles.emptySubtitle}>
                Save articles you want to read later by tapping the bookmark icon on any news article.
              </Text>
            </View>
          ) : filteredArticles.length === 0 ? (
            <View style={styles.emptyContainer}>
              <Icon name="search" size={48} color="#C7C7CC" />
              <Text style={styles.emptyTitle}>No Results Found</Text>
              <Text style={styles.emptySubtitle}>
                Try adjusting your search terms or category filter.
              </Text>
            </View>
          ) : (
            <FlatList
              data={filteredArticles}
              keyExtractor={(item) => item.id}
              renderItem={({ item }) => (
                <View style={styles.savedArticleContainer}>
                  <NewsCard 
                    news={item} 
                    onSave={newsService.saveArticle}
                    onUnsave={handleUnsave}
                    showSaveButton={true}
                  />
                  <TouchableOpacity
                    style={styles.unsaveButton}
                    onPress={() => handleUnsave(item.id)}
                  >
                    <Icon name="bookmark" size={16} color="#FF3B30" />
                    <Text style={styles.unsaveText}>Remove</Text>
                  </TouchableOpacity>
                </View>
              )}
              showsVerticalScrollIndicator={false}
              contentContainerStyle={styles.articlesList}
            />
          )}
        </View>
      </View>
    </Modal>
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
    paddingVertical: 16,
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
    fontSize: 20,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  countBadge: {
    backgroundColor: '#34C759',
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 6,
  },
  countText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  clearButton: {
    padding: 8,
  },
  closeButton: {
    padding: 8,
  },
  filtersContainer: {
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    marginBottom: 16,
    gap: 12,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: '#1C1C1E',
  },
  categoriesContainer: {
    gap: 12,
  },
  categoryFilter: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#F2F2F7',
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  categoryFilterActive: {
    backgroundColor: '#34C759',
    borderColor: '#34C759',
  },
  categoryFilterText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  categoryFilterTextActive: {
    color: '#FFFFFF',
  },
  content: {
    flex: 1,
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
    paddingHorizontal: 40,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 20,
  },
  articlesList: {
    padding: 20,
  },
  savedArticleContainer: {
    position: 'relative',
    marginBottom: 16,
  },
  unsaveButton: {
    position: 'absolute',
    top: 16,
    right: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  unsaveText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FF3B30',
  },
});

export default SavedArticles;
