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
  useDerivedValue,
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
import { LinearGradient } from 'expo-linear-gradient';
import Svg, { 
  Line as SvgLine, 
  Defs, 
  LinearGradient as SvgLinearGradient, 
  Stop
} from 'react-native-svg';
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
  // Safety check - return placeholder if snapshot is missing
  if (!snapshot) {
    return (
      <View style={styles.container}>
        <View style={[styles.coreOrb, { backgroundColor: '#1C1C1E', width: ORB_SIZE, height: ORB_SIZE, borderRadius: ORB_SIZE / 2 }]}>
          <Text style={[styles.netWorthLabel, { color: '#FFFFFF' }]}>Loading...</Text>
        </View>
      </View>
    );
  }
  // Core orb animation (pulsing)
  const orbScale = useSharedValue(1);
  const orbOpacity = useSharedValue(0.9);
  const orbRotation = useSharedValue(0);
  const glowIntensity = useSharedValue(0.3);
  
  // Satellite positions (cash flow and positions)
  const satellite1Angle = useSharedValue(0);
  const satellite2Angle = useSharedValue(120);
  const satellite3Angle = useSharedValue(240);
  
  // Position satellite animations - Initialize all 6 upfront (max positions)
  const positionAngles = useRef<ReturnType<typeof useSharedValue<number>>[]>([
    useSharedValue(60),
    useSharedValue(120),
    useSharedValue(180),
    useSharedValue(240),
    useSharedValue(300),
    useSharedValue(360),
  ]);
  const positionScales = useRef<ReturnType<typeof useSharedValue<number>>[]>([
    useSharedValue(1),
    useSharedValue(1),
    useSharedValue(1),
    useSharedValue(1),
    useSharedValue(1),
    useSharedValue(1),
  ]);
  
  // Performance-based color (based on cashflow and net worth trend)
  const performanceColor = useSharedValue(0); // -1 (loss) to 1 (gain)
  
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

  // Initialize position satellite animations
  useEffect(() => {
    const positions = snapshot?.positions ?? [];
    const numPositions = Math.min(positions.length, 6); // Support up to 6 positions
    
    // Reset and animate only the positions we need
    positionAngles.current.forEach((angle, index) => {
      if (index < numPositions) {
        // Reset to initial angle based on position
        const baseAngle = (index * (360 / numPositions)) + 60;
        angle.value = baseAngle;
        
        // Start rotation animation
        angle.value = withRepeat(
          withTiming(baseAngle + 360, { duration: 30000 + (index * 5000) }),
          -1,
          false
        );
        
        // Start pulsing animation
        positionScales.current[index]!.value = withRepeat(
          withSpring(1.2, { damping: 8, stiffness: 100 }),
          -1,
          true
        );
      } else {
        // Stop animations for unused positions
        angle.value = angle.value; // Keep current value
        positionScales.current[index]!.value = 1; // Reset to 1
      }
    });
  }, [snapshot?.positions?.length]);

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
    
    // Calculate performance color based on cashflow
    const cashflowDelta = snapshot?.cashflow?.delta ?? 0;
    const netWorth = snapshot?.netWorth ?? 0;
    // Normalize performance: positive cashflow = positive performance
    const normalizedPerformance = netWorth > 0 
      ? Math.max(-1, Math.min(1, cashflowDelta / (netWorth * 0.1))) // 10% of net worth as max
      : cashflowDelta > 0 ? 0.5 : -0.5;
    performanceColor.value = withTiming(normalizedPerformance, { duration: 1000 });
  }, [snapshot]);

  // Core orb animated style with enhanced effects
  const orbStyle = useAnimatedStyle(() => {
    return {
      transform: [
        { scale: orbScale.value * feedbackScale.value },
        { rotate: `${orbRotation.value}deg` },
      ] as any,
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

  // Glow effect style with performance-based color
  const glowStyle = useAnimatedStyle(() => {
    // Interpolate glow color based on performance
    const glowColor = interpolate(
      performanceColor.value,
      [-1, 0, 1],
      [0xFF3B30, 0x8E8E93, 0x34C759], // Red, Gray, Green
      Extrapolate.CLAMP
    );
    return {
      shadowOpacity: glowIntensity.value,
      shadowRadius: 20 + glowIntensity.value * 10,
      shadowColor: `#${Math.round(glowColor).toString(16).padStart(6, '0')}`,
    };
  });

  // Calculate satellite positions (cash flow indicators)
  const getSatellitePosition = (angle: ReturnType<typeof useSharedValue<number>>, radius: number) => {
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
  
  // Calculate performance for gradient
  const normalizedPerformance = netWorth > 0 
    ? Math.max(-1, Math.min(1, cashflowDelta / (netWorth * 0.1)))
    : cashflowDelta > 0 ? 0.5 : -0.5;
  
  // Get gradient colors based on performance
  const getGradientColors = (): string[] => {
    if (normalizedPerformance > 0.2) {
      return ['#1C1C1E', '#1a2e1a', '#0d4d0d', '#1C1C1E']; // Green gradient
    } else if (normalizedPerformance < -0.2) {
      return ['#1C1C1E', '#2e1a1a', '#4d0d0d', '#1C1C1E']; // Red gradient
    } else {
      return ['#1C1C1E', '#1a1a2e', '#2d1a4d', '#1C1C1E']; // Blue/purple gradient
    }
  };
  
  const orbGradientColors = getGradientColors();

  return (
      <GestureHandlerRootView style={styles.container}>
        <GestureDetector gesture={composedGesture}>
          <View style={styles.orbContainer}>
            {/* Constellation Lines using SVG - Render behind orb with enhancements */}
            <Svg 
              width={ORB_SIZE} 
              height={ORB_SIZE} 
              style={StyleSheet.absoluteFill}
              pointerEvents="none"
            >
              {/* Defs for gradients */}
              <Defs>
                {/* Gradient for cash flow lines - brighter center fade */}
                <SvgLinearGradient id="cashflowGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <Stop offset="0%" stopColor={cashflowColor || '#34C759'} stopOpacity="0.5" />
                  <Stop offset="30%" stopColor={cashflowColor || '#34C759'} stopOpacity="1" />
                  <Stop offset="70%" stopColor={cashflowColor || '#34C759'} stopOpacity="1" />
                  <Stop offset="100%" stopColor={cashflowColor || '#34C759'} stopOpacity="0.3" />
                </SvgLinearGradient>
                
                {/* Gradient for position lines - brighter center fade */}
                <SvgLinearGradient id="positionGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                  <Stop offset="0%" stopColor="#34C759" stopOpacity="0.5" />
                  <Stop offset="30%" stopColor="#34C759" stopOpacity="1" />
                  <Stop offset="70%" stopColor="#34C759" stopOpacity="1" />
                  <Stop offset="100%" stopColor="#34C759" stopOpacity="0.3" />
                </SvgLinearGradient>
              </Defs>
              
              {/* Cash flow satellite lines with gradient and glow */}
              {cashflowDelta !== 0 && (
                <>
                  <SvgLine
                    x1={ORB_CENTER}
                    y1={ORB_CENTER}
                    x2={ORB_CENTER + (ORB_SIZE * 0.4)}
                    y2={ORB_CENTER}
                    stroke="url(#cashflowGradient)"
                    strokeWidth={6}
                    strokeOpacity={0.9}
                    strokeDasharray="12,6"
                    strokeLinecap="round"
                  />
                  <SvgLine
                    x1={ORB_CENTER}
                    y1={ORB_CENTER}
                    x2={ORB_CENTER + (ORB_SIZE * 0.45 * Math.cos((120 * Math.PI) / 180))}
                    y2={ORB_CENTER + (ORB_SIZE * 0.45 * Math.sin((120 * Math.PI) / 180))}
                    stroke="url(#cashflowGradient)"
                    strokeWidth={6}
                    strokeOpacity={0.9}
                    strokeDasharray="12,6"
                    strokeLinecap="round"
                  />
                </>
              )}
              
              {/* Position satellite lines with gradient and glow */}
              {positions.slice(0, 6).map((position, index) => {
                const numPositions = Math.min(positions.length, 6);
                const baseAngle = (index * (360 / numPositions)) + 60;
                const radius = ORB_SIZE * 0.35;
                const rad = (baseAngle * Math.PI) / 180;
                
                // Calculate line thickness based on position value (if available)
                const positionValue = position.value ?? 0;
                const lineThickness = Math.min(6, Math.max(4, 4 + (Math.abs(positionValue) / 5000)));
                
                return (
                  <SvgLine
                    key={`line-${position.symbol}`}
                    x1={ORB_CENTER}
                    y1={ORB_CENTER}
                    x2={ORB_CENTER + radius * Math.cos(rad)}
                    y2={ORB_CENTER + radius * Math.sin(rad)}
                    stroke="url(#positionGradient)"
                    strokeWidth={lineThickness}
                    strokeOpacity={0.9}
                    strokeDasharray="12,6"
                    strokeLinecap="round"
                  />
                );
              })}
            </Svg>
            
            {/* Core Orb - Net Worth with Gradient */}
            <Animated.View style={[styles.coreOrb, orbStyle, glowStyle]}>
            <LinearGradient
              colors={orbGradientColors as [string, string, ...string[]]}
              style={StyleSheet.absoluteFill}
              start={{ x: 0.5, y: 0.5 }}
              end={{ x: 1, y: 1 }}
            />
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

          {/* Satellites - Portfolio Positions (starry cluster) - Animated */}
          {positions.slice(0, 6).map((position, index) => {
            const numPositions = Math.min(positions.length, 6);
            const radius = ORB_SIZE * 0.35;
            
            // Get animated angle and scale for this position
            const angleValue = positionAngles.current[index];
            const scaleValue = positionScales.current[index];
            
            if (!angleValue || !scaleValue) {
              // Fallback to static position if animation not initialized
              const baseAngle = (index * (360 / numPositions)) + 60;
              const rad = (baseAngle * Math.PI) / 180;
              const x = ORB_CENTER + radius * Math.cos(rad) - 6;
              const y = ORB_CENTER + radius * Math.sin(rad) - 6;
              
              const positionValue = position.value ?? 0;
              const positionColor = positionValue >= 0 ? '#34C759' : '#FF3B30';
              const positionSize = Math.min(8, Math.max(4, 4 + (Math.abs(positionValue) / 1000)));

              return (
                <View
                  key={position.symbol}
                  style={[styles.positionSatellite, { left: x, top: y }]}
                >
                  <View style={[styles.positionDot, { 
                    backgroundColor: positionColor,
                    width: positionSize,
                    height: positionSize,
                    borderRadius: positionSize / 2,
                  }]} />
                  <Text style={styles.positionSymbol}>{position.symbol}</Text>
                </View>
              );
            }
            
            // Calculate position based on animated angle
            const positionStyle = useAnimatedStyle(() => {
              const rad = (angleValue.value * Math.PI) / 180;
              const x = ORB_CENTER + radius * Math.cos(rad) - 6;
              const y = ORB_CENTER + radius * Math.sin(rad) - 6;
              
              return {
                position: 'absolute',
                left: x,
                top: y,
                transform: [{ scale: scaleValue.value }],
              };
            });
            
            // Determine position color based on performance (if available)
            const positionValue = position.value ?? 0;
            const positionColor = positionValue >= 0 ? '#34C759' : '#FF3B30';
            const positionSize = Math.min(8, Math.max(4, 4 + (Math.abs(positionValue) / 1000)));

            return (
              <Animated.View
                key={position.symbol}
                style={[styles.positionSatellite, positionStyle]}
              >
                <View style={[styles.positionDot, { 
                  backgroundColor: positionColor,
                  width: positionSize,
                  height: positionSize,
                  borderRadius: positionSize / 2,
                }]} />
                <Text style={styles.positionSymbol}>{position.symbol}</Text>
              </Animated.View>
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
    overflow: 'hidden', // For gradient
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
    shadowColor: '#34C759',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.6,
    shadowRadius: 4,
    elevation: 3,
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
  constellationLine: {
    position: 'absolute',
    opacity: 0.7,
    borderRadius: 1,
  },
});

export default ConstellationOrb;

