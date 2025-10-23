/**
 * Crypto SBLOC Card — Holdings-Aware (MAX, % chips, Top-up)
 * - Reads user's holdings to show "Available"
 * - MAX + 25/50/75/100% chips from balance
 * - Prevents over-pledging; clear UX
 * - Top-up CTA (prop callback)
 */

import React, { useEffect, useMemo, useState } from 'react';
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity, Alert,
  ActivityIndicator, ScrollView
} from 'react-native';
import { useQuery, useMutation } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

import {
  GET_SUPPORTED_CURRENCIES,
  GET_CRYPTO_PRICE,
  GET_CRYPTO_SBLOC_LOANS,
  CREATE_SBLOC_LOAN
} from '../../cryptoQueries';
import WhatIfSlider from './WhatIfSlider';

// Add this lightweight holdings query (adjust to your schema if needed)
import { gql } from '@apollo/client';
const GET_CRYPTO_HOLDINGS = gql`
  query GetCryptoHoldings {
    cryptoPortfolio {
      holdings {
        cryptocurrency { symbol }
        quantity
      }
    }
  }
`;

const MAX_LTV = 50;
const LIQUIDATION_LTV = 40;
const SAFE_LTV = 35;

const maskify = (_: string | number) => '•••••';

type Props = {
  onLoanSuccess: () => void;
  onTopUpCollateral?: (symbol: string) => void; // optional navigation to buy/deposit
};

const CryptoSBLOCCard: React.FC<Props> = ({ onLoanSuccess, onTopUpCollateral }) => {
  const [selectedSymbol, setSelectedSymbol] = useState('BTC');
  const [collateralQuantity, setCollateralQuantity] = useState('');
  const [loanAmount, setLoanAmount] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [maskAmounts, setMaskAmounts] = useState(false);
  const [errorText, setErrorText] = useState<string | null>(null);

  // Queries
  const { data: currenciesData } = useQuery(GET_SUPPORTED_CURRENCIES);
  const { data: priceData, loading: priceLoading } = useQuery(GET_CRYPTO_PRICE, {
    variables: { symbol: selectedSymbol }, skip: !selectedSymbol,
  });
  const { data: loansData, refetch: refetchLoans } = useQuery(GET_CRYPTO_SBLOC_LOANS);
  const { data: holdingsData, loading: holdingsLoading } = useQuery(GET_CRYPTO_HOLDINGS);

  const [createLoan] = useMutation(CREATE_SBLOC_LOAN);

  const priceUsd = priceData?.cryptoPrice?.priceUsd ?? 0;

  // Find available balance for selected symbol
  const availableQty = useMemo(() => {
    const list = holdingsData?.cryptoPortfolio?.holdings || [];
    const row = list.find((h: any) => h?.cryptocurrency?.symbol === selectedSymbol);
    return row ? parseFloat(row.quantity || 0) : 0;
  }, [holdingsData, selectedSymbol]);

  // Derived values
  const qtyNum = parseFloat(collateralQuantity || '0') || 0;
  const loanNum = parseFloat(loanAmount || '0') || 0;
  const collateralValue = qtyNum > 0 && priceUsd > 0 ? qtyNum * priceUsd : 0;
  const ltv = collateralValue > 0 && loanNum > 0 ? (loanNum / collateralValue) * 100 : 0;
  const bufferToLiquidation = Math.max(0, LIQUIDATION_LTV - ltv);
  const withinLimit = ltv > 0 && ltv <= MAX_LTV;
  const withinBalance = qtyNum <= availableQty;

  // Suggest max LTV when quantity changes and user hasn't set loan
  useEffect(() => {
    if (!collateralQuantity || priceUsd <= 0) return;
    if (!loanAmount || parseFloat(loanAmount) === 0) {
      const v = parseFloat(collateralQuantity) * priceUsd;
      setLoanAmount(((v || 0) * 0.5).toFixed(2));
    }
  }, [collateralQuantity, priceUsd]); // eslint-disable-line

  // Validation
  useEffect(() => {
    if (!collateralQuantity || !loanAmount) { setErrorText(null); return; }
    if (!withinBalance) setErrorText(`You only have ${(availableQty || 0).toFixed(6)} ${selectedSymbol} available`);
    else if (ltv > MAX_LTV) setErrorText(`LTV ${(ltv || 0).toFixed(1)}% exceeds ${MAX_LTV}% maximum`);
    else if (ltv > LIQUIDATION_LTV) setErrorText(`Above liquidation threshold (${LIQUIDATION_LTV}%). Please reduce.`);
    else setErrorText(null);
  }, [ltv, withinBalance, availableQty, selectedSymbol, collateralQuantity, loanAmount]);

  const formatCurrency = (n: number) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n);

  // Quantity helpers from balance
  const setQtyFromBalancePct = (pct: number) => {
    if (availableQty <= 0) return;
    const q = (availableQty * pct) / 100;
    setCollateralQuantity((q || 0).toFixed(8));
  };
  const setQtyMax = () => setQtyFromBalancePct(100);

  // Loan amount helpers from target LTV (based on entered qty)
  const setLoanByTargetLtv = (targetPct: number) => {
    if (qtyNum <= 0 || priceUsd <= 0) return;
    setLoanAmount((((qtyNum || 0) * (priceUsd || 0)) * ((targetPct || 0) / 100)).toFixed(2));
  };

  const handleCreateLoan = async () => {
    if (!qtyNum || !loanNum) return Alert.alert('Error', 'Please fill in all fields');
    if (!withinBalance) return Alert.alert('Error', `Insufficient ${selectedSymbol} available`);
    if (priceUsd <= 0) return Alert.alert('Error', 'Unable to fetch current price. Try again.');
    if (ltv > MAX_LTV) return Alert.alert('Error', `Loan amount exceeds maximum LTV of ${MAX_LTV}%`);

    setIsSubmitting(true);
    try {
      const res = await createLoan({
        variables: { symbol: selectedSymbol, collateralQuantity: qtyNum, loanAmount: loanNum },
      });
      if (res.data?.createSblocLoan?.success) {
        Alert.alert('Success', `SBLOC loan created!\nLoan ID: ${res.data.createSblocLoan.loanId}`, [{
          text: 'OK',
          onPress: () => {
            setCollateralQuantity('');
            setLoanAmount('');
            refetchLoans();
            onLoanSuccess();
          }
        }]);
      } else {
        Alert.alert('Error', res.data?.createSblocLoan?.message || 'Failed to create loan');
      }
    } catch (e) {
      console.error(e);
      Alert.alert('Error', 'Failed to create SBLOC loan. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Colors
  const ltvColor = useMemo(() => {
    if (ltv === 0) return '#8E8E93';
    if (ltv <= SAFE_LTV) return '#34C759';
    if (ltv <= LIQUIDATION_LTV) return '#FF9500';
    if (ltv <= MAX_LTV) return '#FF3B30';
    return '#8B5CF6';
  }, [ltv]);
  const meterWidthPct = Math.min(100, Math.max(0, (ltv / MAX_LTV) * 100));

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Header */}
      <View style={styles.rowBetween}>
        <Text style={styles.headerTitle}>Create SBLOC</Text>
        <TouchableOpacity onPress={() => setMaskAmounts(v => !v)} style={styles.iconBtn}>
          <Icon name={maskAmounts ? 'eye-off' : 'eye'} size={18} color="#8E8E93" />
        </TouchableOpacity>
      </View>

      {/* Symbol picker */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Collateral Cryptocurrency</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.symbolContainer}>
          {(currenciesData?.supportedCurrencies?.slice(0, 5) || []).map((c: any) => (
            <TouchableOpacity
              key={c.symbol}
              style={[styles.symbolButton, selectedSymbol === c.symbol && styles.activeSymbolButton]}
              onPress={() => {
                setSelectedSymbol(c.symbol);
                setCollateralQuantity('');
                setLoanAmount('');
              }}
              activeOpacity={0.85}
            >
              <Text style={[styles.symbolText, selectedSymbol === c.symbol && styles.activeSymbolText]}>
                {c.symbol}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>

      {/* Price + Buffer */}
      <View style={styles.kpiCard}>
        <View style={styles.kpiItem}>
          <Text style={styles.kpiLabel}>Price ({selectedSymbol})</Text>
          {priceLoading ? (
            <ActivityIndicator size="small" color="#007AFF" />
          ) : (
            <Text style={styles.kpiValue}>
              {maskAmounts ? maskify(priceUsd) : formatCurrency(priceUsd || 0)}
            </Text>
          )}
        </View>
        <View style={styles.kpiDivider} />
        <View style={styles.kpiItem}>
          <Text style={styles.kpiLabel}>Buffer to Liquidation</Text>
          <Text style={[styles.kpiValue, { color: bufferToLiquidation > 0 ? '#34C759' : '#FF3B30' }]}>
            {(bufferToLiquidation || 0).toFixed(1)}%
          </Text>
        </View>
      </View>

      {/* Available balance line */}
      <View style={styles.availRow}>
        <Text style={styles.availLabel}>Available</Text>
        {holdingsLoading ? (
          <ActivityIndicator size="small" color="#8E8E93" />
        ) : (
          <Text style={styles.availValue}>
            {(availableQty || 0).toFixed(6)} {selectedSymbol}
          </Text>
        )}
      </View>

      {/* Collateral Quantity (MAX + % chips from balance) */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Collateral Quantity</Text>
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            value={collateralQuantity}
            onChangeText={setCollateralQuantity}
            placeholder="0.00000000"
            keyboardType="numeric"
            autoCapitalize="none"
          />
          <TouchableOpacity onPress={setQtyMax} disabled={availableQty <= 0}>
            <Text style={styles.maxBtn}>MAX</Text>
          </TouchableOpacity>
          <Text style={styles.inputSuffix}>{selectedSymbol}</Text>
        </View>

        <View style={styles.chipsRow}>
          {[25, 50, 75, 100].map(p => (
            <TouchableOpacity
              key={p}
              style={styles.chip}
              onPress={() => setQtyFromBalancePct(p)}
              disabled={availableQty <= 0}
            >
              <Text style={styles.chipText}>{p}% of balance</Text>
            </TouchableOpacity>
          ))}
        </View>

        {collateralValue > 0 && (
          <Text style={styles.subRight}>
            Collateral Value: {maskAmounts ? maskify(collateralValue) : formatCurrency(collateralValue)}
          </Text>
        )}

        {!withinBalance && collateralQuantity ? (
          <View style={styles.inlineWarn}>
            <Icon name="alert-triangle" size={14} color="#FF3B30" />
            <Text style={styles.inlineWarnText}>
              You only have {(availableQty || 0).toFixed(6)} {selectedSymbol}
            </Text>
          </View>
        ) : null}
      </View>

      {/* Loan amount + LTV targets */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Loan Amount (USD)</Text>
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            value={loanAmount}
            onChangeText={setLoanAmount}
            placeholder="0.00"
            keyboardType="numeric"
            autoCapitalize="none"
          />
          <Text style={styles.inputSuffix}>USD</Text>
        </View>

        <View style={styles.chipsRow}>
          {[25, 35, 45, 50].map(p => (
            <TouchableOpacity
              key={p}
              style={[styles.chip, p === 50 && styles.chipOutline]}
              onPress={() => setLoanByTargetLtv(p)}
              disabled={qtyNum <= 0 || priceUsd <= 0}
            >
              <Text style={[styles.chipText, p === 50 && styles.chipTextPrimary]}>{p}% LTV</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* LTV Meter */}
        <View style={styles.meterCard}>
          <View style={styles.meterHeader}>
            <Text style={styles.meterLabel}>Current LTV</Text>
            <Text style={[styles.meterValue, { color: ltvColor }]}>{(ltv || 0).toFixed(1)}%</Text>
          </View>
          <View style={styles.meterTrack}>
            <View style={[styles.meterFill, { width: `${meterWidthPct}%`, backgroundColor: ltvColor }]} />
            <View style={[styles.marker, { left: `${(SAFE_LTV / MAX_LTV) * 100}%` }]} />
            <View style={[styles.marker, { left: `${(LIQUIDATION_LTV / MAX_LTV) * 100}%` }]} />
            <View style={[styles.marker, { left: '100%' }]} />
          </View>
          <View style={styles.meterLegend}>
            <Text style={[styles.legendItem, { color: '#34C759' }]}>≤ {SAFE_LTV}% Safe</Text>
            <Text style={[styles.legendItem, { color: '#FF9500' }]}>≤ {LIQUIDATION_LTV}% Caution</Text>
            <Text style={[styles.legendItem, { color: '#FF3B30' }]}>≤ {MAX_LTV}% Max</Text>
          </View>
          {!!errorText && (
            <View style={styles.errorRow}>
              <Icon name="alert-triangle" size={16} color="#FF3B30" />
              <Text style={styles.errorText}>{errorText}</Text>
            </View>
          )}
        </View>
      </View>

      {/* Top-up CTA */}
      {withinBalance && qtyNum > 0 && ltv > 0 && ltv >= SAFE_LTV && onTopUpCollateral && (
        <TouchableOpacity style={styles.topupBtn} onPress={() => onTopUpCollateral?.(selectedSymbol)}>
          <Icon name="plus-circle" size={18} color="#0F66E9" />
          <Text style={styles.topupText}>Add more {selectedSymbol} as collateral</Text>
        </TouchableOpacity>
      )}

      {/* Terms */}
      <View style={styles.termsCard}>
        <Text style={styles.termsTitle}>Loan Terms</Text>
        <View style={styles.termsList}>
          <View style={styles.termItem}><Icon name="percent" size={16} color="#007AFF" /><Text style={styles.termText}>Interest Rate: 5.0% APR</Text></View>
          <View style={styles.termItem}><Icon name="shield" size={16} color="#007AFF" /><Text style={styles.termText}>Maintenance Margin: 50%</Text></View>
          <View style={styles.termItem}><Icon name="alert-triangle" size={16} color="#FF9500" /><Text style={styles.termText}>Liquidation Threshold: 40%</Text></View>
          <View style={styles.termItem}><Icon name="clock" size={16} color="#007AFF" /><Text style={styles.termText}>No Fixed Term — Repay Anytime</Text></View>
        </View>
      </View>

      {/* Submit */}
      <TouchableOpacity
        style={[styles.submitButton, (isSubmitting || !withinLimit || ltv === 0 || !withinBalance) && styles.submitButtonDisabled]}
        onPress={handleCreateLoan}
        disabled={isSubmitting || !withinLimit || ltv === 0 || !withinBalance}
        activeOpacity={0.85}
      >
        {isSubmitting ? <ActivityIndicator color="#FFFFFF" /> : (
          <>
            <Icon name="credit-card" size={20} color="#FFFFFF" />
            <Text style={styles.submitButtonText}>Create SBLOC Loan</Text>
          </>
        )}
      </TouchableOpacity>

      {/* Loans list + risk note */}
      {loansData?.cryptoSblocLoans?.length > 0 && (
        <View style={styles.loansSection}>
          <Text style={styles.loansTitle}>Your SBLOC Loans</Text>
          {loansData.cryptoSblocLoans.map((loan: any, idx: number) => (
            <View key={idx} style={styles.loanCard}>
              <View style={styles.loanHeader}>
                <Text style={styles.loanSymbol}>{loan.cryptocurrency.symbol}</Text>
                <View style={[styles.statusBadge, { backgroundColor: getStatusColor(loan.status) }]}>
                  <Text style={styles.statusText}>{loan.status}</Text>
                </View>
              </View>
              <View style={styles.loanDetails}>
                <View style={styles.loanDetailItem}>
                  <Text style={styles.loanDetailLabel}>Collateral</Text>
                  <Text style={styles.loanDetailValue}>
                    {(parseFloat(loan.collateralQuantity) || 0).toFixed(6)} {loan.cryptocurrency.symbol}
                  </Text>
                </View>
                <View style={styles.loanDetailItem}>
                  <Text style={styles.loanDetailLabel}>Loan Amount</Text>
                  <Text style={styles.loanDetailValue}>
                    {maskAmounts ? maskify(loan.loanAmount) : formatCurrency(parseFloat(loan.loanAmount))}
                  </Text>
                </View>
                <View style={styles.loanDetailItem}>
                  <Text style={styles.loanDetailLabel}>Interest Rate</Text>
                  <Text style={styles.loanDetailValue}>{((parseFloat(loan.interestRate) || 0) * 100).toFixed(1)}%</Text>
                </View>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* What-if stress test slider */}
      {collateralValue > 0 && loanAmount && (
        <WhatIfSlider
          collateralUsd={collateralValue}
          loanUsd={parseFloat(loanAmount) || 0}
          onStressChange={(stress) => {
            // Handle stress test results
            console.log('Stress test result:', stress);
          }}
        />
      )}

      <View style={styles.warningCard}>
        <Icon name="alert-triangle" size={20} color="#FF9500" />
        <Text style={styles.warningText}>
          SBLOC loans are secured by your crypto collateral. If collateral value drops, your LTV rises and you may face a margin call or liquidation. Keep your LTV comfortably below {LIQUIDATION_LTV}% for a safety buffer.
        </Text>
      </View>
    </ScrollView>
  );
};

const getStatusColor = (s: string) => {
  switch (s) { case 'ACTIVE': return '#34C759'; case 'WARNING': return '#FF9500';
    case 'LIQUIDATED': return '#FF3B30'; case 'REPAID': return '#8E8E93'; default: return '#8E8E93'; }
};

const styles = StyleSheet.create({
  container:{ flex:1, paddingTop:20 },
  rowBetween:{ flexDirection:'row', alignItems:'center', justifyContent:'space-between', marginBottom:8 },
  iconBtn:{ padding:8 }, headerTitle:{ fontSize:18, fontWeight:'700', color:'#111827' },

  section:{ marginBottom:20 }, sectionTitle:{ fontSize:16, fontWeight:'600', color:'#111827', marginBottom:12 },

  symbolContainer:{ flexDirection:'row' },
  symbolButton:{ paddingHorizontal:16, paddingVertical:8, borderRadius:20, backgroundColor:'#F3F4F6', marginRight:8 },
  activeSymbolButton:{ backgroundColor:'#007AFF' },
  symbolText:{ fontSize:14, fontWeight:'600', color:'#6B7280' },
  activeSymbolText:{ color:'#FFFFFF' },

  kpiCard:{ backgroundColor:'#FFFFFF', borderRadius:12, padding:16, marginBottom:12,
    shadowColor:'#000', shadowOffset:{ width:0, height:2 }, shadowOpacity:0.1, shadowRadius:4, elevation:3,
    flexDirection:'row', alignItems:'center', justifyContent:'space-between' },
  kpiItem:{ flex:1 }, kpiDivider:{ width:1, height:32, backgroundColor:'#F3F4F6', marginHorizontal:12 },
  kpiLabel:{ fontSize:12, color:'#8E8E93', marginBottom:4 }, kpiValue:{ fontSize:18, fontWeight:'700', color:'#111827' },

  availRow:{ flexDirection:'row', justifyContent:'space-between', alignItems:'center', marginBottom:8 },
  availLabel:{ fontSize:12, color:'#6B7280' }, availValue:{ fontSize:12, color:'#111827', fontWeight:'600' },

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

  meterCard:{ backgroundColor:'#FFFFFF', borderRadius:12, padding:12, marginTop:12, borderWidth:1, borderColor:'#F3F4F6' },
  meterHeader:{ flexDirection:'row', justifyContent:'space-between', alignItems:'center', marginBottom:8 },
  meterLabel:{ fontSize:12, color:'#6B7280' }, meterValue:{ fontSize:16, fontWeight:'700' },
  meterTrack:{ height:10, borderRadius:6, backgroundColor:'#F3F4F6', overflow:'hidden', position:'relative' },
  meterFill:{ position:'absolute', left:0, top:0, bottom:0, borderRadius:6 },
  marker:{ position:'absolute', top:-2, width:2, height:14, backgroundColor:'#CBD5E1', transform:[{ translateX:-1 }] },
  meterLegend:{ flexDirection:'row', justifyContent:'space-between', marginTop:8 },
  legendItem:{ fontSize:11, fontWeight:'700' },
  errorRow:{ flexDirection:'row', alignItems:'center', gap:6, marginTop:8 },
  errorText:{ fontSize:12, color:'#FF3B30', fontWeight:'600' },
  inlineWarn:{ flexDirection:'row', alignItems:'center', gap:6, marginTop:8 },
  inlineWarnText:{ fontSize:12, color:'#FF3B30', fontWeight:'600' },

  termsCard:{ backgroundColor:'#FFFFFF', borderRadius:12, padding:16, marginTop:8, marginBottom:16,
    shadowColor:'#000', shadowOffset:{ width:0, height:2 }, shadowOpacity:0.1, shadowRadius:4, elevation:3 },
  termsTitle:{ fontSize:16, fontWeight:'600', color:'#111827', marginBottom:12 },
  termsList:{ gap:8 }, termItem:{ flexDirection:'row', alignItems:'center' }, termText:{ fontSize:14, color:'#6B7280', marginLeft:8 },

  topupBtn:{ flexDirection:'row', alignItems:'center', gap:8, alignSelf:'flex-start', marginTop:8, marginBottom:4, paddingHorizontal:10, paddingVertical:6,
    borderRadius:10, backgroundColor:'#EEF6FF', borderWidth:1, borderColor:'#BBD7FF' },
  topupText:{ color:'#0F66E9', fontWeight:'700' },

  submitButton:{ backgroundColor:'#007AFF', flexDirection:'row', alignItems:'center', justifyContent:'center',
    paddingVertical:16, borderRadius:12, marginBottom:20 },
  submitButtonDisabled:{ backgroundColor:'#8E8E93' },
  submitButtonText:{ color:'#FFFFFF', fontSize:16, fontWeight:'600', marginLeft:8 },

  loansSection:{ marginBottom:20 }, loansTitle:{ fontSize:18, fontWeight:'600', color:'#111827', marginBottom:12 },
  loanCard:{ backgroundColor:'#FFFFFF', borderRadius:12, padding:16, marginBottom:12,
    shadowColor:'#000', shadowOffset:{ width:0, height:2 }, shadowOpacity:0.1, shadowRadius:4, elevation:3 },
  loanHeader:{ flexDirection:'row', justifyContent:'space-between', alignItems:'center', marginBottom:12 },
  loanSymbol:{ fontSize:16, fontWeight:'600', color:'#111827' },
  statusBadge:{ paddingHorizontal:8, paddingVertical:4, borderRadius:12 }, statusText:{ fontSize:12, fontWeight:'600', color:'#FFFFFF' },
  loanDetails:{ gap:8 }, loanDetailItem:{ flexDirection:'row', justifyContent:'space-between', alignItems:'center' },
  loanDetailLabel:{ fontSize:14, color:'#8E8E93' }, loanDetailValue:{ fontSize:14, fontWeight:'600', color:'#111827' },

  warningCard:{ flexDirection:'row', backgroundColor:'#FFFBEB', borderRadius:12, padding:16, marginBottom:20, borderWidth:1, borderColor:'#FCD34D' },
  warningText:{ flex:1, fontSize:14, color:'#92400E', marginLeft:12, lineHeight:20 },
});

export default CryptoSBLOCCard;