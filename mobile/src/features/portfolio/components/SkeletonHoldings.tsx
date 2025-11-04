/**
 * SkeletonHoldings - Shimmer loading states for portfolio holdings
 * Phase 3: Latency masking with beautiful skeletons
 */

import React from 'react';
import { View, StyleSheet, Animated, Easing } from 'react-native';

interface SkeletonHoldingsProps {
  count?: number;
}

export const SkeletonHoldings: React.FC<SkeletonHoldingsProps> = ({ count = 3 }) => {
  const shimmerAnim = React.useRef(new Animated.Value(0)).current;

  React.useEffect(() => {
    const shimmer = Animated.loop(
      Animated.sequence([
        Animated.timing(shimmerAnim, {
          toValue: 1,
          duration: 1000,
          easing: Easing.linear,
          useNativeDriver: true,
        }),
        Animated.timing(shimmerAnim, {
          toValue: 0,
          duration: 1000,
          easing: Easing.linear,
          useNativeDriver: true,
        }),
      ])
    );
    shimmer.start();
    return () => shimmer.stop();
  }, [shimmerAnim]);

  const opacity = shimmerAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.3, 0.7],
  });

  return (
    <View style={styles.container}>
      {/* Header skeleton */}
      <View style={styles.header}>
        <View style={styles.titleSkeleton} />
        <View style={styles.totalSkeleton} />
      </View>

      {/* Holdings skeletons */}
      {Array.from({ length: count }).map((_, index) => (
        <View key={index} style={styles.card}>
          <Animated.View style={[styles.shimmerOverlay, { opacity }]} />
          <View style={styles.cardContent}>
            <View style={styles.leftSection}>
              <View style={styles.symbolSkeleton} />
              <View style={styles.badgeSkeleton} />
              <View style={styles.nameSkeleton} />
              <View style={styles.quantitySkeleton} />
            </View>
            <View style={styles.rightSection}>
              <View style={styles.valueSkeleton} />
              <View style={styles.performanceSkeleton} />
              <View style={styles.changeSkeleton} />
            </View>
          </View>
        </View>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    marginVertical: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 2,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
    paddingBottom: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E5E5EA',
  },
  titleSkeleton: {
    width: 180,
    height: 28,
    backgroundColor: '#E5E5EA',
    borderRadius: 8,
  },
  totalSkeleton: {
    width: 100,
    height: 24,
    backgroundColor: '#E5E5EA',
    borderRadius: 8,
  },
  card: {
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    overflow: 'hidden',
    position: 'relative',
  },
  shimmerOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
  },
  cardContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  leftSection: {
    flex: 1,
    marginRight: 12,
  },
  symbolSkeleton: {
    width: 80,
    height: 24,
    backgroundColor: '#E5E5EA',
    borderRadius: 6,
    marginBottom: 8,
  },
  badgeSkeleton: {
    width: 40,
    height: 16,
    backgroundColor: '#E5E5EA',
    borderRadius: 4,
    marginBottom: 6,
  },
  nameSkeleton: {
    width: 140,
    height: 16,
    backgroundColor: '#E5E5EA',
    borderRadius: 4,
    marginBottom: 6,
  },
  quantitySkeleton: {
    width: 90,
    height: 14,
    backgroundColor: '#E5E5EA',
    borderRadius: 4,
  },
  rightSection: {
    alignItems: 'flex-end',
  },
  valueSkeleton: {
    width: 100,
    height: 22,
    backgroundColor: '#E5E5EA',
    borderRadius: 6,
    marginBottom: 8,
  },
  performanceSkeleton: {
    width: 70,
    height: 20,
    backgroundColor: '#E5E5EA',
    borderRadius: 6,
    marginBottom: 6,
  },
  changeSkeleton: {
    width: 60,
    height: 16,
    backgroundColor: '#E5E5EA',
    borderRadius: 4,
  },
});

