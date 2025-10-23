import React, { useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  Dimensions,
  TouchableOpacity,
  Vibration,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { PanGestureHandler, State, GestureHandlerRootView } from 'react-native-gesture-handler';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

const { width, height } = Dimensions.get('window');

interface GestureNavigationProps {
  onNavigate: (screen: string, params?: any) => void;
  currentScreen: string;
  children: React.ReactNode;
}

export default function GestureNavigation({ onNavigate, currentScreen, children }: GestureNavigationProps) {
  const insets = useSafeAreaInsets();
  const [isGestureActive, setIsGestureActive] = useState(false);
  
  // Animation values
  const translateX = useRef(new Animated.Value(0)).current;
  const translateY = useRef(new Animated.Value(0)).current;
  const scale = useRef(new Animated.Value(1)).current;

  // Navigation screens with gesture mappings
  const navigationScreens = {
    home: { left: 'portfolio', right: 'social', up: 'ai-coach', down: 'crypto' },
    portfolio: { left: 'trading', right: 'home', up: 'analytics', down: 'tax-optimization' },
    social: { left: 'home', right: 'community', up: 'wealth-circles', down: 'leaderboard' },
    trading: { left: 'options', right: 'portfolio', up: 'signals', down: 'risk-management' },
    'ai-coach': { left: 'tutor', right: 'assistant', up: 'market-commentary', down: 'home' },
    crypto: { left: 'defi', right: 'nft', up: 'home', down: 'wallet' },
  };

  const onGestureEvent = Animated.event(
    [{ nativeEvent: { translationX: translateX, translationY: translateY } }],
    { useNativeDriver: true }
  );

  const onHandlerStateChange = ({ nativeEvent }: any) => {
    if (nativeEvent.state === State.ACTIVE) {
      setIsGestureActive(true);
      if (Platform.OS === 'ios') {
        Vibration.vibrate(50);
      }
    } else if (nativeEvent.state === State.END) {
      setIsGestureActive(false);
      
      const { translationX: tx, translationY: ty, velocityX: vx, velocityY: vy } = nativeEvent;
      const threshold = 50;
      const velocityThreshold = 0.5;

      // Determine gesture direction
      let direction: 'left' | 'right' | 'up' | 'down' | null = null;
      
      if (Math.abs(tx) > Math.abs(ty)) {
        if (tx > threshold || vx > velocityThreshold) {
          direction = 'right';
        } else if (tx < -threshold || vx < -velocityThreshold) {
          direction = 'left';
        }
      } else {
        if (ty > threshold || vy > velocityThreshold) {
          direction = 'down';
        } else if (ty < -threshold || vy < -velocityThreshold) {
          direction = 'up';
        }
      }

      // Navigate if gesture is valid
      if (direction) {
        const targetScreen = navigationScreens[currentScreen as keyof typeof navigationScreens]?.[direction];
        if (targetScreen) {
          onNavigate(targetScreen);
        }
      }

      // Reset animations
      Animated.parallel([
        Animated.spring(translateX, {
          toValue: 0,
          useNativeDriver: true,
        }),
        Animated.spring(translateY, {
          toValue: 0,
          useNativeDriver: true,
        }),
        Animated.spring(scale, {
          toValue: 1,
          useNativeDriver: true,
        }),
      ]).start();
    }
  };

  const animatedStyle = {
    transform: [
      { translateX },
      { translateY },
      { scale },
    ],
  };

  return (
    <GestureHandlerRootView style={styles.container}>
      <PanGestureHandler
        onGestureEvent={onGestureEvent}
        onHandlerStateChange={onHandlerStateChange}
      >
        <Animated.View style={[styles.gestureContainer, animatedStyle]}>
          {children}
          
          {/* Gesture Indicator */}
          {isGestureActive && (
            <View style={[styles.gestureIndicator, { top: insets.top + 10 }]}>
              <LinearGradient
                colors={['#667eea', '#764ba2']}
                style={styles.gestureIndicatorGradient}
              >
                <Text style={styles.gestureIndicatorText}>👆 Swipe to navigate</Text>
              </LinearGradient>
            </View>
          )}
        </Animated.View>
      </PanGestureHandler>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gestureContainer: {
    flex: 1,
  },
  gestureIndicator: {
    position: 'absolute',
    left: 20,
    right: 20,
    zIndex: 1000,
  },
  gestureIndicatorGradient: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
    alignItems: 'center',
  },
  gestureIndicatorText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
});