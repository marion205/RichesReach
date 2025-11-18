/**
 * Standardized Skeleton Loaders
 * 
 * Unified skeleton components for consistent loading states across the app.
 * All skeletons use the same animation and styling for a cohesive UX.
 */

import React, { useRef, useEffect } from 'react';
import { View, StyleSheet, Animated, Easing } from 'react-native';

// Base skeleton component with shimmer animation
interface BaseSkeletonProps {
  width?: number | string;
  height?: number;
  borderRadius?: number;
  style?: any;
}

export const BaseSkeleton: React.FC<BaseSkeletonProps> = ({
  width = '100%',
  height = 16,
  borderRadius = 8,
  style,
}) => {
  const shimmerAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const animation = Animated.loop(
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
    animation.start();
    return () => animation.stop();
  }, [shimmerAnim]);

  const opacity = shimmerAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.4, 0.8],
  });

  return (
    <View
      style={[
        styles.base,
        { width, height, borderRadius },
        style,
      ]}
    >
      <Animated.View
        style={[
          styles.shimmer,
          { opacity },
        ]}
      />
    </View>
  );
};

// Text skeleton - single line
export const SkeletonText: React.FC<{ width?: number | string; lines?: number }> = ({
  width = '100%',
  lines = 1,
}) => (
  <View>
    {Array.from({ length: lines }).map((_, i) => (
      <BaseSkeleton
        key={i}
        width={i === lines - 1 ? width : '100%'}
        height={16}
        style={{ marginBottom: i < lines - 1 ? 8 : 0 }}
      />
    ))}
  </View>
);

// Avatar skeleton
export const SkeletonAvatar: React.FC<{ size?: number }> = ({ size = 40 }) => (
  <BaseSkeleton width={size} height={size} borderRadius={size / 2} />
);

// Card skeleton
export const SkeletonCard: React.FC<{ height?: number }> = ({ height = 120 }) => (
  <View style={styles.card}>
    <BaseSkeleton width="60%" height={20} style={{ marginBottom: 12 }} />
    <BaseSkeleton width="100%" height={16} style={{ marginBottom: 8 }} />
    <BaseSkeleton width="80%" height={16} />
  </View>
);

// List item skeleton
export const SkeletonListItem: React.FC = () => (
  <View style={styles.listItem}>
    <SkeletonAvatar size={48} />
    <View style={styles.listItemContent}>
      <BaseSkeleton width="60%" height={18} style={{ marginBottom: 8 }} />
      <BaseSkeleton width="40%" height={14} />
    </View>
    <View style={styles.listItemRight}>
      <BaseSkeleton width={60} height={18} style={{ marginBottom: 8 }} />
      <BaseSkeleton width={40} height={14} />
    </View>
  </View>
);

// Grid skeleton
export const SkeletonGrid: React.FC<{ columns?: number; rows?: number }> = ({
  columns = 2,
  rows = 2,
}) => (
  <View style={styles.grid}>
    {Array.from({ length: columns * rows }).map((_, i) => (
      <View key={i} style={[styles.gridItem, { width: `${100 / columns}%` }]}>
        <BaseSkeleton width="100%" height={80} borderRadius={12} />
        <BaseSkeleton width="70%" height={16} style={{ marginTop: 8 }} />
        <BaseSkeleton width="50%" height={14} style={{ marginTop: 4 }} />
      </View>
    ))}
  </View>
);

// Screen skeleton - full screen loading
export const SkeletonScreen: React.FC<{ header?: boolean }> = ({ header = true }) => (
  <View style={styles.screen}>
    {header && (
      <View style={styles.header}>
        <BaseSkeleton width={100} height={24} />
        <SkeletonAvatar size={32} />
      </View>
    )}
    <View style={styles.content}>
      <SkeletonCard height={150} />
      <View style={styles.spacing} />
      <SkeletonListItem />
      <SkeletonListItem />
      <SkeletonListItem />
    </View>
  </View>
);

// Trading-specific skeletons
export const TradingAccountSkeleton: React.FC = () => (
  <View style={styles.tradingCard}>
    <View style={styles.tradingHeader}>
      <BaseSkeleton width={150} height={20} />
      <BaseSkeleton width={60} height={24} borderRadius={12} />
    </View>
    <View style={styles.tradingGrid}>
      {Array.from({ length: 6 }).map((_, i) => (
        <View key={i} style={styles.tradingGridCell}>
          <BaseSkeleton width="80%" height={12} style={{ marginBottom: 8 }} />
          <BaseSkeleton width="100%" height={18} />
        </View>
      ))}
    </View>
  </View>
);

export const TradingPositionSkeleton: React.FC = () => (
  <View style={styles.positionRow}>
    <BaseSkeleton width={40} height={40} borderRadius={8} />
    <View style={styles.positionContent}>
      <View style={styles.positionHeader}>
        <BaseSkeleton width={80} height={18} />
        <View style={styles.positionRight}>
          <BaseSkeleton width={70} height={18} />
          <BaseSkeleton width={60} height={24} borderRadius={12} style={{ marginLeft: 8 }} />
        </View>
      </View>
      <BaseSkeleton width="60%" height={14} style={{ marginTop: 8 }} />
      <BaseSkeleton width="40%" height={14} style={{ marginTop: 8 }} />
    </View>
  </View>
);

export const TradingOrderSkeleton: React.FC = () => (
  <View style={styles.orderRow}>
    <View style={styles.orderLeft}>
      <BaseSkeleton width={60} height={18} />
      <BaseSkeleton width={40} height={14} style={{ marginTop: 4 }} />
    </View>
    <View style={styles.orderCenter}>
      <BaseSkeleton width={80} height={16} />
      <BaseSkeleton width={60} height={14} style={{ marginTop: 4 }} />
    </View>
    <View style={styles.orderRight}>
      <BaseSkeleton width={70} height={18} />
      <BaseSkeleton width={50} height={24} borderRadius={12} style={{ marginTop: 4 }} />
    </View>
  </View>
);

// Portfolio-specific skeletons
export const PortfolioChartSkeleton: React.FC = () => (
  <View style={styles.chartContainer}>
    <View style={styles.chartHeader}>
      <BaseSkeleton width={120} height={24} />
      <BaseSkeleton width={80} height={20} />
    </View>
    <View style={styles.chartArea}>
      <BaseSkeleton width="100%" height={200} borderRadius={12} />
    </View>
    <View style={styles.chartFooter}>
      <BaseSkeleton width="30%" height={16} />
      <BaseSkeleton width="30%" height={16} />
      <BaseSkeleton width="30%" height={16} />
    </View>
  </View>
);

const styles = StyleSheet.create({
  base: {
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
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
  },
  listItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E5E7EB',
  },
  listItemContent: {
    flex: 1,
    marginLeft: 12,
  },
  listItemRight: {
    alignItems: 'flex-end',
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  gridItem: {
    padding: 8,
  },
  screen: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E5E7EB',
  },
  content: {
    padding: 16,
  },
  spacing: {
    height: 16,
  },
  // Trading-specific styles
  tradingCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
  },
  tradingHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  tradingGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  tradingGridCell: {
    width: '50%',
    paddingVertical: 12,
    paddingHorizontal: 12,
  },
  positionRow: {
    flexDirection: 'row',
    paddingVertical: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: '#E9EAF0',
  },
  positionContent: {
    flex: 1,
    marginLeft: 12,
  },
  positionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  positionRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  orderRow: {
    flexDirection: 'row',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#E5E7EB',
  },
  orderLeft: {
    flex: 1,
  },
  orderCenter: {
    flex: 1,
    alignItems: 'center',
  },
  orderRight: {
    flex: 1,
    alignItems: 'flex-end',
  },
  // Portfolio-specific styles
  chartContainer: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
  },
  chartHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  chartArea: {
    marginBottom: 16,
  },
  chartFooter: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
});

