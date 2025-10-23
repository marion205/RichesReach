import React, { useCallback, useMemo, useState } from 'react';
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity,
  ActivityIndicator, ScrollView, Linking, Appearance
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import Toast from 'react-native-toast-message';
import { useAAVEUserData } from '../../hooks/useAAVEUserData';

// Optional: if you have react-native-linear-gradient or expo-linear-gradient, uncomment:
// import LinearGradient from 'react-native-linear-gradient';

type Asset = { symbol: 'USDC' | 'WETH' | 'USDT'; name: string; color: string; decimals?: number };

interface WorkingAAVECardProps {
  onSuccess?: () => void;
  onSupply?: (opts: { symbol: Asset['symbol']; amount: string }) => Promise<{ hash?: string }>;
  onBorrow?: (opts: { symbol: Asset['symbol']; amount: string }) => Promise<{ hash?: string }>;
  explorerTxUrl?: (hash: string) => string;
  healthFactor?: number;
  liquidationThresholdPct?: number;
  supplyApyPct?: number;
  walletAddress?: string | null;
  backendBaseUrl?: string;
}

const ASSETS: Asset[] = [
  { symbol: 'USDC', name: 'USD Coin', color: '#2775CA', decimals: 6 },
  { symbol: 'WETH', name: 'Wrapped Ether', color: '#627EEA', decimals: 18 },
  { symbol: 'USDT', name: 'Tether USD', color: '#26A17B', decimals: 6 },
];

const numberish = (v: string) => /^(\d+(\.\d{0,18})?)?$/.test(v);
const parsePositive = (v: string) => {
  const n = Number(v);
  if (!v || Number.isNaN(n)) return { ok: false, err: 'Enter a valid number' };
  if (n <= 0) return { ok: false, err: 'Amount must be greater than 0' };
  return { ok: true as const, n };
};

const WorkingAAVECard: React.FC<WorkingAAVECardProps> = ({
  onSuccess,
  onSupply,
  onBorrow,
  explorerTxUrl,
  healthFactor = 2.5,
  liquidationThresholdPct = 80,
  supplyApyPct = 3.2,
  walletAddress,
  backendBaseUrl,
}) => {
  const scheme = Appearance.getColorScheme();
  const isDark = scheme === 'dark';

  const theme = useMemo(() => ({
    bg: isDark ? '#0A0B0D' : '#f2f4f7',
    card: isDark ? '#111318' : '#ffffff',
    text: isDark ? '#E6E8EB' : '#121416',
    subtext: isDark ? '#9BA1A6' : '#626D7A',
    border: isDark ? '#1b1f24' : '#E5E9F0',
    tint: '#0a84ff',
    success: '#2ecc71',
    primary: '#0a84ff',
    primaryDark: '#0060cc',
    warning: '#ffcc00',
    danger: '#ff5a5f',
    tile: isDark ? '#0F1115' : '#F7F9FC',
    shadow: isDark ? '#000000' : '#0D1B2A',
  }), [isDark]);

  const [supplyAmount, setSupplyAmount] = useState('100');
  const [borrowAmount, setBorrowAmount] = useState('50');
  const [selectedAsset, setSelectedAsset] = useState<Asset['symbol']>('USDC');
  const [loadingStep, setLoadingStep] = useState<null | 'supply' | 'borrow'>(null);

  const selected = useMemo(() => ASSETS.find(a => a.symbol === selectedAsset)!, [selectedAsset]);

  // Live AAVE data
  const { loading: riskLoading, error: riskError, hf, ltvPct, liqPct, reload } =
    useAAVEUserData({ address: walletAddress, backendBaseUrl: backendBaseUrl || '' });

  const hfStatus = (() => {
    if (hf == null) return { label: '—', color: theme.subtext, bg: isDark ? '#20252b' : '#eef2f7' };
    if (hf >= 2.0) return { label: `${(hf || 0).toFixed(2)}× Safe`, color: '#0f5132', bg: '#d1e7dd' };
    if (hf >= 1.2) return { label: `${(hf || 0).toFixed(2)}× Caution`, color: '#664d03', bg: '#fff3cd' };
    return { label: `${(hf || 0).toFixed(2)}× Risk`, color: '#842029', bg: '#f8d7da' };
  })();

  const setAmountGuarded = (setter: (s: string) => void) => (txt: string) => {
    if (txt === '' || numberish(txt)) setter(txt);
  };

  const openExplorer = useCallback((hash?: string) => {
    if (!hash || !explorerTxUrl) return;
    Linking.openURL(explorerTxUrl(hash)).catch(() => {
      Toast.show({ type: 'info', text1: 'Copy the hash from the toast to view on explorer.' });
    });
  }, [explorerTxUrl]);

  const handleSupply = useCallback(async () => {
    if (loadingStep) return;
    const check = parsePositive(supplyAmount);
    if (!check.ok) {
      Toast.show({ type: 'error', text1: 'Invalid supply amount', text2: check.err });
      return;
    }
    setLoadingStep('supply');
    try {
      Toast.show({ type: 'info', text1: `Approving & supplying ${supplyAmount} ${selectedAsset}…` });
      const result = onSupply
        ? await onSupply({ symbol: selectedAsset, amount: supplyAmount })
        : await new Promise<{ hash?: string }>((r) => setTimeout(() => r({ hash: '0xSIM_SUPPLY' }), 900));
      Toast.show({
        type: 'success',
        text1: `Supply submitted`,
        text2: result?.hash ? 'Tap to view on explorer' : undefined,
        onPress: () => openExplorer(result?.hash),
      });
      onSuccess?.();
    } catch (e: any) {
      Toast.show({ type: 'error', text1: 'Supply failed', text2: e?.message ?? 'Try again.' });
    } finally {
      setLoadingStep(null);
    }
  }, [loadingStep, supplyAmount, selectedAsset, onSupply, onSuccess, openExplorer]);

  const handleBorrow = useCallback(async () => {
    if (loadingStep) return;
    const check = parsePositive(borrowAmount);
    if (!check.ok) {
      Toast.show({ type: 'error', text1: 'Invalid borrow amount', text2: check.err });
      return;
    }
    setLoadingStep('borrow');
    try {
      Toast.show({ type: 'info', text1: `Validating & borrowing ${borrowAmount} ${selectedAsset}…` });
      const result = onBorrow
        ? await onBorrow({ symbol: selectedAsset, amount: borrowAmount })
        : await new Promise<{ hash?: string }>((r) => setTimeout(() => r({ hash: '0xSIM_BORROW' }), 900));
      Toast.show({
        type: 'success',
        text1: `Borrow submitted`,
        text2: result?.hash ? 'Tap to view on explorer' : undefined,
        onPress: () => openExplorer(result?.hash),
      });
      onSuccess?.();
    } catch (e: any) {
      Toast.show({ type: 'error', text1: 'Borrow failed', text2: e?.message ?? 'Try again.' });
    } finally {
      setLoadingStep(null);
    }
  }, [loadingStep, borrowAmount, selectedAsset, onBorrow, onSuccess, openExplorer]);

  const supplyDisabled = loadingStep !== null || !parsePositive(supplyAmount).ok;
  const borrowDisabled = loadingStep !== null || !parsePositive(borrowAmount).ok;

  return (
    <ScrollView
      style={[styles.container, { backgroundColor: theme.bg }]}
      contentContainerStyle={styles.containerContent}
      keyboardShouldPersistTaps="handled"
      testID="aave-scroll"
    >
      {/* Hero */}
      {/* If you have LinearGradient, replace the hero container with a gradient view */}
      <View style={[styles.hero, { backgroundColor: isDark ? '#0E1218' : '#0a84ff' }]}>
        <View style={styles.heroTopRow}>
          <Text style={styles.brand}>RichesReach</Text>
          <View style={styles.badge}>
            <Icon name="zap" size={12} color="#fff" />
            <Text style={styles.badgeText}>Hybrid</Text>
          </View>
        </View>
        <Text style={styles.heroTitle}>AAVE DeFi Lending</Text>
        <Text style={styles.heroSubtitle}>Supply collateral and borrow with live risk checks</Text>
      </View>

      {/* Asset selector as segmented pills */}
      <View style={[styles.section, { backgroundColor: theme.card, shadowColor: theme.shadow }]}>
        <Text style={[styles.sectionTitle, { color: theme.text }]}>Asset</Text>
        <View style={styles.segmentWrap}>
          {ASSETS.map((asset) => {
            const active = selectedAsset === asset.symbol;
            return (
              <TouchableOpacity
                key={asset.symbol}
                onPress={() => setSelectedAsset(asset.symbol)}
                style={[
                  styles.segment,
                  { borderColor: theme.border, backgroundColor: theme.tile },
                  active && { backgroundColor: isDark ? '#162034' : '#e7f1ff', borderColor: theme.primary },
                ]}
                accessibilityRole="button"
              >
                <View style={[styles.segmentDot, { backgroundColor: asset.color }]} />
                <Text style={[styles.segmentText, { color: active ? theme.primary : theme.text }]}>{asset.symbol}</Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {/* Supply */}
      <View style={[styles.section, { backgroundColor: theme.card, shadowColor: theme.shadow }]}>
        <View style={styles.rowBetween}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>Supply</Text>
          <Text style={[styles.helper, { color: theme.subtext }]}>Balance: —</Text>
        </View>
        <View style={[styles.inputContainer, { borderColor: theme.border, backgroundColor: theme.tile }]}>
          <Icon name="plus-circle" size={18} color={theme.subtext} style={{ marginHorizontal: 8 }} />
          <TextInput
            style={[styles.input, { color: theme.text }]}
            value={supplyAmount}
            onChangeText={setAmountGuarded(setSupplyAmount)}
            placeholder="0.00"
            placeholderTextColor={theme.subtext}
            keyboardType="decimal-pad"
            returnKeyType="done"
          />
          <View style={styles.inputSuffix}>
            <Text style={[styles.inputSuffixText, { color: theme.subtext }]}>{selected.symbol}</Text>
          </View>
        </View>

        <TouchableOpacity
          style={[
            styles.cta,
            { backgroundColor: supplyDisabled ? '#98c7ff' : theme.primary, shadowColor: theme.shadow },
          ]}
          onPress={handleSupply}
          disabled={supplyDisabled}
          accessibilityRole="button"
          accessibilityState={{ disabled: supplyDisabled, busy: loadingStep === 'supply' }}
        >
          {loadingStep === 'supply' ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <>
              <Icon name="upload" size={16} color="#fff" />
              <Text style={styles.ctaText}>Supply {selected.symbol}</Text>
            </>
          )}
        </TouchableOpacity>
      </View>

      {/* Borrow */}
      <View style={[styles.section, { backgroundColor: theme.card, shadowColor: theme.shadow }]}>
        <View style={styles.rowBetween}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>Borrow</Text>
          <Text style={[styles.helper, { color: theme.subtext }]}>Available: —</Text>
        </View>
        <View style={[styles.inputContainer, { borderColor: theme.border, backgroundColor: theme.tile }]}>
          <Icon name="minus-circle" size={18} color={theme.subtext} style={{ marginHorizontal: 8 }} />
          <TextInput
            style={[styles.input, { color: theme.text }]}
            value={borrowAmount}
            onChangeText={setAmountGuarded(setBorrowAmount)}
            placeholder="0.00"
            placeholderTextColor={theme.subtext}
            keyboardType="decimal-pad"
            returnKeyType="done"
          />
          <View style={styles.inputSuffix}>
            <Text style={[styles.inputSuffixText, { color: theme.subtext }]}>{selected.symbol}</Text>
          </View>
        </View>

        <TouchableOpacity
          style={[
            styles.cta,
            { backgroundColor: borrowDisabled ? '#98c7ff' : theme.primary, shadowColor: theme.shadow },
          ]}
          onPress={handleBorrow}
          disabled={borrowDisabled}
          accessibilityRole="button"
          accessibilityState={{ disabled: borrowDisabled, busy: loadingStep === 'borrow' }}
        >
          {loadingStep === 'borrow' ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <>
              <Icon name="download" size={16} color="#fff" />
              <Text style={styles.ctaText}>Borrow {selected.symbol}</Text>
            </>
          )}
        </TouchableOpacity>
      </View>

      {/* Risk & Rates */}
      <View style={[styles.section, { backgroundColor: theme.card, shadowColor: theme.shadow }]}>
        <View style={styles.rowBetween}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>Risk & Rates</Text>
          {!!backendBaseUrl && !!walletAddress && (
            <TouchableOpacity onPress={reload} style={[styles.refreshBtn, { backgroundColor: isDark ? '#13233a' : '#e7f1ff' }]}>
              <Icon name="refresh-ccw" size={14} color={theme.primary} />
              <Text style={[styles.refreshTxt, { color: theme.primary }]}>Refresh</Text>
            </TouchableOpacity>
          )}
        </View>

        {riskError ? (
          <View style={styles.infoRow}>
            <Icon name="alert-triangle" size={16} color={theme.danger} />
            <Text style={[styles.infoText, { color: theme.danger }]}>Failed to load: {riskError}</Text>
          </View>
        ) : null}

        <View style={styles.metricGrid}>
          <View style={[styles.metricTile, { backgroundColor: theme.tile }]}>
            <View style={styles.metricHeader}>
              <Icon name="activity" size={14} color={theme.subtext} />
              <Text style={[styles.metricLabel, { color: theme.subtext }]}>Health Factor</Text>
            </View>
            <View style={[styles.hfPill, { backgroundColor: hfStatus.bg }]}>
              <Text style={[styles.hfPillText, { color: hfStatus.color }]}>{hfStatus.label}</Text>
            </View>
          </View>

          <View style={[styles.metricTile, { backgroundColor: theme.tile }]}>
            <View style={styles.metricHeader}>
              <Icon name="shield" size={14} color={theme.subtext} />
              <Text style={[styles.metricLabel, { color: theme.subtext }]}>Liquidation Threshold</Text>
            </View>
            <Text style={[styles.metricValue, { color: theme.text }]}>{liqPct != null ? `${liqPct}%` : '—'}</Text>
          </View>

          <View style={[styles.metricTile, { backgroundColor: theme.tile }]}>
            <View style={styles.metricHeader}>
              <Icon name="trending-up" size={14} color={theme.subtext} />
              <Text style={[styles.metricLabel, { color: theme.subtext }]}>Max LTV</Text>
            </View>
            <Text style={[styles.metricValue, { color: theme.text }]}>{ltvPct != null ? `${ltvPct}%` : '—'}</Text>
          </View>

          <View style={[styles.metricTile, { backgroundColor: theme.tile }]}>
            <View style={styles.metricHeader}>
              <Icon name="percent" size={14} color={theme.subtext} />
              <Text style={[styles.metricLabel, { color: theme.subtext }]}>Supply APY</Text>
            </View>
            <Text style={[styles.metricValue, { color: theme.text }]}>{supplyApyPct}%</Text>
          </View>
        </View>

        {riskLoading && (
          <View style={styles.skeletonRow}>
            <View style={[styles.skeleton, { backgroundColor: isDark ? '#1a1f26' : '#eef2f7' }]} />
            <View style={[styles.skeleton, { backgroundColor: isDark ? '#1a1f26' : '#eef2f7' }]} />
            <View style={[styles.skeleton, { backgroundColor: isDark ? '#1a1f26' : '#eef2f7' }]} />
          </View>
        )}
      </View>

      {/* Educational Info Section */}
      <View style={[styles.section, { backgroundColor: '#e8f5e8', shadowColor: theme.shadow, borderWidth: 1, borderColor: '#c3e6c3' }]}>
        <Text style={[styles.sectionTitle, { color: '#2d5a2d' }]}>What is AAVE DeFi Lending?</Text>
        <Text style={[styles.infoText, { color: '#1b5e20' }]}>
          AAVE is a decentralized lending protocol that allows you to earn interest on your crypto assets by supplying them as collateral, or borrow against your holdings. Your funds are secured by smart contracts and you maintain full control.
        </Text>
        
        <View style={styles.featureGrid}>
          <View style={[styles.featureCard, { backgroundColor: '#f0f8f0' }]}>
            <Icon name="upload" size={20} color="#2d5a2d" />
            <Text style={[styles.featureTitle, { color: '#2d5a2d' }]}>Supply Assets</Text>
            <Text style={[styles.featureDesc, { color: '#4a6741' }]}>
              Deposit crypto assets to earn interest. Your funds remain in your control and can be withdrawn anytime.
            </Text>
          </View>

          <View style={[styles.featureCard, { backgroundColor: '#f0f8f0' }]}>
            <Icon name="download" size={20} color="#2d5a2d" />
            <Text style={[styles.featureTitle, { color: '#2d5a2d' }]}>Borrow Against Collateral</Text>
            <Text style={[styles.featureDesc, { color: '#4a6741' }]}>
              Use your supplied assets as collateral to borrow other tokens. Maintain a healthy collateral ratio.
            </Text>
          </View>

          <View style={[styles.featureCard, { backgroundColor: '#f0f8f0' }]}>
            <Icon name="shield" size={20} color="#2d5a2d" />
            <Text style={[styles.featureTitle, { color: '#2d5a2d' }]}>Health Factor</Text>
            <Text style={[styles.featureDesc, { color: '#4a6741' }]}>
              Your Health Factor shows how safe your position is. Keep it above 1.0 to avoid liquidation.
            </Text>
          </View>

          <View style={[styles.featureCard, { backgroundColor: '#f0f8f0' }]}>
            <Icon name="zap" size={20} color="#2d5a2d" />
            <Text style={[styles.featureTitle, { color: '#2d5a2d' }]}>Instant Liquidity</Text>
            <Text style={[styles.featureDesc, { color: '#4a6741' }]}>
              Access liquidity without selling your assets. Perfect for short-term needs or trading opportunities.
            </Text>
          </View>
        </View>

        <View style={[styles.warningBox, { backgroundColor: '#fff3cd', borderColor: '#ffe69c' }]}>
          <Icon name="alert-triangle" size={16} color="#664d03" />
          <View style={{ flex: 1, marginLeft: 8 }}>
            <Text style={[styles.warningTitle, { color: '#664d03' }]}>Risk Warning</Text>
            <Text style={[styles.warningText, { color: '#664d03' }]}>
              DeFi lending involves smart contract risks, liquidation risks, and market volatility. Only invest what you can afford to lose.
            </Text>
          </View>
        </View>
      </View>

      <View style={{ height: 28 }} />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1 },
  containerContent: { paddingBottom: 24 },

  // HERO
  hero: {
    paddingHorizontal: 20,
    paddingTop: 18,
    paddingBottom: 22,
    borderBottomLeftRadius: 16,
    borderBottomRightRadius: 16,
  },
  heroTopRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  brand: { color: '#fff', fontSize: 12, fontWeight: '700', letterSpacing: 1 },
  badge: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingHorizontal: 10, paddingVertical: 6, borderRadius: 999, backgroundColor: 'rgba(255,255,255,0.18)',
  },
  badgeText: { color: '#fff', fontSize: 12, fontWeight: '700' },
  heroTitle: { color: '#fff', fontSize: 22, fontWeight: '800', marginTop: 8 },
  heroSubtitle: { color: 'rgba(255,255,255,0.85)', fontSize: 13, marginTop: 4 },

  // SECTIONS / CARDS
  section: {
    marginHorizontal: 12, marginTop: 12, padding: 16, borderRadius: 14,
    shadowOpacity: 0.08, shadowRadius: 12, shadowOffset: { width: 0, height: 6 }, elevation: 3,
  },
  sectionTitle: { fontSize: 15, fontWeight: '700' },
  rowBetween: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  helper: { fontSize: 12 },

  // SEGMENTED ASSET PILLS
  segmentWrap: { flexDirection: 'row', gap: 10 },
  segment: {
    flex: 1, paddingVertical: 10, paddingHorizontal: 12, borderRadius: 12,
    borderWidth: 1, flexDirection: 'row', alignItems: 'center', gap: 8,
  },
  segmentDot: { width: 10, height: 10, borderRadius: 5 },
  segmentText: { fontSize: 13, fontWeight: '700' },

  // INPUTS
  inputContainer: {
    flexDirection: 'row', alignItems: 'center',
    borderWidth: 1, borderRadius: 12, marginTop: 10,
  },
  input: { flex: 1, paddingVertical: 12, fontSize: 18 },
  inputSuffix: {
    paddingHorizontal: 12, paddingVertical: 8, borderLeftWidth: StyleSheet.hairlineWidth, borderLeftColor: 'rgba(0,0,0,0.06)',
  },
  inputSuffixText: { fontSize: 13, fontWeight: '700' },

  // CTA BUTTONS
  cta: {
    marginTop: 12, paddingVertical: 14, borderRadius: 12,
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8,
    shadowOpacity: 0.15, shadowRadius: 10, shadowOffset: { width: 0, height: 8 }, elevation: 4,
  },
  ctaText: { color: '#fff', fontSize: 15, fontWeight: '800' },

  // RISK & RATES
  refreshBtn: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 10, paddingVertical: 6, borderRadius: 12 },
  refreshTxt: { fontSize: 12, fontWeight: '800' },

  metricGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginTop: 8 },
  metricTile: { flexBasis: '48%', borderRadius: 12, padding: 12 },
  metricHeader: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 6 },
  metricLabel: { fontSize: 12, fontWeight: '700' },
  metricValue: { fontSize: 18, fontWeight: '800' },

  infoRow: { flexDirection: 'row', alignItems: 'center', marginTop: 8, gap: 8 },

  // HF pill
  hfPill: { paddingVertical: 6, paddingHorizontal: 10, borderRadius: 999 },
  hfPillText: { fontSize: 12, fontWeight: '800' },

  // skeletons
  skeletonRow: { flexDirection: 'row', gap: 10, marginTop: 10 },
  skeleton: { height: 16, borderRadius: 6, flex: 1, opacity: 0.7 },

  // Educational content styles
  infoText: { fontSize: 14, lineHeight: 20, marginBottom: 16 },
  featureGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12, marginTop: 12 },
  featureCard: { flexBasis: '48%', padding: 12, borderRadius: 12, alignItems: 'center' },
  featureTitle: { fontSize: 13, fontWeight: '800', marginTop: 8, marginBottom: 4, textAlign: 'center' },
  featureDesc: { fontSize: 11, lineHeight: 14, textAlign: 'center' },
  warningBox: { flexDirection: 'row', alignItems: 'flex-start', padding: 12, borderRadius: 10, borderWidth: 1, marginTop: 16 },
  warningTitle: { fontSize: 12, fontWeight: '800', marginBottom: 4 },
  warningText: { fontSize: 11, lineHeight: 14 },
});

export default WorkingAAVECard;