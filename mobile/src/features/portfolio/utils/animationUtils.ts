/**
 * Animation utilities for portfolio components
 * Phase 3: Count-up animations, fade-ins
 */

import { useRef, useEffect } from 'react';
import { Animated, Easing } from 'react-native';

/**
 * Count-up animation for values
 * Animates from start to end value over duration
 */
export function useCountUp(
  endValue: number,
  duration: number = 800,
  startValue: number = 0
): Animated.Value {
  const animatedValue = useRef(new Animated.Value(startValue)).current;

  useEffect(() => {
    Animated.timing(animatedValue, {
      toValue: endValue,
      duration,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: false, // We need to interpolate numbers
    }).start();
  }, [endValue, duration, animatedValue]);

  return animatedValue;
}

/**
 * Fade-in animation
 * Fades from 0 to 1 opacity over duration
 */
export function useFadeIn(duration: number = 300, delay: number = 0): Animated.Value {
  const opacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(opacity, {
      toValue: 1,
      duration,
      delay,
      easing: Easing.out(Easing.ease),
      useNativeDriver: true,
    }).start();
  }, [opacity, duration, delay]);

  return opacity;
}

/**
 * Slide-in animation from bottom
 */
export function useSlideIn(
  duration: number = 400,
  delay: number = 0,
  fromY: number = 20
): { opacity: Animated.Value; translateY: Animated.Value } {
  const opacity = useRef(new Animated.Value(0)).current;
  const translateY = useRef(new Animated.Value(fromY)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(opacity, {
        toValue: 1,
        duration,
        delay,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }),
      Animated.timing(translateY, {
        toValue: 0,
        duration,
        delay,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }),
    ]).start();
  }, [opacity, translateY, duration, delay, fromY]);

  return { opacity, translateY };
}

/**
 * Format animated value for currency display
 */
export function formatAnimatedCurrency(value: Animated.Value): Animated.AnimatedInterpolation<string> {
  return value.interpolate({
    inputRange: [0, 1000, 10000, 100000, 1000000],
    outputRange: ['$0', '$1K', '$10K', '$100K', '$1M'],
    extrapolate: 'clamp',
  });
}

