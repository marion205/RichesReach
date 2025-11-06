import React, { useMemo, useState, useCallback, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  useColorScheme,
  ActivityIndicator,
  Alert,
  FlatList,
  RefreshControl,
  ListRenderItemInfo,
  ViewStyle,
} from 'react-native';
import Icon from '@expo/vector-icons/Feather';
import { useQuery } from '@apollo/client';
import { GET_SMART_ALERTS, GET_ALERT_CATEGORIES } from '../../../graphql/smartAlertsQueries';

interface SmartAlert {
  id: string;
  type: string;
  priority: 'high' | 'medium' | 'low';
  category: string;
  title: string;
  message: string;
  details: Record<string, any>;
  actionable: boolean;
  suggested_actions: string[];
  coaching_tip: string;
  timestamp: string;
}

interface AlertCategory {
  category: string;
  name: string;
  description: string;
  icon: string;
  color: string;
}

type Props = {
  portfolioId?: string;
  timeframe?: string;
  style?: ViewStyle | ViewStyle[];
};

const PRIORITY_ORDER: Record<SmartAlert['priority'], number> = {
  high: 3,
  medium: 2,
  low: 1,
};

export default function SmartAlertsCard({ portfolioId, timeframe = '1M', style }: Props) {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [manualRefreshing, setManualRefreshing] = useState(false);

  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';

  const palette = {
    text: isDark ? '#E2E8F0' : '#1F2937',
    sub: isDark ? '#A1A7AF' : '#6B7280',
    bg: isDark ? '#0F1115' : '#FFFFFF',
    cardBg: isDark ? '#161A20' : '#F9FAFB',
    border: isDark ? '#252A32' : '#E5E7EB',
    hairline: isDark ? '#1D2229' : '#ECEFF3',
    accent: isDark ? '#3B82F6' : '#2563EB',
    success: isDark ? '#10B981' : '#059669',
    warning: isDark ? '#F59E0B' : '#D97706',
    error: isDark ? '#EF4444' : '#DC2626',
    info: isDark ? '#06B6D4' : '#0891B2',
    chipBg: isDark ? '#1B1F26' : '#EFF2F6',
  };

  const {
    data: alertsData,
    loading: alertsLoading,
    error: alertsError,
    refetch,
    networkStatus,
  } = useQuery(GET_SMART_ALERTS, {
    variables: { portfolioId, timeframe },
    pollInterval: 30000,
    fetchPolicy: 'cache-and-network',
    notifyOnNetworkStatusChange: true,
    errorPolicy: 'all', // Continue rendering on error
    // Add timeout to prevent infinite loading
    context: {
      fetchOptions: {
        timeout: 10000, // 10 second timeout
      },
    },
  });

  const { data: categoriesData } = useQuery(GET_ALERT_CATEGORIES);
  const alerts: SmartAlert[] = alertsData?.smartAlerts ?? [];
  const categories: AlertCategory[] = categoriesData?.alertCategories ?? [];

  const catMap = useMemo(() => {
    const map = new Map<string, AlertCategory>();
    categories.forEach((c) => map.set(c.category, c));
    return map;
  }, [categories]);

  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    alerts.forEach((a) => {
      counts[a.category] = (counts[a.category] ?? 0) + 1;
    });
    return counts;
  }, [alerts]);

  const getPriorityColor = useCallback(
    (p: SmartAlert['priority']) =>
      p === 'high' ? palette.error : p === 'medium' ? palette.warning : palette.info,
    [palette]
  );

  const getPriorityIcon = (p: SmartAlert['priority']) =>
    p === 'high' ? 'alert-triangle' : p === 'medium' ? 'alert-circle' : 'info';

  const getCategoryBadge = (cat: string) => {
    const meta = catMap.get(cat);
    return {
      icon: meta?.icon ?? 'bell',
      color: meta?.color ?? palette.sub,
      name: meta?.name ?? cat,
    };
  };

  const formatTimestamp = (timestamp: string) => {
    // keep your readable "time ago"
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.max(0, now.getTime() - date.getTime());
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'Just now';
    if (mins < 60) return `${mins}m ago`;
    if (mins < 1440) return `${Math.floor(mins / 60)}h ago`;
    return date.toLocaleDateString();
  };

  const filteredSorted = useMemo(() => {
    const base =
      selectedCategory === 'all'
        ? alerts
        : alerts.filter((a) => a.category === selectedCategory);

    // keep the server priority, but sort deterministic locally too
    return [...base].sort((a, b) => {
      const pa = PRIORITY_ORDER[a.priority];
      const pb = PRIORITY_ORDER[b.priority];
      if (pa !== pb) return pb - pa;
      return (new Date(b.timestamp).getTime() || 0) - (new Date(a.timestamp).getTime() || 0);
    });
  }, [alerts, selectedCategory]);

  const onRefresh = useCallback(async () => {
    try {
      setManualRefreshing(true);
      await refetch();
    } finally {
      setManualRefreshing(false);
    }
  }, [refetch]);

  const toggleExpanded = useCallback((id: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  const handleAlertAction = useCallback((alert: SmartAlert) => {
    if (alert.actionable && alert.suggested_actions.length > 0) {
      Alert.alert(
        alert.title,
        `Suggested actions:\n\n${alert.suggested_actions
          .map((a, i) => `${i + 1}. ${a}`)
          .join('\n')}\n\n${alert.coaching_tip}`,
        [
          { text: 'Dismiss', style: 'cancel' },
          { text: 'View Details', onPress: () => toggleExpanded(alert.id) },
        ]
      );
    }
  }, [toggleExpanded]);

  const renderItem = useCallback(
    ({ item }: ListRenderItemInfo<SmartAlert>) => {
      const expandedNow = expanded.has(item.id);
      const priorityColor = getPriorityColor(item.priority);
      const cat = getCategoryBadge(item.category);

      return (
        <TouchableOpacity
          key={item.id}
          activeOpacity={0.8}
          onPress={() => handleAlertAction(item)}
          accessibilityRole="button"
          accessibilityLabel={`${item.title}. Priority ${item.priority}`}
          style={[
            styles.alertCard,
            {
              backgroundColor: palette.bg,
              borderColor: palette.border,
              borderLeftColor: priorityColor,
            },
          ]}
        >
          <View style={styles.alertHeader}>
            <View style={styles.alertTitleRow}>
              <Icon name={getPriorityIcon(item.priority) as any} size={16} color={priorityColor} />
              <Text style={[styles.alertTitle, { color: palette.text }]} numberOfLines={2}>
                {item.title}
              </Text>
              <View style={[styles.priorityBadge, { backgroundColor: priorityColor }]}>
                <Text style={styles.priorityBadgeText}>{item.priority.toUpperCase()}</Text>
              </View>
            </View>

            <View style={styles.metaRow}>
              <View style={styles.catPill}>
                <Icon name={cat.icon as any} size={12} color={cat.color} />
                <Text style={[styles.catText, { color: palette.sub }]} numberOfLines={1}>
                  {cat.name}
                </Text>
              </View>
              <Text style={[styles.alertTimestamp, { color: palette.sub }]}>{formatTimestamp(item.timestamp)}</Text>
            </View>
          </View>

          <Text style={[styles.alertMessage, { color: palette.sub }]}>{item.message}</Text>

          {expandedNow && (
            <View style={[styles.alertDetails, { borderTopColor: palette.hairline }]}>
              {item.suggested_actions.length > 0 && (
                <View style={styles.suggestedActions}>
                  <Text style={[styles.sectionTitle, { color: palette.text }]}>Suggested Actions</Text>
                  {item.suggested_actions.map((action, idx) => (
                    <Text key={idx} style={[styles.actionItem, { color: palette.sub }]}>
                      • {action}
                    </Text>
                  ))}
                </View>
              )}
              <View style={styles.coachingTip}>
                <Icon name="zap" size={14} color={palette.warning} />
                <Text style={[styles.coachingTipText, { color: palette.sub }]}>{item.coaching_tip}</Text>
              </View>
            </View>
          )}

          {item.actionable && (
            <View style={styles.alertFooter}>
              <TouchableOpacity
                style={[styles.actionButton, { backgroundColor: palette.accent }]}
                onPress={() => toggleExpanded(item.id)}
                accessibilityRole="button"
                accessibilityLabel={expandedNow ? 'Hide details' : 'View details'}
              >
                <Text style={styles.actionButtonText}>{expandedNow ? 'Hide Details' : 'View Details'}</Text>
                <Icon name={expandedNow ? 'chevron-up' : 'chevron-down'} size={14} color="#FFFFFF" />
              </TouchableOpacity>
            </View>
          )}
        </TouchableOpacity>
      );
    },
    [expanded, getPriorityColor, handleAlertAction, palette, toggleExpanded]
  );

  const listEmpty = (
    <View style={styles.emptyContainer}>
      <Icon name="check-circle" size={32} color={palette.success} />
      <Text style={[styles.emptyTitle, { color: palette.text }]}>All Good!</Text>
      <Text style={[styles.emptyText, { color: palette.sub }]}>
        No alerts right now. We'll notify you when there's something important.
      </Text>
    </View>
  );

  // Loading state (initial) - but timeout after 10 seconds
  const [loadingTimeout, setLoadingTimeout] = useState(false);
  useEffect(() => {
    if (alertsLoading && networkStatus !== 7) {
      const timeout = setTimeout(() => {
        setLoadingTimeout(true);
      }, 10000); // 10 second timeout
      return () => clearTimeout(timeout);
    } else {
      setLoadingTimeout(false);
    }
  }, [alertsLoading, networkStatus]);

  // Show loading only if not timed out and not in error state
  if (alertsLoading && networkStatus !== 7 && !loadingTimeout) {
    return (
      <View style={[styles.container, { backgroundColor: palette.cardBg }, style]}>
        <View style={styles.header}>
          <View style={styles.titleRow}>
            <Icon name="zap" size={20} color={palette.accent} />
            <Text style={[styles.title, { color: palette.text }]}>Smart Alerts</Text>
          </View>
          <ActivityIndicator size="small" color={palette.accent} />
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={palette.accent} />
          <Text style={[styles.loadingText, { color: palette.sub }]}>Analyzing your portfolio…</Text>
        </View>
      </View>
    );
  }

  return (
    <View style={[styles.container, { backgroundColor: palette.cardBg }, style]}>
      <View style={styles.header}>
        <View style={styles.titleRow}>
          <Icon name="zap" size={20} color={palette.accent} />
          <Text style={[styles.title, { color: palette.text }]}>Smart Alerts</Text>
          <View style={[styles.badge, { backgroundColor: palette.accent }]}>
            <Text style={styles.badgeText}>{filteredSorted.length}</Text>
          </View>
        </View>

        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
          {alertsError && (
            <View style={[styles.errorPill, { borderColor: palette.border }]}>
              <Icon name="alert-circle" size={14} color={palette.error} />
              <Text style={{ color: palette.error, fontSize: 12, marginLeft: 6 }}>Sync issue</Text>
            </View>
          )}
          <TouchableOpacity onPress={() => refetch()} accessibilityRole="button" accessibilityLabel="Refresh alerts">
            <Icon name="refresh-cw" size={18} color={palette.sub} />
          </TouchableOpacity>
        </View>
      </View>

      {/* Category filter row */}
      <FlatList
        data={[{ category: 'all', name: 'All', icon: 'grid', color: palette.accent }, ...categories]}
        keyExtractor={(c) => c.category}
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={{ paddingRight: 8 }}
        renderItem={({ item }) => {
          const isAll = item.category === 'all';
          const active = selectedCategory === item.category;
          const badge =
            isAll ? alerts.length : (categoryCounts[item.category] ?? 0);
          const tint = isAll ? palette.accent : (catMap.get(item.category)?.color ?? palette.sub);

          return (
            <TouchableOpacity
              onPress={() => setSelectedCategory(item.category)}
              activeOpacity={0.85}
              accessibilityRole="button"
              accessibilityLabel={`Filter ${item.name}`}
              style={[
                styles.categoryChip,
                {
                  backgroundColor: active ? tint : palette.chipBg,
                  borderColor: palette.border,
                },
              ]}
            >
              <Icon
                name={(item.icon as any) ?? 'bell'}
                size={14}
                color={active ? '#fff' : tint}
                style={styles.categoryIcon}
              />
              <Text
                style={[
                  styles.categoryChipText,
                  { color: active ? '#fff' : palette.text },
                ]}
                numberOfLines={1}
              >
                {item.name}
              </Text>
              <View style={[styles.catBadge, { backgroundColor: active ? '#fff2' : '#00000010' }]}>
                <Text style={{ fontSize: 10, color: active ? '#fff' : palette.sub }}>{badge}</Text>
              </View>
            </TouchableOpacity>
          );
        }}
        style={{ marginBottom: 12 }}
      />

      {/* Alerts list */}
      <FlatList
        data={filteredSorted}
        keyExtractor={(a) => a.id}
        renderItem={renderItem}
        ListEmptyComponent={listEmpty}
        ItemSeparatorComponent={() => <View style={[styles.sep, { backgroundColor: palette.hairline }]} />}
        refreshControl={
          <RefreshControl
            refreshing={manualRefreshing}
            onRefresh={onRefresh}
            tintColor={palette.accent}
          />
        }
        showsVerticalScrollIndicator={false}
        style={{ maxHeight: 420 }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { borderRadius: 12, padding: 16, marginVertical: 8 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  titleRow: { flexDirection: 'row', alignItems: 'center' },
  title: { fontSize: 18, fontWeight: '600', marginLeft: 8 },
  badge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 10, marginLeft: 8 },
  badgeText: { color: '#FFFFFF', fontSize: 12, fontWeight: '600' },

  // inline error pill
  errorPill: { flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderRadius: 999, paddingHorizontal: 8, paddingVertical: 4 },

  // categories
  categoryChip: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 16, borderWidth: 1, marginRight: 8 },
  categoryIcon: { marginRight: 6 },
  categoryChipText: { fontSize: 12, fontWeight: '600', maxWidth: 140 },
  catBadge: { marginLeft: 8, borderRadius: 999, paddingHorizontal: 6, paddingVertical: 2 },

  // list items
  sep: { height: 8, opacity: 0 }, // spacing between cards (card has own margins)
  alertCard: { borderRadius: 10, padding: 12, borderWidth: 1, borderLeftWidth: 4 },
  alertHeader: { marginBottom: 8 },
  alertTitleRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 4 },
  alertTitle: { fontSize: 14, fontWeight: '700', marginLeft: 6, flex: 1 },
  priorityBadge: { paddingHorizontal: 6, paddingVertical: 2, borderRadius: 4 },
  priorityBadgeText: { color: '#FFFFFF', fontSize: 10, fontWeight: '700' },

  metaRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  catPill: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  catText: { fontSize: 11 },

  alertTimestamp: { fontSize: 11 },
  alertMessage: { fontSize: 13, lineHeight: 18 },

  alertDetails: { marginTop: 12, paddingTop: 12, borderTopWidth: 1 },
  suggestedActions: { marginBottom: 12 },
  sectionTitle: { fontSize: 12, fontWeight: '700', marginBottom: 6 },
  actionItem: { fontSize: 12, lineHeight: 16, marginBottom: 2 },

  coachingTip: { flexDirection: 'row', alignItems: 'flex-start' },
  coachingTipText: { fontSize: 12, fontStyle: 'italic', marginLeft: 6, flex: 1, lineHeight: 16 },

  alertFooter: { marginTop: 12, alignItems: 'flex-end' },
  actionButton: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 6 },
  actionButtonText: { color: '#FFFFFF', fontSize: 12, fontWeight: '600', marginRight: 6 },

  // loading / empty
  loadingContainer: { alignItems: 'center', paddingVertical: 32 },
  loadingText: { marginTop: 12, fontSize: 14, textAlign: 'center' },
  emptyContainer: { alignItems: 'center', paddingVertical: 32 },
  emptyTitle: { fontSize: 16, fontWeight: '700', marginTop: 12 },
  emptyText: { fontSize: 14, textAlign: 'center', marginTop: 4, lineHeight: 20 },
});
