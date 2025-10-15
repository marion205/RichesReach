import React, { useMemo, useState, useEffect } from 'react';
import {
  Modal, View, Text, StyleSheet, TouchableOpacity,
  TextInput, ActivityIndicator, Platform
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

type Props = {
  visible: boolean;
  onClose: () => void;

  // inputs
  apr: number;               // e.g. 8.5
  eligibleEquity: number;    // e.g. 50000
  maxLtvPct?: number;        // policy cap, default 50
  currentDebt?: number;      // existing SBLOC balance (optional)

  // start value (optional)
  initialAmount?: number;

  // UX
  loading?: boolean;
  onApply?: (amount: number) => void;   // route to your application flow
};

const clamp = (v:number, lo:number, hi:number) => Math.max(lo, Math.min(hi, v));
const toNum = (v:any, def:number = 0) => {
  const n = Number(v);
  return Number.isFinite(n) ? n : def;
};
const toMoney = (n:any) => `$${Math.round(toNum(n)).toLocaleString()}`;
const to2 = (n:any) => toNum(n).toFixed(2);

const SblocCalculatorModal: React.FC<Props> = ({
  visible, onClose,
  apr = 0, eligibleEquity = 0,
  maxLtvPct = 50,
  currentDebt = 0,
  initialAmount = 0,
  loading,
  onApply
}) => {
  const maxBorrow = useMemo(
    () => Math.max(0, Math.floor((eligibleEquity * maxLtvPct) / 100) - currentDebt),
    [eligibleEquity, maxLtvPct, currentDebt]
  );

  const [amount, setAmount] = useState<number>(clamp(initialAmount || maxBorrow * 0.5, 0, maxBorrow));

  // keep amount in bounds when inputs change
  useEffect(() => setAmount(a => clamp(a, 0, maxBorrow)), [maxBorrow]);

  const impliedLtv = useMemo(() => {
    const totalDebt = currentDebt + amount;
    if (eligibleEquity <= 0) return 0;
    return clamp((totalDebt / eligibleEquity) * 100, 0, 100);
  }, [amount, eligibleEquity, currentDebt]);

  const monthlyInterest = useMemo(() => (amount * (apr / 100)) / 12, [amount, apr]);

  // "safety buffer" until policy LTV
  const bufferPct = clamp(maxLtvPct - impliedLtv, -100, 100);
  const bufferColor =
    bufferPct <= 2 ? '#FF3B30' :
    bufferPct <= 5 ? '#FF9500' : '#22C55E';

  const pctOfMax = maxBorrow === 0 ? 0 : (amount / maxBorrow) * 100;

  const onNudge = (dir: 'down' | 'up') => {
    if (maxBorrow <= 0) return;
    const step = Math.max(100, Math.round(maxBorrow * 0.02)); // 2% or $100
    setAmount(a => clamp(a + (dir === 'up' ? step : -step), 0, maxBorrow));
  };

  const onChangeAmountText = (t:string) => {
    const clean = t.replace(/[^\d.]/g, '');
    const val = Number.parseFloat(clean);
    if (Number.isFinite(val)) setAmount(clamp(val, 0, maxBorrow));
    else if (t === '') setAmount(0);
  };

  return (
    <Modal visible={visible} animationType="slide" presentationStyle="pageSheet" onRequestClose={onClose}>
      <View style={s.modal}>
        {/* Header */}
        <View style={s.header}>
          <TouchableOpacity onPress={onClose} style={s.iconBtn}>
            <Icon name="x" size={22} color="#8E8E93" />
          </TouchableOpacity>
          <Text style={s.title}>SBLOC Calculator</Text>
          <View style={{ width: 36 }} />
        </View>

        {loading ? (
          <View style={s.loading}>
            <ActivityIndicator color="#007AFF" />
            <Text style={s.loadingText}>Loading…</Text>
          </View>
        ) : (
          <>
            {/* Borrow input */}
            <View style={s.card}>
              <Text style={s.label}>How much do you want to borrow?</Text>

              <View style={s.row}>
                <TouchableOpacity style={s.nudgeBtn} onPress={() => onNudge('down')}>
                  <Icon name="minus" size={18} color="#0F172A" />
                </TouchableOpacity>

                <TextInput
                  style={s.amountInput}
                  keyboardType={Platform.OS === 'ios' ? 'decimal-pad' : 'numeric'}
                  value={amount ? String(Math.round(amount)) : ''}
                  onChangeText={onChangeAmountText}
                  placeholder="0"
                />

                <TouchableOpacity style={s.nudgeBtn} onPress={() => onNudge('up')}>
                  <Icon name="plus" size={18} color="#0F172A" />
                </TouchableOpacity>
              </View>

              <Text style={s.hint}>Max available: <Text style={s.hintStrong}>{toMoney(maxBorrow)}</Text></Text>

              {/* Progress bar vs max */}
              <View style={s.progressTrack}>
                <View style={[s.progressFill, { width: `${pctOfMax}%` }]} />
              </View>
            </View>

            {/* Metrics */}
            <View style={s.metrics}>
              <View style={s.metric}>
                <Text style={s.metricLabel}>Implied LTV</Text>
                <Text style={s.metricValue}>{to2(impliedLtv)}%</Text>
              </View>
              <View style={s.divider} />
              <View style={s.metric}>
                <Text style={s.metricLabel}>Monthly Interest @ {to2(apr)}%</Text>
                <Text style={s.metricValue}>{toMoney(monthlyInterest)}</Text>
              </View>
            </View>

            {/* Safety */}
            <View style={s.safety}>
              <View style={[s.dot, { backgroundColor: bufferColor }]} />
              <Text style={s.safetyText}>
                {bufferPct >= 0
                  ? `${to2(bufferPct)}% below policy LTV cap (${maxLtvPct}%).`
                  : `Exceeds policy LTV cap by ${to2(Math.abs(bufferPct))}%. Reduce amount.`}
              </Text>
            </View>

            {/* Footer actions */}
            <View style={s.footer}>
              <TouchableOpacity style={s.secondary} onPress={onClose}>
                <Text style={s.secondaryText}>Close</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[s.primary, amount <= 0 || impliedLtv > maxLtvPct ? { opacity: 0.6 } : null]}
                disabled={amount <= 0 || impliedLtv > maxLtvPct}
                onPress={() => onApply?.(Math.round(amount))}
              >
                <Text style={s.primaryText}>Proceed</Text>
                <Icon name="chevron-right" size={16} color="#fff" style={{ marginLeft: 6 }} />
              </TouchableOpacity>
            </View>
          </>
        )}
      </View>
    </Modal>
  );
};

const s = StyleSheet.create({
  modal: { flex: 1, backgroundColor: '#F2F2F7' },

  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: 20, paddingTop: 60, paddingBottom: 16, backgroundColor: '#fff',
    borderBottomWidth: 1, borderBottomColor: '#E5E5EA',
  },
  iconBtn: { width: 36, height: 36, alignItems: 'center', justifyContent: 'center' },
  title: { fontSize: 18, fontWeight: '800', color: '#111827' },

  loading: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  loadingText: { marginTop: 8, color: '#8E8E93' },

  card: {
    backgroundColor: '#fff', margin: 20, padding: 16, borderRadius: 14,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.06, shadowRadius: 6, elevation: 2,
  },
  label: { fontSize: 14, fontWeight: '700', color: '#0F172A', marginBottom: 10 },

  row: { flexDirection: 'row', alignItems: 'center' },
  amountInput: {
    flex: 1, height: 52, borderRadius: 10, borderWidth: 1, borderColor: '#E5E7EB',
    paddingHorizontal: 12, fontSize: 22, fontWeight: '800', color: '#0F172A', backgroundColor: '#F8FAFC',
    textAlign: 'center',
  },
  nudgeBtn: {
    width: 40, height: 40, borderRadius: 20, backgroundColor: '#EEF2F7',
    alignItems: 'center', justifyContent: 'center', marginHorizontal: 8,
  },
  hint: { marginTop: 8, color: '#64748B' },
  hintStrong: { fontWeight: '800', color: '#0F172A' },

  progressTrack: { height: 8, backgroundColor: '#EEF2F6', borderRadius: 999, marginTop: 12, overflow: 'hidden' },
  progressFill: { height: '100%', backgroundColor: '#007AFF' },

  metrics: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: '#fff',
    marginHorizontal: 20, padding: 16, borderRadius: 14,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.06, shadowRadius: 6, elevation: 2,
  },
  metric: { flex: 1 },
  metricLabel: { fontSize: 12, color: '#64748B', fontWeight: '700', letterSpacing: 0.3 },
  metricValue: { marginTop: 4, fontSize: 16, color: '#0F172A', fontWeight: '900' },
  divider: { width: 1, height: 28, backgroundColor: '#E5E7EB', marginHorizontal: 12 },

  safety: { flexDirection: 'row', alignItems: 'center', marginHorizontal: 20, marginTop: 12 },
  dot: { width: 8, height: 8, borderRadius: 4, marginRight: 8 },
  safetyText: { color: '#475569', fontWeight: '600' },

  footer: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 16, paddingHorizontal: 20 },
  secondary: { paddingVertical: 14, paddingHorizontal: 18, borderRadius: 10, backgroundColor: '#EAECEF' },
  secondaryText: { color: '#1F2937', fontWeight: '800' },
  primary: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    paddingVertical: 14, paddingHorizontal: 18, borderRadius: 10, backgroundColor: '#007AFF',
  },
  primaryText: { color: '#fff', fontWeight: '900' },
});

export default SblocCalculatorModal;