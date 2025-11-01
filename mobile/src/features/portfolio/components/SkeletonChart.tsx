/**
 * SkeletonChart - Shimmer loading state for portfolio chart
 * Phase 3: Latency masking
 */

import React from 'react';
import { View, StyleSheet, Animated, Easing } from 'react-native';

export const SkeletonChart: React.FC = () => {
  const shimmerAnim = React.useRef(new Animated.Value(0)).current;

  React.useEffect(() => {
    const shimmer = Animated.loop(
      Animated.sequence([
        Animated.timing(shimmerAnim, {
          toValue: 1,
          duration: 1200,
          easing: Easing.linear,
          useNativeDriver: true,
        }),
        Animated.timing(shimmerAnim, {
          toValue: 0,
          duration: 1200,
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
        <View style={styles.tabsSkeleton} />
      </View>

      {/* KPI skeletons */}
      <View style={styles.kpiRow}>
        <View style={styles.valueSkeleton} />
        <View style={styles.pnlSkeleton} />
      </View>

      {/* Chart skeleton */}
      <View style={styles.chartContainer}>
        <Animated.View style={[styles.shimmerOverlay, { opacity }]} />
        <View style={styles.chartArea}>
          {/* Grid lines */}
          {Array.from({ length: 5 }).map((_, i) => (
            <View key={i} style={[styles.gridLine, { top: `${i * 25}%` }]} />
          ))}
          {/* Fake line */}
          <View style={styles.linePath} />
        </View>
      </View>

      {/* Footer skeleton */}
      <View style={styles.footer}>
        <View style={styles.footerTextSkeleton} />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    marginVertical: 12,
  },
  header: {
    marginBottom: 16,
  },
  titleSkeleton: {
    width: 160,
    height: 20,
    backgroundColor: '#E5E5EA',
    borderRadius: 6,
    marginBottom: 12,
  },
  tabsSkeleton: {
    flexDirection: 'row',
    gap: 8,
    height: 32,
  },
  kpiRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  valueSkeleton: {
    width: 120,
    height: 32,
    backgroundColor: '#E5E5EA',
    borderRadius: 8,
  },
  pnlSkeleton: {
    width: 100,
    height: 24,
    backgroundColor: '#E5E5EA',
    borderRadius: 8,
  },
  chartContainer: {
    height: 200,
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    overflow: 'hidden',
    position: 'relative',
    marginBottom: 12,
  },
  shimmerOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
  },
  chartArea: {
    flex: 1,
    padding: 16,
    position: 'relative',
  },
  gridLine: {
    position: 'absolute',
    left: 0,
    right: 0,
    height: 1,
    backgroundColor: '#E5E5EA',
  },
  linePath: {
    position: 'absolute',
    bottom: 20,
    left: 16,
    right: 16,
    height: 2,
    backgroundColor: '#007AFF',
    borderRadius: 1,
    transform: [{ translateY: -50 }],
  },
  footer: {
    alignItems: 'center',
  },
  footerTextSkeleton: {
    width: 200,
    height: 14,
    backgroundColor: '#E5E5EA',
    borderRadius: 4,
  },
});

