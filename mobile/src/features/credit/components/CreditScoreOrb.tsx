/**
 * Credit Score Orb Component
 * Visual representation of credit score (similar to Constellation Orb)
 */

import React, { useEffect, useMemo, useCallback } from 'react';
import { View, Text, StyleSheet, Pressable, Platform } from 'react-native';
// CRITICAL: Import Animated from Reanimated, not react-native
import Animated, {
  useAnimatedStyle,
  useSharedValue,
  withSpring,
  withTiming,
  withRepeat,
  runOnJS,
} from 'react-native-reanimated';
import * as Haptics from 'expo-haptics';
import { CreditScore, CreditProjection } from '../types/CreditTypes';

// Polyfill structuredClone for React Native (if not available)
if (typeof structuredClone === 'undefined') {
  (global as any).structuredClone = (obj: any) => {
    try {
      return JSON.parse(JSON.stringify(obj));
    } catch {
      // Fallback for non-serializable objects
      return obj ? { ...obj } : obj;
    }
  };
}

// Helper to safely clone objects (handles frozen objects)
const safeClone = <T,>(obj: T | null | undefined): T | null => {
  if (!obj) return null;
  try {
    // Check if frozen
    if (Object.isFrozen(obj)) {
      return structuredClone(obj) as T;
    }
    // Check if it's a plain object that needs cloning
    if (typeof obj === 'object' && obj.constructor === Object) {
      return { ...obj } as T;
    }
    return obj;
  } catch (error) {
    console.warn('[CreditScoreOrb] Clone failed, using fallback:', error);
    // Last resort: try JSON roundtrip
    try {
      return JSON.parse(JSON.stringify(obj)) as T;
    } catch {
      return obj;
    }
  }
};

interface CreditScoreOrbProps {
  score?: CreditScore | null;
  projection?: CreditProjection;
  size?: number;
}

const ORB_SIZE = 120;
const ORB_CENTER = ORB_SIZE / 2;

// Default fallback score object
const DEFAULT_SCORE: CreditScore = {
  score: 580,
  scoreRange: 'Fair',
  lastUpdated: new Date().toISOString(),
  provider: 'self_reported',
};

// Internal component that receives normalized, non-frozen props
// IMPORTANT: NO REFS - use shared values for all mutable state to avoid worklet freeze
// This component receives ONLY primitive values to avoid any frozen object access
const CreditScoreOrbInternal: React.FC<{
  scoreValue: number;
  scoreRange: string;
  projectionGain?: number;
  size: number;
}> = ({ scoreValue, scoreRange, projectionGain, size }) => {
  // All values are already extracted as primitives - no frozen object access
  const validScore = scoreValue;
  const validScoreRange = scoreRange;
  const projectionValue = projectionGain ?? 0;
  
  // Create shared values LOCALLY - NO REFS - prevents Reanimated from capturing frozen objects
  // Use shared values for ALL mutable state (replaces refs)
  const orbScale = useSharedValue(1);
  const orbOpacity = useSharedValue(1);
  const animatedScoreValue = useSharedValue(validScore);
  const pulseAnim = useSharedValue(1);
  const isFocused = useSharedValue(0); // Replaces ref.current for focus state

  // Guarded animation setter - uses runOnJS for cross-thread safety
  const safeSetScoreValue = useCallback((value: number) => {
    try {
      animatedScoreValue.value = withSpring(value, {
        damping: 15,
        stiffness: 100,
      });
    } catch (error) {
      console.warn('[CreditScoreOrb] Reanimated mutation guarded:', error);
      // Fallback: set directly without animation
      try {
        animatedScoreValue.value = value;
      } catch {
        // Ignore - component will use static value
      }
    }
  }, [animatedScoreValue]);

  // Guarded pulse setter - NO REFS
  const safeSetPulse = useCallback(() => {
    try {
      pulseAnim.value = withRepeat(
        withTiming(1.1, { duration: 2000 }),
        -1,
        true
      );
    } catch (error) {
      console.warn('[CreditScoreOrb] Pulse animation guarded:', error);
      // Fallback: static pulse
      try {
        pulseAnim.value = 1;
      } catch {
        // Ignore
      }
    }
  }, [pulseAnim]);

  // Tap handler - uses runOnJS, NO REFS
  const handleTap = useCallback(() => {
    // Use runOnJS for haptics (cross-thread safety)
    runOnJS(() => {
      try {
        Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
      } catch {
        // Ignore haptics errors
      }
    })();
    
    // Bounce animation - no ref needed
    try {
      orbScale.value = withTiming(1.1, { duration: 200 }, () => {
        orbScale.value = withTiming(1, { duration: 200 });
      });
      // Focus glow
      isFocused.value = withTiming(1, { duration: 100 }, () => {
        isFocused.value = withTiming(0, { duration: 300 });
      });
    } catch (error) {
      console.warn('[CreditScoreOrb] Tap animation guarded:', error);
    }
  }, [orbScale, isFocused]);

  // Animate score change - use guarded setter
  useEffect(() => {
    safeSetScoreValue(validScore);
  }, [validScore, safeSetScoreValue]);

  // Pulse animation - use guarded setter (runs once on mount)
  useEffect(() => {
    safeSetPulse();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run once - pulse is infinite
  
  // Get color based on score range
  const getScoreColor = (range: string): string => {
    switch (range) {
      case 'Excellent':
        return '#34C759'; // Green
      case 'Very Good':
        return '#5AC8FA'; // Light blue
      case 'Good':
        return '#007AFF'; // Blue
      case 'Fair':
        return '#FF9500'; // Orange
      case 'Poor':
        return '#FF3B30'; // Red
      default:
        return '#8E8E93'; // Gray
    }
  };

  const orbColor = getScoreColor(validScoreRange);

  const orbStyle = useAnimatedStyle(() => {
    // NO REFS in worklet - use shared values only
    // Add focus glow effect via shared value
    const focusGlow = 1 + (isFocused.value * 0.05);
    return {
      width: size,
      height: size,
      borderRadius: size / 2,
      backgroundColor: orbColor,
      opacity: orbOpacity.value * 0.8,
      transform: [
        { scale: orbScale.value * pulseAnim.value * focusGlow },
      ],
    };
  }, [size, orbColor]); // Only depend on static values

  const scoreTextStyle = useAnimatedStyle(() => {
    return {
      opacity: orbOpacity.value,
    };
  });

  const projectedScore = projectionValue > 0
    ? validScore + projectionValue
    : validScore;

  return (
    <View style={styles.container}>
      <Pressable onPress={handleTap} style={{ width: size, height: size }}>
        <Animated.View style={[styles.orb, orbStyle]}>
          <Animated.View style={[styles.scoreContainer, scoreTextStyle]}>
            <Text style={styles.currentScore}>{validScore}</Text>
            {projectionValue > 0 && (
              <Text style={styles.projectedScore}>
                → {projectedScore}
              </Text>
            )}
          </Animated.View>
        </Animated.View>
      </Pressable>
      <Text style={[styles.scoreRange, { color: orbColor }]}>
        {validScoreRange}
      </Text>
      {projectionValue > 0 && (
        <Text style={styles.projectionText}>
          +{projectionValue} in 6 months
        </Text>
      )}
    </View>
  );
};

// Public component that normalizes props before passing to internal component
export const CreditScoreOrb: React.FC<CreditScoreOrbProps> = (props) => {
  // Extract ALL primitive values immediately - before any hooks or component rendering
  // This completely isolates us from frozen props
  const normalizedValues = useMemo(() => {
    try {
      // Safely extract score value
      let scoreValue = 580;
      let scoreRange = 'Fair';
      
      const scoreProp = props.score;
      if (scoreProp && typeof scoreProp === 'object') {
        // Try to access score property - use try-catch in case it's frozen
        try {
          scoreValue = typeof scoreProp.score === 'number' ? scoreProp.score : 580;
          scoreRange = (scoreProp.scoreRange as any) || 'Fair';
        } catch (e) {
          // If access fails, use defaults
          console.warn('[CreditScoreOrb] Could not access score prop, using defaults');
        }
      }
      
      // Safely extract projection value
      let projectionGain = 0;
      const projectionProp = props.projection;
      if (projectionProp && typeof projectionProp === 'object') {
        try {
          projectionGain = typeof projectionProp.scoreGain6m === 'number' ? projectionProp.scoreGain6m : 0;
        } catch (e) {
          // If access fails, use default
          console.warn('[CreditScoreOrb] Could not access projection prop, using defaults');
        }
      }
      
      return {
        scoreValue,
        scoreRange,
        projectionGain,
        size: props.size || ORB_SIZE,
      };
    } catch (error) {
      console.warn('[CreditScoreOrb] Error extracting values:', error);
      // Return safe defaults on error
      return {
        scoreValue: 580,
        scoreRange: 'Fair',
        projectionGain: 0,
        size: props.size || ORB_SIZE,
      };
    }
  }, [
    // Use primitive values for dependencies - extract them safely
    // We'll use JSON.stringify to create stable keys without accessing frozen objects
    props.score ? (() => {
      try {
        const s = props.score;
        return s && typeof s === 'object' && 'score' in s ? String(s.score) : '580';
      } catch {
        return '580';
      }
    })() : '580',
    props.projection ? (() => {
      try {
        const p = props.projection;
        return p && typeof p === 'object' && 'scoreGain6m' in p ? String(p.scoreGain6m) : '0';
      } catch {
        return '0';
      }
    })() : '0',
    props.size,
  ]);
  
  return (
    <CreditScoreOrbInternal
      scoreValue={normalizedValues.scoreValue}
      scoreRange={normalizedValues.scoreRange}
      projectionGain={normalizedValues.projectionGain}
      size={normalizedValues.size}
    />
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  orb: {
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  scoreContainer: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  currentScore: {
    fontSize: 32,
    fontWeight: '700',
    color: '#FFFFFF',
    textShadowColor: 'rgba(0, 0, 0, 0.3)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  projectedScore: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    opacity: 0.9,
    marginTop: 4,
  },
  scoreRange: {
    fontSize: 18,
    fontWeight: '600',
    marginTop: 12,
    textTransform: 'capitalize',
  },
  projectionText: {
    fontSize: 14,
    color: '#8E8E93',
    marginTop: 4,
  },
});

