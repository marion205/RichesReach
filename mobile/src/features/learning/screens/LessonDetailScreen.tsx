/**
 * Lesson Detail Screen
 * Displays full lesson content with completion tracking
 */

import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  SafeAreaView,
  Alert,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Feather';
import { LinearGradient } from 'expo-linear-gradient';
import { API_HTTP } from '../../../config/api';
import { useAuth } from '../../../contexts/AuthContext';
import * as Haptics from 'expo-haptics';

interface LessonDetail {
  id: string;
  title: string;
  description: string;
  duration_minutes: number;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  category: string;
  concepts: string[];
  content: string;
  key_takeaways: string[];
  completed: boolean;
  progress_percent: number;
}

const difficultyColors: Record<string, string> = {
  beginner: '#10B981',
  intermediate: '#F59E0B',
  advanced: '#EF4444',
};

export default function LessonDetailScreen({ navigateTo }: { navigateTo?: (screen: string, params?: any) => void }) {
  const { token } = useAuth();
  const navigation = useNavigation();
  const route = useRoute();
  
  // Try multiple ways to get lessonId from route params
  const lessonId = 
    (route.params as any)?.lessonId || 
    (route.params as any)?.lesson?.id ||
    ((route as any).params?.lessonId) ||
    '';
  
  console.log('[LessonDetail] Route params:', route.params);
  console.log('[LessonDetail] Extracted lessonId:', lessonId);
  
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(false);
  const [lesson, setLesson] = useState<LessonDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log('[LessonDetail] useEffect triggered, lessonId:', lessonId);
    if (lessonId) {
      loadLesson();
    } else {
      console.error('[LessonDetail] No lessonId provided in route params');
      setError('Lesson ID is required');
      setLoading(false);
    }
  }, [lessonId, token]);

  const loadLesson = async () => {
    try {
      setLoading(true);
      setError(null);

      if (!token) {
        throw new Error('Authentication required');
      }

      if (!lessonId) {
        throw new Error('Lesson ID required');
      }

      console.log('[LessonDetail] Loading lesson:', lessonId);
      const url = `${API_HTTP}/api/lessons/${lessonId}`;
      console.log('[LessonDetail] Fetching from:', url);
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setLesson(data);
    } catch (error: any) {
      console.error('Error loading lesson:', error);
      setError(error.message || 'Failed to load lesson');
    } finally {
      setLoading(false);
    }
  };

  const handleComplete = async () => {
    if (!lesson || completing) return;

    try {
      setCompleting(true);

      const response = await fetch(`${API_HTTP}/api/lessons/${lesson.id}/complete`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      // Haptic feedback
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);

      // Update lesson state
      setLesson({ ...lesson, completed: true, progress_percent: 100 });

      // Show achievement if any unlocked
      if (data.achievements_unlocked && data.achievements_unlocked.length > 0) {
        // TODO: Show achievement celebration
        console.log('Achievements unlocked:', data.achievements_unlocked);
      }

      // Navigate back after a short delay
      setTimeout(() => {
        if (navigateTo) {
          navigateTo('lesson-library');
        } else {
          navigation.goBack();
        }
      }, 1000);
    } catch (error: any) {
      console.error('Error completing lesson:', error);
      // Still mark as completed locally
      if (lesson) {
        setLesson({ ...lesson, completed: true, progress_percent: 100 });
      }
    } finally {
      setCompleting(false);
    }
  };

  const getDifficultyColor = (difficulty: string): string => {
    return difficultyColors[difficulty] || '#666';
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#667eea" />
          <Text style={styles.loadingText}>Loading lesson...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error || !lesson) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={48} color="#FF6B6B" />
          <Text style={styles.errorText}>{error || 'Failed to load lesson'}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={loadLesson}>
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
              navigateTo('lesson-library');
            } else {
              navigation.goBack();
            }
          }}
        >
          <Icon name="arrow-left" size={24} color="#1a1a1a" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Lesson</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Lesson Header */}
        <View style={styles.lessonHeader}>
          <View style={styles.lessonHeaderTop}>
            <View style={[styles.difficultyBadge, { backgroundColor: `${getDifficultyColor(lesson.difficulty)}20` }]}>
              <Text style={[styles.difficultyText, { color: getDifficultyColor(lesson.difficulty) }]}>
                {lesson.difficulty.charAt(0).toUpperCase() + lesson.difficulty.slice(1)}
              </Text>
            </View>
            {lesson.completed && (
              <View style={styles.completedBadge}>
                <Icon name="check" size={16} color="#10B981" />
                <Text style={styles.completedText}>Completed</Text>
              </View>
            )}
          </View>
          
          <Text style={styles.lessonTitle}>{lesson.title}</Text>
          <Text style={styles.lessonDescription}>{lesson.description}</Text>
          
          <View style={styles.lessonMeta}>
            <View style={styles.metaItem}>
              <Icon name="clock" size={16} color="#8E8E93" />
              <Text style={styles.metaText}>{lesson.duration_minutes} min</Text>
            </View>
            <View style={styles.metaItem}>
              <Icon name="tag" size={16} color="#8E8E93" />
              <Text style={styles.metaText}>{lesson.category}</Text>
            </View>
          </View>
        </View>

        {/* Lesson Content */}
        <View style={styles.contentSection}>
          <Text style={styles.contentText}>{lesson.content}</Text>
        </View>

        {/* Key Takeaways */}
        {lesson.key_takeaways && lesson.key_takeaways.length > 0 && (
          <View style={styles.takeawaysSection}>
            <Text style={styles.takeawaysTitle}>Key Takeaways</Text>
            {lesson.key_takeaways.map((takeaway, index) => (
              <View key={index} style={styles.takeawayItem}>
                <Icon name="check-circle" size={20} color="#10B981" />
                <Text style={styles.takeawayText}>{takeaway}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Concepts */}
        {lesson.concepts && lesson.concepts.length > 0 && (
          <View style={styles.conceptsSection}>
            <Text style={styles.conceptsTitle}>Concepts Covered</Text>
            <View style={styles.conceptsList}>
              {lesson.concepts.map((concept, index) => (
                <View key={index} style={styles.conceptTag}>
                  <Text style={styles.conceptText}>{concept}</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {/* Complete Button */}
        {!lesson.completed && (
          <TouchableOpacity
            style={styles.completeButton}
            onPress={handleComplete}
            disabled={completing}
          >
            <LinearGradient
              colors={['#667eea', '#764ba2']}
              style={styles.completeButtonGradient}
            >
              {completing ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <>
                  <Icon name="check-circle" size={20} color="#fff" />
                  <Text style={styles.completeButtonText}>Mark as Complete</Text>
                </>
              )}
            </LinearGradient>
          </TouchableOpacity>
        )}

        {lesson.completed && (
          <View style={styles.completedMessage}>
            <Icon name="check-circle" size={24} color="#10B981" />
            <Text style={styles.completedMessageText}>You've completed this lesson!</Text>
          </View>
        )}
      </ScrollView>
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
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 40,
  },
  lessonHeader: {
    backgroundColor: '#fff',
    padding: 20,
    marginBottom: 16,
  },
  lessonHeaderTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  difficultyBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  difficultyText: {
    fontSize: 12,
    fontWeight: '600',
  },
  completedBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    backgroundColor: '#10B98120',
    gap: 6,
  },
  completedText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#10B981',
  },
  lessonTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  lessonDescription: {
    fontSize: 16,
    color: '#666',
    lineHeight: 24,
    marginBottom: 16,
  },
  lessonMeta: {
    flexDirection: 'row',
    gap: 16,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  metaText: {
    fontSize: 14,
    color: '#8E8E93',
  },
  contentSection: {
    backgroundColor: '#fff',
    padding: 20,
    marginBottom: 16,
  },
  contentText: {
    fontSize: 16,
    lineHeight: 28,
    color: '#333',
  },
  takeawaysSection: {
    backgroundColor: '#fff',
    padding: 20,
    marginBottom: 16,
  },
  takeawaysTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  takeawayItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 12,
    gap: 12,
  },
  takeawayText: {
    flex: 1,
    fontSize: 16,
    lineHeight: 24,
    color: '#333',
  },
  conceptsSection: {
    backgroundColor: '#fff',
    padding: 20,
    marginBottom: 16,
  },
  conceptsTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1a1a1a',
    marginBottom: 12,
  },
  conceptsList: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  conceptTag: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#F0F0F5',
  },
  conceptText: {
    fontSize: 14,
    color: '#667eea',
    fontWeight: '500',
  },
  completeButton: {
    marginHorizontal: 20,
    marginTop: 8,
    marginBottom: 20,
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#667eea',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  completeButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    paddingHorizontal: 24,
    gap: 8,
  },
  completeButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
  },
  completedMessage: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginHorizontal: 20,
    marginTop: 8,
    marginBottom: 20,
    padding: 16,
    backgroundColor: '#10B98120',
    borderRadius: 12,
    gap: 8,
  },
  completedMessageText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#10B981',
  },
});

