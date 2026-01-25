import React, { useCallback, useMemo, useState } from 'react';
import {
  View, Text, StyleSheet, TextInput, TouchableOpacity,
  ActivityIndicator, ScrollView, Linking, Appearance, Modal, Pressable
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import Toast from 'react-native-toast-message';
import { useAAVEUserData } from '../../hooks/useAaveUserData';
import { useAllowance } from '../../hooks/useAllowance';
import { useFiatPrice } from '../../utils/useFiatPrice';

type Asset = { symbol: 'USDC' | 'WETH' | 'USDT'; name: string; color: string; decimals?: number };

interface ProAaveCardProps {
  // Success callback
  onSuccess?: () => void;

  // Wire real flows; return { hash, needsApproval? } where needsApproval true means show approve step
  onApprove?: (opts: { symbol: Asset['symbol']; amount: string }) => Promise<{ hash?: string }>;
  onSupply?: (opts: { symbol: Asset['symbol']; amount: string }) => Promise<{ hash?: string; needsApproval?: boolean }>;
  onBorrow?: (opts: { symbol: Asset['symbol']; amount: string; rateMode?: 1|2 }) => Promise<{ hash?: string }>;

  // Optional utilities
  explorerTxUrl?: (hash: string) => string;
  getBalance?: (symbol: Asset['symbol']) => Promise<string>;      // returns human balance string
  getAllowance?: (symbol: Asset['symbol']) => Promise<string>;    // returns human allowance string
  toFiat?: (symbol: Asset['symbol'], humanAmount: string) => Promise<number>; // USD estimate

  // Live risk
  walletAddress?: string | null;
  backendBaseUrl?: string;

  // Visual details
  networkName?: string;         // e.g., 'Sepolia'
  brand?: string;               // e.g., 'RichesReach'
}

const ASSETS: Asset[] = [
  { symbol: 'USDC', name: 'USD Coin', color: '#2775CA', decimals: 6 },
  { symbol: 'WETH', name: 'Wrapped Ether', color: '#627EEA', decimals: 18 },
  { symbol: 'USDT', name: 'Tether USD', color: '#26A17B', decimals: 6 },
];

// Sepolia testnet addresses - replace with mainnet addresses for production
const ASSET_ADDRESSES = {
  USDC: '0x94a9D9AC8a22534E3FaCa9F4e7F2E2cf85d5E4C8', // Sepolia USDC
  WETH: '0xfFf9976782d46CC05687D3e5e4A18A9C6D6b7bc2', // Sepolia WETH
  USDT: '0x7169D38820dfd117C3FA1f22a697dba58d90BA06', // Sepolia USDT
};

// AAVE Pool address on Sepolia
const AAVE_POOL_ADDRESS = '0x6Ae43d3271ff6888e7Fc43Fd7321a503ff738951';

const numberish = (v: string) => /^(\d+(\.\d{0,18})?)?$/.test(v);
const parsePositive = (v: string) => {
  const n = Number(v);
  if (!v || Number.isNaN(n)) return { ok: false, err: 'Enter a valid number' };
  if (n <= 0) return { ok: false, err: 'Amount must be greater than 0' };
  return { ok: true as const, n };
};

const short = (addr?: string | null) => (addr ? `${addr.slice(0,6)}...${addr.slice(-4)}` : '--');

const ProAaveCard: React.FC<ProAaveCardProps> = ({
  onSuccess,
  onApprove,
  onSupply,
  onBorrow,
  explorerTxUrl,
  getBalance,
  getAllowance,
  toFiat,
  walletAddress,
  backendBaseUrl,
  networkName = 'Sepolia',
  brand = 'RichesReach',
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
    primary: '#0a84ff',
    primarySoft: '#e7f1ff',
    success: '#2ecc71',
    danger: '#ff5a5f',
    tile: isDark ? '#0F1115' : '#F7F9FC',
    shadow: isDark ? '#000000' : '#0D1B2A',
  }), [isDark]);

  // State
  const [assetModal, setAssetModal] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<Asset['symbol']>('USDC');
  const selected = useMemo(() => ASSETS.find(a => a.symbol === selectedAsset)!, [selectedAsset]);

  const [supplyAmount, setSupplyAmount] = useState('100');
  const [borrowAmount, setBorrowAmount] = useState('50');
  const [loadingStep, setLoadingStep] = useState<null | 'approve' | 'supply' | 'borrow'>(null);

  const [balance, setBalance] = useState<string | undefined>();
  const [allowance, setAllowance] = useState<string | undefined>();
  const [fiat, setFiat] = useState<number | undefined>();

  // Live risk (HF, LTV, Liq)
  const { loading: riskLoading, error: riskError, hf, ltvPct, liqPct, reload } =
    useAAVEUserData({ address: walletAddress, backendBaseUrl: backendBaseUrl || '' });

  // Mock provider for allowance checking (replace with real provider in production)
  const mockProvider = useMemo(() => ({
    call: async ({ to, data }: { to: string; data: string }) => {
      // Mock allowance response - in production, this would be a real Web3 provider
      if (data.startsWith('0xdd62ed3e')) { // allowance call
        return '0x0000000000000000000000000000000000000000000000000000000000000000'; // 0 allowance
      }
      if (data.startsWith('0x313ce567')) { // decimals call
        return '0x0000000000000000000000000000000000000000000000000000000000000006'; // 6 decimals
      }
      return '0x0000000000000000000000000000000000000000000000000000000000000000';
    }
  }), []);

  // Allowance hook
  const { allowanceHuman, loading: allowanceLoading, reload: reloadAllowance } = useAllowance({
    provider: mockProvider,
    tokenAddress: ASSET_ADDRESSES[selectedAsset],
    owner: walletAddress || undefined,
    spender: AAVE_POOL_ADDRESS,
    decimals: selected.decimals,
    pollMs: 8000,
  });

  // Fiat price hook
  const { price, loading: priceLoading, toFiat: toFiatLocal } = useFiatPrice({
    symbol: selectedAsset,
    backendBaseUrl,
    pollMs: 30_000,
  });

  // Pre-flight risk (rough): warn if projected HF might go < 1.2 after borrow.
  const projectedHF = useMemo(() => {
    if (!hf || !borrowAmount) return null;
    const amt = Number(borrowAmount);
    if (!Number.isFinite(amt) || amt <= 0) return hf;
    // Simple heuristic: as debt increases, HF trends down. We'll show a caution band if close to 1.2.
    const decay = Math.min(0.8, amt / 1000); // tunable heuristic
    return Math.max(0.5, hf - decay);
  }, [hf, borrowAmount]);

  const hfPill = (() => {
    const val = projectedHF ?? hf;
    if (val == null) return { label: '--', color: theme.subtext, bg: isDark ? '#20252b' : '#eef2f7' };
    if (val >= 2.0) return { label: `${(val || 0).toFixed(2)}x Safe`, color: '#0f5132', bg: '#d1e7dd' };
    if (val >= 1.2) return { label: `${(val || 0).toFixed(2)}x Caution`, color: '#664d03', bg: '#fff3cd' };
    return { label: `${(val || 0).toFixed(2)}x Risk`, color: '#842029', bg: '#f8d7da' };
  })();

  const setAmountGuarded = (setter: (s: string) => void, doFiat?: boolean, sym?: Asset['symbol']) => async (txt: string) => {
    if (txt === '' || numberish(txt)) {
      setter(txt);
      if (doFiat && toFiat && txt && sym) {
        try { const usd = await toFiat(sym, txt); setFiat(usd); } catch { /* ignore */ }
      }
    }
  };

  const openExplorer = useCallback((hash?: string) => {
    if (!hash || !explorerTxUrl) return;
    Linking.openURL(explorerTxUrl(hash)).catch(() => {
      Toast.show({ type: 'info', text1: 'Copy the hash from the toast to view on explorer.' });
    });
  }, [explorerTxUrl]);

  const refreshWalletMeta = useCallback(async () => {
    try {
      if (getBalance) { setBalance(await getBalance(selectedAsset)); }
      if (getAllowance) { setAllowance(await getAllowance(selectedAsset)); }
    } catch { /* ignore */ }
  }, [getBalance, getAllowance, selectedAsset]);

  // Actions
  const doApproveIfNeeded = useCallback(async (amount: string) => {
    if (!onApprove) return { hash: undefined };
    setLoadingStep('approve');
    const res = await onApprove({ symbol: selectedAsset, amount });
    if (res?.hash) {
      Toast.show({ type: 'success', text1: 'Approval submitted', text2: 'Tap to view on explorer', onPress: () => openExplorer(res.hash) });
      reloadAllowance(); // Refresh allowance after approval
    }
    return res;
  }, [onApprove, selectedAsset, openExplorer]);

  const doSupply = useCallback(async () => {
    if (loadingStep) return;
    const check = parsePositive(supplyAmount);
    if (!check.ok) {
      Toast.show({ type: 'error', text1: 'Invalid amount', text2: check.err });
      return;
    }
    try {
      // If allowance is known and lower than amount, show approve step
      if (allowanceHuman && Number(allowanceHuman) < Number(supplyAmount) && onApprove) {
        await doApproveIfNeeded(supplyAmount);
      }
      setLoadingStep('supply');
      Toast.show({ type: 'info', text1: `Supplying ${supplyAmount} ${selectedAsset}...` });
      const res = onSupply
        ? await onSupply({ symbol: selectedAsset, amount: supplyAmount })
        : await new Promise<{ hash?: string }>((r) => setTimeout(() => r({ hash: '0xSIM_SUPPLY' }), 900));
      Toast.show({ type: 'success', text1: 'Supply submitted', text2: res?.hash ? 'Tap to view on explorer' : undefined, onPress: () => openExplorer(res?.hash) });
      onSuccess?.();
      refreshWalletMeta();
      reloadAllowance();
    } catch (e: any) {
      Toast.show({ type: 'error', text1: 'Supply failed', text2: e?.message ?? 'Try again.' });
    } finally {
      setLoadingStep(null);
    }
  }, [loadingStep, supplyAmount, selectedAsset, onSupply, onSuccess, allowance, onApprove, doApproveIfNeeded, openExplorer, refreshWalletMeta]);

  const doBorrow = useCallback(async () => {
    if (loadingStep) return;
    const check = parsePositive(borrowAmount);
    if (!check.ok) {
      Toast.show({ type: 'error', text1: 'Invalid amount', text2: check.err });
      return;
    }
    // Pre-flight warning if risky
    if (projectedHF != null && projectedHF < 1.2) {
      Toast.show({ type: 'error', text1: 'Borrow too risky', text2: 'Projected health factor < 1.2' });
      return;
    }
    try {
      setLoadingStep('borrow');
      Toast.show({ type: 'info', text1: `Borrowing ${borrowAmount} ${selectedAsset}...` });
      const res = onBorrow
        ? await onBorrow({ symbol: selectedAsset, amount: borrowAmount, rateMode: 2 })
        : await new Promise<{ hash?: string }>((r) => setTimeout(() => r({ hash: '0xSIM_BORROW' }), 900));
      Toast.show({ type: 'success', text1: 'Borrow submitted', text2: res?.hash ? 'Tap to view on explorer' : undefined, onPress: () => openExplorer(res?.hash) });
      onSuccess?.();
      reload?.();
    } catch (e: any) {
      Toast.show({ type: 'error', text1: 'Borrow failed', text2: e?.message ?? 'Try again.' });
    } finally {
      setLoadingStep(null);
    }
  }, [loadingStep, borrowAmount, selectedAsset, onBorrow, onSuccess, openExplorer, projectedHF, reload]);

  const supplyDisabled = loadingStep !== null || !parsePositive(supplyAmount).ok;
  const borrowDisabled = loadingStep !== null || !parsePositive(borrowAmount).ok;

  // Quick chips
  const setPct = (pct: number, which: 'supply'|'borrow') => {
    const src = which === 'supply' ? balance : balance; // for demo; adapt if you track availableBorrow
    const base = src ? Number(src) : 100;
    const val = ((base || 0) * (pct || 0)).toFixed( selected.decimals === 6 ? 2 : 4 );
    which === 'supply' ? setSupplyAmount(val) : setBorrowAmount(val);
  };

  return (
    <ScrollView
      style={{ flex: 1, backgroundColor: theme.bg }}
      contentContainerStyle={{ paddingBottom: 24 }}
      keyboardShouldPersistTaps="handled"
    >
      {/* Header */}
      <View style={[styles.hero, { backgroundColor: isDark ? '#0E1218' : theme.primary }]}>
        <View style={styles.heroTopRow}>
          <Text style={styles.brand}>{brand}</Text>
          <View style={styles.networkBadge}>
            <Icon name="globe" size={12} color="#fff" />
            <Text style={styles.networkTxt}>{networkName}</Text>
          </View>
        </View>
        <Text style={styles.heroTitle}>AAVE DeFi Lending</Text>
        <Text style={styles.heroSubtitle}>Connect - Validate - Execute</Text>

        <View style={styles.walletRow}>
          <Icon name="credit-card" size={14} color="#fff" />
          <Text style={styles.walletTxt}>{short(walletAddress)}</Text>
          <View style={styles.dot} />
          <Pressable onPress={reload} style={styles.refreshInline}>
            <Icon name="refresh-ccw" size={12} color="#fff" />
            <Text style={styles.refreshInlineTxt}>Refresh</Text>
          </Pressable>
        </View>
      </View>

      {/* Asset / Summary Card */}
      <View style={[styles.card, { backgroundColor: theme.card, shadowColor: theme.shadow }]}>
        <View style={styles.rowBetween}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>Asset</Text>
          <TouchableOpacity onPress={() => { setAssetModal(true); refreshWalletMeta(); }} style={[styles.assetBtn, { borderColor: theme.border }]}>
            <View style={[styles.assetDot, { backgroundColor: selected.color }]} />
            <Text style={[styles.assetBtnTxt, { color: theme.text }]}>{selected.symbol}</Text>
            <Icon name="chevron-down" size={16} color={theme.subtext} />
          </TouchableOpacity>
        </View>

        <View style={styles.summaryRow}>
          <Text style={[styles.helper, { color: theme.subtext }]}>Balance</Text>
          <Text style={[styles.helperStrong, { color: theme.text }]}>{balance ?? '--'}</Text>
        </View>
        <View style={styles.summaryRow}>
          <Text style={[styles.helper, { color: theme.subtext }]}>Allowance</Text>
          <Text style={[styles.helperStrong, { color: theme.text }]}>
            {allowanceLoading ? '...' : (allowanceHuman ?? '--')}
          </Text>
        </View>
      </View>

      {/* Supply */}
      <View style={[styles.card, { backgroundColor: theme.card, shadowColor: theme.shadow }]}>
        <Text style={[styles.sectionTitle, { color: theme.text }]}>Supply</Text>
        <View style={[styles.inputRow, { borderColor: theme.border, backgroundColor: theme.tile }]}>
          <Icon name="plus-circle" size={18} color={theme.subtext} style={{ marginHorizontal: 8 }} />
          <TextInput
            style={[styles.input, { color: theme.text }]}
            value={supplyAmount}
            onChangeText={setAmountGuarded(setSupplyAmount, true, selectedAsset)}
            placeholder="0.00"
            placeholderTextColor={theme.subtext}
            keyboardType="decimal-pad"
            returnKeyType="done"
          />
          <Text style={[styles.suffix, { color: theme.subtext }]}>{selected.symbol}</Text>
        </View>

        {/* Quick chips */}
        <View style={styles.chipsRow}>
          {[0.25, 0.5, 0.75, 1].map((p) => (
            <TouchableOpacity key={p} onPress={() => setPct(p, 'supply')} style={[styles.chip, { borderColor: theme.border }]}>
              <Text style={[styles.chipTxt, { color: theme.text }]}>{p === 1 ? 'MAX' : `${p*100}%`}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {!!toFiatLocal && toFiatLocal(supplyAmount) && (
          <Text style={[styles.fiatHint, { color: theme.subtext }]}>
            ~ ${(toFiatLocal(supplyAmount) || 0).toFixed(2)} USD
          </Text>
        )}

        <TouchableOpacity
          style={[styles.cta, { backgroundColor: supplyDisabled ? '#98c7ff' : theme.primary }]}
          onPress={doSupply}
          disabled={supplyDisabled}
          accessibilityState={{ disabled: supplyDisabled, busy: loadingStep === 'supply' || loadingStep === 'approve' }}
        >
          {loadingStep === 'approve' ? (
            <>
              <ActivityIndicator color="#fff" />
              <Text style={styles.ctaText}>Approving...</Text>
            </>
          ) : loadingStep === 'supply' ? (
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
      <View style={[styles.card, { backgroundColor: theme.card, shadowColor: theme.shadow }]}>
        <Text style={[styles.sectionTitle, { color: theme.text }]}>Borrow</Text>
        <View style={[styles.inputRow, { borderColor: theme.border, backgroundColor: theme.tile }]}>
          <Icon name="minus-circle" size={18} color={theme.subtext} style={{ marginHorizontal: 8 }} />
          <TextInput
            style={[styles.input, { color: theme.text }]}
            value={borrowAmount}
            onChangeText={setAmountGuarded(setBorrowAmount, true, selectedAsset)}
            placeholder="0.00"
            placeholderTextColor={theme.subtext}
            keyboardType="decimal-pad"
            returnKeyType="done"
          />
          <Text style={[styles.suffix, { color: theme.subtext }]}>{selected.symbol}</Text>
        </View>

        <View style={styles.chipsRow}>
          {[0.25, 0.5, 0.75].map((p) => (
            <TouchableOpacity key={p} onPress={() => setPct(p, 'borrow')} style={[styles.chip, { borderColor: theme.border }]}>
              <Text style={[styles.chipTxt, { color: theme.text }]}>{`${p*100}%`}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {!!toFiatLocal && toFiatLocal(borrowAmount) && (
          <Text style={[styles.fiatHint, { color: theme.subtext }]}>
            ~ ${(toFiatLocal(borrowAmount) || 0).toFixed(2)} USD
          </Text>
        )}

        {/* Pre-flight risk banner */}
        {projectedHF != null && projectedHF < 1.2 && (
          <View style={[styles.banner, { backgroundColor: '#fff3cd', borderColor: '#ffe69c' }]}>
            <Icon name="alert-triangle" size={14} color="#664d03" />
            <Text style={[styles.bannerTxt, { color: '#664d03' }]}>
              Projected HF {'<'} 1.2 - borrowing is risky
            </Text>
          </View>
        )}

        <TouchableOpacity
          style={[styles.cta, { backgroundColor: borrowDisabled ? '#98c7ff' : theme.primary }]}
          onPress={doBorrow}
          disabled={borrowDisabled}
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
      <View style={[styles.card, { backgroundColor: theme.card, shadowColor: theme.shadow }]}>
        <View style={styles.rowBetween}>
          <Text style={[styles.sectionTitle, { color: theme.text }]}>Risk & Rates</Text>
          {!!backendBaseUrl && !!walletAddress && (
            <TouchableOpacity onPress={reload} style={[styles.refreshBtn, { backgroundColor: theme.primarySoft }]}>
              <Icon name="refresh-ccw" size={14} color={theme.tint} />
              <Text style={[styles.refreshTxt, { color: theme.tint }]}>Refresh</Text>
            </TouchableOpacity>
          )}
        </View>

        {riskError ? (
          <View style={styles.infoRow}>
            <Icon name="alert-triangle" size={16} color={theme.danger} />
            <Text style={[styles.infoTextSmall, { color: theme.danger }]}>Failed to load: {riskError}</Text>
          </View>
        ) : null}

        <View style={styles.metricGrid}>
          <View style={[styles.metricTile, { backgroundColor: theme.tile }]}>
            <View style={styles.metricHeader}>
              <Icon name="activity" size={14} color={theme.subtext} />
              <Text style={[styles.metricLabel, { color: theme.subtext }]}>Health Factor</Text>
            </View>
            <View style={[styles.hfPill, { backgroundColor: hfPill.bg }]}>
              <Text style={[styles.hfPillText, { color: hfPill.color }]}>{hfPill.label}</Text>
            </View>
          </View>

          <View style={[styles.metricTile, { backgroundColor: theme.tile }]}>
            <View style={styles.metricHeader}>
              <Icon name="shield" size={14} color={theme.subtext} />
              <Text style={[styles.metricLabel, { color: theme.subtext }]}>Liquidation Threshold</Text>
            </View>
            <Text style={[styles.metricValue, { color: theme.text }]}>{liqPct != null ? `${liqPct}%` : '--'}</Text>
          </View>

          <View style={[styles.metricTile, { backgroundColor: theme.tile }]}>
            <View style={styles.metricHeader}>
              <Icon name="trending-up" size={14} color={theme.subtext} />
              <Text style={[styles.metricLabel, { color: theme.subtext }]}>Max LTV</Text>
            </View>
            <Text style={[styles.metricValue, { color: theme.text }]}>{ltvPct != null ? `${ltvPct}%` : '--'}</Text>
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

      {/* Asset Modal */}
      <Modal visible={assetModal} transparent animationType="fade" onRequestClose={() => setAssetModal(false)}>
        <Pressable style={styles.modalBackdrop} onPress={() => setAssetModal(false)}>
          <View />
        </Pressable>
        <View style={[styles.modalCard, { backgroundColor: theme.card }]}>
          <Text style={[styles.modalTitle, { color: theme.text }]}>Select Asset</Text>
          {ASSETS.map(a => (
            <TouchableOpacity
              key={a.symbol}
              style={[styles.modalRow, { borderColor: theme.border }]}
              onPress={() => { setSelectedAsset(a.symbol); setAssetModal(false); refreshWalletMeta(); }}
            >
              <View style={[styles.assetDot, { backgroundColor: a.color }]} />
              <View style={{ flex: 1 }}>
                <Text style={[styles.modalAssetSymbol, { color: theme.text }]}>{a.symbol}</Text>
                <Text style={[styles.modalAssetName, { color: theme.subtext }]}>{a.name}</Text>
              </View>
              {selectedAsset === a.symbol && <Icon name="check" size={18} color={theme.tint} />}
            </TouchableOpacity>
          ))}
        </View>
      </Modal>

      {/* Educational Info Section */}
      <View style={[styles.card, { backgroundColor: '#e7f1ff', shadowColor: theme.shadow, borderWidth: 1, borderColor: '#b3d9ff' }]}>
        <Text style={[styles.sectionTitle, { color: '#0a84ff' }]}>What is AAVE DeFi Lending?</Text>
        <Text style={[styles.infoText, { color: '#1e40af' }]}>
          AAVE is a decentralized lending protocol that allows you to earn interest on your crypto assets by supplying them as collateral, or borrow against your holdings. Your funds are secured by smart contracts and you maintain full control.
        </Text>
        
        <View style={styles.featureGrid}>
          <View style={[styles.featureCard, { backgroundColor: '#f0f7ff' }]}>
            <Icon name="upload" size={24} color="#0a84ff" />
            <View style={{ flex: 1 }}>
              <Text style={[styles.featureTitle, { color: '#0a84ff' }]}>Supply Assets</Text>
              <Text style={[styles.featureDesc, { color: '#1e40af' }]}>
                Deposit crypto assets to earn interest. Your funds remain in your control and can be withdrawn anytime.
              </Text>
            </View>
          </View>

          <View style={[styles.featureCard, { backgroundColor: '#f0f7ff' }]}>
            <Icon name="download" size={24} color="#0a84ff" />
            <View style={{ flex: 1 }}>
              <Text style={[styles.featureTitle, { color: '#0a84ff' }]}>Borrow Against Collateral</Text>
              <Text style={[styles.featureDesc, { color: '#1e40af' }]}>
                Use your supplied assets as collateral to borrow other tokens. Maintain a healthy collateral ratio.
              </Text>
            </View>
          </View>

          <View style={[styles.featureCard, { backgroundColor: '#f0f7ff' }]}>
            <Icon name="shield" size={24} color="#0a84ff" />
            <View style={{ flex: 1 }}>
              <Text style={[styles.featureTitle, { color: '#0a84ff' }]}>Health Factor</Text>
              <Text style={[styles.featureDesc, { color: '#1e40af' }]}>
                Your Health Factor shows how safe your position is. Keep it above 1.0 to avoid liquidation.
              </Text>
            </View>
          </View>

          <View style={[styles.featureCard, { backgroundColor: '#f0f7ff' }]}>
            <Icon name="zap" size={24} color="#0a84ff" />
            <View style={{ flex: 1 }}>
              <Text style={[styles.featureTitle, { color: '#0a84ff' }]}>Instant Liquidity</Text>
              <Text style={[styles.featureDesc, { color: '#1e40af' }]}>
                Access liquidity without selling your assets. Perfect for short-term needs or trading opportunities.
              </Text>
            </View>
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

      <View style={{ height: 40 }} />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  // Header
  hero: {
    paddingHorizontal: 20, paddingTop: 18, paddingBottom: 22,
    borderBottomLeftRadius: 16, borderBottomRightRadius: 16,
  },
  heroTopRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  brand: { color: '#fff', fontSize: 12, fontWeight: '700', letterSpacing: 1 },
  networkBadge: { flexDirection: 'row', gap: 6, alignItems: 'center', backgroundColor: 'rgba(255,255,255,0.18)', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 999 },
  networkTxt: { color: '#fff', fontSize: 12, fontWeight: '700' },
  heroTitle: { color: '#fff', fontSize: 22, fontWeight: '800', marginTop: 8 },
  heroSubtitle: { color: 'rgba(255,255,255,0.85)', fontSize: 13, marginTop: 4 },
  walletRow: { marginTop: 10, flexDirection: 'row', alignItems: 'center', gap: 8 },
  walletTxt: { color: '#fff', fontSize: 12, fontWeight: '700' },
  dot: { width: 4, height: 4, borderRadius: 2, backgroundColor: 'rgba(255,255,255,0.55)' },
  refreshInline: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 999, backgroundColor: 'rgba(255,255,255,0.18)' },
  refreshInlineTxt: { color: '#fff', fontSize: 12, fontWeight: '700' },

  // Cards
  card: {
    marginHorizontal: 12, marginTop: 12, padding: 16, borderRadius: 14,
    shadowOpacity: 0.08, shadowRadius: 12, shadowOffset: { width: 0, height: 6 }, elevation: 3,
  },
  sectionTitle: { fontSize: 15, fontWeight: '800' },
  rowBetween: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },

  // Asset selector
  assetBtn: { flexDirection: 'row', alignItems: 'center', gap: 8, borderWidth: 1, paddingHorizontal: 12, paddingVertical: 8, borderRadius: 12 },
  assetBtnTxt: { fontSize: 13, fontWeight: '800' },
  assetDot: { width: 10, height: 10, borderRadius: 5 },

  summaryRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 8 },
  helper: { fontSize: 12 },
  helperStrong: { fontSize: 12, fontWeight: '800' },

  // Inputs
  inputRow: { flexDirection: 'row', alignItems: 'center', borderWidth: 1, borderRadius: 12, marginTop: 10 },
  input: { flex: 1, paddingVertical: 12, fontSize: 18 },
  suffix: { paddingHorizontal: 12, fontWeight: '800' },

  chipsRow: { flexDirection: 'row', gap: 8, marginTop: 10 },
  chip: { borderWidth: 1, paddingHorizontal: 10, paddingVertical: 6, borderRadius: 999 },
  chipTxt: { fontSize: 12, fontWeight: '800' },
  fiatHint: { marginTop: 8, fontSize: 12 },

  // CTA
  cta: { marginTop: 12, paddingVertical: 14, borderRadius: 12, flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8 },
  ctaText: { color: '#fff', fontSize: 15, fontWeight: '900' },

  // Risk
  refreshBtn: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingHorizontal: 10, paddingVertical: 6, borderRadius: 12 },
  refreshTxt: { fontSize: 12, fontWeight: '800' },
  infoRow: { flexDirection: 'row', alignItems: 'center', marginTop: 8, gap: 8 },
  infoTextSmall: { fontSize: 13 },

  metricGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginTop: 10 },
  metricTile: { flexBasis: '48%', borderRadius: 12, padding: 12 },
  metricHeader: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 6 },
  metricLabel: { fontSize: 12, fontWeight: '700' },
  metricValue: { fontSize: 18, fontWeight: '900' },

  hfPill: { paddingVertical: 6, paddingHorizontal: 10, borderRadius: 999, alignSelf: 'flex-start' },
  hfPillText: { fontSize: 12, fontWeight: '900' },

  // Banner
  banner: { flexDirection: 'row', alignItems: 'center', gap: 8, padding: 10, borderRadius: 10, borderWidth: 1, marginTop: 10 },
  bannerTxt: { fontSize: 12, fontWeight: '800' },

  // Skeletons
  skeletonRow: { flexDirection: 'row', gap: 10, marginTop: 10 },
  skeleton: { height: 16, borderRadius: 6, flex: 1, opacity: 0.7 },

  // Modal
  modalBackdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.35)' },
  modalCard: { position: 'absolute', left: 12, right: 12, top: 120, borderRadius: 14, padding: 12, elevation: 6 },
  modalTitle: { fontSize: 14, fontWeight: '900', marginBottom: 6 },
  modalRow: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 10, borderBottomWidth: StyleSheet.hairlineWidth },
  modalAssetSymbol: { fontSize: 14, fontWeight: '900' },
  modalAssetName: { fontSize: 12 },

  // Educational content styles
  infoText: { fontSize: 14, lineHeight: 20, marginBottom: 16 },
  featureGrid: { flexDirection: 'column', gap: 12, marginTop: 16 },
  featureCard: { flexDirection: 'row', padding: 16, borderRadius: 12, alignItems: 'center', minHeight: 80 },
  featureTitle: { fontSize: 14, fontWeight: '800', marginBottom: 4, textAlign: 'left' },
  featureDesc: { fontSize: 12, lineHeight: 16, textAlign: 'left' },
  warningBox: { flexDirection: 'row', alignItems: 'flex-start', padding: 12, borderRadius: 10, borderWidth: 1, marginTop: 16 },
  warningTitle: { fontSize: 12, fontWeight: '800', marginBottom: 4 },
  warningText: { fontSize: 11, lineHeight: 14 },
});

export default ProAaveCard;
