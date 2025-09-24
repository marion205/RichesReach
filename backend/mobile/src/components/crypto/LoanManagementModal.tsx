/**
 * LoanManagementModal
 * - Filters loans by symbol
 * - Actions: Add Collateral, Repay (with bottom-sheet style flow)
 */

import React, { useMemo, useState } from 'react';
import { View, Text, StyleSheet, Modal, TouchableOpacity, ScrollView, TextInput } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

type Loan = {
  id: string;
  status: 'ACTIVE' | 'WARNING' | 'LIQUIDATED' | 'REPAID';
  collateralQuantity: string | number;
  loanAmount: string | number;          // outstanding principal (for demo)
  interestRate: string | number;        // decimal, e.g. 0.05
  cryptocurrency: { symbol: string };
  // optional demo field to illustrate days of accrual
  daysAccrued?: number;                 // e.g., 7
};

interface Props {
  visible: boolean;
  onClose: () => void;
  symbol: string | null;
  loans: Loan[];
  onAddCollateral: (loanId: string, symbol: string) => void;
  // NEW: provide repay handler with amount (USD). Fallback to old onRepayLoan if not provided.
  onRepayConfirm?: (loanId: string, symbol: string, amountUsd: number) => void;
  // Legacy fallback (kept for compatibility)
  onRepayLoan?: (loanId: string, symbol: string) => void;
  // Loading state for repay button
  isRepaying?: boolean;
}

const fmtUsd = (n: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(n);

const LoanManagementModal: React.FC<Props> = ({
  visible,
  onClose,
  symbol,
  loans = [],
  onAddCollateral,
  onRepayConfirm,
  onRepayLoan,
  isRepaying = false,
}) => {
  const [repayOpen, setRepayOpen] = useState(false);
  const [activeLoan, setActiveLoan] = useState<Loan | null>(null);
  const [repayAmount, setRepayAmount] = useState<string>('');

  const filtered = useMemo(
    () => loans.filter((l) => (symbol ? l.cryptocurrency?.symbol === symbol : true)),
    [loans, symbol]
  );

  const openRepay = (loan: Loan) => {
    setActiveLoan(loan);
    setRepayAmount('');
    setRepayOpen(true);
  };

  const closeRepay = () => {
    setRepayOpen(false);
    setActiveLoan(null);
    setRepayAmount('');
  };

  // --- simple interest accrual demo (not compounding) ---
  const computeBreakdown = (loan: Loan | null, amt: number) => {
    if (!loan) return { principal: 0, interest: 0 };
    const principalOutstanding = Number(loan.loanAmount || 0);
    const apr = Number(loan.interestRate || 0); // e.g. 0.05
    const days = Number(loan.daysAccrued ?? 7); // pretend 7 days accrued
    const interestAccrued = principalOutstanding * (apr / 365) * days;

    // Repayment first covers accrued interest, then principal
    const interestPortion = Math.min(amt, Math.max(0, interestAccrued));
    const principalPortion = Math.max(0, amt - interestPortion);

    return { principal: principalPortion, interest: interestPortion };
  };

  const validateAndConfirm = () => {
    if (!activeLoan) return;
    const outstanding = Number(activeLoan.loanAmount || 0);
    const amt = parseFloat(repayAmount || '0');

    if (Number.isNaN(amt) || amt <= 0) {
      return; // UX: disable state handles this
    }
    if (amt < 10) {
      return; // UX: disabled + helper text; keep silent here
    }
    if (amt > outstanding) {
      return;
    }

    // Prefer the new callback; fall back to legacy if provided
    if (onRepayConfirm) {
      onRepayConfirm(activeLoan.id, activeLoan.cryptocurrency.symbol, amt);
    } else if (onRepayLoan) {
      onRepayLoan(activeLoan.id, activeLoan.cryptocurrency.symbol);
    }
    closeRepay();
  };

  const repayDisabled = (() => {
    if (!activeLoan) return true;
    const amt = parseFloat(repayAmount || '0');
    const outstanding = Number(activeLoan.loanAmount || 0);
    return Number.isNaN(amt) || amt <= 0 || amt < 10 || amt > outstanding;
  })();

  const sliderPercent = (() => {
    if (!activeLoan) return 0;
    const amt = parseFloat(repayAmount || '0');
    const outstanding = Number(activeLoan.loanAmount || 0);
    if (!outstanding || amt <= 0) return 0;
    return Math.min(100, Math.max(0, (amt / outstanding) * 100));
  })();

  const setPercent = (p: number) => {
    if (!activeLoan) return;
    const outstanding = Number(activeLoan.loanAmount || 0);
    const amt = (p / 100) * outstanding;
    setRepayAmount(amt.toFixed(2));
  };

  const breakdown = computeBreakdown(activeLoan, parseFloat(repayAmount || '0'));

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet" onRequestClose={onClose}>
      {/* Top bar */}
      <View style={styles.header}>
        <TouchableOpacity onPress={onClose} style={styles.headerBtn}>
          <Icon name="x" size={22} color="#111827" />
        </TouchableOpacity>
        <Text style={styles.title}>{symbol ? `${symbol} Loans` : 'Loans'}</Text>
        <View style={styles.headerBtn} />
      </View>

      {/* Body */}
      <ScrollView style={styles.body} showsVerticalScrollIndicator={false}>
        {filtered.length === 0 ? (
          <View style={styles.empty}>
            <Icon name="inbox" size={40} color="#C7C7CC" />
            <Text style={styles.emptyTitle}>No Loans</Text>
            <Text style={styles.emptySub}>
              You don't have any {symbol ? symbol + ' ' : ''}SBLOC loans yet.
            </Text>
          </View>
        ) : (
          filtered.map((loan) => (
            <View key={loan.id} style={styles.card}>
              <View style={styles.cardHeader}>
                <Text style={styles.cardTitle}>{loan.cryptocurrency.symbol}</Text>
                <View style={[styles.badge, { backgroundColor: badgeColor(loan.status) }]}>
                  <Text style={styles.badgeText}>{loan.status}</Text>
                </View>
              </View>

              <View style={styles.row}>
                <Text style={styles.label}>Loan Amount</Text>
                <Text style={styles.value}>{fmtUsd(Number(loan.loanAmount || 0))}</Text>
              </View>
              <View style={styles.row}>
                <Text style={styles.label}>Collateral</Text>
                <Text style={styles.value}>
                  {Number(loan.collateralQuantity || 0).toFixed(6)} {loan.cryptocurrency.symbol}
                </Text>
              </View>
              <View style={styles.row}>
                <Text style={styles.label}>Interest</Text>
                <Text style={styles.value}>{(Number(loan.interestRate || 0) * 100).toFixed(2)}% APR</Text>
              </View>

              <View style={styles.actions}>
                <TouchableOpacity
                  style={[styles.actionBtn, styles.primary]}
                  onPress={() => onAddCollateral(loan.id, loan.cryptocurrency.symbol)}
                >
                  <Icon name="plus-circle" size={18} color="#FFFFFF" />
                  <Text style={styles.actionTextPrimary}>Add Collateral</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.actionBtn, styles.secondary]}
                  onPress={() => openRepay(loan)}
                >
                  <Icon name="credit-card" size={18} color="#111827" />
                  <Text style={styles.actionTextSecondary}>Repay</Text>
                </TouchableOpacity>
              </View>
            </View>
          ))
        )}
        <View style={{ height: 24 }} />
      </ScrollView>

      {/* ---- Repay Sheet ---- */}
      <Modal visible={repayOpen} animationType="slide" transparent onRequestClose={closeRepay}>
        <View style={styles.sheetBackdrop}>
          <TouchableOpacity style={{ flex: 1 }} activeOpacity={1} onPress={closeRepay} />
          <View style={styles.sheet}>
            <View style={styles.sheetHeader}>
              <Text style={styles.sheetTitle}>Repay Loan</Text>
              <TouchableOpacity onPress={closeRepay} style={styles.headerBtn}>
                <Icon name="x" size={22} color="#111827" />
              </TouchableOpacity>
            </View>

            {activeLoan && (
              <>
                <View style={styles.sheetRow}>
                  <Text style={styles.sheetLabel}>Outstanding</Text>
                  <Text style={styles.sheetValue}>{fmtUsd(Number(activeLoan.loanAmount || 0))}</Text>
                </View>

                <View style={styles.inputWrap}>
                  <Text style={styles.inputLabel}>Amount (USD)</Text>
                  <View style={styles.inputBox}>
                    <TextInput
                      style={styles.input}
                      value={repayAmount}
                      onChangeText={setRepayAmount}
                      placeholder="0.00"
                      keyboardType="numeric"
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
                  <Text style={styles.sliderHint}>Repaying ~{sliderPercent.toFixed(0)}% of outstanding</Text>
                  {/* You can swap this hint for a proper slider if you prefer a native slider component */}
                </View>

                {/* Breakdown */}
                {parseFloat(repayAmount || '0') > 0 && (
                  <View style={styles.breakdown}>
                    <Text style={styles.breakdownTitle}>Breakdown</Text>
                    <View style={styles.sheetRow}>
                      <Text style={styles.sheetLabel}>Interest</Text>
                      <Text style={styles.sheetValue}>{fmtUsd(breakdown.interest)}</Text>
                    </View>
                    <View style={styles.sheetRow}>
                      <Text style={styles.sheetLabel}>Principal</Text>
                      <Text style={styles.sheetValue}>{fmtUsd(breakdown.principal)}</Text>
                    </View>
                  </View>
                )}

                {/* Helper / validation */}
                <Text style={[styles.helper, repayDisabled ? { color: '#EF4444' } : { color: '#10B981' }]}>
                  {(() => {
                    const amt = parseFloat(repayAmount || '0');
                    const outstanding = Number(activeLoan.loanAmount || 0);
                    if (Number.isNaN(amt) || amt <= 0) return 'Enter an amount to repay.';
                    if (amt < 10) return 'Minimum repayment is $10.';
                    if (amt > outstanding) return 'Amount exceeds outstanding balance.';
                    return 'Looks good — ready to repay.';
                  })()}
                </Text>

                <TouchableOpacity
                  style={[styles.confirmBtn, (repayDisabled || isRepaying) && { backgroundColor: '#9CA3AF' }]}
                  disabled={repayDisabled || isRepaying}
                  onPress={validateAndConfirm}
                >
                  <Text style={styles.confirmText}>
                    {isRepaying ? 'Processing…' : 'Confirm Repayment'}
                  </Text>
                </TouchableOpacity>
              </>
            )}
          </View>
        </View>
      </Modal>
    </Modal>
  );
};

const badgeColor = (status: string) => {
  switch (status) {
    case 'ACTIVE': return '#34C759';
    case 'WARNING': return '#FF9500';
    case 'LIQUIDATED': return '#FF3B30';
    case 'REPAID': return '#8E8E93';
    default: return '#8E8E93';
  }
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

  inputWrap: { marginTop: 8 },
  inputLabel: { fontSize: 13, fontWeight: '600', color: '#111827', marginBottom: 6 },
  inputBox: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFFFFF', borderRadius: 12,
    paddingHorizontal: 14, paddingVertical: 10, borderWidth: 1, borderColor: '#E5E7EB',
  },
  input: { flex: 1, fontSize: 16, color: '#111827' },
  quickRow: { flexDirection: 'row', gap: 8, marginTop: 10 },
  quickBtn: { paddingHorizontal: 10, paddingVertical: 8, borderRadius: 999, backgroundColor: '#F3F4F6' },
  quickBtnText: { fontSize: 12, fontWeight: '700', color: '#111827' },
  sliderHint: { marginTop: 8, fontSize: 12, color: '#6B7280' },

  breakdown: { marginTop: 12, paddingTop: 8, borderTopWidth: 1, borderTopColor: '#F3F4F6' },
  breakdownTitle: { fontSize: 14, fontWeight: '700', color: '#111827', marginBottom: 4 },

  helper: { marginTop: 10, fontSize: 12 },
  confirmBtn: { marginTop: 12, backgroundColor: '#007AFF', borderRadius: 10, alignItems: 'center', paddingVertical: 12 },
  confirmText: { color: '#FFFFFF', fontSize: 15, fontWeight: '700' },
});

export default LoanManagementModal;