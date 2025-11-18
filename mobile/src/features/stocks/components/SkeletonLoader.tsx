import React from 'react';
import { View, StyleSheet, Animated, Easing } from 'react-native';

const C = {
  skeleton: '#E5E7EB',
  shimmer: '#F3F4F6',
};

interface SkeletonLoaderProps {
  width?: number | string;
  height?: number;
  borderRadius?: number;
  style?: any;
}

export const SkeletonBox: React.FC<SkeletonLoaderProps> = ({
  width = '100%',
  height = 20,
  borderRadius = 4,
  style,
}) => {
  const shimmerAnim = React.useRef(new Animated.Value(0)).current;

  React.useEffect(() => {
    Animated.loop(
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
    ).start();
  }, [shimmerAnim]);

  const opacity = shimmerAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.5, 1],
  });

  return (
    <Animated.View
      style={[
        {
          width,
          height,
          borderRadius,
          backgroundColor: C.skeleton,
          opacity,
        },
        style,
      ]}
    />
  );
};

export const AccountSummarySkeleton: React.FC = React.memo(() => (
  <View style={styles.card}>
    <View style={styles.cardHeader}>
      <SkeletonBox width={150} height={20} />
      <SkeletonBox width={60} height={24} borderRadius={12} />
    </View>
    <View style={styles.grid}>
      {[...Array(6)].map((_, i) => (
        <View key={i} style={styles.gridCell}>
          <SkeletonBox width="80%" height={12} style={{ marginBottom: 8 }} />
          <SkeletonBox width="100%" height={18} />
        </View>
      ))}
    </View>
  </View>
));

AccountSummarySkeleton.displayName = 'AccountSummarySkeleton';

export const PositionRowSkeleton: React.FC = React.memo(() => (
  <View style={styles.positionRow}>
    <SkeletonBox width={40} height={40} borderRadius={8} />
    <View style={{ flex: 1, marginLeft: 12 }}>
      <View style={styles.rowBetween}>
        <SkeletonBox width={80} height={18} />
        <View style={{ flexDirection: 'row', gap: 8 }}>
          <SkeletonBox width={70} height={18} />
          <SkeletonBox width={60} height={24} borderRadius={12} />
        </View>
      </View>
      <SkeletonBox width="60%" height={14} style={{ marginTop: 8 }} />
      <SkeletonBox width="40%" height={14} style={{ marginTop: 8 }} />
    </View>
  </View>
));

PositionRowSkeleton.displayName = 'PositionRowSkeleton';

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginTop: 12,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  gridCell: {
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
  rowBetween: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
});

