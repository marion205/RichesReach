/**
 * PositionManagementModal (AAVE)
 * - Filters positions by reserve symbol
 * - Actions: Supply (add collateral), Repay (wallet or aTokens)
 * - Shows HF/LTV/Liq. Threshold and est. HF after repay
 */

import React, { useMemo, useState } from 'react';
import { View, Text, StyleSheet, Modal, TouchableOpacity, ScrollView, TextInput, Platform } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

type Tier = 'SAFE' | 'WARN' | 'AT_RISK' | 'LIQUIDATE';

type AAVEPosition = {
  id: string;                        // can be reserve address or composed id
  reserveSymbol: string;             // e.g., 'ETH'
  debtUsd: number;                   // total debt in USD for this reserve
  debtMode?: 'variable' | 'stable';
  variableApr?: number;              // e.g., 0.036
  stableApr?: number;                // e.g., 0.048
  collateralAmount: number;          // token amount used as collateral
  collateralUsd: number;             // USD value of collateral for this reserve
  ltv: number;                       // 0..1 (AAVE LTV)
  liqThreshold: number;              // 0..1 (AAVE liquidation threshold)
  healthFactor: number;              // current HF
  // convenient balances for validation (optional)
  walletBalanceUsd?: number;         // user wallet USD of the same asset used to repay
  aTokenBalanceUsd?: number;         // user aToken USD balance (same asset)
};

interface Props {
  visible: boolean;
  onClose: () => void;
  symbol: string | null;                   // filter by reserve symbol
  positions: AAVEPosition[];
  onSupply: (reserveSymbol: string) => void;
  onRepayConfirm: (args: {
    positionId: string;
    reserveSymbol: string;
    amountUsd: number;
    source: 'wallet' | 'aTokens';
  }) => void;
  isRepaying?: boolean;
}

const fmtUsd = (n: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(Math.max(0, n || 0));

const pct = (n: number) => `${(n * 100).toFixed(0)}%`;

const tierFromHF = (hf: number): Tier => {
  if (!isFinite(hf) || hf > 1.5) return 'SAFE';
  if (hf > 1.2) return 'WARN';
  if (hf > 1.0) return 'AT_RISK';
  return 'LIQUIDATE';
};

const tierColor = (t: Tier) =>
  ({ SAFE:'#10B981', WARN:'#F59E0B', AT_RISK:'#DC2626', LIQUIDATE:'#7C2D12' }[t] || '#6B7280');

const PositionManagementModal: React.FC<Props> = ({
  visible,
  onClose,
  symbol,
  positions = [],
  onSupply,
  onRepayConfirm,
  isRepaying = false,
}) => {
  const [repayOpen, setRepayOpen] = useState(false);
  const [active, setActive] = useState<AAVEPosition | null>(null);
  const [repayAmount, setRepayAmount] = useState<string>(''); // USD
  const [repaySource, setRepaySource] = useState<'wallet' | 'aTokens'>('wallet');

  const filtered = useMemo(
    () => positions.filter(p => (symbol ? p.reserveSymbol === symbol : true)),
    [positions, symbol]
  );

  const openRepay = (p: AAVEPosition) => {
    setActive(p);
    setRepayAmount('');
    setRepaySource('wallet');
    setRepayOpen(true);
  };

  const closeRepay = () => {
    setRepayOpen(false);
    setActive(null);
    setRepayAmount('');
  };

  const setPercent = (p: number) => {
    if (!active) return;
    const amt = (p / 100) * active.debtUsd;
    setRepayAmount(amt.toFixed(2));
  };

  const est = (() => {
    if (!active) return null;
    const amt = Math.max(0, parseFloat(repayAmount || '0') || 0);
    const newDebt = Math.max(0, active.debtUsd - amt);
    // HF = (collateralUsd * liqThreshold) / debt
    const hf = newDebt > 0 ? (active.collateralUsd * active.liqThreshold) / newDebt : Infinity;
    const ltvPct = newDebt > 0 ? (newDebt / Math.max(0.01, active.collateralUsd)) * 100 : 0;
    const capUsd = active.collateralUsd * active.ltv;
    const headroom = Math.max(0, capUsd - newDebt);
    const tier = tierFromHF(hf);
    return { newDebt, hf, ltvPct, capUsd, headroom, tier };
  })();

  const repayDisabled = (() => {
    if (!active) return true;
    const amt = parseFloat(repayAmount || '0');
    if (!isFinite(amt) || amt <= 0) return true;
    if (amt < 10) return true; // minimum
    if (amt > active.debtUsd) return true;
    // source balance checks if provided
    if (repaySource === 'wallet' && active.walletBalanceUsd != null && amt > active.walletBalanceUsd) return true;
    if (repaySource === 'aTokens' && active.aTokenBalanceUsd != null && amt > active.aTokenBalanceUsd) return true;
    return false;
  })();

  const confirm = () => {
    if (!active || repayDisabled) return;
    const amt = parseFloat(repayAmount || '0');
    onRepayConfirm({
      positionId: active.id,
      reserveSymbol: active.reserveSymbol,
      amountUsd: amt,
      source: repaySource,
    });
    closeRepay();
  };

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet" onRequestClose={onClose}>
      {/* Top bar */}
      <View style={styles.header}>
        <TouchableOpacity onPress={onClose} style={styles.headerBtn} accessibilityLabel="Close">
          <Icon name="x" size={22} color="#111827" />
        </TouchableOpacity>
        <Text style={styles.title}>{symbol ? `${symbol} Positions` : 'AAVE Positions'}</Text>
        <View style={styles.headerBtn} />
      </View>

      {/* Body */}
      <ScrollView style={styles.body} showsVerticalScrollIndicator={false}>
        {filtered.length === 0 ? (
          <View style={styles.empty}>
            <Icon name="inbox" size={40} color="#C7C7CC" />
            <Text style={styles.emptyTitle}>No Positions</Text>
            <Text style={styles.emptySub}>
              You don't have any {symbol ? symbol + ' ' : ''}debt/collateral positions yet.
            </Text>
          </View>
        ) : (
          filtered.map((p) => {
            const tier = tierFromHF(p.healthFactor);
            return (
              <View key={p.id} style={styles.card}>
                <View style={styles.cardHeader}>
                  <Text style={styles.cardTitle}>{p.reserveSymbol}</Text>
                  <View style={[styles.badge, { backgroundColor: tierColor(tier) }]}>
                    <Text style={styles.badgeText}>{tier}</Text>
                  </View>
                </View>

                <View style={styles.row}><Text style={styles.label}>Health Factor</Text>
                  <Text style={[styles.value, { color: tierColor(tier) }]}>{isFinite(p.healthFactor) ? p.healthFactor.toFixed(2) : '∞'}</Text>
                </View>
                <View style={styles.row}><Text style={styles.label}>Collateral</Text>
                  <Text style={styles.value}>{fmtUsd(p.collateralUsd)}</Text>
                </View>
                <View style={styles.row}><Text style={styles.label}>Debt</Text>
                  <Text style={styles.value}>{fmtUsd(p.debtUsd)}</Text>
                </View>
                <View style={styles.row}><Text style={styles.label}>LTV / Liq. Thresh.</Text>
                  <Text style={styles.value}>{pct(p.ltv)} / {pct(p.liqThreshold)}</Text>
                </View>
                {!!p.variableApr && (
                  <View style={styles.row}><Text style={styles.label}>Variable APR</Text>
                    <Text style={styles.value}>{(p.variableApr * 100).toFixed(2)}%</Text>
                  </View>
                )}
                {!!p.stableApr && (
                  <View style={styles.row}><Text style={styles.label}>Stable APR</Text>
                    <Text style={styles.value}>{(p.stableApr * 100).toFixed(2)}%</Text>
                  </View>
                )}

                <View style={styles.actions}>
                  <TouchableOpacity
                    style={[styles.actionBtn, styles.primary]}
                    onPress={() => onSupply(p.reserveSymbol)}
                  >
                    <Icon name="plus-circle" size={18} color="#FFFFFF" />
                    <Text style={styles.actionTextPrimary}>Supply</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={[styles.actionBtn, styles.secondary]}
                    onPress={() => openRepay(p)}
                  >
                    <Icon name="credit-card" size={18} color="#111827" />
                    <Text style={styles.actionTextSecondary}>Repay</Text>
                  </TouchableOpacity>
                </View>
              </View>
            );
          })
        )}
        <View style={{ height: 24 }} />
      </ScrollView>

      {/* ---- Repay Sheet ---- */}
      <Modal visible={repayOpen} animationType="slide" transparent onRequestClose={closeRepay}>
        <View style={styles.sheetBackdrop}>
          <TouchableOpacity style={{ flex: 1 }} activeOpacity={1} onPress={closeRepay} />
          <View style={styles.sheet}>
            <View style={styles.sheetHeader}>
              <Text style={styles.sheetTitle}>Repay Debt</Text>
              <TouchableOpacity onPress={closeRepay} style={styles.headerBtn}>
                <Icon name="x" size={22} color="#111827" />
              </TouchableOpacity>
            </View>

            {active && (
              <>
                <View style={styles.sheetRow}>
                  <Text style={styles.sheetLabel}>Outstanding</Text>
                  <Text style={styles.sheetValue}>{fmtUsd(active.debtUsd)}</Text>
                </View>

                {/* Source toggle */}
                <View style={styles.segment}>
                  <TouchableOpacity
                    style={[styles.segmentBtn, repaySource === 'wallet' && styles.segmentOn]}
                    onPress={() => setRepaySource('wallet')}
                  >
                    <Text style={[styles.segmentText, repaySource === 'wallet' && styles.segmentTextOn]}>
                      Wallet
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.segmentBtn, repaySource === 'aTokens' && styles.segmentOn]}
                    onPress={() => setRepaySource('aTokens')}
                  >
                    <Text style={[styles.segmentText, repaySource === 'aTokens' && styles.segmentTextOn]}>
                      aTokens
                    </Text>
                  </TouchableOpacity>
                </View>

                {/* Balances (if provided) */}
                <View style={styles.sheetRow}>
                  <Text style={styles.sheetLabel}>Balance ({repaySource})</Text>
                  <Text style={styles.sheetValue}>
                    {repaySource === 'wallet'
                      ? fmtUsd(active.walletBalanceUsd ?? NaN)
                      : fmtUsd(active.aTokenBalanceUsd ?? NaN)}
                  </Text>
                </View>

                {/* Amount */}
                <View style={styles.inputWrap}>
                  <Text style={styles.inputLabel}>Amount (USD)</Text>
                  <View style={styles.inputBox}>
                    <TextInput
                      style={styles.input}
                      value={repayAmount}
                      onChangeText={setRepayAmount}
                      placeholder="0.00"
                      keyboardType={Platform.select({ ios: 'decimal-pad', android: 'numeric' })}
                      autoCapitalize="none"
                    />
                  </View>
                  <View style={styles.quickRow}>
                    {[25, 50, 75, 100].map((p) => (
                      <TouchableOpacity key={p} style={styles.quickBtn} onPress={() => setPercent(p)}>
                        <Text style={styles.quickBtnText}>{p}%</Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </View>

                {/* Estimations */}
                <View style={styles.breakdown}>
                  <Text style={styles.breakdownTitle}>After Repay (est.)</Text>
                  <View style={styles.sheetRow}>
                    <Text style={styles.sheetLabel}>Debt</Text>
                    <Text style={styles.sheetValue}>{fmtUsd(est?.newDebt ?? 0)}</Text>
                  </View>
                  <View style={styles.sheetRow}>
                    <Text style={styles.sheetLabel}>Health Factor</Text>
                    <Text style={[styles.sheetValue, { color: tierColor(est?.tier || 'SAFE') }]}>
                      {est ? (isFinite(est.hf) ? est.hf.toFixed(2) : '∞') : '--'}
                    </Text>
                  </View>
                  <View style={styles.sheetRow}>
                    <Text style={styles.sheetLabel}>LTV</Text>
                    <Text style={styles.sheetValue}>{est ? `${est.ltvPct.toFixed(1)}%` : '--'}</Text>
                  </View>
                </View>

                {/* Helper / validation */}
                <Text style={[
                  styles.helper,
                  repayDisabled ? { color: '#EF4444' } : { color: '#10B981' },
                ]}>
                  {(() => {
                    if (!active) return '';
                    const amt = parseFloat(repayAmount || '0');
                    if (!isFinite(amt) || amt <= 0) return 'Enter an amount to repay.';
                    if (amt < 10) return 'Minimum repayment is $10.';
                    if (amt > active.debtUsd) return 'Amount exceeds outstanding debt.';
                    if (repaySource === 'wallet' && active.walletBalanceUsd != null && amt > active.walletBalanceUsd)
                      return 'Insufficient wallet balance.';
                    if (repaySource === 'aTokens' && active.aTokenBalanceUsd != null && amt > active.aTokenBalanceUsd)
                      return 'Insufficient aToken balance.';
                    return 'Looks good — ready to repay.';
                  })()}
                </Text>

                <TouchableOpacity
                  style={[styles.confirmBtn, (repayDisabled || isRepaying) && { backgroundColor: '#9CA3AF' }]}
                  disabled={repayDisabled || isRepaying}
                  onPress={confirm}
                >
                  <Text style={styles.confirmText}>{isRepaying ? 'Processing…' : 'Confirm Repayment'}</Text>
                </TouchableOpacity>
              </>
            )}
          </View>
        </View>
      </Modal>
    </Modal>
  );
};

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 20, paddingTop: 14, paddingBottom: 12, backgroundColor: '#FFF',
    borderBottomWidth: 1, borderBottomColor: '#E5E7EB',
  },
  headerBtn: { width: 32, height: 32, alignItems: 'center', justifyContent: 'center' },
  title: { fontSize: 18, fontWeight: '700', color: '#111827' },
  body: { flex: 1, backgroundColor: '#F8F9FA', paddingHorizontal: 20, paddingTop: 16 },

  empty: { alignItems: 'center', paddingVertical: 48 },
  emptyTitle: { fontSize: 18, fontWeight: '600', color: '#111827', marginTop: 12 },
  emptySub: { fontSize: 14, color: '#6B7280', marginTop: 4, textAlign: 'center' },

  card: {
    backgroundColor: '#FFFFFF', borderRadius: 12, padding: 16, marginBottom: 12,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.08, shadowRadius: 4, elevation: 2,
  },
  cardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  cardTitle: { fontSize: 16, fontWeight: '700', color: '#111827' },
  badge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 999 },
  badgeText: { color: '#FFFFFF', fontSize: 12, fontWeight: '700' },

  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 6 },
  label: { fontSize: 13, color: '#6B7280' },
  value: { fontSize: 14, fontWeight: '600', color: '#111827' },

  actions: { flexDirection: 'row', gap: 8, marginTop: 12 },
  actionBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 12, borderRadius: 10 },
  primary: { backgroundColor: '#007AFF' },
  secondary: { backgroundColor: '#EEF2FF' },
  actionTextPrimary: { color: '#FFFFFF', fontSize: 14, fontWeight: '700', marginLeft: 8 },
  actionTextSecondary: { color: '#111827', fontSize: 14, fontWeight: '700', marginLeft: 8 },

  // Repay sheet
  sheetBackdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.25)', justifyContent: 'flex-end' },
  sheet: {
    backgroundColor: '#FFF', paddingHorizontal: 20, paddingTop: 16, paddingBottom: 24,
    borderTopLeftRadius: 16, borderTopRightRadius: 16,
  },
  sheetHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  sheetTitle: { fontSize: 18, fontWeight: '700', color: '#111827' },
  sheetRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 6 },
  sheetLabel: { fontSize: 13, color: '#6B7280' },
  sheetValue: { fontSize: 14, fontWeight: '700', color: '#111827' },

  segment: {
    flexDirection: 'row', backgroundColor: '#F3F4F6', borderRadius: 999, padding: 4, alignSelf: 'flex-start', marginTop: 6,
  },
  segmentBtn: { paddingVertical: 6, paddingHorizontal: 12, borderRadius: 999 },
  segmentOn: { backgroundColor: '#FFFFFF', borderWidth: 1, borderColor: '#E5E7EB' },
  segmentText: { fontSize: 12, fontWeight: '700', color: '#6B7280' },
  segmentTextOn: { color: '#111827' },

  inputWrap: { marginTop: 12 },
  inputLabel: { fontSize: 13, fontWeight: '600', color: '#111827', marginBottom: 6 },
  inputBox: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFFFFF', borderRadius: 12,
    paddingHorizontal: 14, paddingVertical: 10, borderWidth: 1, borderColor: '#E5E7EB',
  },
  input: { flex: 1, fontSize: 16, color: '#111827' },
  quickRow: { flexDirection: 'row', gap: 8, marginTop: 10 },
  quickBtn: { paddingHorizontal: 10, paddingVertical: 8, borderRadius: 999, backgroundColor: '#F3F4F6' },
  quickBtnText: { fontSize: 12, fontWeight: '700', color: '#111827' },

  breakdown: { marginTop: 14, paddingTop: 10, borderTopWidth: 1, borderTopColor: '#F3F4F6' },
  breakdownTitle: { fontSize: 14, fontWeight: '700', color: '#111827', marginBottom: 4 },

  helper: { marginTop: 10, fontSize: 12 },
  confirmBtn: { marginTop: 12, backgroundColor: '#007AFF', borderRadius: 10, alignItems: 'center', paddingVertical: 12 },
  confirmText: { color: '#FFFFFF', fontSize: 15, fontWeight: '700' },
});

export default PositionManagementModal;
