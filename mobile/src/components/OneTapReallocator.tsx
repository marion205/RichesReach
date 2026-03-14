/**
 * OneTapReallocator
 * =================
 * A slider-based UI for instantly redirecting money to investments.
 * From the blueprint: "User toggles leaks OFF, sees future value, confirms with one tap."
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  Animated,
  Switch,
  ScrollView,
} from 'react-native';
import { Feather } from '@expo/vector-icons';
import { LinearGradient } from 'expo-linear-gradient';

interface LeakItem {
  id: string;
  name: string;
  amount: number;
  category: string;
  lastUsed?: string;
  usage?: 'none' | 'low' | 'medium' | 'high';
}

interface OneTapReallocatorProps {
  leaks: LeakItem[];
  onConfirm: (redirectedLeaks: LeakItem[], totalAmount: number, destinationEtf: string) => void;
  onCancel?: () => void;
}

const D = {
  green:         '#10B981',
  greenFaint:    '#D1FAE5',
  indigo:        '#6366F1',
  indigoFaint:   '#EEF2FF',
  amber:         '#F59E0B',
  red:           '#EF4444',
  navy:          '#0B1426',
  white:         '#FFFFFF',
  textPrimary:   '#0F172A',
  textSecondary: '#64748B',
  textMuted:     '#94A3B8',
  card:          '#FFFFFF',
  bg:            '#F1F5F9',
};

const DEMO_LEAKS: LeakItem[] = [
  { id: '1', name: 'Unused Gym Membership', amount: 59, category: 'Fitness', lastUsed: '3 months ago', usage: 'none' },
  { id: '2', name: 'Duplicate Streaming', amount: 15.99, category: 'Entertainment', lastUsed: '2 weeks ago', usage: 'low' },
  { id: '3', name: 'Old Cloud Storage', amount: 9.99, category: 'Tech', lastUsed: 'Never', usage: 'none' },
  { id: '4', name: 'Magazine Subscription', amount: 12, category: 'Media', lastUsed: '6 months ago', usage: 'none' },
  { id: '5', name: 'Premium App Tier', amount: 29.99, category: 'Apps', lastUsed: '1 month ago', usage: 'low' },
];

const DESTINATION_ETFS = [
  { ticker: 'VTI', name: 'Total Stock Market', expense: '0.03%', description: 'The "Simple Path" default' },
  { ticker: 'VOO', name: 'S&P 500', expense: '0.03%', description: 'Large-cap focus' },
  { ticker: 'SCHD', name: 'Dividend Equity', expense: '0.06%', description: 'Income focus' },
];

function calculateFutureValue(monthly: number, years: number = 20): number {
  const r = 0.07 / 12;
  const n = years * 12;
  return monthly * (((1 + r) ** n - 1) / r);
}

export default function OneTapReallocator({
  leaks = DEMO_LEAKS,
  onConfirm,
  onCancel,
}: OneTapReallocatorProps) {
  const [selectedLeaks, setSelectedLeaks] = useState<Set<string>>(new Set());
  const [selectedEtf, setSelectedEtf] = useState(DESTINATION_ETFS[0]);
  const totalCountAnim = useRef(new Animated.Value(0)).current;
  const [displayTotal, setDisplayTotal] = useState(0);

  // Calculate totals
  const totalMonthly = leaks
    .filter(l => selectedLeaks.has(l.id))
    .reduce((sum, l) => sum + l.amount, 0);
  const futureValue = calculateFutureValue(totalMonthly);

  // Animate total
  useEffect(() => {
    Animated.spring(totalCountAnim, {
      toValue: totalMonthly,
      tension: 40,
      friction: 10,
      useNativeDriver: false,
    }).start();

    const listener = totalCountAnim.addListener(({ value }) => {
      setDisplayTotal(Math.round(value));
    });

    return () => totalCountAnim.removeListener(listener);
  }, [totalMonthly]);

  const toggleLeak = (leakId: string) => {
    const newSelected = new Set(selectedLeaks);
    if (newSelected.has(leakId)) {
      newSelected.delete(leakId);
    } else {
      newSelected.add(leakId);
    }
    setSelectedLeaks(newSelected);
  };

  const selectAll = () => {
    if (selectedLeaks.size === leaks.length) {
      setSelectedLeaks(new Set());
    } else {
      setSelectedLeaks(new Set(leaks.map(l => l.id)));
    }
  };

  const handleConfirm = () => {
    const redirected = leaks.filter(l => selectedLeaks.has(l.id));
    onConfirm(redirected, totalMonthly, selectedEtf.ticker);
  };

  const getUsageColor = (usage?: string) => {
    switch (usage) {
      case 'none': return D.red;
      case 'low': return D.amber;
      case 'medium': return D.green;
      default: return D.textMuted;
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Redirect to Wealth</Text>
        <Pressable onPress={selectAll} style={styles.selectAllBtn}>
          <Text style={styles.selectAllText}>
            {selectedLeaks.size === leaks.length ? 'Deselect All' : 'Select All'}
          </Text>
        </Pressable>
      </View>

      {/* Summary Card */}
      <LinearGradient
        colors={[D.navy, '#0A2518']}
        style={styles.summaryCard}
      >
        <View style={styles.summaryRow}>
          <View style={styles.summaryItem}>
            <Text style={styles.summaryLabel}>Monthly Redirect</Text>
            <Text style={styles.summaryValue}>${displayTotal}</Text>
          </View>
          <View style={styles.summaryDivider} />
          <View style={styles.summaryItem}>
            <Text style={styles.summaryLabel}>20-Year Value</Text>
            <Text style={[styles.summaryValue, { color: D.green }]}>
              ${(futureValue / 1000).toFixed(0)}K
            </Text>
          </View>
        </View>
        <View style={styles.destinationRow}>
          <Feather name="arrow-right" size={14} color={D.textMuted} />
          <Text style={styles.destinationText}>
            Into {selectedEtf.ticker} ({selectedEtf.name})
          </Text>
        </View>
      </LinearGradient>

      {/* Leak List */}
      <ScrollView style={styles.leakList} showsVerticalScrollIndicator={false}>
        {leaks.map((leak) => (
          <LeakToggleRow
            key={leak.id}
            leak={leak}
            isSelected={selectedLeaks.has(leak.id)}
            onToggle={() => toggleLeak(leak.id)}
            usageColor={getUsageColor(leak.usage)}
          />
        ))}

        {/* ETF Selection */}
        <View style={styles.etfSection}>
          <Text style={styles.etfSectionTitle}>Destination ETF</Text>
          {DESTINATION_ETFS.map((etf) => (
            <Pressable
              key={etf.ticker}
              style={[
                styles.etfOption,
                selectedEtf.ticker === etf.ticker && styles.etfOptionSelected,
              ]}
              onPress={() => setSelectedEtf(etf)}
            >
              <View style={styles.etfInfo}>
                <Text style={styles.etfTicker}>{etf.ticker}</Text>
                <Text style={styles.etfName}>{etf.name}</Text>
                <Text style={styles.etfDescription}>{etf.description}</Text>
              </View>
              <View style={styles.etfExpense}>
                <Text style={styles.etfExpenseText}>{etf.expense}</Text>
              </View>
              {selectedEtf.ticker === etf.ticker && (
                <View style={styles.etfCheck}>
                  <Feather name="check" size={16} color={D.white} />
                </View>
              )}
            </Pressable>
          ))}
        </View>
      </ScrollView>

      {/* Confirm Button */}
      <View style={styles.footer}>
        <Pressable
          style={[
            styles.confirmButton,
            selectedLeaks.size === 0 && styles.confirmButtonDisabled,
          ]}
          onPress={handleConfirm}
          disabled={selectedLeaks.size === 0}
        >
          <Text style={styles.confirmButtonText}>
            {selectedLeaks.size === 0
              ? 'Select Leaks to Redirect'
              : `Invest $${totalMonthly.toFixed(0)}/mo Now`}
          </Text>
          {selectedLeaks.size > 0 && (
            <Feather name="arrow-right" size={18} color={D.white} />
          )}
        </Pressable>
        {totalMonthly > 0 && (
          <Text style={styles.footerSubtext}>
            This will become ${(futureValue / 1000).toFixed(0)}K in 20 years
          </Text>
        )}
      </View>
    </View>
  );
}

// Leak Toggle Row Component
function LeakToggleRow({
  leak,
  isSelected,
  onToggle,
  usageColor,
}: {
  leak: LeakItem;
  isSelected: boolean;
  onToggle: () => void;
  usageColor: string;
}) {
  const scaleAnim = useRef(new Animated.Value(1)).current;

  const handlePress = () => {
    Animated.sequence([
      Animated.timing(scaleAnim, { toValue: 0.97, duration: 100, useNativeDriver: true }),
      Animated.timing(scaleAnim, { toValue: 1, duration: 100, useNativeDriver: true }),
    ]).start();
    onToggle();
  };

  const futureValue = calculateFutureValue(leak.amount);

  return (
    <Animated.View style={{ transform: [{ scale: scaleAnim }] }}>
      <Pressable
        style={[styles.leakRow, isSelected && styles.leakRowSelected]}
        onPress={handlePress}
      >
        <View style={[styles.usageIndicator, { backgroundColor: usageColor }]} />
        <View style={styles.leakInfo}>
          <Text style={styles.leakName}>{leak.name}</Text>
          <View style={styles.leakMeta}>
            <Text style={styles.leakCategory}>{leak.category}</Text>
            {leak.lastUsed && (
              <Text style={[styles.leakUsage, { color: usageColor }]}>
                • {leak.lastUsed}
              </Text>
            )}
          </View>
        </View>
        <View style={styles.leakAmounts}>
          <Text style={styles.leakAmount}>${leak.amount.toFixed(0)}/mo</Text>
          {isSelected && (
            <Text style={styles.leakFuture}>→ ${(futureValue / 1000).toFixed(0)}K</Text>
          )}
        </View>
        <Switch
          value={isSelected}
          onValueChange={onToggle}
          trackColor={{ false: '#E2E8F0', true: D.green + '50' }}
          thumbColor={isSelected ? D.green : '#94A3B8'}
        />
      </Pressable>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: D.bg,
  },
  
  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: D.textPrimary,
  },
  selectAllBtn: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: D.indigoFaint,
    borderRadius: 8,
  },
  selectAllText: {
    fontSize: 13,
    fontWeight: '600',
    color: D.indigo,
  },
  
  // Summary Card
  summaryCard: {
    marginHorizontal: 16,
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  summaryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  summaryItem: {
    flex: 1,
    alignItems: 'center',
  },
  summaryLabel: {
    fontSize: 11,
    color: 'rgba(255,255,255,0.6)',
    marginBottom: 4,
  },
  summaryValue: {
    fontSize: 28,
    fontWeight: '800',
    color: D.white,
  },
  summaryDivider: {
    width: 1,
    height: 40,
    backgroundColor: 'rgba(255,255,255,0.1)',
  },
  destinationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.1)',
  },
  destinationText: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.7)',
  },
  
  // Leak List
  leakList: {
    flex: 1,
    paddingHorizontal: 16,
  },
  leakRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: D.card,
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
  },
  leakRowSelected: {
    borderWidth: 1.5,
    borderColor: D.green,
    backgroundColor: D.greenFaint + '30',
  },
  usageIndicator: {
    width: 4,
    height: 36,
    borderRadius: 2,
    marginRight: 12,
  },
  leakInfo: {
    flex: 1,
  },
  leakName: {
    fontSize: 14,
    fontWeight: '600',
    color: D.textPrimary,
    marginBottom: 2,
  },
  leakMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  leakCategory: {
    fontSize: 11,
    color: D.textMuted,
  },
  leakUsage: {
    fontSize: 11,
  },
  leakAmounts: {
    alignItems: 'flex-end',
    marginRight: 12,
  },
  leakAmount: {
    fontSize: 14,
    fontWeight: '700',
    color: D.textPrimary,
  },
  leakFuture: {
    fontSize: 11,
    color: D.green,
    fontWeight: '600',
  },
  
  // ETF Section
  etfSection: {
    marginTop: 20,
    paddingTop: 20,
    borderTopWidth: 1,
    borderTopColor: D.card,
  },
  etfSectionTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: D.textPrimary,
    marginBottom: 12,
  },
  etfOption: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: D.card,
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  etfOptionSelected: {
    borderColor: D.green,
  },
  etfInfo: {
    flex: 1,
  },
  etfTicker: {
    fontSize: 16,
    fontWeight: '700',
    color: D.textPrimary,
  },
  etfName: {
    fontSize: 12,
    color: D.textSecondary,
  },
  etfDescription: {
    fontSize: 11,
    color: D.textMuted,
    marginTop: 2,
  },
  etfExpense: {
    backgroundColor: D.greenFaint,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    marginRight: 10,
  },
  etfExpenseText: {
    fontSize: 11,
    fontWeight: '600',
    color: D.green,
  },
  etfCheck: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: D.green,
    alignItems: 'center',
    justifyContent: 'center',
  },
  
  // Footer
  footer: {
    padding: 16,
    paddingBottom: 32,
    backgroundColor: D.bg,
  },
  confirmButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: D.green,
    paddingVertical: 16,
    borderRadius: 14,
  },
  confirmButtonDisabled: {
    backgroundColor: D.textMuted,
  },
  confirmButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: D.white,
  },
  footerSubtext: {
    fontSize: 12,
    color: D.textSecondary,
    textAlign: 'center',
    marginTop: 8,
  },
});
