/**
 * Daily Brief Screen
 * Core daily hook for RichesReach - delivers plain-English investing guidance
 * Takes < 2 minutes, builds confidence, creates daily habit
 */

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  SafeAreaView,
  Animated,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import Icon from 'react-native-vector-icons/Feather';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Notifications from 'expo-notifications';
import { API_HTTP } from '../../../config/api';
import { useAuth } from '../../../contexts/AuthContext';
import * as Haptics from 'expo-haptics';
import DailyBriefOnboardingScreen, { isDailyBriefOnboardingCompleted } from './DailyBriefOnboardingScreen';
import { dailyBriefNotificationScheduler } from '../services/DailyBriefNotificationScheduler';
import logger from '../../../utils/logger';
import { safeNavigate, safeGoBack } from '../../../utils/navigation';
import { TIMING, API } from '../../../config/constants';

// Extended DailyBrief interface for this screen's specific needs
interface DailyBrief {
  id: string;
  date: string;
  market_summary: string;
  personalized_action: string;
  action_type: string;
  lesson_id?: string;
  lesson_title?: string;
  lesson_content?: string;
  experience_level: string;
  is_completed: boolean;
  streak: number;
  weekly_progress: {
    briefs_completed: number;
    goal: number;
    lessons_completed: number;
  };
  confidence_score: number;
  achievements_unlocked?: string[];
}

interface DailyBriefScreenProps {
  navigateTo?: (screen: string, params?: Record<string, unknown>) => void;
}

interface SectionItem {
  id: string;
  type: 'header' | 'market_summary' | 'action' | 'lesson' | 'progress' | 'complete';
  data?: DailyBrief | Record<string, unknown>;
}

const CACHE_KEY = '@daily_brief_cache';
const CACHE_EXPIRY_MS = API.CACHE_TTL_LONG; // 24 hours

export default function DailyBriefScreen({ navigateTo }: DailyBriefScreenProps) {
  const { token, user } = useAuth();
  const navigation = useNavigation();
  const [brief, setBrief] = useState<DailyBrief | null>(null);
  const [loading, setLoading] = useState(true);
  const [completing, setCompleting] = useState(false);
  const [sectionsViewed, setSectionsViewed] = useState<Set<string>>(new Set());
  const [lessonExpanded, setLessonExpanded] = useState(false);
  const [showAchievement, setShowAchievement] = useState<string | null>(null);
  const [snoozeScheduled, setSnoozeScheduled] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  
  // Animation for achievements
  const achievementScale = useRef(new Animated.Value(0)).current;
  
  // Refs for proper state management
  const startTimeRef = useRef<number>(Date.now());
  const retryCountRef = useRef<number>(0);
  const isRetryingRef = useRef<boolean>(false);
  const completionInProgressRef = useRef<boolean>(false);
  const flatListRef = useRef<FlatList>(null);
  const timeoutIdRef = useRef<NodeJS.Timeout | null>(null);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const scrollFallbackTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const onboardingCheckTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  
  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
        scrollTimeoutRef.current = null;
      }
      if (scrollFallbackTimeoutRef.current) {
        clearTimeout(scrollFallbackTimeoutRef.current);
        scrollFallbackTimeoutRef.current = null;
      }
      if (onboardingCheckTimeoutRef.current) {
        clearTimeout(onboardingCheckTimeoutRef.current);
        onboardingCheckTimeoutRef.current = null;
      }
    };
  }, []);

  // Get time-based greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 17) return 'Good afternoon';
    return 'Good evening';
  };

  // Load cached brief if available
  const loadCachedBrief = async (): Promise<DailyBrief | null> => {
    try {
      const cached = await AsyncStorage.getItem(CACHE_KEY);
      if (cached) {
        const { brief: cachedBrief, timestamp } = JSON.parse(cached);
        const age = Date.now() - timestamp;
        if (age < CACHE_EXPIRY_MS) {
          return cachedBrief;
        }
      }
    } catch (error) {
      logger.log('Error loading cache:', error);
    }
    return null;
  };

  // Save brief to cache
  const saveBriefToCache = async (brief: DailyBrief) => {
    try {
      await AsyncStorage.setItem(CACHE_KEY, JSON.stringify({
        brief,
        timestamp: Date.now(),
      }));
    } catch (error) {
      logger.log('Error saving cache:', error);
    }
  };

  useEffect(() => {
    // Check if onboarding is needed with proper error handling
    const checkOnboarding = async () => {
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        // Add timeout to prevent hanging - if check takes > 300ms, skip onboarding
        const onboardingCheck = Promise.race([
          isDailyBriefOnboardingCompleted(),
          new Promise<boolean>((resolve) => {
            if (onboardingCheckTimeoutRef.current) {
              clearTimeout(onboardingCheckTimeoutRef.current);
            }
            onboardingCheckTimeoutRef.current = setTimeout(() => {
              logger.log('[DailyBrief] Onboarding check timed out, skipping onboarding');
              resolve(true); // Default to completed after timeout
              onboardingCheckTimeoutRef.current = null;
            }, TIMING.DEBOUNCE_SHORT);
          }),
        ]);
        
        const completed = await onboardingCheck;
        if (!completed) {
          logger.log('[DailyBrief] Onboarding not completed, showing onboarding screen');
          setShowOnboarding(true);
        } else {
          logger.log('[DailyBrief] Onboarding completed, loading brief');
          loadBrief();
        }
      } catch (error) {
        logger.error('[DailyBrief] Error checking onboarding status:', error);
        // On error, skip onboarding and load brief directly
        loadBrief();
      }
    };
    
    checkOnboarding();

    // Initialize daily reminder notification (non-blocking)
    const initializeNotifications = async () => {
      try {
        const preferences = await dailyBriefNotificationScheduler.getPreferences();
        if (preferences.enabled) {
          await dailyBriefNotificationScheduler.scheduleDailyReminder(preferences);
        }
      } catch (error) {
        logger.error('[DailyBrief] Error initializing notifications:', error);
      }
    };
    initializeNotifications();

    // Cleanup timeouts on unmount
    return () => {
      if (timeoutIdRef.current) {
        clearTimeout(timeoutIdRef.current);
        timeoutIdRef.current = null;
      }
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = null;
      }
    };
  }, [token]);

  // Build sections for FlatList - must be defined before any conditional returns
  const buildSections = useCallback((): SectionItem[] => {
    if (!brief) return [];
    
    const sections: SectionItem[] = [
      { id: 'header', type: 'header' },
      { id: 'market_summary', type: 'market_summary' },
      { id: 'action', type: 'action' },
    ];

    if (brief.lesson_title && brief.lesson_content) {
      sections.push({ id: 'lesson', type: 'lesson' });
    }

    sections.push(
      { id: 'progress', type: 'progress' },
      { id: 'complete', type: 'complete' }
    );

    return sections;
  }, [brief]);

  // Memoize sections to prevent unnecessary re-renders - must be before conditional returns
  const sections = useMemo(() => buildSections(), [buildSections]);

  const loadBrief = async (isRetry = false) => {
    logger.log('[DailyBrief] 🔄 loadBrief called, isRetry:', isRetry, 'hasToken:', !!token);
    try {
      if (!isRetry) {
        logger.log('[DailyBrief] Setting loading state to true...');
        setLoading(true);
        isRetryingRef.current = false;
        retryCountRef.current = 0;
        
        // Try to load cached brief first
        logger.log('[DailyBrief] Checking for cached brief...');
        const cached = await loadCachedBrief();
        if (cached) {
          logger.log('[DailyBrief] ✅ Found cached brief, using it');
          setBrief(cached);
          setLoading(false);
          return; // Return early if we have cached data
        }
        logger.log('[DailyBrief] No cached brief found, fetching from API...');
      }
      
      if (!token) {
        logger.error('[DailyBrief] ❌ No token available!');
        setLoading(false);
        throw new Error('Authentication required. Please log in.');
      }
      
      logger.log('[DailyBrief] Token available, making API request...');

      const controller = new AbortController();
      // Clear any existing timeout
      if (timeoutIdRef.current) {
        clearTimeout(timeoutIdRef.current);
      }
      timeoutIdRef.current = setTimeout(() => controller.abort(), TIMING.TIMEOUT_MEDIUM);

      // Fetch today's brief (backend will auto-detect and regenerate old mock data)
      const url = `${API_HTTP}/api/daily-brief/today`;
      logger.log(`[DailyBrief] 🔍 Fetching from: ${url}`);
      logger.log(`[DailyBrief] 🔍 API_HTTP: ${API_HTTP}`);
      logger.log(`[DailyBrief] 🔍 Token exists: ${!!token}`);
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        signal: controller.signal,
      });
      
      logger.log(`[DailyBrief] ✅ Response status: ${response.status}`);
      
      if (timeoutIdRef.current) {
        clearTimeout(timeoutIdRef.current);
        timeoutIdRef.current = null;
      }

      if (!response.ok) {
        const errorText = await response.text().catch(() => 'No error details');
        logger.error(`[DailyBrief] ❌ Response not OK: ${response.status} - ${errorText}`);
        if (response.status === 503) {
          throw new Error('Daily brief service is starting up. Please wait a moment and try again.');
        }
        if (response.status === 401) {
          throw new Error('Authentication failed. Please log in again.');
        }
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: DailyBrief = await response.json();
      logger.log('[DailyBrief] ✅ Received brief data, setting state...');
      setBrief(data);
      startTimeRef.current = Date.now(); // Reset timer on successful load
      await saveBriefToCache(data);
      retryCountRef.current = 0;
      isRetryingRef.current = false;
      setLoading(false);
      logger.log('[DailyBrief] ✅ Brief loaded and state updated!');
    } catch (error: any) {
      logger.error('Error loading daily brief:', error);
      
      // Auto-retry for network errors (up to 1 retry, faster)
      if (
        (error.message?.includes('Network request failed') || 
         error.message?.includes('Failed to fetch') ||
         error.name === 'AbortError') &&
        retryCountRef.current < 1
      ) {
        isRetryingRef.current = true;
        retryCountRef.current += 1;
        const delay = API.RETRY_DELAY; // 1 second retry
        
        logger.log(`[DailyBrief] Retrying... (attempt ${retryCountRef.current + 1}/2) in ${delay}ms`);
        
        // Clear any existing retry timeout
        if (retryTimeoutRef.current) {
          clearTimeout(retryTimeoutRef.current);
        }
        retryTimeoutRef.current = setTimeout(() => {
          loadBrief(true);
          retryTimeoutRef.current = null;
        }, delay);
        return; // Don't set loading=false or show alert yet
      }
      
      // Only show error if we're not retrying
      if (!isRetryingRef.current) {
        setLoading(false);
        
        let errorMessage = 'Unable to load your daily brief.';
        let errorTitle = 'Connection Error';
        
        if (error.message?.includes('Network request failed') || error.message?.includes('Failed to fetch') || error.name === 'AbortError') {
          errorTitle = 'Connection Failed';
          errorMessage = 'Cannot connect to the server.\n\nPlease check:\n• Your internet connection\n• Backend server is running\n• Try again in a moment';
        } else if (error.message?.includes('starting up')) {
          errorTitle = 'Service Starting';
          errorMessage = 'The daily brief service is starting up. Please wait a moment and try again.';
        } else if (error.message?.includes('Authentication') || error.message?.includes('401')) {
          errorTitle = 'Authentication Required';
          errorMessage = 'Please log in again to access your daily brief.';
        } else if (error.message?.includes('503')) {
          errorTitle = 'Service Unavailable';
          errorMessage = 'The service is temporarily unavailable. Please try again in a few moments.';
        } else if (error.message?.includes('500')) {
          errorTitle = 'Server Error';
          errorMessage = 'Something went wrong on our end. We\'re working on it!';
        }
        
        Alert.alert(errorTitle, errorMessage, [
          { text: 'Retry', onPress: () => {
            retryCountRef.current = 0;
            isRetryingRef.current = false;
            loadBrief();
          }},
          { text: 'Go Back', style: 'cancel', onPress: () => {
            safeNavigate('home', navigateTo, navigation);
          }}
        ]);
      }
    }
  };

  // Track viewable sections with FlatList
  const onViewableItemsChanged = useRef(({ viewableItems }: any) => {
    const viewed = new Set<string>();
    viewableItems.forEach((item: any) => {
      if (item.item.type && item.item.type !== 'header' && item.item.type !== 'complete') {
        viewed.add(item.item.type);
      }
    });
    if (viewed.size > 0) {
      setSectionsViewed(prev => new Set([...prev, ...viewed]));
    }
  }).current;

  const viewabilityConfig = {
    itemVisiblePercentThreshold: 60, // Mark as viewed when 60% visible
    minimumViewTime: 500, // Must be visible for 500ms
  };

  const handleComplete = async () => {
    if (!brief || completionInProgressRef.current) return;

    try {
      completionInProgressRef.current = true;
      setCompleting(true);
      const timeSpent = Math.floor((Date.now() - startTimeRef.current) / 1000);

      const response = await fetch(`${API_HTTP}/api/daily-brief/complete`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          brief_id: brief.id, // Make idempotent
          time_spent_seconds: timeSpent,
          sections_viewed: Array.from(sectionsViewed),
          lesson_completed: sectionsViewed.has('lesson'),
          action_completed: sectionsViewed.has('action'),
        }),
      });

      if (!response.ok) {
        // If already completed (409), still navigate
        if (response.status === 409) {
          logger.log('Brief already completed');
        } else {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
      }

      const data: DailyBrief = await response.json();

      // Update brief state to mark as completed
      setBrief(prev => prev ? { ...prev, is_completed: true } : null);

      // Clear cache to prevent stale data
      await AsyncStorage.removeItem(CACHE_KEY);

      // Haptic feedback
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);

      // Show achievement celebration if any unlocked
      if (data.achievements_unlocked && data.achievements_unlocked.length > 0) {
        const achievement = data.achievements_unlocked[0];
        setShowAchievement(achievement);
        
        // Animate achievement
        Animated.sequence([
          Animated.spring(achievementScale, {
            toValue: 1,
            useNativeDriver: true,
            tension: 50,
            friction: 7,
          }),
          Animated.delay(2000),
          Animated.timing(achievementScale, {
            toValue: 0,
            duration: 300,
            useNativeDriver: true,
          }),
        ]).start(() => {
          setShowAchievement(null);
          // Use safeGoBack to prevent loop
          safeGoBack(navigateTo, navigation, 'home');
        });
      } else {
        // Use safeGoBack to prevent loop
        safeGoBack(navigateTo, navigation, 'home');
      }
    } catch (error: any) {
      logger.error('Error completing brief:', error);
      let errorMessage = 'Failed to complete daily brief.';
      if (error.message?.includes('Network') || error.message?.includes('Failed to fetch')) {
        errorMessage = 'Connection error. Your progress may not have been saved. Please check your connection and try again.';
      } else if (error.message?.includes('409')) {
        errorMessage = 'This brief has already been completed.';
      } else if (error.message?.includes('401')) {
        errorMessage = 'Please log in again to save your progress.';
      }
      Alert.alert('Error', errorMessage);
      completionInProgressRef.current = false;
    } finally {
      setCompleting(false);
    }
  };

  const handleActionButton = () => {
    switch (brief?.action_type) {
      case 'learn_lesson':
        setLessonExpanded(true);
        markSectionViewed('lesson');
        markSectionViewed('action'); // Also mark action as viewed
        // Scroll to lesson section - it's always index 3 if lesson exists (header=0, market=1, action=2, lesson=3)
        if (scrollTimeoutRef.current) {
          clearTimeout(scrollTimeoutRef.current);
        }
        scrollTimeoutRef.current = setTimeout(() => {
          if (brief?.lesson_title && brief?.lesson_content) {
            flatListRef.current?.scrollToIndex({ index: 3, animated: true });
          }
          scrollTimeoutRef.current = null;
        }, TIMING.ANIMATION_DURATION_SHORT - 100); // 200ms for scroll delay
        break;
      case 'review_portfolio':
        safeNavigate('portfolio', navigateTo, navigation);
        markSectionViewed('action');
        break;
      case 'set_goal':
        safeNavigate('goals', navigateTo, navigation);
        markSectionViewed('action');
        break;
      default:
        markSectionViewed('action');
    }
  };

  const getActionButtonText = () => {
    switch (brief?.action_type) {
      case 'learn_lesson':
        return 'Start 2-Minute Lesson';
      case 'review_portfolio':
        return 'Review My Portfolio';
      case 'set_goal':
        return 'Set a Goal';
      case 'rebalance':
        return 'Check Rebalancing';
      default:
        return 'Take Action';
    }
  };

  const getActionIcon = () => {
    switch (brief?.action_type) {
      case 'learn_lesson':
        return 'book-open';
      case 'review_portfolio':
        return 'trending-up';
      case 'set_goal':
        return 'target';
      case 'rebalance':
        return 'refresh-cw';
      default:
        return 'arrow-right';
    }
  };

  const markSectionViewed = (section: string) => {
    setSectionsViewed(prev => new Set([...prev, section]));
  };

  const handleSnooze = async () => {
    try {
      // Request notification permissions
      const { status } = await Notifications.getPermissionsAsync();
      if (status !== 'granted') {
        const { status: newStatus } = await Notifications.requestPermissionsAsync();
        if (newStatus !== 'granted') {
          Alert.alert('Permission Needed', 'Please enable notifications to use snooze.');
          return;
        }
      }

      // Schedule notification for 1 hour from now
      const oneHourLater = new Date();
      oneHourLater.setHours(oneHourLater.getHours() + 1);

      await Notifications.scheduleNotificationAsync({
        content: {
          title: '📚 Your Daily Brief is ready',
          body: 'Time to check your 2-minute investing guide!',
          data: { type: 'daily_brief_reminder', screen: 'daily-brief' },
          sound: true,
        },
        trigger: {
          date: oneHourLater,
        } as Notifications.DateTriggerInput,
      });

      setSnoozeScheduled(true);
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      
      Alert.alert(
        '⏰ Snoozed',
        'We\'ll remind you in 1 hour!',
        [{ text: 'OK' }]
      );

      // Navigate back to home
      safeNavigate('home', navigateTo, navigation);
    } catch (error) {
      logger.error('Error scheduling snooze:', error);
      Alert.alert('Error', 'Failed to schedule reminder. Please try again.');
    }
  };

  const getAchievementMessage = (achievement: string): string => {
    const messages: Record<string, string> = {
      'streak_3': '🎉 3-Day Streak! You\'re building a great habit!',
      'streak_7': '🔥 7-Day Streak! You\'re on fire!',
      'streak_30': '🏆 30-Day Streak! You\'re a champion!',
      'lessons_10': '📚 10 Lessons Learned! Keep learning!',
      'lessons_25': '📚 25 Lessons Learned! You\'re becoming an expert!',
      'lessons_50': '📚 50 Lessons Learned! Master investor!',
      'first_lesson': '📚 First Lesson Complete! Keep learning!',
      'first_action': '✅ First Action Taken! Great start!',
      'weekly_goal': '🎯 Weekly Goal Achieved! You\'re consistent!',
      'confidence_7': '💪 Confidence Level 7! You\'re getting there!',
      'confidence_9': '🌟 Confidence Level 9! You\'re a pro!',
    };
    return messages[achievement] || `🎉 Achievement Unlocked: ${achievement}`;
  };

  // Calculate safe progress percentage
  const getProgressPercentage = (current: number, goal: number): number => {
    if (!goal || goal <= 0) return 0;
    return Math.min(100, Math.max(0, (current / goal) * 100));
  };

  // buildSections moved to top of component (before conditional returns)

  const renderSection = ({ item }: { item: SectionItem }) => {
    if (!brief) return null;

    switch (item.type) {
      case 'header':
        return (
          <View style={styles.header}>
            <View style={styles.headerTop}>
              <Text style={styles.greeting}>
                {getGreeting()}, {user?.name || 'there'}
              </Text>
            </View>
            <View style={styles.dateRow}>
              <Text style={styles.date}>
                {new Date(brief.date).toLocaleDateString('en-US', { 
                  weekday: 'long', 
                  month: 'long', 
                  day: 'numeric' 
                })}
              </Text>
              <View style={styles.streakContainer}>
                <Text style={{ fontSize: 14, marginRight: 4 }}>🔥</Text>
                <Text style={styles.streakText} numberOfLines={1}>
                  Day {brief.streak}
                </Text>
              </View>
            </View>
          </View>
        );

      case 'market_summary':
        return (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Icon name="trending-up" size={20} color="#667eea" />
              <Text style={styles.sectionTitle}>What's happening in the market today</Text>
            </View>
            <Text style={styles.sectionContent}>{brief.market_summary}</Text>
          </View>
        );

      case 'action':
        return (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Icon name="target" size={20} color="#10B981" />
              <Text style={styles.sectionTitle}>Suggested action for today</Text>
            </View>
            <Text style={styles.sectionContent}>{brief.personalized_action}</Text>
            <TouchableOpacity 
              style={styles.actionButton}
              onPress={handleActionButton}
              activeOpacity={0.8}
            >
              <LinearGradient
                colors={['#10B981', '#059669']}
                style={styles.actionButtonGradient}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 0 }}
              >
                <Icon name={getActionIcon()} size={18} color="#fff" style={{ marginRight: 8 }} />
                <Text style={styles.actionButtonText}>{getActionButtonText()}</Text>
                <Icon name="arrow-right" size={16} color="#fff" style={{ marginLeft: 8 }} />
              </LinearGradient>
            </TouchableOpacity>
          </View>
        );

      case 'lesson':
        if (!brief.lesson_title || !brief.lesson_content) return null;
        
        return (
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Icon name="book-open" size={20} color="#8B5CF6" />
              <Text style={styles.sectionTitle}>Learn something new today</Text>
            </View>
            <TouchableOpacity
              style={styles.viewLibraryButton}
              onPress={() => {
                // Navigate to lesson-library nested under Learn stack
                try {
                  // Try using globalNavigate for nested navigation
                  const { globalNavigate } = require('../../../navigation/NavigationService');
                  globalNavigate('Learn', {
                    screen: 'lesson-library',
                  });
                } catch (error) {
                  // Fallback to navigateTo or direct navigation
                  if (navigateTo) {
                    navigateTo('Learn', { screen: 'lesson-library' } as any);
                  } else if (navigation?.navigate) {
                    (navigation as any).navigate('Learn', { screen: 'lesson-library' });
                  } else {
                    // Last resort: direct navigation
                    safeNavigate('lesson-library', navigateTo, navigation);
                  }
                }
              }}
            >
              <Icon name="book" size={14} color="#8B5CF6" />
              <Text style={styles.viewLibraryText}>View Library</Text>
              <Icon name="arrow-right" size={12} color="#8B5CF6" />
            </TouchableOpacity>
            {lessonExpanded && (
              <>
                <Text style={styles.lessonTitle}>{brief.lesson_title}</Text>
                <Text style={styles.lessonContent}>{brief.lesson_content}</Text>
              </>
            )}
            {!lessonExpanded && (
              <TouchableOpacity 
                style={styles.expandButton}
                onPress={() => {
                  setLessonExpanded(true);
                  markSectionViewed('lesson');
                }}
              >
                <Text style={styles.expandButtonText}>Expand to read lesson</Text>
                <Icon name="chevron-down" size={16} color="#8B5CF6" />
              </TouchableOpacity>
            )}
          </View>
        );

      case 'progress':
        return (
          <View style={styles.progressSection}>
            <View style={styles.progressHeaderRow}>
              <Text style={styles.progressTitle}>Your progress this week</Text>
              <TouchableOpacity
                style={styles.viewFullProgressButton}
                onPress={() => {
                  safeNavigate('streak-progress', navigateTo, navigation);
                }}
              >
                <Text style={styles.viewFullProgressText} numberOfLines={1}>View Full Progress</Text>
                <Icon name="arrow-right" size={12} color="#667eea" />
              </TouchableOpacity>
            </View>
            <View style={styles.progressRow}>
              <View style={styles.progressItem}>
                <Text style={styles.progressLabel}>Daily Briefs</Text>
                <Text style={styles.progressValue}>
                  {brief.weekly_progress.briefs_completed} / {brief.weekly_progress.goal}
                </Text>
                <View style={styles.progressBar}>
                  <View 
                    style={[
                      styles.progressFill,
                      { width: `${getProgressPercentage(brief.weekly_progress.briefs_completed, brief.weekly_progress.goal)}%` }
                    ]} 
                  />
                </View>
              </View>
              <View style={styles.progressItem}>
                <Text style={styles.progressLabel}>Confidence</Text>
                <Text style={styles.progressValue}>{brief.confidence_score}/10</Text>
                <View style={styles.progressBar}>
                  <View 
                    style={[
                      styles.progressFill,
                      { width: `${getProgressPercentage(brief.confidence_score, 10)}%` }
                    ]} 
                  />
                </View>
              </View>
            </View>
          </View>
        );

      case 'complete':
        return (
          <View style={styles.completeSection}>
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
                  <Text style={styles.completeButtonText}>
                    ✅ I'm done for today
                  </Text>
                )}
              </LinearGradient>
            </TouchableOpacity>
            <TouchableOpacity
              style={styles.snoozeButton}
              onPress={handleSnooze}
              disabled={snoozeScheduled}
            >
              <Icon name="clock" size={16} color="#8E8E93" />
              <Text style={styles.snoozeButtonText}>
                {snoozeScheduled ? 'Reminder set' : 'Remind me in 1 hour'}
              </Text>
            </TouchableOpacity>
          </View>
        );

      default:
        return null;
    }
  };

  if (loading && !brief) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#667eea" />
          <Text style={styles.loadingText}>Loading your daily brief...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!brief) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.errorContainer}>
          <Icon name="alert-circle" size={48} color="#FF6B6B" />
          <Text style={styles.errorText}>Failed to load daily brief</Text>
          <TouchableOpacity style={styles.retryButton} onPress={() => {
            retryCountRef.current = 0;
            isRetryingRef.current = false;
            loadBrief();
          }}>
            <Text style={styles.retryButtonText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  // Show onboarding if needed
  if (showOnboarding) {
    return (
      <DailyBriefOnboardingScreen
        onComplete={() => {
          setShowOnboarding(false);
          loadBrief();
        }}
        onSkip={() => {
          setShowOnboarding(false);
          loadBrief();
        }}
      />
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <FlatList
        ref={flatListRef}
        data={sections}
        renderItem={renderSection}
        keyExtractor={(item) => item.id}
        showsVerticalScrollIndicator={false}
        onViewableItemsChanged={onViewableItemsChanged}
        viewabilityConfig={viewabilityConfig}
        contentContainerStyle={styles.listContent}
        onScrollToIndexFailed={(info) => {
          // Fallback if scroll fails
          if (scrollFallbackTimeoutRef.current) {
            clearTimeout(scrollFallbackTimeoutRef.current);
          }
          scrollFallbackTimeoutRef.current = setTimeout(() => {
            flatListRef.current?.scrollToOffset({ offset: info.averageItemLength * info.index, animated: true });
            scrollFallbackTimeoutRef.current = null;
          }, TIMING.NAVIGATION_DELAY * 2); // 100ms for scroll fallback
        }}
      />
      
      {/* Achievement Celebration Overlay */}
      {showAchievement && (
        <Animated.View 
          style={[
            styles.achievementOverlay,
            {
              transform: [{ scale: achievementScale }],
              opacity: achievementScale,
            }
          ]}
        >
          <View style={styles.achievementCard}>
            <Text style={styles.achievementEmoji}>🎉</Text>
            <Text style={styles.achievementTitle}>Achievement Unlocked!</Text>
            <Text style={styles.achievementMessage}>
              {getAchievementMessage(showAchievement)}
            </Text>
          </View>
        </Animated.View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  listContent: {
    paddingBottom: 40,
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
    backgroundColor: '#fff',
    padding: 20,
    paddingTop: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  greeting: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1a1a1a',
  },
  streakContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFF4E6',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 16,
    maxWidth: '100%',
    flexShrink: 1,
  },
  streakText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#FF6B35',
    flexShrink: 1,
  },
  dateRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  date: {
    fontSize: 16,
    color: '#666',
    flex: 1,
  },
  section: {
    backgroundColor: '#fff',
    marginTop: 16,
    padding: 20,
    borderRadius: 12,
    marginHorizontal: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    marginLeft: 8,
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  viewLibraryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: '#F0F0F5',
    marginTop: 8,
    marginBottom: 12,
    gap: 6,
  },
  viewLibraryText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8B5CF6',
  },
  sectionContent: {
    fontSize: 16,
    lineHeight: 24,
    color: '#333',
  },
  lessonTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1a1a1a',
    marginBottom: 12,
  },
  lessonContent: {
    fontSize: 16,
    lineHeight: 24,
    color: '#333',
  },
  actionButton: {
    marginTop: 16,
    borderRadius: 12,
    overflow: 'hidden',
    alignSelf: 'stretch',
    shadowColor: '#10B981',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  actionButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    paddingHorizontal: 24,
  },
  actionButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
    flex: 1,
    textAlign: 'center',
  },
  expandButton: {
    marginTop: 12,
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 8,
  },
  expandButtonText: {
    color: '#8B5CF6',
    fontSize: 16,
    fontWeight: '600',
    marginRight: 8,
  },
  progressSection: {
    backgroundColor: '#fff',
    marginTop: 16,
    padding: 20,
    borderRadius: 12,
    marginHorizontal: 16,
  },
  progressHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
    gap: 8,
  },
  progressTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1a1a1a',
    flex: 1,
    flexShrink: 1,
    marginRight: 8,
  },
  viewFullProgressButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 7,
    paddingHorizontal: 10,
    borderRadius: 8,
    backgroundColor: '#F0F0F5',
    gap: 4,
    flexShrink: 0,
  },
  viewFullProgressText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#667eea',
  },
  progressRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  progressItem: {
    flex: 1,
    marginHorizontal: 8,
  },
  progressLabel: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  progressValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  progressBar: {
    height: 8,
    backgroundColor: '#E5E5EA',
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#667eea',
    borderRadius: 4,
  },
  completeSection: {
    marginTop: 24,
    marginBottom: 40,
    marginHorizontal: 16,
  },
  completeButton: {
    borderRadius: 12,
    overflow: 'hidden',
    marginBottom: 12,
    shadowColor: '#667eea',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  completeButtonGradient: {
    paddingVertical: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  completeButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
  },
  snoozeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    backgroundColor: '#F2F2F7',
  },
  snoozeButtonText: {
    color: '#8E8E93',
    fontSize: 14,
    fontWeight: '500',
    marginLeft: 6,
  },
  achievementOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
  },
  achievementCard: {
    backgroundColor: '#fff',
    borderRadius: 20,
    padding: 32,
    alignItems: 'center',
    maxWidth: '80%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.3,
    shadowRadius: 16,
    elevation: 10,
  },
  achievementEmoji: {
    fontSize: 64,
    marginBottom: 16,
  },
  achievementTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1a1a1a',
    marginBottom: 8,
  },
  achievementMessage: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    lineHeight: 24,
  },
});
