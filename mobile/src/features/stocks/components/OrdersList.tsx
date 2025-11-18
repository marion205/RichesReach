import React, { useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

const C = {
  card: '#FFFFFF',
  line: '#E9EAF0',
  text: '#111827',
  sub: '#6B7280',
  primary: '#007AFF',
  green: '#22C55E',
  red: '#EF4444',
  amber: '#F59E0B',
};

interface OrdersListProps {
  orders: any[];
  loading?: boolean;
  filter: 'all' | 'open' | 'filled' | 'cancelled';
  onFilterChange: (filter: 'all' | 'open' | 'filled' | 'cancelled') => void;
  onRefresh?: () => void;
  onCancelOrder?: (orderId: string) => void;
}

const getStatusMeta = (status: string) => {
  const s = status?.toLowerCase();
  if (s === 'filled') return { color: C.green, icon: 'check-circle' };
  if (s === 'pending' || s === 'new' || s === 'accepted' || s === 'open')
    return { color: C.amber, icon: 'clock' };
  if (s === 'rejected') return { color: C.red, icon: 'x-circle' };
  if (s === 'cancelled' || s === 'canceled') return { color: '#9CA3AF', icon: 'slash' };
  return { color: '#9CA3AF', icon: 'more-horizontal' };
};

const isOpen = (s: string) => ['pending', 'accepted', 'new', 'open'].includes(String(s).toLowerCase());

const groupOrders = (orders: any[]) => {
  const today = new Date();
  const startOfDay = new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime();
  const startOfWeek = (() => {
    const day = today.getDay();
    const diffDate = today.getDate() - day;
    return new Date(today.getFullYear(), today.getMonth(), diffDate).getTime();
  })();

  const buckets: Record<string, any[]> = { Today: [], 'This Week': [], Earlier: [] };
  for (const o of orders) {
    const t = new Date(o.createdAt).getTime();
    if (t >= startOfDay) buckets['Today'].push(o);
    else if (t >= startOfWeek) buckets['This Week'].push(o);
    else buckets['Earlier'].push(o);
  }
  return buckets;
};

const fmtTime = (iso: string) => {
  try {
    const d = new Date(iso);
    return d
      .toLocaleString(undefined, { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit' })
      .replace(',', '');
  } catch {
    return iso;
  }
};

export const OrdersList: React.FC<OrdersListProps> = React.memo(
  ({ orders, loading = false, filter, onFilterChange, onRefresh, onCancelOrder }) => {
    const filtered = useMemo(() => {
      return orders.filter((o: any) => {
        if (filter === 'all') return true;
        if (filter === 'open') return isOpen(o.status);
        return String(o.status).toLowerCase() === filter;
      });
    }, [orders, filter]);

    const sections = useMemo(() => groupOrders(filtered), [filtered]);

    // Flatten sections into a single list with section headers
    const flatListData = useMemo(() => {
      if (loading || filtered.length === 0) return [];
      
      const items: Array<{ type: 'section' | 'order'; label?: string; order?: any }> = [];
      (['Today', 'This Week', 'Earlier'] as const).forEach((label) => {
        if (sections[label].length > 0) {
          items.push({ type: 'section', label });
          sections[label].forEach((order) => {
            items.push({ type: 'order', order });
          });
        }
      });
      return items;
    }, [sections, loading, filtered.length]);

    const renderOrderItem = ({ item }: { item: any }) => {
      if (item.type === 'section') {
        return <Text style={styles.sectionDivider}>{item.label}</Text>;
      }

      const o = item.order;
      const sideBuy = String(o.side).toLowerCase() === 'buy';
      const { color: statusColor, icon } = getStatusMeta(o.status);
      const showCancel = String(o.status).toLowerCase() === 'pending';

      return (
        <View style={styles.orderCardRow}>
          {/* Left accent by side */}
          <View
            style={[
              styles.sideAccent,
              { backgroundColor: sideBuy ? '#16A34A' : '#DC2626' },
            ]}
          />

          <View style={{ flex: 1 }}>
            {/* Top line: Ticker + chips + status */}
            <View style={styles.rowBetween}>
              <View
                style={{
                  flexDirection: 'row',
                  alignItems: 'center',
                  gap: 8,
                  flexShrink: 1,
                }}
              >
                <Text style={styles.ticker}>{o.symbol}</Text>
                <View style={[styles.badge, styles.badgeInfo]}>
                  <Text style={styles.badgeText}>
                    {String(o.orderType).toUpperCase()}
                  </Text>
                </View>
                <View
                  style={[
                    styles.badge,
                    sideBuy ? styles.badgeSuccess : styles.badgeDanger,
                  ]}
                >
                  <Text style={styles.badgeText}>{String(o.side).toUpperCase()}</Text>
                </View>
              </View>

              <View style={[styles.badge, { backgroundColor: `${statusColor}1A` }]}>
                <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                  <Icon name={icon as any} size={14} color={statusColor} />
                  <Text style={[styles.badgeText, { color: statusColor }]}>
                    {String(o.status).toUpperCase()}
                  </Text>
                </View>
              </View>
            </View>

            {/* Middle: size / price */}
            <View style={styles.rowWrap}>
              <Text style={styles.sub}>{o.quantity} shares</Text>
              {o.price ? <Text style={styles.sub}>@ ${o.price.toFixed(2)}</Text> : null}
              {o.stopPrice ? (
                <Text style={styles.sub}>Stop ${o.stopPrice.toFixed(2)}</Text>
              ) : null}
            </View>

            {/* Bottom: time + Cancel */}
            <View style={styles.rowBetween}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                <Icon name="calendar" size={14} color={C.sub} />
                <Text style={styles.meta}>{fmtTime(o.createdAt)}</Text>
              </View>
              {showCancel && onCancelOrder && (
                <TouchableOpacity
                  style={styles.ghostDangerBtn}
                  onPress={() => onCancelOrder(o.id)}
                >
                  <Icon name="x-circle" size={14} color="#EF4444" />
                  <Text style={styles.ghostDangerText}>Cancel</Text>
                </TouchableOpacity>
              )}
            </View>

            {o.notes ? <Text style={styles.note}>"{o.notes}"</Text> : null}
          </View>
        </View>
      );
    };

    const ListHeaderComponent = () => (
      <View style={styles.card}>
        {/* Header + refresh */}
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle}>Recent Orders</Text>
          {onRefresh && (
            <TouchableOpacity onPress={onRefresh} style={styles.iconBtn}>
              <Icon name="refresh-ccw" size={18} color={C.sub} />
            </TouchableOpacity>
          )}
        </View>

        {/* Filter bar */}
        <View style={styles.filterBar}>
          {(['all', 'open', 'filled', 'cancelled'] as const).map((k) => (
            <TouchableOpacity
              key={k}
              onPress={() => onFilterChange(k)}
              style={[styles.filterPill, filter === k && styles.filterPillActive]}
            >
              <Text style={[styles.filterPillText, filter === k && styles.filterPillTextActive]}>
                {k === 'all'
                  ? 'All'
                  : k === 'open'
                  ? 'Open'
                  : k.charAt(0).toUpperCase() + k.slice(1)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>
    );

    if (loading) {
      return (
        <View style={styles.scroller}>
          <ListHeaderComponent />
          <View style={styles.skeletonBlock}>
            {[...Array(3)].map((_, i) => (
              <View key={i} style={styles.skeletonRow}>
                <View style={styles.skeletonAccent} />
                <View style={{ flex: 1 }}>
                  <View style={styles.skeletonLineWide} />
                  <View style={styles.skeletonLine} />
                  <View style={styles.skeletonLineShort} />
                </View>
              </View>
            ))}
          </View>
        </View>
      );
    }

    if (filtered.length === 0) {
      return (
        <View style={styles.scroller}>
          <ListHeaderComponent />
          <View style={styles.emptyBlock}>
            <Icon name="clipboard" size={44} color={C.sub} />
            <Text style={styles.emptyTitle}>No matching orders</Text>
            <Text style={styles.emptySub}>
              {filter === 'all'
                ? 'Place your first order to get started.'
                : 'Try a different filter.'}
            </Text>
          </View>
        </View>
      );
    }

    return (
      <FlatList
        style={styles.scroller}
        data={flatListData}
        keyExtractor={(item, index) => 
          item.type === 'section' 
            ? `section-${item.label}-${index}` 
            : `order-${item.order?.id || index}`
        }
        renderItem={renderOrderItem}
        ListHeaderComponent={ListHeaderComponent}
        ListFooterComponent={() => <View style={{ height: 16 }} />}
        showsVerticalScrollIndicator={false}
        // Performance optimizations
        removeClippedSubviews={true}
        initialNumToRender={10}
        maxToRenderPerBatch={5}
        windowSize={10}
        updateCellsBatchingPeriod={50}
        getItemLayout={(data, index) => {
          const item = data?.[index];
          const height = item?.type === 'section' ? 40 : 120; // Section header: 40px, Order: 120px
          return {
            length: height,
            offset: (data || []).slice(0, index).reduce((acc: number, i: any) => {
              return acc + (i?.type === 'section' ? 40 : 120);
            }, 0),
            index,
          };
        }}
      />
    );
  },
  (prevProps, nextProps) => {
    // Custom comparison for better memoization
    return (
      prevProps.orders.length === nextProps.orders.length &&
      prevProps.loading === nextProps.loading &&
      prevProps.filter === nextProps.filter &&
      prevProps.orders.every(
        (o, i) => o.id === nextProps.orders[i]?.id && o.status === nextProps.orders[i]?.status
      )
    );
  }
);

OrdersList.displayName = 'OrdersList';

const styles = StyleSheet.create({
  scroller: {
    paddingHorizontal: 16,
  },
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
  filterBar: {
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 4,
    paddingBottom: 8,
  },
  filterPill: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 14,
    backgroundColor: '#F3F4F6',
  },
  filterPillActive: {
    backgroundColor: '#E0ECFF',
  },
  filterPillText: {
    fontSize: 13,
    color: '#6B7280',
    fontWeight: '600',
  },
  filterPillTextActive: {
    color: '#1D4ED8',
  },
  iconBtn: {
    padding: 6,
    borderRadius: 8,
    backgroundColor: '#F3F4F6',
  },
  skeletonBlock: {
    paddingTop: 8,
  },
  skeletonRow: {
    flexDirection: 'row',
    gap: 12,
    backgroundColor: '#fff',
    padding: 14,
    borderRadius: 12,
    marginTop: 10,
  },
  skeletonAccent: {
    width: 4,
    borderRadius: 6,
    backgroundColor: '#E5E7EB',
  },
  skeletonLineWide: {
    height: 12,
    backgroundColor: '#E5E7EB',
    borderRadius: 6,
    marginBottom: 8,
    width: '60%',
  },
  skeletonLine: {
    height: 10,
    backgroundColor: '#E5E7EB',
    borderRadius: 6,
    marginBottom: 8,
    width: '40%',
  },
  skeletonLineShort: {
    height: 10,
    backgroundColor: '#E5E7EB',
    borderRadius: 6,
    width: '28%',
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
  sectionDivider: {
    fontSize: 12,
    fontWeight: '700',
    color: '#6B7280',
    marginTop: 12,
    marginBottom: 2,
    paddingHorizontal: 2,
    letterSpacing: 0.3,
    textTransform: 'uppercase',
  },
  orderCardRow: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    marginTop: 10,
    shadowColor: '#000',
    shadowOpacity: 0.06,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 6,
    elevation: 2,
  },
  sideAccent: {
    width: 4,
    borderRadius: 6,
    marginRight: 12,
  },
  rowBetween: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: 6,
  },
  rowWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 6,
  },
  ticker: {
    fontSize: 16,
    fontWeight: '800',
    color: C.text,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 999,
    backgroundColor: '#EEF2FF',
  },
  badgeText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#1F2937',
  },
  badgeInfo: {
    backgroundColor: '#E3F2FD',
  },
  badgeSuccess: {
    backgroundColor: '#E7F7EE',
  },
  badgeDanger: {
    backgroundColor: '#FDECEC',
  },
  sub: {
    fontSize: 13,
    color: C.sub,
  },
  meta: {
    fontSize: 12,
    color: C.sub,
  },
  ghostDangerBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: '#FEE2E2',
  },
  ghostDangerText: {
    color: '#EF4444',
    fontWeight: '700',
    fontSize: 12,
  },
  note: {
    marginTop: 6,
    fontStyle: 'italic',
    color: C.sub,
    fontSize: 12,
  },
});

