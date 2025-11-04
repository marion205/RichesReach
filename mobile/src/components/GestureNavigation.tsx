// src/components/GestureNavigation.tsx
import React, { useMemo } from 'react';
import { View, StyleSheet } from 'react-native';
import Animated, {
  runOnJS,
  useAnimatedStyle,
  useSharedValue,
  withSpring,
} from 'react-native-reanimated';
import { Gesture, GestureDetector } from 'react-native-gesture-handler';

type Props = {
  onNavigate?: (screen: string, params?: any) => void;
  currentScreen?: string;
  onBack?: () => void;       // e.g., navigation.goBack()
  onForward?: () => void;    // e.g., navigation.navigate('Next')
  children?: React.ReactNode;
  swipeThreshold?: number;   // px
};

const SWIPE_DEFAULT = 60;

export default function GestureNavigation({
  onNavigate,
  currentScreen,
  onBack,
  onForward,
  children,
  swipeThreshold = SWIPE_DEFAULT,
}: Props) {
  const translateX = useSharedValue(0);
  const startX = useSharedValue(0);

  // Handle navigation via onNavigate if provided, otherwise use onBack/onForward
  const handleNavigate = (screen: string, params?: any) => {
    if (onNavigate) {
      onNavigate(screen, params);
    }
  };

  const handleBackJS = onBack || (() => {
    // Fallback navigation logic if needed
    if (currentScreen && onNavigate) {
      // Simple back logic - go to home if on other screens
      if (currentScreen !== 'home') {
        handleNavigate('home');
      }
    }
  });

  const handleForwardJS = onForward || (() => {
    // Fallback forward logic if needed
    if (currentScreen && onNavigate) {
      // Navigate forward based on current screen
      if (currentScreen === 'home') {
        handleNavigate('InvestMain'); // Swipe left from home goes to invest
      } else if (currentScreen === 'InvestMain' || currentScreen === 'invest') {
        handleNavigate('portfolio'); // Swipe left from invest goes to portfolio
      } else {
        handleNavigate('portfolio'); // Default fallback
      }
    }
  });

  const pan = useMemo(
    () =>
      Gesture.Pan()
        .activeOffsetX([-10, 10]) // Activate quickly on horizontal movement for navigation
        .failOffsetY([-15, 15]) // Fail on vertical movement to allow scrolling
        .onBegin(() => {
          'worklet';
          startX.value = translateX.value;
        })
        .onUpdate((e) => {
          'worklet';
          translateX.value = startX.value + e.translationX;
        })
        .onEnd((e) => {
          'worklet';
          const dx = e.translationX;
          const vx = e.velocityX;

          // Swipe right (positive dx) = go forward (to next screen)
          // Swipe left (negative dx) = go back (to previous screen)
          const shouldForward =
            dx > swipeThreshold && Math.abs(vx) > 150 && !!handleForwardJS;
          const shouldBack =
            dx < -swipeThreshold && Math.abs(vx) > 150 && !!handleBackJS;

          if (shouldBack) {
            runOnJS(handleBackJS)();
          } else if (shouldForward) {
            runOnJS(handleForwardJS)();
          }

          translateX.value = withSpring(0, { damping: 18, stiffness: 180 });
        }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [onBack, onForward, swipeThreshold]
  );

  const style = useAnimatedStyle(() => ({
    transform: [{ translateX: translateX.value }],
  }));

  return (
    <GestureDetector gesture={pan}>
      <Animated.View style={[styles.container, style]}>
        {children ?? <View />}
      </Animated.View>
    </GestureDetector>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
});
