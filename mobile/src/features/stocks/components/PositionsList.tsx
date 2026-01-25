import React from 'react';
import { View, Text, StyleSheet, FlatList, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { PositionRow } from './PositionRow';
import { PositionRowSkeleton } from './SkeletonLoader';

const C = {
  bg: '#F5F6FA',
  card: '#FFFFFF',
  line: '#E9EAF0',
  text: '#111827',
  sub: '#6B7280',
  primary: '#007AFF',
};

interface PositionsListProps {
  positions: any[];
  loading?: boolean;
  onRefresh?: () => void;
  refreshing?: boolean;
}

export const PositionsList: React.FC<PositionsListProps> = React.memo(
  ({ positions, loading = false, onRefresh, refreshing = false }) => {
    if (loading) {
      return (
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Positions</Text>
            {onRefresh && (
              <TouchableOpacity onPress={onRefresh}>
                <Icon name="refresh-ccw" size={18} color={C.sub} />
              </TouchableOpacity>
            )}
          </View>
          {[...Array(3)].map((_, i) => (
            <PositionRowSkeleton key={i} />
          ))}
        </View>
      );
    }

    if (positions.length === 0) {
      return (
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Positions</Text>
            {onRefresh && (
              <TouchableOpacity onPress={onRefresh}>
                <Icon name="refresh-ccw" size={18} color={C.sub} />
              </TouchableOpacity>
            )}
          </View>
          <View style={styles.emptyBlock}>
            <Icon name="briefcase" size={40} color={C.sub} />
            <Text style={styles.emptyTitle}>No positions yet</Text>
            <Text style={styles.emptySub}>Start trading to see positions here.</Text>
          </View>
        </View>
      );
    }

    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle}>Positions</Text>
          {onRefresh && (
            <TouchableOpacity onPress={onRefresh}>
              <Icon name="refresh-ccw" size={18} color={C.sub} />
            </TouchableOpacity>
          )}
        </View>
        <FlatList
          data={positions}
          keyExtractor={(item) => item.id || item.symbol}
          renderItem={({ item }) => <PositionRow position={item} />}
          ItemSeparatorComponent={() => <View style={{ height: 1, backgroundColor: C.line }} />}
          scrollEnabled={false}
          refreshing={refreshing}
          onRefresh={onRefresh}
          // Performance optimizations
          removeClippedSubviews={true}
          initialNumToRender={5}
          maxToRenderPerBatch={3}
          windowSize={5}
          updateCellsBatchingPeriod={50}
          getItemLayout={(_, index) => ({
            length: 91, // Estimated item height (90px) + separator (1px)
            offset: 91 * index,
            index,
          })}
        />
      </View>
    );
  },
  (prevProps, nextProps) => {
    // Custom comparison for better memoization
    return (
      prevProps.positions.length === nextProps.positions.length &&
      prevProps.loading === nextProps.loading &&
      prevProps.refreshing === nextProps.refreshing &&
      prevProps.positions.every(
        (p, i) => p.id === nextProps.positions[i]?.id && p.symbol === nextProps.positions[i]?.symbol
      )
    );
  }
);

PositionsList.displayName = 'PositionsList';

const styles = StyleSheet.create({
  card: {
    backgroundColor: C.card,
    borderRadius: 16,
    padding: 16,
    marginTop: 12,
    shadowColor: 'rgba(16,24,40,0.08)',
    shadowOpacity: 1,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: C.text,
  },
  centerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
  },
  sub: {
    fontSize: 13,
    color: C.sub,
  },
  emptyBlock: {
    alignItems: 'center',
    paddingVertical: 24,
    gap: 6,
  },
  emptyTitle: {
    fontWeight: '700',
    color: C.text,
    fontSize: 16,
  },
  emptySub: {
    color: C.sub,
  },
});

