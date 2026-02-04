/**
 * Lesson Library Screen
 * Browse and access all available investing lessons.
 * Uses paginated API (GET /api/lessons/?page=1&limit=10) with infinite scroll and search.
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  SafeAreaView,
  TextInput,
  Alert,
  RefreshControl,
} from 'react-native';
import { useNavigation, NavigationProp, CommonActions } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Feather';
import { API_HTTP } from '../../../config/api';
import { useAuth } from '../../../contexts/AuthContext';
import logger from '../../../utils/logger';

const PAGE_SIZE = 10;

interface Lesson {
  id: string;
  title: string;
  description: string;
  duration_minutes: number;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  category: string;
  concepts: string[];
  completed: boolean;
  progress_percent: number;
}

interface LessonListResponse {
  items: Lesson[];
  total: number;
  page: number;
  limit: number;
}

interface LessonCategory {
  id: string;
  name: string;
  icon: string;
  color: string;
  lessonCount: number;
}

const categories: LessonCategory[] = [
  { id: 'basics', name: 'Basics', icon: 'book-open', color: '#10B981', lessonCount: 0 },
  { id: 'stocks', name: 'Stocks', icon: 'trending-up', color: '#667eea', lessonCount: 0 },
  { id: 'bonds', name: 'Bonds', icon: 'shield', color: '#8B5CF6', lessonCount: 0 },
  { id: 'portfolio', name: 'Portfolio', icon: 'pie-chart', color: '#FF6B35', lessonCount: 0 },
  { id: 'risk', name: 'Risk Management', icon: 'alert-triangle', color: '#F59E0B', lessonCount: 0 },
  { id: 'tax', name: 'Tax & Strategy', icon: 'file-text', color: '#06B6D4', lessonCount: 0 },
];

const difficultyColors: Record<string, string> = {
  beginner: '#10B981',
  intermediate: '#F59E0B',
  advanced: '#EF4444',
};

export default function LessonLibraryScreen({ navigateTo }: { navigateTo?: (screen: string, params?: any) => void }) {
  const { token } = useAuth();
  const navigation = useNavigation<NavigationProp<any>>();
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [error, setError] = useState<string | null>(null);
  const searchDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const fetchLessons = useCallback(
    async (pageNum: number, isRefreshing: boolean = false) => {
      if (!token) {
        setError('Authentication required');
        setLoading(false);
        return;
      }
      if (loading && !isRefreshing) return;
      if (loadingMore && !isRefreshing && pageNum > 1) return;
      if (!hasMore && !isRefreshing && pageNum > 1) return;

      if (pageNum === 1) {
        if (isRefreshing) {
          setRefreshing(true);
        } else {
          setLoading(true);
        }
      } else {
        setLoadingMore(true);
      }
      setError(null);

      try {
        const params = new URLSearchParams();
        params.set('page', String(pageNum));
        params.set('limit', String(PAGE_SIZE));
        if (selectedCategory) params.set('category', selectedCategory);
        if (searchQuery.trim()) params.set('search', searchQuery.trim());

        const url = `${API_HTTP}/api/lessons/?${params.toString()}`;
        const response = await fetch(url, {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data: LessonListResponse = await response.json();
        const newItems = data.items || [];

        setLessons((prev) => (isRefreshing ? newItems : prev.concat(newItems)));
        setTotal(data.total ?? 0);
        setPage(data.page ?? pageNum);
        setHasMore((data.page ?? pageNum) * (data.limit ?? PAGE_SIZE) < (data.total ?? 0));
      } catch (err: any) {
        logger.error('Error loading lessons:', err);
        setError(err.message || 'Failed to load lessons');
        if (pageNum === 1) setLessons([]);
      } finally {
        setLoading(false);
        setLoadingMore(false);
        setRefreshing(false);
      }
    },
    [token, selectedCategory, searchQuery]
  );

  useEffect(() => {
    setPage(1);
    setHasMore(true);
    fetchLessons(1, true);
  }, [token, selectedCategory, searchQuery, fetchLessons]);

  useEffect(() => {
    if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);
    searchDebounceRef.current = setTimeout(() => {
      setSearchQuery(searchInput.trim());
    }, 400);
    return () => {
      if (searchDebounceRef.current) clearTimeout(searchDebounceRef.current);
    };
  }, [searchInput]);

  const handleRefresh = useCallback(() => {
    setPage(1);
    setHasMore(true);
    fetchLessons(1, true);
  }, [fetchLessons]);

  const handleLoadMore = useCallback(() => {
    if (!hasMore || loadingMore || loading) return;
    fetchLessons(page + 1, false);
  }, [hasMore, loadingMore, loading, page, fetchLessons]);

  const handleLessonPress = (lesson: Lesson) => {
    logger.log('[LessonLibrary] 🔵 Lesson pressed:', lesson.id, lesson.title);
    
    // First, try globalNavigate which handles nested navigation properly
    try {
      logger.log('[LessonLibrary] Attempting navigation via globalNavigate (nested)...');
      const { globalNavigate } = require('../../../navigation/NavigationService');
      globalNavigate('Learn', {
        screen: 'lesson-detail',
        params: { lessonId: lesson.id },
      });
      logger.log('[LessonLibrary] ✅ globalNavigate called successfully');
      return;
    } catch (error: any) {
      logger.error('[LessonLibrary] ❌ globalNavigate error:', error);
    }
    
    // Try using CommonActions with the current navigator
    try {
      logger.log('[LessonLibrary] Attempting CommonActions navigation...');
      const action = CommonActions.navigate({
        name: 'lesson-detail',
        params: { lessonId: lesson.id },
      });
      navigation.dispatch(action);
      logger.log('[LessonLibrary] ✅ CommonActions navigation dispatched');
      return;
    } catch (error: any) {
      logger.error('[LessonLibrary] ❌ CommonActions error:', error);
    }
    
    // Try direct navigation (should work since we're in the same stack)
    if (navigation && typeof (navigation as any).navigate === 'function') {
      try {
        logger.log('[LessonLibrary] Attempting direct navigation...');
        (navigation as any).navigate('lesson-detail', { lessonId: lesson.id });
        logger.log('[LessonLibrary] ✅ Direct navigation called (may still fail)');
        // Don't return here - let it try other methods if this fails
      } catch (error: any) {
        logger.error('[LessonLibrary] ❌ Direct navigation error:', error.message);
      }
    }
    
    // Last resort: use navigateTo if available
    if (navigateTo) {
      logger.log('[LessonLibrary] Trying navigateTo function...');
      try {
        navigateTo('lesson-detail', { lessonId: lesson.id });
        logger.log('[LessonLibrary] ✅ navigateTo called successfully');
        return;
      } catch (navError) {
        logger.error('[LessonLibrary] ❌ navigateTo error:', navError);
      }
    }
    
    // Final fallback: show error
    logger.error('[LessonLibrary] ❌ All navigation methods failed');
    Alert.alert('Navigation Error', `Unable to open lesson "${lesson.title}". The screen may not be registered in the navigator.`);
  };

  const getDifficultyBadge = (difficulty: string) => {
    const color = difficultyColors[difficulty] || '#666';
    return (
      <View style={[styles.difficultyBadge, { backgroundColor: `${color}20` }]}>
        <Text style={[styles.difficultyText, { color }]}>
          {difficulty.charAt(0).toUpperCase() + difficulty.slice(1)}
        </Text>
      </View>
    );
  };

  const renderCategory = ({ item }: { item: LessonCategory }) => {
    const isSelected = selectedCategory === item.id;
    const countLabel = isSelected ? `${total} lessons` : '—';
    return (
      <TouchableOpacity
        style={[
          styles.categoryCard,
          isSelected && { backgroundColor: `${item.color}20`, borderColor: item.color },
        ]}
        onPress={() => setSelectedCategory(isSelected ? null : item.id)}
      >
        <View style={[styles.categoryIcon, { backgroundColor: `${item.color}20` }]}>
          <Icon name={item.icon as any} size={24} color={item.color} />
        </View>
        <Text style={[styles.categoryName, isSelected && { color: item.color, fontWeight: '700' }]}>
          {item.name}
        </Text>
        <Text style={styles.categoryCount}>{countLabel}</Text>
      </TouchableOpacity>
    );
  };

  const renderLesson = ({ item }: { item: Lesson }) => {
    return (
      <TouchableOpacity
        style={styles.lessonCard}
        onPress={() => {
          logger.log('[LessonLibrary] 🔵 TouchableOpacity onPress triggered for:', item.id);
          handleLessonPress(item);
        }}
        activeOpacity={0.7}
      >
        <View style={styles.lessonHeader}>
          <View style={styles.lessonHeaderLeft}>
            <Text style={styles.lessonTitle}>{item.title}</Text>
            {getDifficultyBadge(item.difficulty)}
          </View>
          {item.completed && (
            <View style={styles.completedBadge}>
              <Icon name="check" size={16} color="#10B981" />
            </View>
          )}
        </View>
        
        <Text style={styles.lessonDescription}>{item.description}</Text>
        
        <View style={styles.lessonFooter}>
          <View style={styles.lessonMeta}>
            <Icon name="clock" size={14} color="#8E8E93" />
            <Text style={styles.lessonMetaText}>{item.duration_minutes} min</Text>
            <Icon name="tag" size={14} color="#8E8E93" style={{ marginLeft: 12 }} />
            <Text style={styles.lessonMetaText}>{item.category}</Text>
          </View>
          
          {item.progress_percent > 0 && item.progress_percent < 100 && (
            <View style={styles.progressContainer}>
              <View style={styles.progressBar}>
                <View 
                  style={[
                    styles.progressFill,
                    { width: `${item.progress_percent}%` }
                  ]} 
                />
              </View>
              <Text style={styles.progressText}>{item.progress_percent}%</Text>
            </View>
          )}
        </View>
      </TouchableOpacity>
    );
  };

  if (loading && lessons.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#667eea" />
          <Text style={styles.loadingText}>Loading lessons...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error && lessons.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={48} color="#FF6B6B" />
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={handleRefresh}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => {
            if (navigateTo) {
              navigateTo('home');
            } else {
              navigation.goBack();
            }
          }}
        >
          <Icon name="arrow-left" size={24} color="#1a1a1a" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Lesson Library</Text>
        <View style={{ width: 24 }} />
      </View>

      {/* Search Bar — debounced; sends search query param to API */}
      <View style={styles.searchContainer}>
        <Icon name="search" size={20} color="#8E8E93" style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search lessons..."
          placeholderTextColor="#8E8E93"
          value={searchInput}
          onChangeText={setSearchInput}
        />
        {searchInput.length > 0 && (
          <TouchableOpacity onPress={() => setSearchInput('')}>
            <Icon name="x" size={20} color="#8E8E93" />
          </TouchableOpacity>
        )}
      </View>

      {/* Categories */}
      <View style={styles.categoriesContainer}>
        <FlatList
          data={categories}
          renderItem={renderCategory}
          keyExtractor={(item) => item.id}
          horizontal
          showsHorizontalScrollIndicator={false}
          contentContainerStyle={styles.categoriesList}
        />
      </View>

      {/* Lessons List — infinite scroll + pull-to-refresh */}
      <View style={styles.lessonsContainer}>
        <Text style={styles.sectionTitle}>
          {selectedCategory
            ? `${categories.find((c) => c.id === selectedCategory)?.name} Lessons`
            : 'All Lessons'}
          {total > 0 && ` (${total})`}
        </Text>

        {lessons.length === 0 && !loading ? (
          <View style={styles.emptyContainer}>
            <Icon name="book-open" size={48} color="#8E8E93" />
            <Text style={styles.emptyText}>No lessons found</Text>
            <Text style={styles.emptySubtext}>
              {searchQuery ? 'Try a different search term' : 'Check back soon for new lessons'}
            </Text>
          </View>
        ) : (
          <FlatList
            data={lessons}
            renderItem={renderLesson}
            keyExtractor={(item) => item.id}
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.lessonsList}
            onEndReached={handleLoadMore}
            onEndReachedThreshold={0.5}
            ListFooterComponent={
              loadingMore ? (
                <View style={styles.footerLoader}>
                  <ActivityIndicator size="small" color="#667eea" />
                  <Text style={styles.footerLoaderText}>Loading more...</Text>
                </View>
              ) : null
            }
            refreshControl={
              <RefreshControl
                refreshing={refreshing}
                onRefresh={handleRefresh}
                colors={['#667eea']}
              />
            }
          />
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
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
    padding: 20,
  },
  errorText: {
    marginTop: 16,
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 20,
    paddingVertical: 12,
    paddingHorizontal: 24,
    backgroundColor: '#667eea',
    borderRadius: 8,
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
    padding: 20,
    paddingTop: 10,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1a1a1a',
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    marginHorizontal: 16,
    marginTop: 16,
    marginBottom: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  searchIcon: {
    marginRight: 12,
  },
  searchInput: {
    flex: 1,
    fontSize: 16,
    color: '#1a1a1a',
  },
  categoriesContainer: {
    marginTop: 8,
    marginBottom: 16,
  },
  categoriesList: {
    paddingHorizontal: 16,
    gap: 12,
  },
  categoryCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    minWidth: 100,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  categoryIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  categoryName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  categoryCount: {
    fontSize: 12,
    color: '#8E8E93',
  },
  lessonsContainer: {
    flex: 1,
    paddingHorizontal: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1a1a1a',
    marginBottom: 12,
  },
  lessonsList: {
    paddingBottom: 20,
  },
  lessonCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  lessonHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  lessonHeaderLeft: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 8,
  },
  lessonTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1a1a1a',
    flex: 1,
  },
  difficultyBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  difficultyText: {
    fontSize: 12,
    fontWeight: '600',
  },
  completedBadge: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#10B98120',
    justifyContent: 'center',
    alignItems: 'center',
  },
  lessonDescription: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
    marginBottom: 12,
  },
  lessonFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  lessonMeta: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  lessonMetaText: {
    fontSize: 12,
    color: '#8E8E93',
    marginLeft: 4,
  },
  progressContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  progressBar: {
    width: 60,
    height: 4,
    backgroundColor: '#E5E5EA',
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#667eea',
    borderRadius: 2,
  },
  progressText: {
    fontSize: 12,
    color: '#667eea',
    fontWeight: '600',
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 60,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#666',
    marginTop: 16,
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
  },
  footerLoader: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 20,
    gap: 8,
  },
  footerLoaderText: {
    fontSize: 14,
    color: '#8E8E93',
  },
});

