/**
 * Lesson Library Screen
 * Browse and access all available investing lessons
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  SafeAreaView,
  TextInput,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Feather';
import { LinearGradient } from 'expo-linear-gradient';
import { API_HTTP } from '../../../config/api';
import { useAuth } from '../../../contexts/AuthContext';

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

export default function LessonLibraryScreen({ navigateTo }: { navigateTo?: (screen: string) => void }) {
  const { token } = useAuth();
  const navigation = useNavigation();
  const [loading, setLoading] = useState(true);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [filteredLessons, setFilteredLessons] = useState<Lesson[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadLessons();
  }, [token]);

  useEffect(() => {
    filterLessons();
  }, [lessons, selectedCategory, searchQuery]);

  const loadLessons = async () => {
    try {
      setLoading(true);
      setError(null);

      if (!token) {
        throw new Error('Authentication required');
      }

      // TODO: Replace with actual API endpoint when available
      // For now, using mock data
      const mockLessons: Lesson[] = [
        {
          id: '1',
          title: 'What is a Stock?',
          description: 'Learn the fundamentals of stocks and how they work',
          duration_minutes: 2,
          difficulty: 'beginner',
          category: 'basics',
          concepts: ['stocks', 'equity', 'ownership'],
          completed: false,
          progress_percent: 0,
        },
        {
          id: '2',
          title: 'Understanding Market Volatility',
          description: 'Why markets go up and down, and what it means for you',
          duration_minutes: 3,
          difficulty: 'beginner',
          category: 'basics',
          concepts: ['volatility', 'market cycles'],
          completed: true,
          progress_percent: 100,
        },
        {
          id: '3',
          title: 'Building Your First Portfolio',
          description: 'Step-by-step guide to creating a diversified portfolio',
          duration_minutes: 5,
          difficulty: 'intermediate',
          category: 'portfolio',
          concepts: ['diversification', 'asset allocation'],
          completed: false,
          progress_percent: 0,
        },
        {
          id: '4',
          title: 'Risk vs. Reward',
          description: 'Understanding the relationship between risk and potential returns',
          duration_minutes: 4,
          difficulty: 'intermediate',
          category: 'risk',
          concepts: ['risk', 'returns', 'correlation'],
          completed: false,
          progress_percent: 45,
        },
      ];

      // Simulate API delay
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setLessons(mockLessons);
    } catch (error: any) {
      console.error('Error loading lessons:', error);
      setError(error.message || 'Failed to load lessons');
    } finally {
      setLoading(false);
    }
  };

  const filterLessons = () => {
    let filtered = [...lessons];

    // Filter by category
    if (selectedCategory) {
      filtered = filtered.filter(lesson => lesson.category === selectedCategory);
    }

    // Filter by search query
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(lesson =>
        lesson.title.toLowerCase().includes(query) ||
        lesson.description.toLowerCase().includes(query) ||
        lesson.concepts.some(concept => concept.toLowerCase().includes(query))
      );
    }

    setFilteredLessons(filtered);
  };

  const handleLessonPress = (lesson: Lesson) => {
    // Navigate to lesson detail screen
    // TODO: Create lesson detail screen
    console.log('Lesson pressed:', lesson.id);
    // For now, just show an alert
    // navigation.navigate('lesson-detail', { lessonId: lesson.id });
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
    const categoryLessons = lessons.filter(l => l.category === item.id);
    
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
        <Text style={styles.categoryCount}>{categoryLessons.length} lessons</Text>
      </TouchableOpacity>
    );
  };

  const renderLesson = ({ item }: { item: Lesson }) => {
    return (
      <TouchableOpacity
        style={styles.lessonCard}
        onPress={() => handleLessonPress(item)}
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

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#667eea" />
          <Text style={styles.loadingText}>Loading lessons...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={48} color="#FF6B6B" />
          <Text style={styles.errorText}>{error}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={loadLessons}>
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

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <Icon name="search" size={20} color="#8E8E93" style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search lessons..."
          placeholderTextColor="#8E8E93"
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
        {searchQuery.length > 0 && (
          <TouchableOpacity onPress={() => setSearchQuery('')}>
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

      {/* Lessons List */}
      <View style={styles.lessonsContainer}>
        <Text style={styles.sectionTitle}>
          {selectedCategory 
            ? `${categories.find(c => c.id === selectedCategory)?.name} Lessons`
            : 'All Lessons'}
          {filteredLessons.length > 0 && ` (${filteredLessons.length})`}
        </Text>
        
        {filteredLessons.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Icon name="book-open" size={48} color="#8E8E93" />
            <Text style={styles.emptyText}>No lessons found</Text>
            <Text style={styles.emptySubtext}>
              {searchQuery ? 'Try a different search term' : 'Check back soon for new lessons'}
            </Text>
          </View>
        ) : (
          <FlatList
            data={filteredLessons}
            renderItem={renderLesson}
            keyExtractor={(item) => item.id}
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.lessonsList}
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
});

