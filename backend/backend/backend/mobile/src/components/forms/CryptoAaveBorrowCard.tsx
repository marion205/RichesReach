/**
 * Crypto AAVE Borrow Card — Holdings-aware Supply & Borrow
 * - Select collateral + borrow asset
 * - MAX + 25/50/75/100% chips from balance / headroom
 * - Health Factor (AAVE), weighted LTV, liquidation threshold
 * - Info buttons for education
 */

import React, { useEffect, useMemo, useState } from 'react';
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity, Alert,
  ActivityIndicator, ScrollView,
} from 'react-native';
import { gql, useMutation, useQuery } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import AAVEWhatIfSlider from '../crypto/AAVEWhatIfSlider';
import WalletConnection from '../crypto/WalletConnection';
import useWallet from '../../shared/hooks/useWallet';
import { HybridTransactionService } from '../../services/HybridTransactionService';

/* ===================== GraphQL (adjust to your schema) ===================== */
const GET_AAVE_RESERVES = gql`
  query GetAAVEReserves {
    defiReserves {
      symbol
      name
      ltv
      liquidationThreshold
      canBeCollateral
      supplyApy
      variableBorrowApy
      stableBorrowApy
    }
  }
`;

const GET_AAVE_ACCOUNT = gql`
  query GetAAVEAccount {
    defiAccount {
      healthFactor
      availableBorrowUsd
      collateralUsd
      debtUsd
      ltvWeighted
      liqThresholdWeighted
      supplies { 
        symbol 
        quantity 
        useAsCollateral 
      }
      borrows { 
        symbol 
        amount 
        rateMode 
      }
      pricesUsd
    }
  }
`;

const AAVE_SUPPLY = gql`
  mutation AAVESupply($symbol: String!, $quantity: Float!, $useAsCollateral: Boolean) {
    defiSupply(symbol: $symbol, quantity: $quantity, useAsCollateral: $useAsCollateral) {
      success
      message
      position {
        quantity
        useAsCollateral
      }
    }
  }
`;

const AAVE_BORROW = gql`
  mutation AAVEBorrow($symbol: String!, $amount: Float!, $rateMode: String) {
    defiBorrow(symbol: $symbol, amount: $amount, rateMode: $rateMode) {
      success
      message
      position {
        amount
        rateMode
      }
      healthFactorAfter
    }
  }
`;

/* ===================== Helpers ===================== */
const maskify = (_: string | number) => '•••••';
const fmtUsd = (n: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n);
const clamp = (v: number, min: number, max: number) => Math.min(max, Math.max(min, v));

type Tier = 'SAFE' | 'WARN' | 'TOP_UP' | 'AT_RISK' | 'LIQUIDATE';

const tierFromHF = (hf: number): Tier => {
  if (!isFinite(hf) || hf > 2.0) return 'SAFE';
  if (hf > 1.2) return 'WARN';
  if (hf > 1.05) return 'TOP_UP';
  if (hf > 1.0) return 'AT_RISK';
  return 'LIQUIDATE';
};

const colorFromTier = (t: Tier) => ({
  SAFE: '#10B981',
  WARN: '#F59E0B',
  TOP_UP: '#EF4444',
  AT_RISK: '#DC2626',
  LIQUIDATE: '#7C2D12',
}[t]);

/* ===================== Component ===================== */
type Props = {
  onSuccess?: () => void;                 // called after both supply+borrow succeed
  defaultCollateral?: string;             // e.g. "ETH"
  defaultBorrow?: string;                 // e.g. "USDC"
};

const CryptoAAVEBorrowCard: React.FC<Props> = ({
  onSuccess,
  defaultCollateral = 'ETH',
  defaultBorrow = 'USDC',
}) => {
  const [collSymbol, setCollSymbol] = useState(defaultCollateral);
  const [borrowSymbol, setBorrowSymbol] = useState(defaultBorrow);

  const [supplyQty, setSupplyQty] = useState('');     // collateral quantity
  const [borrowUsd, setBorrowUsd] = useState('');     // borrow amount in USD

  const [mask, setMask] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Wallet integration
  const {
    isConnected,
    walletInfo,
    aaveReserves,
    userAccountData,
    supplyAsset,
    withdrawAsset,
    borrowAsset,
    repayAsset,
    toggleCollateral,
    error: walletError,
  } = useWallet();

  const { data: reservesData, loading: reservesLoading, refetch: refetchRes } = useQuery(GET_AAVE_RESERVES, { fetchPolicy: 'cache-first' });
  const { data: acctData, loading: acctLoading, refetch: refetchAcct } = useQuery(GET_AAVE_ACCOUNT, { fetchPolicy: 'cache-first' });

  const [doSupply] = useMutation(AAVE_SUPPLY);
  const [doBorrow] = useMutation(AAVE_BORROW);

  const reserves = reservesData?.defiReserves || [];
  const account = acctData?.defiAccount;

  const collRes = useMemo(() => reserves.find((r: any) => r.symbol === collSymbol), [reserves, collSymbol]);
  const borRes  = useMemo(() => reserves.find((r: any) => r.symbol === borrowSymbol), [reserves, borrowSymbol]);

  // Get prices from account data or use mock prices
  const collPx = Number(account?.pricesUsd?.[collSymbol] || 0);
  const borPx  = Number(account?.pricesUsd?.[borrowSymbol] || 1); // USDC ~ 1

  // Mock wallet balance for now - you can integrate with actual wallet data
  const availQty = 1.5; // Mock ETH balance
  const qtyNum   = parseFloat(supplyQty || '0') || 0;
  const borNum   = parseFloat(borrowUsd || '0') || 0;

  // AAVE core math (single-collateral simplification)
  const collateralUsd       = qtyNum * collPx;
  const weightedLTV         = Number(collRes?.ltv ?? 0);                 // 0..1
  const weightedLiq         = Number(collRes?.liquidationThreshold ?? 0);// 0..1
  const currentDebtUsd      = borNum; // single borrow entry on this card
  const borrowCapUsd        = collateralUsd * weightedLTV;
  const availableBorrowUsd  = Math.max(0, borrowCapUsd - currentDebtUsd);
  const healthFactor        = currentDebtUsd > 0
    ? (collateralUsd * weightedLiq) / currentDebtUsd
    : Infinity;

  const tier = tierFromHF(healthFactor);
  const tierColor = colorFromTier(tier);

  // suggest a 50% headroom borrow if user fills collateral first
  useEffect(() => {
    if (!qtyNum || !collPx || !!borNum) return;
    const headroom = collateralUsd * weightedLTV;
    if (headroom > 0) setBorrowUsd((headroom * 0.5).toFixed(2));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [qtyNum, collPx, weightedLTV]);

  // validation text
  const errorText = useMemo(() => {
    if (!supplyQty && !borrowUsd) return null;
    if (qtyNum > availQty) return `You only have ${availQty.toFixed(6)} ${collSymbol} available`;
    if (currentDebtUsd > borrowCapUsd) return `Borrow exceeds LTV cap (${(weightedLTV * 100).toFixed(0)}%)`;
    if (healthFactor <= 1.0) return 'Health Factor ≤ 1.00 — liquidation risk';
    return null;
  }, [qtyNum, availQty, collSymbol, currentDebtUsd, borrowCapUsd, weightedLTV, healthFactor]);

  const setQtyFromBalancePct = (pct: number) => {
    if (availQty <= 0) return;
    const q = (availQty * pct) / 100;
    setSupplyQty(q.toFixed(8));
  };

  const setBorrowFromHeadroomPct = (pct: number) => {
    const cap = collateralUsd * weightedLTV;
    if (cap <= 0) return;
    setBorrowUsd(((cap * pct) / 100).toFixed(2));
  };

  const onInfo = (key: 'hf' | 'ltv' | 'liq' | 'avail') => {
    const texts = {
      hf: 'Health Factor (HF) = (Collateral USD × Liquidation Threshold) / Debt USD.\nIf HF ≤ 1.0 your position can be liquidated. Aim for HF > 1.2.',
      ltv: 'LTV is the maximum borrowable percentage of your collateral. Example: LTV 70% on $100 collateral → $70 borrow cap.',
      liq: 'Liquidation Threshold is the percentage of collateral counted at liquidation. HF uses this (not LTV).',
      avail: 'Available to borrow = Collateral USD × LTV − Current Debt USD.',
    } as const;
    Alert.alert('What is this?', texts[key]);
  };

  const submit = async () => {
    if (!qtyNum && !borNum) {
      Alert.alert('Error', 'Enter a supply amount and/or borrow amount.');
      return;
    }
    if (errorText) {
      Alert.alert('Check inputs', errorText);
      return;
    }

    if (!isConnected) {
      Alert.alert('Wallet Required', 'Please connect your wallet to perform transactions.');
      return;
    }

    setSubmitting(true);
    try {
      // 1) Supply (optional) - Use hybrid transaction service
      if (qtyNum > 0) {
        const supplyResult = await HybridTransactionService.supplyAsset({
          assetSymbol: collSymbol,
          amount: qtyNum.toString(),
          useAsCollateral: true,
        });

        if (!supplyResult.success) {
          throw new Error(supplyResult.message);
        }

        HybridTransactionService.showTransactionResult(supplyResult);
      }

      // 2) Borrow (optional) - Use hybrid transaction service
      if (borNum > 0) {
        const borrowResult = await HybridTransactionService.borrowAsset({
          assetSymbol: borrowSymbol,
          amount: borNum.toString(),
          interestRateMode: 'VARIABLE',
        });

        if (!borrowResult.success) {
          throw new Error(borrowResult.message);
        }

        HybridTransactionService.showTransactionResult(borrowResult);
      }

      // Refresh data from both backend and blockchain
      await Promise.all([refetchRes(), refetchAcct()]);
      setSupplyQty('');
      setBorrowUsd('');
      onSuccess?.();
    } catch (e: any) {
      console.error(e);
      Alert.alert('Error', e.message || 'Transaction failed');
    } finally {
      setSubmitting(false);
    }
  };

  /* ===================== Render ===================== */
  return (
    <ScrollView style={s.container} showsVerticalScrollIndicator={false}>
      {/* Wallet Connection */}
      <WalletConnection 
        onWalletConnected={() => {
          console.log('Wallet connected, refreshing data...');
          refetchRes();
          refetchAcct();
        }}
        onWalletDisconnected={() => {
          console.log('Wallet disconnected');
        }}
        style={{ marginBottom: 16 }}
      />

      {/* Header */}
      <View style={s.rowBetween}>
        <Text style={s.headerTitle}>AAVE — Supply & Borrow</Text>
        <TouchableOpacity onPress={() => setMask(v => !v)} style={s.iconBtn}>
          <Icon name={mask ? 'eye-off' : 'eye'} size={18} color="#8E8E93" />
        </TouchableOpacity>
      </View>

      {/* Collateral picker */}
      <View style={s.section}>
        <View style={s.rowBetween}>
          <Text style={s.sectionTitle}>Collateral</Text>
          <TouchableOpacity onPress={() => onInfo('ltv')} style={s.infoBtn}><Icon name="info" size={14} color="#6B7280" /></TouchableOpacity>
        </View>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.symbolRow}>
          {(reserves || []).filter((r: any) => r.canBeCollateral).slice(0, 7).map((r: any) => (
            <TouchableOpacity
              key={r.symbol}
              style={[s.symBtn, collSymbol === r.symbol && s.symBtnActive]}
              onPress={() => { setCollSymbol(r.symbol); setSupplyQty(''); setBorrowUsd(''); }}
              activeOpacity={0.85}
            >
              <Text style={[s.symText, collSymbol === r.symbol && s.symTextActive]}>{r.symbol}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Price + Wallet */}
        <View style={s.kpiCard}>
          <View style={s.kpiItem}>
            <Text style={s.kpiLabel}>Price ({collSymbol})</Text>
            {reservesLoading ? <ActivityIndicator size="small" color="#007AFF" /> : (
              <Text style={s.kpiValue}>{mask ? maskify(collPx) : fmtUsd(collPx || 0)}</Text>
            )}
          </View>
          <View style={s.kpiDivider} />
          <View style={s.kpiItem}>
            <Text style={s.kpiLabel}>Wallet</Text>
            {reservesLoading ? <ActivityIndicator size="small" color="#8E8E93" /> : (
              <Text style={s.kpiValueSmall}>{(availQty || 0).toFixed(6)} {collSymbol}</Text>
            )}
          </View>
        </View>

        {/* Supply input */}
        <Text style={s.inputLabel}>Supply Amount</Text>
        <View style={s.inputContainer}>
          <TextInput
            style={s.input}
            value={supplyQty}
            onChangeText={setSupplyQty}
            placeholder="0.00000000"
            keyboardType="numeric"
          />
          <TouchableOpacity onPress={() => setSupplyQty(availQty.toFixed(8))} disabled={availQty <= 0}>
            <Text style={s.maxBtn}>MAX</Text>
          </TouchableOpacity>
          <Text style={s.inputSuffix}>{collSymbol}</Text>
        </View>
        <View style={s.chipsRow}>
          {[25, 50, 75, 100].map(p => (
            <TouchableOpacity key={p} style={s.chip} onPress={() => setQtyFromBalancePct(p)} disabled={availQty <= 0}>
              <Text style={s.chipText}>{p}% of balance</Text>
            </TouchableOpacity>
          ))}
        </View>
        {collateralUsd > 0 && <Text style={s.subRight}>Collateral: {mask ? maskify(collateralUsd) : fmtUsd(collateralUsd)}</Text>}
      </View>

      {/* Borrow picker */}
      <View style={s.section}>
        <View style={s.rowBetween}>
          <Text style={s.sectionTitle}>Borrow Asset</Text>
          <TouchableOpacity onPress={() => onInfo('avail')} style={s.infoBtn}><Icon name="info" size={14} color="#6B7280" /></TouchableOpacity>
        </View>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.symbolRow}>
          {(reserves || []).slice(0, 7).map((r: any) => (
            <TouchableOpacity
              key={r.symbol}
              style={[s.symBtn, borrowSymbol === r.symbol && s.symBtnActive]}
              onPress={() => { setBorrowSymbol(r.symbol); setBorrowUsd(''); }}
              activeOpacity={0.85}
            >
              <Text style={[s.symText, borrowSymbol === r.symbol && s.symTextActive]}>{r.symbol}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Borrow input */}
        <Text style={s.inputLabel}>Borrow Amount (USD)</Text>
        <View style={s.inputContainer}>
          <TextInput
            style={s.input}
            value={borrowUsd}
            onChangeText={setBorrowUsd}
            placeholder="0.00"
            keyboardType="numeric"
          />
          <Text style={s.inputSuffix}>USD</Text>
        </View>

        {/* Headroom chips */}
        <View style={s.chipsRow}>
          {[25, 50, 75, 100].map(p => (
            <TouchableOpacity
              key={p}
              style={[s.chip, p === 100 && s.chipOutline]}
              onPress={() => setBorrowFromHeadroomPct(p)}
              disabled={collateralUsd <= 0 || weightedLTV <= 0}
            >
              <Text style={[s.chipText, p === 100 && s.chipTextPrimary]}>{p}% of cap</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Key metrics + info buttons */}
        <View style={s.metricsCard}>
          <View style={s.metricRow}>
            <View style={s.metricL}>
              <Text style={s.metricLabel}>Weighted LTV</Text>
              <TouchableOpacity onPress={() => onInfo('ltv')}><Icon name="info" size={14} color="#6B7280" /></TouchableOpacity>
            </View>
            <Text style={s.metricVal}>{(weightedLTV * 100).toFixed(0)}%</Text>
          </View>
          <View style={s.metricRow}>
            <View style={s.metricL}>
              <Text style={s.metricLabel}>Liquidation Threshold</Text>
              <TouchableOpacity onPress={() => onInfo('liq')}><Icon name="info" size={14} color="#6B7280" /></TouchableOpacity>
            </View>
            <Text style={s.metricVal}>{(weightedLiq * 100).toFixed(0)}%</Text>
          </View>
          <View style={s.metricRow}>
            <View style={s.metricL}>
              <Text style={s.metricLabel}>Available to Borrow</Text>
              <TouchableOpacity onPress={() => onInfo('avail')}><Icon name="info" size={14} color="#6B7280" /></TouchableOpacity>
            </View>
            <Text style={s.metricVal}>{mask ? maskify(availableBorrowUsd) : fmtUsd(availableBorrowUsd)}</Text>
          </View>
          <View style={[s.metricRow, { marginTop: 6 }]}>
            <View style={s.metricL}>
              <Text style={s.metricLabel}>Health Factor</Text>
              <TouchableOpacity onPress={() => onInfo('hf')}><Icon name="info" size={14} color="#6B7280" /></TouchableOpacity>
            </View>
            <Text style={[s.metricVal, { color: tierColor }]}>{isFinite(healthFactor) ? healthFactor.toFixed(2) : '∞'}</Text>
          </View>

          {/* HF meter (0 → 2.0) */}
          <View style={s.meterTrack}>
            <View style={[s.meterFill, {
              width: `${clamp((isFinite(healthFactor) ? healthFactor : 2) / 2, 0, 1) * 100}%`,
              backgroundColor: tierColor,
            }]} />
            <View style={[s.marker, { left: `${(1.0 / 2) * 100}%` }]} />
            <View style={[s.marker, { left: `${(1.2 / 2) * 100}%` }]} />
            <View style={[s.marker, { left: '100%' }]} />
          </View>

          {!!errorText && (
            <View style={s.errorRow}>
              <Icon name="alert-triangle" size={16} color="#FF3B30" />
              <Text style={s.errorText}>{errorText}</Text>
            </View>
          )}
        </View>
      </View>

      {/* Submit */}
      <TouchableOpacity
        style={[s.submitButton, (submitting || !!errorText) && s.submitButtonDisabled]}
        onPress={submit}
        disabled={submitting || !!errorText}
        activeOpacity={0.85}
      >
        {submitting ? <ActivityIndicator color="#FFFFFF" /> : (
          <>
            <Icon name="arrow-up-right" size={18} color="#FFFFFF" />
            <Text style={s.submitButtonText}>Supply & Borrow</Text>
          </>
        )}
      </TouchableOpacity>

      {/* AAVE What-if stress testing */}
      {collateralUsd > 0 && (
        <AAVEWhatIfSlider
          collateralUsd={collateralUsd}
          debtUsd={currentDebtUsd}
          ltv={weightedLTV}
          liqThreshold={weightedLiq}
          onStressChange={(result) => {
            console.log('AAVE stress test result:', result);
            // You can call your /defi/stress-test endpoint and show HF under shocks
          }}
        />
      )}

      {/* Risk note */}
      <View style={s.warningCard}>
        <Icon name="alert-triangle" size={20} color="#FF9500" />
        <Text style={s.warningText}>
          On AAVE, liquidation risk is based on your Health Factor (HF). Keep HF comfortably above 1.2. Borrow caps and rates can change with market conditions.
        </Text>
      </View>
    </ScrollView>
  );
};

export default CryptoAAVEBorrowCard;

/* ===================== Styles ===================== */
const s = StyleSheet.create({
  container:{ flex:1, paddingTop:20 },
  rowBetween:{ flexDirection:'row', alignItems:'center', justifyContent:'space-between', marginBottom:8 },
  iconBtn:{ padding:8 }, headerTitle:{ fontSize:18, fontWeight:'700', color:'#111827' },

  section:{ marginBottom:20 },
  sectionTitle:{ fontSize:16, fontWeight:'600', color:'#111827' },
  infoBtn:{ padding:6 },

  symbolRow:{ flexDirection:'row', marginTop:10 },
  symBtn:{ paddingHorizontal:14, paddingVertical:8, borderRadius:20, backgroundColor:'#F3F4F6', marginRight:8 },
  symBtnActive:{ backgroundColor:'#007AFF' },
  symText:{ fontSize:14, fontWeight:'600', color:'#6B7280' },
  symTextActive:{ color:'#FFFFFF' },

  kpiCard:{ backgroundColor:'#FFFFFF', borderRadius:12, padding:16, marginTop:10, marginBottom:12,
    shadowColor:'#000', shadowOffset:{ width:0, height:2 }, shadowOpacity:0.1, shadowRadius:4, elevation:3,
    flexDirection:'row', alignItems:'center', justifyContent:'space-between' },
  kpiItem:{ flex:1 }, kpiDivider:{ width:1, height:32, backgroundColor:'#F3F4F6', marginHorizontal:12 },
  kpiLabel:{ fontSize:12, color:'#8E8E93', marginBottom:4 },
  kpiValue:{ fontSize:18, fontWeight:'700', color:'#111827' },
  kpiValueSmall:{ fontSize:14, fontWeight:'700', color:'#111827' },

  inputLabel:{ fontSize:12, color:'#6B7280', marginBottom:6, marginTop:6 },
  inputContainer:{ flexDirection:'row', alignItems:'center', backgroundColor:'#FFFFFF', borderRadius:12,
    paddingHorizontal:12, paddingVertical:10, shadowColor:'#000', shadowOffset:{ width:0, height:2 },
    shadowOpacity:0.1, shadowRadius:4, elevation:3 },
  input:{ flex:1, fontSize:16, color:'#111827' },
  inputSuffix:{ fontSize:16, fontWeight:'600', color:'#8E8E93', marginLeft:8 },
  maxBtn:{ fontSize:12, fontWeight:'800', color:'#0F66E9', marginRight:8 },

  chipsRow:{ flexDirection:'row', gap:8, marginTop:10, flexWrap:'wrap' },
  chip:{ paddingHorizontal:10, paddingVertical:6, borderRadius:14, backgroundColor:'#F3F4F6' },
  chipOutline:{ backgroundColor:'#EEF6FF', borderWidth:1, borderColor:'#BBD7FF' },
  chipText:{ fontSize:12, fontWeight:'700', color:'#6B7280' },
  chipTextPrimary:{ color:'#0F66E9' },

  subRight:{ fontSize:14, color:'#6B7280', marginTop:8, textAlign:'right' },

  metricsCard:{ backgroundColor:'#FFFFFF', borderRadius:12, padding:12, marginTop:12, borderWidth:1, borderColor:'#F3F4F6' },
  metricRow:{ flexDirection:'row', justifyContent:'space-between', alignItems:'center', paddingVertical:4 },
  metricL:{ flexDirection:'row', alignItems:'center', gap:6 },
  metricLabel:{ fontSize:12, color:'#6B7280' },
  metricVal:{ fontSize:16, fontWeight:'700', color:'#111827' },

  meterTrack:{ height:10, borderRadius:6, backgroundColor:'#F3F4F6', overflow:'hidden', position:'relative', marginTop:8 },
  meterFill:{ position:'absolute', left:0, top:0, bottom:0, borderRadius:6 },
  marker:{ position:'absolute', top:-2, width:2, height:14, backgroundColor:'#CBD5E1', transform:[{ translateX:-1 }] },

  errorRow:{ flexDirection:'row', alignItems:'center', gap:6, marginTop:8 },
  errorText:{ fontSize:12, color:'#FF3B30', fontWeight:'600' },

  submitButton:{ backgroundColor:'#007AFF', flexDirection:'row', alignItems:'center', justifyContent:'center',
    paddingVertical:16, borderRadius:12, marginTop:6, marginBottom:20, gap:8 },
  submitButtonDisabled:{ backgroundColor:'#8E8E93' },
  submitButtonText:{ color:'#FFFFFF', fontSize:16, fontWeight:'600' },

  warningCard:{ flexDirection:'row', backgroundColor:'#FFFBEB', borderRadius:12, padding:16, marginBottom:20, borderWidth:1, borderColor:'#FCD34D' },
  warningText:{ flex:1, fontSize:14, color:'#92400E', marginLeft:12, lineHeight:20 },
});
