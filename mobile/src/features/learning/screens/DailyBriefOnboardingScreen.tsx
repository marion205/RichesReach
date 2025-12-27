/**
 * Daily Brief Onboarding Screen
 * Introduces users to the Daily Brief feature and sets expectations
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  SafeAreaView,
  Animated,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import Icon from 'react-native-vector-icons/Feather';
import * as Haptics from 'expo-haptics';
import AsyncStorage from '@react-native-async-storage/async-storage';

const { width } = Dimensions.get('window');

const DAILY_BRIEF_ONBOARDING_KEY = 'dailyBriefOnboardingCompleted';

interface DailyBriefOnboardingScreenProps {
  onComplete: () => void;
  onSkip?: () => void;
}

const steps = [
  {
    id: 'welcome',
    emoji: '📚',
    title: 'Your Daily Brief',
    subtitle: 'Your 2-minute investing guide',
    description: 'Get plain-English market updates, personalized actions, and quick lessons—all in under 2 minutes.',
    color: '#667eea',
  },
  {
    id: 'benefits',
    emoji: '✨',
    title: 'Why Daily Brief?',
    subtitle: 'Build confidence, build habits',
    description: '• Understand markets in plain English\n• Get personalized actions for your portfolio\n• Learn something new every day\n• Track your progress and streaks',
    color: '#10B981',
  },
  {
    id: 'commitment',
    emoji: '🔥',
    title: 'Make it a habit',
    subtitle: 'Just 2 minutes a day',
    description: 'We\'ll send you a gentle reminder each morning. Complete your brief to keep your streak going and watch your confidence grow!',
    color: '#FF6B35',
  },
];

export default function DailyBriefOnboardingScreen({ 
  onComplete, 
  onSkip 
}: DailyBriefOnboardingScreenProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const fadeAnim = useRef(new Animated.Value(1)).current;
  const slideAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Animate entrance
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 400,
        useNativeDriver: true,
      }),
      Animated.spring(slideAnim, {
        toValue: 0,
        tension: 50,
        friction: 7,
        useNativeDriver: true,
      }),
    ]).start();
  }, [currentStep]);

  const handleNext = async () => {
    if (currentStep < steps.length - 1) {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      setCurrentStep(currentStep + 1);
    } else {
      await handleComplete();
    }
  };

  const handleBack = async () => {
    if (currentStep > 0) {
      await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = async () => {
    try {
      await AsyncStorage.setItem(DAILY_BRIEF_ONBOARDING_KEY, 'true');
      await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      onComplete();
    } catch (error) {
      console.error('Error saving onboarding completion:', error);
      onComplete(); // Still complete even if storage fails
    }
  };

  const handleSkip = async () => {
    try {
      await AsyncStorage.setItem(DAILY_BRIEF_ONBOARDING_KEY, 'true');
      if (onSkip) {
        onSkip();
      } else {
        onComplete();
      }
    } catch (error) {
      console.error('Error saving onboarding skip:', error);
      if (onSkip) {
        onSkip();
      } else {
        onComplete();
      }
    }
  };

  const currentStepData = steps[currentStep];
  const progress = ((currentStep + 1) / steps.length) * 100;

  return (
    <SafeAreaView style={styles.container}>
      <LinearGradient
        colors={[currentStepData.color, `${currentStepData.color}CC`]}
        style={styles.gradient}
      >
        {/* Skip button */}
        {onSkip && (
          <TouchableOpacity 
            style={styles.skipButton}
            onPress={handleSkip}
          >
            <Text style={styles.skipButtonText}>Skip</Text>
          </TouchableOpacity>
        )}

        {/* Progress bar */}
        <View style={styles.progressContainer}>
          <View style={styles.progressBar}>
            <Animated.View 
              style={[
                styles.progressFill,
                { width: `${progress}%` }
              ]}
            />
          </View>
          <Text style={styles.progressText}>
            {currentStep + 1} of {steps.length}
          </Text>
        </View>

        {/* Content */}
        <Animated.View 
          style={[
            styles.content,
            {
              opacity: fadeAnim,
              transform: [{ translateX: slideAnim }],
            }
          ]}
        >
          <View style={styles.emojiContainer}>
            <Text style={styles.emoji}>{currentStepData.emoji}</Text>
          </View>

          <Text style={styles.title}>{currentStepData.title}</Text>
          <Text style={styles.subtitle}>{currentStepData.subtitle}</Text>
          <Text style={styles.description}>{currentStepData.description}</Text>
        </Animated.View>

        {/* Navigation buttons */}
        <View style={styles.navigation}>
          {currentStep > 0 && (
            <TouchableOpacity 
              style={styles.backButton}
              onPress={handleBack}
            >
              <Icon name="arrow-left" size={20} color="#666" />
              <Text style={styles.backButtonText}>Back</Text>
            </TouchableOpacity>
          )}
          
          <TouchableOpacity 
            style={styles.nextButton}
            onPress={handleNext}
          >
            <LinearGradient
              colors={[currentStepData.color, `${currentStepData.color}DD`]}
              style={styles.nextButtonGradient}
            >
              <Text style={styles.nextButtonText}>
                {currentStep === steps.length - 1 ? 'Get Started' : 'Next'}
              </Text>
              <Icon name="arrow-right" size={20} color="#fff" />
            </LinearGradient>
          </TouchableOpacity>
        </View>
      </LinearGradient>
    </SafeAreaView>
  );
}

// Static method to check if onboarding is completed
export const isDailyBriefOnboardingCompleted = async (): Promise<boolean> => {
  try {
    const completed = await AsyncStorage.getItem(DAILY_BRIEF_ONBOARDING_KEY);
    return completed === 'true';
  } catch (error) {
    console.error('Error checking onboarding status:', error);
    return false;
  }
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    flex: 1,
    padding: 24,
    paddingTop: 60,
  },
  skipButton: {
    alignSelf: 'flex-end',
    padding: 8,
    marginBottom: 24,
  },
  skipButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '500',
    opacity: 0.9,
  },
  progressContainer: {
    marginBottom: 40,
  },
  progressBar: {
    height: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    borderRadius: 2,
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#fff',
    borderRadius: 2,
  },
  progressText: {
    color: '#fff',
    fontSize: 12,
    textAlign: 'right',
    opacity: 0.8,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  emojiContainer: {
    marginBottom: 32,
  },
  emoji: {
    fontSize: 80,
  },
  title: {
    fontSize: 32,
    fontWeight: '700',
    color: '#fff',
    textAlign: 'center',
    marginBottom: 12,
  },
  subtitle: {
    fontSize: 20,
    fontWeight: '500',
    color: '#fff',
    textAlign: 'center',
    marginBottom: 24,
    opacity: 0.9,
  },
  description: {
    fontSize: 18,
    lineHeight: 28,
    color: '#fff',
    textAlign: 'center',
    opacity: 0.95,
    paddingHorizontal: 20,
  },
  navigation: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 40,
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 12,
  },
  backButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  nextButton: {
    flex: 1,
    marginLeft: 12,
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
  },
  nextButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    paddingHorizontal: 24,
  },
  nextButtonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '700',
    marginRight: 8,
  },
});

