/**
 * CollateralHealthCard
 * - Summarizes portfolio LTV and per-asset collateral/loan health
 * - Tapping a row calls onAssetPress(symbol) → opens LoanManagementModal
 */

import React, { useMemo } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

type Loan = {
  id: string;
  status: 'ACTIVE' | 'WARNING' | 'LIQUIDATED' | 'REPAID';
  collateralQuantity: string | number;
  loanAmount: string | number;
  cryptocurrency: { symbol: string };
};

interface Props {
  loans: Loan[];
  priceMap: Record<string, number>; // { BTC: 67000, ETH: 3400, ... }
  onAssetPress: (symbol: string) => void;
}

const CollateralHealthCard: React.FC<Props> = ({ loans = [], priceMap = {}, onAssetPress }) => {
  const { perAsset, totals } = useMemo(() => {
    const per: Record<string, { collateralUsd: number; loanUsd: number; statusCounts: Record<string, number> }> = {};
    let totalCollat = 0;
    let totalLoans = 0;

    loans.forEach((l) => {
      const sym = l.cryptocurrency?.symbol || '???';
      const px = priceMap[sym] || 0;
      const qty = Number(l.collateralQuantity || 0);
      const loan = Number(l.loanAmount || 0);
      const collatUsd = qty * px;

      if (!per[sym]) per[sym] = { collateralUsd: 0, loanUsd: 0, statusCounts: {} };
      per[sym].collateralUsd += collatUsd;
      per[sym].loanUsd += loan;
      per[sym].statusCounts[l.status] = (per[sym].statusCounts[l.status] || 0) + 1;

      totalCollat += collatUsd;
      totalLoans += loan;
    });

    return {
      perAsset: per,
      totals: {
        totalCollat,
        totalLoans,
        ltv: totalCollat > 0 ? (totalLoans / totalCollat) * 100 : 0,
      },
    };
  }, [loans, priceMap]);

  const ltvPill = (ltv: number) => {
    let color = '#34C759', label = 'SAFE';
    if (ltv > 35 && ltv <= 40) { color = '#FF9500'; label = 'CAUTION'; }
    else if (ltv > 40 && ltv <= 50) { color = '#F59E0B'; label = 'AT RISK'; }
    else if (ltv > 50) { color = '#FF3B30'; label = 'DANGER'; }
    return { color, label };
  };

  const fmt = (n: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(n);

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <Text style={styles.title}>Collateral Health</Text>
        <View style={[styles.ltvPill, { backgroundColor: `${ltvPill(totals.ltv).color}22`, borderColor: ltvPill(totals.ltv).color }]}>
          <Icon name="shield" size={14} color={ltvPill(totals.ltv).color} />
          <Text style={[styles.ltvPillText, { color: ltvPill(totals.ltv).color }]}>
            {ltvPill(totals.ltv).label} • {totals.ltv.toFixed(1)}% LTV
          </Text>
        </View>
      </View>

      {/* Totals */}
      <View style={styles.totalsRow}>
        <View>
          <Text style={styles.subLabel}>Collateral</Text>
          <Text style={styles.totalsValue}>{fmt(totals.totalCollat)}</Text>
        </View>
        <View>
          <Text style={styles.subLabel}>Loans</Text>
          <Text style={styles.totalsValue}>{fmt(totals.totalLoans)}</Text>
        </View>
      </View>

      {/* Per-asset rows */}
      {Object.entries(perAsset).map(([symbol, data]) => {
        const assetLtv = data.collateralUsd > 0 ? (data.loanUsd / data.collateralUsd) * 100 : 0;
        const pill = ltvPill(assetLtv);
        return (
          <TouchableOpacity
            key={symbol}
            style={styles.assetRow}
            activeOpacity={0.85}
            onPress={() => onAssetPress(symbol)}
          >
            <View style={styles.assetLeft}>
              <View style={styles.iconCircle}>
                <Text style={styles.symbol}>{symbol.slice(0, 3).toUpperCase()}</Text>
              </View>
              <View>
                <Text style={styles.assetTitle}>{symbol}</Text>
                <Text style={styles.assetSub}>{fmt(data.collateralUsd)} collateral</Text>
              </View>
            </View>
            <View style={styles.assetRight}>
              <Text style={styles.loanValue}>{fmt(data.loanUsd)}</Text>
              <View style={[styles.assetLtvPill, { backgroundColor: `${pill.color}22` }]}>
                <Text style={[styles.assetLtvText, { color: pill.color }]}>{assetLtv.toFixed(1)}%</Text>
              </View>
              <Icon name="chevron-right" size={18} color="#CBD5E1" />
            </View>
          </TouchableOpacity>
        );
      })}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginTop: 16,
    marginBottom: 20,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.08, shadowRadius: 4, elevation: 2,
  },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  title: { fontSize: 18, fontWeight: '700', color: '#111827' },
  ltvPill: { flexDirection: 'row', alignItems: 'center', gap: 6, borderWidth: 1, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 999 },
  ltvPillText: { fontSize: 12, fontWeight: '700' },
  totalsRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8, marginBottom: 4 },
  subLabel: { fontSize: 12, color: '#6B7280' },
  totalsValue: { fontSize: 16, fontWeight: '600', color: '#111827' },
  assetRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 12, borderTopWidth: 1, borderTopColor: '#F3F4F6' },
  assetLeft: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  iconCircle: { width: 36, height: 36, borderRadius: 18, backgroundColor: '#EFF6FF', alignItems: 'center', justifyContent: 'center' },
  symbol: { fontSize: 12, fontWeight: '700', color: '#007AFF' },
  assetTitle: { fontSize: 15, fontWeight: '600', color: '#111827' },
  assetSub: { fontSize: 12, color: '#6B7280' },
  assetRight: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  loanValue: { fontSize: 14, fontWeight: '600', color: '#111827' },
  assetLtvPill: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 999 },
  assetLtvText: { fontSize: 12, fontWeight: '700' },
});

export default CollateralHealthCard;