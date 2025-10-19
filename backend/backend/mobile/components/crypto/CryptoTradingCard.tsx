/**
 * Crypto Trading Card (Pro++ with Stop / Take-Profit)
 */

import React, { useEffect, useMemo, useState } from 'react';
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity, Alert,
  ActivityIndicator, ScrollView, Modal
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useQuery, useMutation } from '@apollo/client';
import {
  GET_SUPPORTED_CURRENCIES,
  GET_CRYPTO_PRICE,
  EXECUTE_CRYPTO_TRADE,
} from '../../graphql/cryptoQueries';

type TradeSide = 'BUY' | 'SELL';
type InputMode = 'QTY' | 'USD';
type OrderType = 'MARKET' | 'LIMIT' | 'STOP_MARKET' | 'STOP_LIMIT' | 'TAKE_PROFIT_LIMIT';
type TimeInForce = 'GTC' | 'IOC' | 'FOK' | 'DAY';

interface CryptoTradingCardProps {
  onTradeSuccess: () => void;
  balances?: Record<string, number>;
  usdAvailable?: number;
}

const FEE_RATE = 0.001;          // 0.10%
const SLIPPAGE_BPS = 50;         // 0.50% estimate for preview

const CryptoTradingCard: React.FC<CryptoTradingCardProps> = ({
  onTradeSuccess, balances, usdAvailable,
}) => {
  const [selectedSymbol, setSelectedSymbol] = useState('BTC');
  const [tradeType, setTradeType] = useState<TradeSide>('BUY');

  const [orderType, setOrderType] = useState<OrderType>('MARKET');
  const [timeInForce, setTimeInForce] = useState<TimeInForce>('GTC');

  const [mode, setMode] = useState<InputMode>('QTY');
  const [qty, setQty] = useState('');
  const [usd, setUsd] = useState('');

  // Price fields
  const [limitPrice, setLimitPrice] = useState('');    // used by LIMIT / STOP_LIMIT / TP_LIMIT
  const [triggerPrice, setTriggerPrice] = useState(''); // used by STOP_MARKET / STOP_LIMIT

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [error, setError] = useState('');

  const { data: currenciesData } = useQuery(GET_SUPPORTED_CURRENCIES);
  const { data: priceData, loading: priceLoading, refetch: refetchPrice } = useQuery(
    GET_CRYPTO_PRICE, { variables: { symbol: selectedSymbol }, skip: !selectedSymbol }
  );
  const [executeTrade] = useMutation(EXECUTE_CRYPTO_TRADE);

  const currentPrice = priceData?.cryptoPrice?.priceUsd || 0;
  const change24h = priceData?.cryptoPrice?.priceChangePercentage24h ?? null;

  // Keep limitPrice seeded to live when symbol/price changes (handy as a starting value)
  useEffect(() => {
    if (priceData?.cryptoPrice?.priceUsd) {
      setLimitPrice(String(priceData.cryptoPrice.priceUsd));
    }
  }, [priceData, selectedSymbol]);

  // Effective price for preview:
  // - MARKET / STOP_MARKET: use live
  // - LIMIT / STOP_LIMIT / TAKE_PROFIT_LIMIT: use limitPrice
  const effectivePrice =
    orderType === 'MARKET' || orderType === 'STOP_MARKET'
      ? currentPrice
      : parseFloat(limitPrice || '0');

  // Cross-calc qty <-> usd
  const qtyNum = parseFloat(qty || '0');
  const usdNum = parseFloat(usd || '0');
  useEffect(() => {
    setError('');
    const p = Number(effectivePrice);
    if (!p) return;

    if (mode === 'QTY') {
      const q = parseFloat(qty || '0');
      if (q > 0) setUsd((q * p).toFixed(2));
      else setUsd('');
    } else {
      const u = parseFloat(usd || '0');
      if (u > 0) setQty((u / p).toFixed(8));
      else setQty('');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mode, qty, usd, effectivePrice]);

  // Costs
  const fee = useMemo(() => (usdNum > 0 ? usdNum * FEE_RATE : 0), [usdNum]);
  const estSlippage = useMemo(
    () => (usdNum > 0 && (orderType === 'MARKET' || orderType === 'STOP_MARKET'))
      ? (usdNum * SLIPPAGE_BPS) / 10000
      : 0,
    [usdNum, orderType]
  );
  const totalCost = tradeType === 'BUY'
    ? usdNum + fee + estSlippage
    : Math.max(usdNum - fee - estSlippage, 0);

  /* ---------- Validations (dynamic) ---------- */
  useEffect(() => {
    const err = validate();
    setError(err || '');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tradeType, orderType, qty, usd, limitPrice, triggerPrice, effectivePrice, currentPrice, timeInForce]);

  const validate = (): string | null => {
    // Basic inputs
    if (!qty && !usd) return null;
    if (qtyNum <= 0) return 'Enter a valid quantity.';
    if (effectivePrice <= 0) return 'Enter a valid price.';

    // Wallet / cash checks
    if (tradeType === 'SELL') {
      const bal = balances?.[selectedSymbol];
      if (typeof bal === 'number' && qtyNum > bal + 1e-10) {
        return `You only have ${bal.toFixed(8)} ${selectedSymbol} available.`;
      }
    } else if (tradeType === 'BUY' && typeof usdAvailable === 'number') {
      if (totalCost > usdAvailable + 1e-6) {
        return `Insufficient USD: need ${fmtUSD(totalCost)}, available ${fmtUSD(usdAvailable)}.`;
      }
    }

    // Order-type specific
    const trig = parseFloat(triggerPrice || '0');
    const lim = parseFloat(limitPrice || '0');

    if (orderType === 'LIMIT' || orderType === 'STOP_LIMIT' || orderType === 'TAKE_PROFIT_LIMIT') {
      if (!lim || lim <= 0) return 'Limit price is required.';
    }
    if (orderType === 'STOP_MARKET' || orderType === 'STOP_LIMIT') {
      if (!trig || trig <= 0) return 'Trigger price is required for stop orders.';
      if (tradeType === 'BUY' && trig < currentPrice) {
        return 'For BUY stop orders, trigger must be ≥ current price.';
      }
      if (tradeType === 'SELL' && trig > currentPrice) {
        return 'For SELL stop orders, trigger must be ≤ current price.';
      }
    }
    if (orderType === 'STOP_LIMIT') {
      if (tradeType === 'BUY' && lim < trig) {
        return 'For BUY stop-limit, limit price should be ≥ trigger.';
      }
      if (tradeType === 'SELL' && lim > trig) {
        return 'For SELL stop-limit, limit price should be ≤ trigger.';
      }
    }
    if (orderType === 'TAKE_PROFIT_LIMIT') {
      // Convention used here:
      //  - BUY TP-LIMIT (enter on dip): limit ≤ current
      //  - SELL TP-LIMIT (exit into strength): limit ≥ current
      if (tradeType === 'BUY' && lim > currentPrice) {
        return 'For BUY take-profit limit, price should be ≤ current price (buy the dip).';
      }
      if (tradeType === 'SELL' && lim < currentPrice) {
        return 'For SELL take-profit limit, price should be ≥ current price.';
      }
    }

    // IOC/FOK sanity: avoid MARKET+GTC (not valid on many venues)
    if ((timeInForce === 'IOC' || timeInForce === 'FOK') && orderType === 'LIMIT') {
      // ok, many exchanges support limit-IOC/FOK
    }
    if ((timeInForce === 'IOC' || timeInForce === 'FOK') && orderType === 'MARKET') {
      // Many venues treat MARKET as Immediate-or-Cancel implicitly; allow.
    }

    return null;
  };

  /* ---------- UI helpers ---------- */
  const setPreset = (pct: number) => {
    const p = Number(effectivePrice);
    if (!p) return;
    if (tradeType === 'SELL') {
      const bal = balances?.[selectedSymbol] ?? 0;
      const q = bal * pct;
      setMode('QTY');
      setQty(q > 0 ? q.toFixed(8) : '');
    } else {
      const avail = typeof usdAvailable === 'number' ? usdAvailable : 0;
      const u = avail * pct;
      setMode('USD');
      setUsd(u > 0 ? u.toFixed(2) : '');
    }
  };
  const setMax = () => {
    if (tradeType === 'SELL') {
      const bal = balances?.[selectedSymbol] ?? 0;
      setMode('QTY'); setQty(bal > 0 ? bal.toFixed(8) : '');
    } else if (typeof usdAvailable === 'number') {
      setMode('USD'); setUsd(usdAvailable > 0 ? usdAvailable.toFixed(2) : '');
    }
  };

  const canSubmit = !isSubmitting && !error && parseFloat(qty || '0') > 0 &&
    (orderType === 'MARKET' || orderType === 'STOP_MARKET' || !!limitPrice) &&
    (orderType !== 'STOP_MARKET' && orderType !== 'STOP_LIMIT' ? true : !!triggerPrice);

  const openConfirm = () => {
    if (!canSubmit) return;
    setConfirmOpen(true);
  };

  const submitTrade = async () => {
    setConfirmOpen(false);
    setIsSubmitting(true);
    try {
      // Send: pricePerUnit = effective execution price field (limit price for limit types; live for market/stop-market)
      // Send: triggerPrice only for STOP_* (server can ignore otherwise)
      const variables: any = {
        symbol: selectedSymbol,
        tradeType,
        quantity: parseFloat(qty),
        pricePerUnit: Number(
          orderType === 'MARKET' || orderType === 'STOP_MARKET'
            ? currentPrice
            : limitPrice
        ),
        orderType,
        timeInForce,
        triggerPrice: (orderType === 'STOP_MARKET' || orderType === 'STOP_LIMIT') ? Number(triggerPrice) : null,
      };

      const { data } = await executeTrade({ variables });
      if (data?.executeCryptoTrade?.success) {
        Alert.alert('Success', `Trade executed!\nOrder ID: ${data.executeCryptoTrade.orderId}`, [
          { text: 'OK', onPress: () => onTradeSuccess() },
        ]);
        setQty(''); setUsd(''); // keep price fields
        if (orderType !== 'LIMIT' && orderType !== 'TAKE_PROFIT_LIMIT') setLimitPrice('');
        setTriggerPrice('');
      } else {
        Alert.alert('Error', data?.executeCryptoTrade?.message || 'Trade failed');
      }
    } catch (e) {
      console.error('Trade error:', e);
      Alert.alert('Error', 'Failed to execute trade. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  /* ---------- Render ---------- */
  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Side */}
      <View style={styles.segment}>
        <SegBtn active={tradeType === 'BUY'} color="#0EA5E9" icon="trending-up" onPress={() => setTradeType('BUY')} label="Buy" />
        <SegBtn active={tradeType === 'SELL'} color="#7C3AED" icon="trending-down" onPress={() => setTradeType('SELL')} label="Sell" />
      </View>

      {/* Symbol */}
      <View style={styles.section}>
        <Text style={styles.label}>Cryptocurrency</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingVertical: 4 }}>
          {(currenciesData?.supportedCurrencies?.slice(0, 5) || []).map((c: any) => (
            <TouchableOpacity
              key={c.symbol}
              style={[styles.chip, selectedSymbol === c.symbol && styles.chipActive]}
              onPress={() => setSelectedSymbol(c.symbol)}
            >
              <Text style={[styles.chipText, selectedSymbol === c.symbol && styles.chipTextActive]}>{c.symbol}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Order type + TIF */}
      <View style={styles.rowSplit}>
        <View style={{ flex: 1, marginRight: 8 }}>
          <Text style={styles.label}>Order Type</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingVertical: 4 }}>
            {(['MARKET','LIMIT','STOP_MARKET','STOP_LIMIT','TAKE_PROFIT_LIMIT'] as OrderType[]).map(t => (
              <TouchableOpacity
                key={t}
                style={[styles.pill, orderType === t && styles.pillActive]}
                onPress={() => setOrderType(t)}
              >
                <Text style={[styles.pillText, orderType === t && styles.pillTextActive]}>{t.replace(/_/g,' ')}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
        <View style={{ flex: 1, marginLeft: 8 }}>
          <Text style={styles.label}>Time in Force</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ paddingVertical: 4 }}>
            {(['GTC','DAY','IOC','FOK'] as TimeInForce[]).map(t => (
              <TouchableOpacity
                key={t}
                style={[styles.pillSm, timeInForce === t && styles.pillActiveSm]}
                onPress={() => setTimeInForce(t)}
              >
                <Text style={[styles.pillSmText, timeInForce === t && styles.pillSmTextActive]}>{t}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      </View>

      {/* Live price block */}
      <View style={styles.priceCard}>
        <View style={styles.priceRow}>
          <Text style={styles.priceLabel}>Current</Text>
          <TouchableOpacity onPress={() => refetchPrice()}><Icon name="refresh-cw" size={16} color="#007AFF" /></TouchableOpacity>
        </View>
        <View style={styles.priceRow}>
          <Text style={styles.priceValue}>{fmtUSD(currentPrice)}</Text>
          {change24h !== null && (
            <View style={[
              styles.changePill,
              { backgroundColor: (change24h ?? 0) >= 0 ? '#ECFDF5' : '#FEF2F2',
                borderColor:   (change24h ?? 0) >= 0 ? '#A7F3D0' : '#FECACA' }
            ]}>
              <Icon name={(change24h ?? 0) >= 0 ? 'trending-up' : 'trending-down'}
                    size={12} color={(change24h ?? 0) >= 0 ? '#10B981' : '#EF4444'} />
              <Text style={[
                styles.changeText,
                { color: (change24h ?? 0) >= 0 ? '#10B981' : '#EF4444' }
              ]}>
                {(change24h ?? 0) >= 0 ? '+' : ''}{(change24h ?? 0).toFixed(2)}%
              </Text>
            </View>
          )}
        </View>
      </View>

      {/* Price inputs (conditionally enabled) */}
      {(orderType === 'LIMIT' || orderType === 'STOP_LIMIT' || orderType === 'TAKE_PROFIT_LIMIT') && (
        <View style={styles.section}>
          <Text style={styles.label}>Limit Price</Text>
          <View style={styles.inputRow}>
            <TextInput
              style={styles.input}
              value={limitPrice}
              onChangeText={setLimitPrice}
              placeholder="0.00"
              keyboardType="decimal-pad"
              autoCapitalize="none"
            />
            <Text style={styles.suffix}>USD</Text>
          </View>
        </View>
      )}

      {(orderType === 'STOP_MARKET' || orderType === 'STOP_LIMIT') && (
        <View style={styles.section}>
          <Text style={styles.label}>Trigger Price (Stop)</Text>
          <View style={styles.inputRow}>
            <TextInput
              style={styles.input}
              value={triggerPrice}
              onChangeText={setTriggerPrice}
              placeholder="0.00"
              keyboardType="decimal-pad"
              autoCapitalize="none"
            />
            <Text style={styles.suffix}>USD</Text>
          </View>
          <Text style={styles.hintSmall}>
            {tradeType === 'BUY'
              ? 'BUY stop triggers at or above current price.'
              : 'SELL stop triggers at or below current price.'}
          </Text>
        </View>
      )}

      {/* Mode toggle + qty/usd */}
      <View style={styles.modeRow}>
        <ToggleTwo
          left={{ label: 'Quantity', active: mode === 'QTY', onPress: () => setMode('QTY') }}
          right={{ label: 'USD', active: mode === 'USD', onPress: () => setMode('USD') }}
        />
        <View style={{ flex: 1 }} />
        <TouchableOpacity onPress={setMax}><Text style={styles.maxLink}>{tradeType === 'SELL' ? 'Max' : 'Use All $'}</Text></TouchableOpacity>
      </View>

      {mode === 'QTY' ? (
        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            value={qty}
            onChangeText={setQty}
            placeholder="0.00000000"
            keyboardType="decimal-pad"
            autoCapitalize="none"
          />
          <Text style={styles.suffix}>{selectedSymbol}</Text>
        </View>
      ) : (
        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            value={usd}
            onChangeText={setUsd}
            placeholder="0.00"
            keyboardType="decimal-pad"
            autoCapitalize="none"
          />
          <Text style={styles.suffix}>USD</Text>
        </View>
      )}

      {/* Presets */}
      <View style={styles.presetRow}>
        {[0.25, 0.5, 0.75, 1].map(p => (
          <TouchableOpacity key={p} style={styles.presetBtn} onPress={() => setPreset(p)}>
            <Text style={styles.presetText}>{Math.round(p * 100)}%</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Summary */}
      {(qtyNum > 0 || usdNum > 0) && (
        <View style={styles.summaryCard}>
          <Row label="Notional" value={fmtUSD(usdNum)} />
          <Row label="Est. Fee (0.10%)" value={fmtUSD(fee)} />
          {(orderType === 'MARKET' || orderType === 'STOP_MARKET') && (
            <Row label="Est. Slippage (0.50%)" value={fmtUSD(estSlippage)} />
          )}
          <View style={styles.divider} />
          <Row label={tradeType === 'BUY' ? 'Total Cost' : 'Est. Proceeds'} value={fmtUSD(totalCost)} bold />
        </View>
      )}

      {/* Error */}
      {!!error && (
        <View style={styles.errorBox}>
          <Icon name="alert-triangle" size={16} color="#B45309" />
          <Text style={styles.errorText}>{error}</Text>
        </View>
      )}

      {/* Submit */}
      <TouchableOpacity
        style={[
          styles.submitBtn,
          (!canSubmit || !!error) && styles.submitDisabled,
          tradeType === 'BUY' ? styles.buyBtn : styles.sellBtn,
        ]}
        disabled={!canSubmit || !!error}
        onPress={openConfirm}
      >
        {isSubmitting ? <ActivityIndicator color="#fff" /> : (
          <>
            <Icon name={tradeType === 'BUY' ? 'trending-up' : 'trending-down'} size={18} color="#fff" />
            <Text style={styles.submitText}>{tradeType} {selectedSymbol}</Text>
          </>
        )}
      </TouchableOpacity>

      {/* Risk */}
      <View style={styles.notice}>
        <Icon name="alert-triangle" size={16} color="#92400E" />
        <Text style={styles.noticeText}>Crypto orders may execute partially or not at all depending on liquidity and your time-in-force.</Text>
      </View>

      {/* Confirm Sheet */}
      <Modal animationType="slide" transparent visible={confirmOpen} onRequestClose={() => setConfirmOpen(false)}>
        <View style={styles.sheetOverlay}>
          <View style={styles.sheet}>
            <Text style={styles.sheetTitle}>Confirm Order</Text>
            <View style={{ height: 8 }} />
            <Row label="Side" value={tradeType} />
            <Row label="Type" value={orderType.replace(/_/g,' ')} />
            <Row label="TIF" value={timeInForce} />
            <Row label="Symbol" value={selectedSymbol} />
            {orderType === 'STOP_MARKET' || orderType === 'STOP_LIMIT'
              ? <Row label="Trigger" value={fmtUSD(Number(triggerPrice || '0'))} />
              : null}
            {(orderType === 'LIMIT' || orderType === 'STOP_LIMIT' || orderType === 'TAKE_PROFIT_LIMIT') && (
              <Row label="Limit" value={fmtUSD(Number(limitPrice || '0'))} />
            )}
            <Row label="Quantity" value={`${qtyNum.toFixed(8)} ${selectedSymbol}`} />
            <Row label="Preview Px" value={fmtUSD(effectivePrice)} />
            <View style={styles.divider} />
            <Row label="Notional" value={fmtUSD(usdNum)} />
            <Row label="Est. Fee" value={fmtUSD(fee)} />
            {(orderType === 'MARKET' || orderType === 'STOP_MARKET') && (
              <Row label="Est. Slippage" value={fmtUSD(estSlippage)} />
            )}
            <View style={styles.divider} />
            <Row label={tradeType === 'BUY' ? 'Total Cost' : 'Est. Proceeds'} value={fmtUSD(totalCost)} bold />
            <View style={{ height: 16 }} />
            <View style={styles.sheetBtns}>
              <TouchableOpacity style={[styles.sheetBtn, styles.sheetCancel]} onPress={() => setConfirmOpen(false)}>
                <Text style={styles.sheetCancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity style={[styles.sheetBtn, styles.sheetConfirm]} onPress={submitTrade}>
                <Text style={styles.sheetConfirmText}>Confirm</Text>
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
};

/* ---------- tiny comps & helpers ---------- */
const SegBtn = ({ active, color, icon, label, onPress }: any) => (
  <TouchableOpacity style={[styles.segBtn, active && { backgroundColor: color }]} onPress={onPress} activeOpacity={0.85}>
    <Icon name={icon} size={18} color={active ? '#fff' : color} />
    <Text style={[styles.segText, active && styles.segTextActive]}>{label}</Text>
  </TouchableOpacity>
);

const ToggleTwo = ({ left, right }: any) => (
  <View style={styles.toggleTwo}>
    <TouchableOpacity style={[styles.toggleItem, left.active && styles.toggleActive]} onPress={left.onPress}>
      <Text style={[styles.toggleText, left.active && styles.toggleTextActive]}>{left.label}</Text>
    </TouchableOpacity>
    <TouchableOpacity style={[styles.toggleItem, right.active && styles.toggleActive]} onPress={right.onPress}>
      <Text style={[styles.toggleText, right.active && styles.toggleTextActive]}>{right.label}</Text>
    </TouchableOpacity>
  </View>
);

const Row = ({ label, value, bold }: { label: string; value: string; bold?: boolean }) => (
  <View style={styles.row}>
    <Text style={[styles.rowLabel, bold && { fontWeight: '700', color: '#111827' }]}>{label}</Text>
    <Text style={[styles.rowValue, bold && { fontWeight: '700', color: '#111827' }]}>{value}</Text>
  </View>
);

const fmtUSD = (v: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(v);

/* ---------- styles ---------- */
const styles = StyleSheet.create({
  container: { flex: 1, paddingTop: 20 },

  segment: { flexDirection: 'row', backgroundColor: '#FFFFFF', borderRadius: 12, padding: 4, marginBottom: 16,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.08, shadowRadius: 6, elevation: 2 },
  segBtn: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 12, borderRadius: 8, gap: 8 },
  segText: { fontSize: 16, fontWeight: '600', color: '#111827' },
  segTextActive: { color: '#fff' },

  section: { marginBottom: 16 },
  label: { fontSize: 14, fontWeight: '600', color: '#111827', marginBottom: 8 },

  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 18, backgroundColor: '#F3F4F6', marginRight: 8 },
  chipActive: { backgroundColor: '#111827' },
  chipText: { fontSize: 14, fontWeight: '600', color: '#6B7280' },
  chipTextActive: { color: '#fff' },

  rowSplit: { flexDirection: 'row', marginBottom: 8 },
  pill: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 10, backgroundColor: '#F3F4F6', marginRight: 8 },
  pillActive: { backgroundColor: '#111827' },
  pillText: { color: '#6B7280', fontWeight: '700' },
  pillTextActive: { color: '#fff' },
  pillSm: { paddingHorizontal: 10, paddingVertical: 8, borderRadius: 999, backgroundColor: '#F3F4F6', marginRight: 8 },
  pillActiveSm: { backgroundColor: '#111827' },
  pillSmText: { color: '#6B7280', fontWeight: '700', fontSize: 12 },
  pillSmTextActive: { color: '#fff' },

  priceCard: { backgroundColor: '#fff', borderRadius: 12, padding: 16, marginBottom: 16,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.08, shadowRadius: 6, elevation: 2 },
  priceRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  priceLabel: { fontSize: 12, color: '#6B7280' },
  priceValue: { fontSize: 24, fontWeight: '700', color: '#111827', marginVertical: 4 },
  changePill: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 999, borderWidth: 1 },
  changeText: { fontSize: 12, fontWeight: '700' },

  inputRow: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#FFFFFF', borderRadius: 12, paddingHorizontal: 16, paddingVertical: 12,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.08, shadowRadius: 6, elevation: 2 },
  input: { flex: 1, fontSize: 16, color: '#111827' },
  suffix: { fontSize: 16, fontWeight: '700', color: '#6B7280', marginLeft: 8 },
  hintSmall: { marginTop: 6, fontSize: 12, color: '#6B7280' },

  modeRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 8, gap: 8 },
  toggleTwo: { flexDirection: 'row', backgroundColor: '#F3F4F6', borderRadius: 10, padding: 2 },
  toggleItem: { paddingVertical: 8, paddingHorizontal: 12, borderRadius: 8 },
  toggleActive: { backgroundColor: '#111827' },
  toggleText: { color: '#6B7280', fontWeight: '700' },
  toggleTextActive: { color: '#fff' },
  maxLink: { color: '#007AFF', fontWeight: '700' },

  presetRow: { flexDirection: 'row', gap: 8, marginTop: 10, marginBottom: 6 },
  presetBtn: { flex: 1, alignItems: 'center', paddingVertical: 10, borderRadius: 10, backgroundColor: '#EFF6FF' },
  presetText: { color: '#1D4ED8', fontWeight: '700' },

  summaryCard: { backgroundColor: '#FFFFFF', borderRadius: 12, padding: 16, marginTop: 10, marginBottom: 16,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.08, shadowRadius: 6, elevation: 2 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginVertical: 4 },
  rowLabel: { fontSize: 14, color: '#6B7280' },
  rowValue: { fontSize: 14, color: '#111827', fontWeight: '600' },
  divider: { height: 1, backgroundColor: '#F3F4F6', marginVertical: 6 },

  errorBox: { flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: '#FFFBEB', borderColor: '#FCD34D', borderWidth: 1, padding: 12, borderRadius: 10, marginBottom: 14 },
  errorText: { color: '#92400E', fontSize: 14, flex: 1 },

  submitBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', paddingVertical: 16, borderRadius: 12, gap: 8, marginBottom: 16 },
  submitDisabled: { opacity: 0.6 },
  buyBtn: { backgroundColor: '#0EA5E9' },
  sellBtn: { backgroundColor: '#7C3AED' },
  submitText: { color: '#fff', fontWeight: '700', fontSize: 16 },

  notice: { flexDirection: 'row', gap: 8, backgroundColor: '#FFFBEB', borderColor: '#FCD34D', borderWidth: 1, padding: 12, borderRadius: 10, marginBottom: 20 },
  noticeText: { color: '#92400E', fontSize: 14, flex: 1 },

  sheetOverlay: { flex: 1, backgroundColor: 'rgba(0,0,0,0.4)', justifyContent: 'flex-end' },
  sheet: { backgroundColor: '#fff', padding: 16, borderTopLeftRadius: 16, borderTopRightRadius: 16, maxHeight: '80%' },
  sheetTitle: { fontSize: 18, fontWeight: '700', color: '#111827' },
  sheetBtns: { flexDirection: 'row', gap: 10 },
  sheetBtn: { flex: 1, paddingVertical: 12, borderRadius: 10, alignItems: 'center' },
  sheetCancel: { backgroundColor: '#F3F4F6' },
  sheetConfirm: { backgroundColor: '#111827' },
  sheetCancelText: { color: '#111827', fontWeight: '700' },
  sheetConfirmText: { color: '#fff', fontWeight: '700' },
});

export default CryptoTradingCard;