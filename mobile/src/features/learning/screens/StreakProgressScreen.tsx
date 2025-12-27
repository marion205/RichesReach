/**
 * Streak & Progress Screen
 * Displays user's daily brief streaks, weekly progress, learning progress, and achievements
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
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Feather';
import { LinearGradient } from 'expo-linear-gradient';
import { API_HTTP } from '../../../config/api';
import { useAuth } from '../../../contexts/AuthContext';

interface ProgressData {
  streak: {
    current: number;
    longest: number;
    last_completion_date: string | null;
  };
  weekly_progress: {
    briefs_completed: number;
    goal: number;
    lessons_completed: number;
  };
  monthly_progress: {
    lessons_completed: number;
    goal: number;
  };
  overall: {
    concepts_learned: number;
    lessons_completed: number;
    current_level: string;
    confidence_score: number;
  };
  achievements: Array<{
    achievement_type: string;
    unlocked_at: string;
  }>;
}

const achievementIcons: Record<string, string> = {
  'streak_3': '🔥',
  'streak_7': '🔥',
  'streak_30': '🏆',
  'lessons_10': '📚',
  'first_lesson': '🎓',
  'first_action': '✅',
};

const achievementNames: Record<string, string> = {
  'streak_3': '3-Day Streak',
  'streak_7': '7-Day Streak',
  'streak_30': '30-Day Streak',
  'lessons_10': '10 Lessons Learned',
  'first_lesson': 'First Lesson',
  'first_action': 'First Action',
};

export default function StreakProgressScreen({ navigateTo }: { navigateTo?: (screen: string) => void }) {
  const { token } = useAuth();
  const navigation = useNavigation();
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProgress();
  }, [token]);

  const loadProgress = async () => {
    try {
      setLoading(true);
      setError(null);

      if (!token) {
        throw new Error('Authentication required');
      }

      const response = await fetch(`${API_HTTP}/api/daily-brief/progress`, {
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
      
      // Transform API response to match expected structure
      const transformedData: ProgressData = {
        streak: {
          current: data.streak || 0,
          longest: data.longest_streak || 0,
          last_completion_date: null, // API doesn't return this yet
        },
        weekly_progress: {
          briefs_completed: data.weekly_briefs_completed || 0,
          goal: data.weekly_goal || 5,
          lessons_completed: data.weekly_lessons_completed || 0,
        },
        monthly_progress: {
          lessons_completed: data.monthly_lessons_completed || 0,
          goal: data.monthly_goal || 20,
        },
        overall: {
          concepts_learned: data.concepts_learned || 0,
          lessons_completed: data.weekly_lessons_completed || 0, // Using weekly as total for now
          current_level: data.current_level || 'beginner',
          confidence_score: data.confidence_score || 5,
        },
        achievements: (data.achievements || []).map((a: any) => ({
          achievement_type: a.achievement_type,
          unlocked_at: a.unlocked_at,
        })),
      };
      
      setProgress(transformedData);
    } catch (error: any) {
      console.error('Error loading progress:', error);
      setError(error.message || 'Failed to load progress');
    } finally {
      setLoading(false);
    }
  };

  const getProgressPercentage = (current: number, goal: number): number => {
    if (!goal || goal <= 0) return 0;
    return Math.min(100, Math.max(0, (current / goal) * 100));
  };

  const getLevelColor = (level: string): string => {
    switch (level.toLowerCase()) {
      case 'beginner':
        return '#10B981';
      case 'intermediate':
        return '#667eea';
      case 'advanced':
        return '#8B5CF6';
      default:
        return '#667eea';
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#667eea" />
          <Text style={styles.loadingText}>Loading your progress...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (error || !progress) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={48} color="#FF6B6B" />
          <Text style={styles.errorText}>{error || 'Failed to load progress'}</Text>
          <TouchableOpacity style={styles.retryButton} onPress={loadProgress}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
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
          <Text style={styles.headerTitle}>Your Progress</Text>
          <View style={{ width: 24 }} />
        </View>

        {/* Streak Card */}
        <View style={styles.streakCard}>
          <LinearGradient
            colors={['#FF6B35', '#FF8C42']}
            style={styles.streakGradient}
          >
            <View style={styles.streakContent}>
              <Text style={styles.streakEmoji}>🔥</Text>
              <Text style={styles.streakTitle}>Current Streak</Text>
              <Text style={styles.streakNumber}>{progress?.streak?.current || 0}</Text>
              <Text style={styles.streakLabel}>days in a row</Text>
              {progress?.streak?.longest && progress.streak.longest > (progress?.streak?.current || 0) && (
                <Text style={styles.streakBest}>
                  Best: {progress.streak.longest} days
                </Text>
              )}
            </View>
          </LinearGradient>
        </View>

        {/* Weekly Progress */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>This Week</Text>
          <View style={styles.progressCard}>
            <View style={styles.progressItem}>
              <View style={styles.progressHeader}>
                <Text style={styles.progressLabel}>Daily Briefs</Text>
                <Text style={styles.progressValue}>
                  {progress?.weekly_progress?.briefs_completed || 0} / {progress?.weekly_progress?.goal || 5}
                </Text>
              </View>
              <View style={styles.progressBar}>
                <View 
                  style={[
                    styles.progressFill,
                    { 
                      width: `${getProgressPercentage(
                        progress?.weekly_progress?.briefs_completed || 0, 
                        progress?.weekly_progress?.goal || 5
                      )}%` 
                    }
                  ]} 
                />
              </View>
            </View>
            <View style={styles.progressItem}>
              <View style={styles.progressHeader}>
                <Text style={styles.progressLabel}>Lessons Completed</Text>
                <Text style={styles.progressValue}>
                  {progress?.weekly_progress?.lessons_completed || 0}
                </Text>
              </View>
            </View>
          </View>
        </View>

        {/* Monthly Progress */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>This Month</Text>
          <View style={styles.progressCard}>
            <View style={styles.progressItem}>
              <View style={styles.progressHeader}>
                <Text style={styles.progressLabel}>Lessons Completed</Text>
                <Text style={styles.progressValue}>
                  {progress?.monthly_progress?.lessons_completed || 0} / {progress?.monthly_progress?.goal || 20}
                </Text>
              </View>
              <View style={styles.progressBar}>
                <View 
                  style={[
                    styles.progressFill,
                    { 
                      width: `${getProgressPercentage(
                        progress?.monthly_progress?.lessons_completed || 0, 
                        progress?.monthly_progress?.goal || 20
                      )}%` 
                    }
                  ]} 
                />
              </View>
            </View>
          </View>
        </View>

        {/* Overall Stats */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Overall Progress</Text>
          <View style={styles.statsGrid}>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>{progress?.overall?.concepts_learned || 0}</Text>
              <Text style={styles.statLabel}>Concepts Learned</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>{progress?.overall?.lessons_completed || 0}</Text>
              <Text style={styles.statLabel}>Lessons Completed</Text>
            </View>
          </View>
          
          <View style={styles.levelCard}>
            <View style={styles.levelHeader}>
              <Text style={styles.levelLabel}>Current Level</Text>
              <View 
                style={[
                  styles.levelBadge,
                  { backgroundColor: getLevelColor(progress?.overall?.current_level || 'beginner') }
                ]}
              >
                <Text style={styles.levelText}>{progress?.overall?.current_level || 'beginner'}</Text>
              </View>
            </View>
          </View>

          <View style={styles.confidenceCard}>
            <View style={styles.confidenceHeader}>
              <Text style={styles.confidenceLabel}>Confidence Score</Text>
              <Text style={styles.confidenceValue}>
                {progress?.overall?.confidence_score || 5}/10
              </Text>
            </View>
            <View style={styles.progressBar}>
              <View 
                style={[
                  styles.progressFill,
                  { 
                    width: `${getProgressPercentage(progress?.overall?.confidence_score || 5, 10)}%`,
                    backgroundColor: '#667eea',
                  }
                ]} 
              />
            </View>
          </View>
        </View>

        {/* Achievements */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Achievements</Text>
          {!progress?.achievements || progress.achievements.length === 0 ? (
            <View style={styles.emptyAchievements}>
              <Text style={styles.emptyText}>No achievements yet</Text>
              <Text style={styles.emptySubtext}>Complete your daily briefs to unlock achievements!</Text>
            </View>
          ) : (
            <View style={styles.achievementsGrid}>
              {(progress?.achievements || []).map((achievement, index) => (
                <View key={index} style={styles.achievementCard}>
                  <Text style={styles.achievementEmoji}>
                    {achievementIcons[achievement.achievement_type] || '🏆'}
                  </Text>
                  <Text style={styles.achievementName}>
                    {achievementNames[achievement.achievement_type] || achievement.achievement_type}
                  </Text>
                  <Text style={styles.achievementDate}>
                    {new Date(achievement.unlocked_at).toLocaleDateString()}
                  </Text>
                </View>
              ))}
            </View>
          )}
        </View>
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
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 40,
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
  streakCard: {
    margin: 16,
    borderRadius: 16,
    overflow: 'hidden',
    shadowColor: '#FF6B35',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  streakGradient: {
    padding: 24,
  },
  streakContent: {
    alignItems: 'center',
  },
  streakEmoji: {
    fontSize: 48,
    marginBottom: 8,
  },
  streakTitle: {
    fontSize: 16,
    fontWeight: '500',
    color: '#fff',
    opacity: 0.9,
    marginBottom: 4,
  },
  streakNumber: {
    fontSize: 56,
    fontWeight: '700',
    color: '#fff',
    marginBottom: 4,
  },
  streakLabel: {
    fontSize: 14,
    color: '#fff',
    opacity: 0.9,
  },
  streakBest: {
    fontSize: 12,
    color: '#fff',
    opacity: 0.8,
    marginTop: 8,
  },
  section: {
    marginTop: 24,
    paddingHorizontal: 16,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1a1a1a',
    marginBottom: 12,
  },
  progressCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  progressItem: {
    marginBottom: 16,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  progressLabel: {
    fontSize: 14,
    color: '#666',
  },
  progressValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1a1a1a',
  },
  progressBar: {
    height: 8,
    backgroundColor: '#E5E5EA',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#10B981',
    borderRadius: 4,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  statCard: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginHorizontal: 4,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  statValue: {
    fontSize: 32,
    fontWeight: '700',
    color: '#667eea',
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
  },
  levelCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  levelHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  levelLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  levelBadge: {
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 20,
  },
  levelText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#fff',
    textTransform: 'capitalize',
  },
  confidenceCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  confidenceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  confidenceLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  confidenceValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#667eea',
  },
  achievementsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  achievementCard: {
    width: '48%',
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  achievementEmoji: {
    fontSize: 32,
    marginBottom: 8,
  },
  achievementName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1a1a1a',
    textAlign: 'center',
    marginBottom: 4,
  },
  achievementDate: {
    fontSize: 12,
    color: '#666',
  },
  emptyAchievements: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 32,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#666',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#999',
    textAlign: 'center',
  },
});

