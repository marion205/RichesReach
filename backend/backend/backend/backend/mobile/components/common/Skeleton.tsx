// Skeleton loading components for smooth UX
import React, { useEffect, useRef } from 'react';
import { View, StyleSheet, Animated } from 'react-native';

interface SkeletonProps {
  height?: number;
  width?: number | string;
  borderRadius?: number;
  style?: any;
  animated?: boolean;
}

export const Skeleton: React.FC<SkeletonProps> = ({ 
  height = 16, 
  width = '100%', 
  borderRadius = 8, 
  style,
  animated = true 
}) => {
  const shimmer = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (animated) {
      const animation = Animated.loop(
        Animated.sequence([
          Animated.timing(shimmer, {
            toValue: 1,
            duration: 1000,
            useNativeDriver: true,
          }),
          Animated.timing(shimmer, {
            toValue: 0,
            duration: 1000,
            useNativeDriver: true,
          }),
        ])
      );
      animation.start();
      return () => animation.stop();
    }
  }, [animated, shimmer]);

  const shimmerStyle = animated ? {
    opacity: shimmer.interpolate({
      inputRange: [0, 1],
      outputRange: [0.3, 0.7],
    }),
  } : {};

  return (
    <View style={[styles.skeleton, { height, width, borderRadius }, style]}>
      {animated && (
        <Animated.View style={[styles.shimmer, shimmerStyle]} />
      )}
    </View>
  );
};

// Pre-built skeleton components for common use cases
export const SkeletonText: React.FC<{ lines?: number; width?: string }> = ({ 
  lines = 1, 
  width = '100%' 
}) => (
  <View style={styles.textContainer}>
    {Array.from({ length: lines }).map((_, i) => (
      <Skeleton 
        key={i} 
        height={16} 
        width={i === lines - 1 ? '60%' : width} 
        style={{ marginBottom: i < lines - 1 ? 8 : 0 }}
      />
    ))}
  </View>
);

export const SkeletonCard: React.FC = () => (
  <View style={styles.card}>
    <View style={styles.cardHeader}>
      <Skeleton height={20} width={120} />
      <Skeleton height={16} width={60} />
    </View>
    <Skeleton height={32} width="80%" style={{ marginVertical: 12 }} />
    <View style={styles.cardFooter}>
      <Skeleton height={14} width={100} />
      <Skeleton height={14} width={80} />
    </View>
  </View>
);

export const SkeletonPortfolioCard: React.FC = () => (
  <View style={styles.portfolioCard}>
    <View style={styles.portfolioHeader}>
      <Skeleton height={18} width={120} />
      <Skeleton height={16} width={20} />
    </View>
    <Skeleton height={36} width="70%" style={{ marginVertical: 8 }} />
    <View style={styles.chipsRow}>
      <Skeleton height={24} width={80} borderRadius={12} />
      <Skeleton height={24} width={60} borderRadius={12} />
    </View>
    <View style={styles.holdingsSection}>
      <Skeleton height={16} width={100} style={{ marginBottom: 8 }} />
      {Array.from({ length: 3 }).map((_, i) => (
        <View key={i} style={styles.holdingRow}>
          <View style={styles.holdingLeft}>
            <Skeleton height={40} width={40} borderRadius={20} />
            <View style={styles.holdingInfo}>
              <Skeleton height={16} width={60} />
              <Skeleton height={12} width={80} />
            </View>
          </View>
          <View style={styles.holdingRight}>
            <Skeleton height={16} width={80} />
            <Skeleton height={14} width={50} />
          </View>
        </View>
      ))}
    </View>
  </View>
);

export const SkeletonTradingCard: React.FC = () => (
  <View style={styles.tradingCard}>
    <View style={styles.segmentRow}>
      <Skeleton height={40} width={80} borderRadius={20} />
      <Skeleton height={40} width={80} borderRadius={20} />
    </View>
    <Skeleton height={16} width={100} style={{ marginTop: 16 }} />
    <View style={styles.symbolRow}>
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} height={32} width={60} borderRadius={16} style={{ marginRight: 8 }} />
      ))}
    </View>
    <Skeleton height={16} width={120} style={{ marginTop: 16 }} />
    <Skeleton height={48} width="100%" style={{ marginTop: 8 }} />
    <Skeleton height={16} width={100} style={{ marginTop: 16 }} />
    <Skeleton height={48} width="100%" style={{ marginTop: 8 }} />
    <View style={styles.presetRow}>
      {Array.from({ length: 4 }).map((_, i) => (
        <Skeleton key={i} height={32} width={60} borderRadius={16} style={{ marginRight: 8 }} />
      ))}
    </View>
    <Skeleton height={48} width="100%" style={{ marginTop: 16 }} />
  </View>
);

const styles = StyleSheet.create({
  skeleton: {
    backgroundColor: '#E5E7EB',
    overflow: 'hidden',
  },
  shimmer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: '#F3F4F6',
  },
  textContainer: {
    flex: 1,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  portfolioCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  portfolioHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  chipsRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
  },
  holdingsSection: {
    marginTop: 16,
  },
  holdingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
  },
  holdingLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  holdingInfo: {
    marginLeft: 12,
    flex: 1,
  },
  holdingRight: {
    alignItems: 'flex-end',
  },
  tradingCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  segmentRow: {
    flexDirection: 'row',
    gap: 8,
  },
  symbolRow: {
    flexDirection: 'row',
    marginTop: 8,
  },
  presetRow: {
    flexDirection: 'row',
    marginTop: 8,
  },
});
