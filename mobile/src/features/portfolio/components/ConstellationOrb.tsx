/**
 * ConstellationOrb Component
 * Jobs-inspired minimalist wealth visualization
 * - Core Orb: Total net worth
 * - Satellites: Cash flow (shooting stars), Portfolio positions (starry cluster)
 * - Gestures: Tap → Life event petals, Swipe → What-if simulator, Pinch → Zoom
 */

import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  TouchableOpacity,
} from 'react-native';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withSpring,
  withRepeat,
  withTiming,
  interpolate,
  Extrapolate,
  runOnJS,
  withSequence,
} from 'react-native-reanimated';
import {
  GestureDetector,
  Gesture,
  GestureHandlerRootView,
} from 'react-native-gesture-handler';
import * as Haptics from 'expo-haptics';
import Icon from 'react-native-vector-icons/Feather';
import { MoneySnapshot } from '../services/MoneySnapshotService';
import { gestureAnalyticsService } from '../services/GestureAnalyticsService';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const ORB_SIZE = Math.min(SCREEN_WIDTH * 0.7, 280);
const ORB_CENTER = ORB_SIZE / 2;

interface ConstellationOrbProps {
  snapshot: MoneySnapshot;
  onTap?: () => void; // Show life event petals
  onDoubleTap?: () => void; // Quick actions menu
  onLongPress?: () => void; // Detailed breakdown
  onSwipeLeft?: () => void; // Market crash shield
  onSwipeRight?: () => void; // Growth projection
  onPinch?: () => void; // What-if simulator
  // Direct modal control (optional - for parent to manage)
  showLifeEvents?: boolean;
  showShield?: boolean;
  showGrowth?: boolean;
  showWhatIf?: boolean;
  onCloseLifeEvents?: () => void;
  onCloseShield?: () => void;
  onCloseGrowth?: () => void;
  onCloseWhatIf?: () => void;
}

export const ConstellationOrb: React.FC<ConstellationOrbProps> = ({
  snapshot,
  onTap,
  onDoubleTap,
  onLongPress,
  onSwipeLeft,
  onSwipeRight,
  onPinch,
}) => {
  // Core orb animation (pulsing)
  const orbScale = useSharedValue(1);
  const orbOpacity = useSharedValue(0.9);
  const orbRotation = useSharedValue(0);
  const glowIntensity = useSharedValue(0.3);
  
  // Satellite positions (cash flow and positions)
  const satellite1Angle = useSharedValue(0);
  const satellite2Angle = useSharedValue(120);
  const satellite3Angle = useSharedValue(240);
  
  // Gesture feedback animations
  const feedbackScale = useSharedValue(1);
  const feedbackOpacity = useSharedValue(1);

  // Helper functions defined outside worklet context
  const triggerHapticJS = async (type: 'light' | 'medium' | 'heavy' | 'success' | 'warning') => {
    try {
      switch (type) {
        case 'light':
          await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          break;
        case 'medium':
          await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
          break;
        case 'heavy':
          await Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy);
          break;
        case 'success':
          await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
          break;
        case 'warning':
          await Haptics.notificationAsync(Haptics.NotificationFeedbackType.Warning);
          break;
      }
    } catch (error) {
      // Silently fail if haptics not available
    }
  };

  // Capture snapshot values outside worklet context
  const snapshotData = {
    netWorth: snapshot?.netWorth ?? 0,
    hasPositions: (snapshot?.positions?.length ?? 0) > 0,
    cashflowDelta: snapshot?.cashflow?.delta ?? 0,
  };

  const trackGestureJS = (
    gesture: 'tap' | 'double_tap' | 'long_press' | 'swipe_left' | 'swipe_right' | 'pinch',
    data: { netWorth: number; hasPositions: boolean; cashflowDelta: number }
  ) => {
    gestureAnalyticsService.trackGesture(gesture, data);
  };

  // Worklet-safe wrappers
  const triggerHaptic = (type: 'light' | 'medium' | 'heavy' | 'success' | 'warning') => {
    'worklet';
    runOnJS(triggerHapticJS)(type);
  };

  const trackGesture = (gesture: 'tap' | 'double_tap' | 'long_press' | 'swipe_left' | 'swipe_right' | 'pinch') => {
    'worklet';
    // Pass captured data, not snapshot directly
    runOnJS(trackGestureJS)(gesture, snapshotData);
  };

  // Gesture feedback animation
  const triggerFeedbackAnimation = () => {
    'worklet';
    feedbackScale.value = withSequence(
      withSpring(1.1, { damping: 10, stiffness: 300 }),
      withSpring(1, { damping: 10, stiffness: 300 })
    );
    feedbackOpacity.value = withSequence(
      withTiming(0.7, { duration: 100 }),
      withTiming(1, { duration: 200 })
    );
  };

  // Initialize animations
  useEffect(() => {
    // Enhanced pulsing orb animation with rotation
    orbScale.value = withRepeat(
      withSpring(1.05, { damping: 8, stiffness: 100 }),
      -1,
      true
    );
    
    orbOpacity.value = withRepeat(
      withTiming(1, { duration: 2000 }),
      -1,
      true
    );

    // Subtle rotation for depth
    orbRotation.value = withRepeat(
      withTiming(360, { duration: 60000 }),
      -1,
      false
    );

    // Glow intensity animation
    glowIntensity.value = withRepeat(
      withTiming(0.5, { duration: 3000 }),
      -1,
      true
    );

    // Rotating satellites
    satellite1Angle.value = withRepeat(
      withTiming(360, { duration: 20000 }),
      -1,
      false
    );
    satellite2Angle.value = withRepeat(
      withTiming(360, { duration: 25000 }),
      -1,
      false
    );
    satellite3Angle.value = withRepeat(
      withTiming(360, { duration: 30000 }),
      -1,
      false
    );
  }, []);

  // Core orb animated style with enhanced effects
  const orbStyle = useAnimatedStyle(() => {
    return {
      transform: [
        { scale: orbScale.value * feedbackScale.value },
        { rotate: `${orbRotation.value}deg` },
      ],
      opacity: orbOpacity.value * feedbackOpacity.value,
    };
  });

  // Counter-rotation for inner content (keeps text upright)
  const innerContentStyle = useAnimatedStyle(() => {
    return {
      transform: [
        { rotate: `${-orbRotation.value}deg` }, // Counter-rotate to keep text upright
      ],
    };
  });

  // Glow effect style
  const glowStyle = useAnimatedStyle(() => {
    return {
      shadowOpacity: glowIntensity.value,
      shadowRadius: 20 + glowIntensity.value * 10,
    };
  });

  // Calculate satellite positions (cash flow indicators)
  const getSatellitePosition = (angle: Animated.SharedValue<number>, radius: number) => {
    return useAnimatedStyle(() => {
      const rad = (angle.value * Math.PI) / 180;
      const x = ORB_CENTER + radius * Math.cos(rad) - 8; // -8 for center of satellite
      const y = ORB_CENTER + radius * Math.sin(rad) - 8;
      
      return {
        position: 'absolute',
        left: x,
        top: y,
      };
    });
  };

  const satellite1Style = getSatellitePosition(satellite1Angle, ORB_SIZE * 0.4);
  const satellite2Style = getSatellitePosition(satellite2Angle, ORB_SIZE * 0.45);
  const satellite3Style = getSatellitePosition(satellite3Angle, ORB_SIZE * 0.5);

  // Gesture handlers with haptics and analytics
  const tapGesture = Gesture.Tap()
    .numberOfTaps(1)
    .onEnd(() => {
      'worklet';
      triggerFeedbackAnimation();
      triggerHaptic('light');
      trackGesture('tap');
      if (onTap) {
        const callback = onTap;
        runOnJS(callback)();
      }
    });

  const doubleTapGesture = Gesture.Tap()
    .numberOfTaps(2)
    .onEnd(() => {
      'worklet';
      triggerFeedbackAnimation();
      triggerHaptic('medium');
      trackGesture('double_tap');
      if (onDoubleTap) {
        const callback = onDoubleTap;
        runOnJS(callback)();
      }
    });

  const longPressGesture = Gesture.LongPress()
    .minDuration(500)
    .onStart(() => {
      'worklet';
      triggerFeedbackAnimation();
      triggerHaptic('heavy');
      trackGesture('long_press');
      if (onLongPress) {
        const callback = onLongPress;
        runOnJS(callback)();
      }
    });

  const panGesture = Gesture.Pan()
    .onEnd((e) => {
      'worklet';
      if (e.translationX < -50 && onSwipeLeft) {
        triggerFeedbackAnimation();
        triggerHaptic('medium');
        trackGesture('swipe_left');
        const callback = onSwipeLeft;
        runOnJS(callback)();
      } else if (e.translationX > 50 && onSwipeRight) {
        triggerFeedbackAnimation();
        triggerHaptic('medium');
        trackGesture('swipe_right');
        const callback = onSwipeRight;
        runOnJS(callback)();
      }
    });

  const pinchGesture = Gesture.Pinch()
    .onEnd(() => {
      'worklet';
      triggerFeedbackAnimation();
      triggerHaptic('success');
      trackGesture('pinch');
      if (onPinch) {
        const callback = onPinch;
        runOnJS(callback)();
      }
    });

  // Compose gestures with proper priority
  const composedGesture = Gesture.Race(
    doubleTapGesture,
    longPressGesture,
    Gesture.Simultaneous(
      tapGesture,
      panGesture,
      pinchGesture
    )
  );

  // Format currency
  const formatCurrency = (amount: number) => {
    if (amount >= 1000000) {
      return `$${(amount / 1000000).toFixed(2)}M`;
    } else if (amount >= 1000) {
      return `$${(amount / 1000).toFixed(1)}K`;
    }
    return `$${amount.toFixed(0)}`;
  };

  // Cash flow indicator color (with safety checks)
  const cashflowDelta = snapshot?.cashflow?.delta ?? 0;
  const cashflowColor = cashflowDelta >= 0 ? '#34C759' : '#FF3B30';
  const cashflowIcon = cashflowDelta >= 0 ? 'arrow-up' : 'arrow-down';
  const netWorth = snapshot?.netWorth ?? 0;
  const positions = snapshot?.positions ?? [];

  return (
    <GestureHandlerRootView style={styles.container}>
      <GestureDetector gesture={composedGesture}>
        <View style={styles.orbContainer}>
          {/* Core Orb - Net Worth */}
          <Animated.View style={[styles.coreOrb, orbStyle, glowStyle]}>
            <Animated.View style={[styles.orbInner, innerContentStyle]}>
              <Text style={styles.netWorthLabel}>Net Worth</Text>
              <Text style={styles.netWorthValue}>
                {formatCurrency(netWorth)}
              </Text>
              
              {/* Cash Flow Indicator */}
              <View style={styles.cashflowIndicator}>
                <Icon name={cashflowIcon} size={14} color={cashflowColor} />
                <Text style={[styles.cashflowText, { color: cashflowColor }]}>
                  {formatCurrency(Math.abs(cashflowDelta))} this month
                </Text>
              </View>
            </Animated.View>
          </Animated.View>

          {/* Satellites - Cash Flow (shooting stars) */}
          {cashflowDelta !== 0 && (
            <>
              <Animated.View style={[styles.satellite, satellite1Style]}>
                <View style={[
                  styles.satelliteDot,
                  { backgroundColor: cashflowColor }
                ]} />
              </Animated.View>
              <Animated.View style={[styles.satellite, satellite2Style]}>
                <View style={[
                  styles.satelliteDot,
                  { backgroundColor: cashflowColor, opacity: 0.7 }
                ]} />
              </Animated.View>
            </>
          )}

          {/* Satellites - Portfolio Positions (starry cluster) */}
          {positions.slice(0, 3).map((position, index) => {
            const angle = (index * 120) + 60; // Distribute around orb
            const radius = ORB_SIZE * 0.35;
            const rad = (angle * Math.PI) / 180;
            const x = ORB_CENTER + radius * Math.cos(rad) - 6;
            const y = ORB_CENTER + radius * Math.sin(rad) - 6;

            return (
              <View
                key={position.symbol}
                style={[
                  styles.positionSatellite,
                  {
                    left: x,
                    top: y,
                  },
                ]}
              >
                <View style={styles.positionDot} />
                <Text style={styles.positionSymbol}>{position.symbol}</Text>
              </View>
            );
          })}

        </View>
      </GestureDetector>
      {/* Gesture Hint (subtle) - Outside orbContainer to avoid clipping */}
      <View style={styles.gestureHint}>
        <Text style={styles.gestureHintText} numberOfLines={1} adjustsFontSizeToFit>
          Tap • Double tap • Long press • Swipe • Pinch
        </Text>
      </View>
    </GestureHandlerRootView>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 24,
  },
  orbContainer: {
    width: ORB_SIZE,
    height: ORB_SIZE,
    position: 'relative',
    alignItems: 'center',
    justifyContent: 'center',
  },
  coreOrb: {
    width: ORB_SIZE,
    height: ORB_SIZE,
    borderRadius: ORB_SIZE / 2,
    backgroundColor: '#1C1C1E',
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#34C759',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  orbInner: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  netWorthLabel: {
    fontSize: 14,
    color: '#8E8E93',
    fontWeight: '500',
    marginBottom: 8,
  },
  netWorthValue: {
    fontSize: 32,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 12,
  },
  cashflowIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 4,
  },
  cashflowText: {
    fontSize: 12,
    fontWeight: '600',
  },
  satellite: {
    width: 16,
    height: 16,
    position: 'absolute',
  },
  satelliteDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  positionSatellite: {
    position: 'absolute',
    alignItems: 'center',
  },
  positionDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#34C759',
    marginBottom: 2,
  },
  positionSymbol: {
    fontSize: 10,
    color: '#8E8E93',
    fontWeight: '600',
  },
  gestureHint: {
    marginTop: 16,
    width: '100%',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
  },
  gestureHintText: {
    fontSize: 11,
    color: '#8E8E93',
    opacity: 0.8,
    textAlign: 'center',
    flexShrink: 1,
    includeFontPadding: false,
  },
});

export default ConstellationOrb;

