/**
 * Dawn Ritual Component
 * Daily 30-second sunrise animation syncing Yodlee transactions
 * with motivational haikus about wealth and financial growth
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  Dimensions,
  TouchableOpacity,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import * as Haptics from 'expo-haptics';
import Icon from 'react-native-vector-icons/Feather';
import { dawnRitualService } from '../services/DawnRitualService';

// Safe haptics wrapper
const triggerHaptic = (type: 'light' | 'medium' | 'success') => {
  try {
    if (Haptics && Haptics.impactAsync) {
      if (type === 'light') {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      } else if (type === 'medium') {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
      } else if (type === 'success') {
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      }
    }
  } catch (error) {
    // Haptics not available, silently continue
    console.log('[DawnRitual] Haptics not available');
  }
};

const { width, height } = Dimensions.get('window');
const RITUAL_DURATION = 30000; // 30 seconds

interface DawnRitualProps {
  visible: boolean;
  onComplete?: (syncedTransactions: number) => void;
  onSkip?: () => void;
}

export const DawnRitual: React.FC<DawnRitualProps> = ({
  visible,
  onComplete,
  onSkip,
}) => {
  const [phase, setPhase] = useState<'sunrise' | 'syncing' | 'haiku' | 'complete'>('sunrise');
  const [haiku, setHaiku] = useState<string>('');
  const [syncedCount, setSyncedCount] = useState<number>(0);
  const [progress, setProgress] = useState<number>(0);
  
  // Animation values
  const sunY = useRef(new Animated.Value(height + 100)).current;
  const sunOpacity = useRef(new Animated.Value(0)).current;
  const skyGradient = useRef(new Animated.Value(0)).current; // 0 = dark, 1 = light
  const haikuOpacity = useRef(new Animated.Value(0)).current;
  const progressWidth = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (!visible) {
      // Reset on close
      sunY.setValue(height + 100);
      sunOpacity.setValue(0);
      skyGradient.setValue(0);
      haikuOpacity.setValue(0);
      progressWidth.setValue(0);
      setPhase('sunrise');
      setHaiku('');
      setSyncedCount(0);
      setProgress(0);
      return;
    }

    // Start ritual when visible becomes true
    // Use a small delay to ensure component is fully mounted
    const timer = setTimeout(() => {
      startRitual();
    }, 100);

    return () => clearTimeout(timer);
  }, [visible]);

  const startRitual = async () => {
    try {
      // Phase 1: Sunrise Animation (15 seconds)
      setPhase('sunrise');
      triggerHaptic('light');
      
      // Reset sun position to start from bottom
      sunY.setValue(height + 100);
      sunOpacity.setValue(0);
      skyGradient.setValue(0);
      
      // Animate sun rising
      Animated.parallel([
        Animated.timing(sunY, {
          toValue: height * 0.3, // Sun position at top
          duration: 15000,
          useNativeDriver: true,
        }),
        Animated.timing(sunOpacity, {
          toValue: 1,
          duration: 5000,
          useNativeDriver: true,
        }),
        Animated.timing(skyGradient, {
          toValue: 1, // Dark to light
          duration: 15000,
          useNativeDriver: false,
        }),
      ]).start();

      // Phase 2: Sync Transactions (10 seconds)
      await new Promise(resolve => setTimeout(resolve, 15000));
      
      setPhase('syncing');
      triggerHaptic('medium');
      
      // Reset progress bar
      progressWidth.setValue(0);
      
      // Animate progress bar
      Animated.timing(progressWidth, {
        toValue: width * 0.8,
        duration: 10000,
        useNativeDriver: false,
      }).start();

      // Sync transactions and get haiku
      const result = await dawnRitualService.performDawnRitual();
      setSyncedCount(result.transactionsSynced);
      setHaiku(result.haiku);
      
      // Phase 3: Show Haiku (5 seconds)
      await new Promise(resolve => setTimeout(resolve, 10000));
      
      setPhase('haiku');
      triggerHaptic('success');
      
      haikuOpacity.setValue(0);
      Animated.timing(haikuOpacity, {
        toValue: 1,
        duration: 1000,
        useNativeDriver: true,
      }).start();

      // Phase 4: Complete
      await new Promise(resolve => setTimeout(resolve, 5000));
      
      setPhase('complete');
      if (onComplete) {
        onComplete(result.transactionsSynced);
      }
    } catch (error) {
      console.error('[DawnRitual] Error:', error);
      // Still complete even if sync fails
      if (onComplete) {
        onComplete(0);
      }
    }
  };

  // Removed unused skyColors interpolation

  if (!visible) return null;

  return (
    <View style={styles.container}>
      {/* Sky Gradient Background - Always visible dark background */}
      <View style={styles.skyContainer}>
        <LinearGradient
          colors={['#0a0a1a', '#1a1a3a', '#2a2a5a']}
          style={StyleSheet.absoluteFill}
          start={{ x: 0, y: 0 }}
          end={{ x: 0, y: 1 }}
        />
      </View>

      {/* Sunrise Gradient Overlay - Animated opacity */}
      <Animated.View
        style={[
          styles.sunriseOverlay,
          {
            opacity: skyGradient,
          },
        ]}
      >
        <LinearGradient
          colors={['#ff6b6b', '#ffa500', '#ffd700', '#87ceeb']}
          style={StyleSheet.absoluteFill}
          start={{ x: 0, y: 1 }}
          end={{ x: 0, y: 0 }}
        />
      </Animated.View>

      {/* Sun */}
      <Animated.View
        style={[
          styles.sun,
          {
            transform: [{ translateY: sunY }],
            opacity: sunOpacity,
          },
        ]}
      >
        <View style={styles.sunCore} />
        <View style={styles.sunGlow} />
      </Animated.View>

      {/* Content Overlay */}
      <View style={styles.contentContainer}>
        {phase === 'sunrise' && (
          <View style={styles.phaseContainer}>
            <Text style={styles.phaseTitle}>Dawn Ritual</Text>
            <Text style={styles.phaseSubtitle}>Awakening your wealth</Text>
          </View>
        )}

        {phase === 'syncing' && (
          <View style={styles.phaseContainer}>
            <Icon name="refresh-cw" size={48} color="#FFFFFF" />
            <Text style={styles.phaseTitle}>Syncing Transactions</Text>
            <Text style={styles.phaseSubtitle}>Connecting to your accounts...</Text>
            <View style={styles.progressBarContainer}>
              <Animated.View
                style={[
                  styles.progressBar,
                  {
                    width: progressWidth,
                  },
                ]}
              />
            </View>
          </View>
        )}

        {phase === 'haiku' && haiku && (
          <Animated.View
            style={[
              styles.haikuContainer,
              {
                opacity: haikuOpacity,
              },
            ]}
          >
            <Text style={styles.haikuText}>{haiku}</Text>
            {syncedCount > 0 && (
              <Text style={styles.syncCount}>
                {syncedCount} transaction{syncedCount !== 1 ? 's' : ''} synced
              </Text>
            )}
          </Animated.View>
        )}

        {phase === 'complete' && (
          <View style={styles.phaseContainer}>
            <Icon name="check-circle" size={64} color="#34C759" />
            <Text style={styles.phaseTitle}>Ritual Complete</Text>
            <Text style={styles.phaseSubtitle}>Your wealth awakens</Text>
          </View>
        )}

        {/* Skip Button */}
        {phase !== 'complete' && (
          <TouchableOpacity
            style={styles.skipButton}
            onPress={onSkip}
          >
            <Text style={styles.skipText}>Skip</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#0a0a1a',
  },
  skyContainer: {
    ...StyleSheet.absoluteFillObject,
  },
  sunriseOverlay: {
    ...StyleSheet.absoluteFillObject,
  },
  sun: {
    position: 'absolute',
    left: width / 2 - 50,
    width: 100,
    height: 100,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sunCore: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#ffd700',
    shadowColor: '#ffd700',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 1,
    shadowRadius: 30,
    elevation: 10,
  },
  sunGlow: {
    position: 'absolute',
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: '#ffa500',
    opacity: 0.5,
  },
  contentContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  phaseContainer: {
    alignItems: 'center',
    gap: 16,
  },
  phaseTitle: {
    fontSize: 32,
    fontWeight: '700',
    color: '#FFFFFF',
    textAlign: 'center',
    textShadowColor: 'rgba(0, 0, 0, 0.5)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  phaseSubtitle: {
    fontSize: 18,
    color: '#FFFFFF',
    opacity: 0.9,
    textAlign: 'center',
  },
  progressBarContainer: {
    width: width * 0.8,
    height: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    borderRadius: 2,
    marginTop: 20,
    overflow: 'hidden',
  },
  progressBar: {
    height: '100%',
    backgroundColor: '#34C759',
    borderRadius: 2,
  },
  haikuContainer: {
    alignItems: 'center',
    padding: 32,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    borderRadius: 20,
    maxWidth: width * 0.9,
  },
  haikuText: {
    fontSize: 24,
    fontWeight: '600',
    color: '#FFFFFF',
    textAlign: 'center',
    lineHeight: 36,
    fontStyle: 'italic',
    textShadowColor: 'rgba(0, 0, 0, 0.8)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  syncCount: {
    fontSize: 14,
    color: '#FFFFFF',
    opacity: 0.7,
    marginTop: 16,
  },
  skipButton: {
    position: 'absolute',
    top: 60,
    right: 20,
    padding: 12,
  },
  skipText: {
    color: '#FFFFFF',
    opacity: 0.7,
    fontSize: 16,
  },
});

