import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  SafeAreaView,
  Dimensions,
  ActivityIndicator,
  Switch,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useLazyQuery } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

const { width } = Dimensions.get('window');

/* ----------------------------- GraphQL ----------------------------- */

const CALCULATE_POSITION_SIZE = gql`
  query CalculatePositionSize(
    $accountEquity: Float!
    $entryPrice: Float!
    $stopPrice: Float!
    $riskPerTrade: Float
    $maxPositionPct: Float
    $confidence: Float
  ) {
    calculatePositionSize(
      accountEquity: $accountEquity
      entryPrice: $entryPrice
      stopPrice: $stopPrice
      riskPerTrade: $riskPerTrade
      maxPositionPct: $maxPositionPct
      confidence: $confidence
    ) {
      positionSize
      dollarRisk
      positionValue
      positionPct
      riskPerTradePct
      method
      riskPerShare
      maxSharesFixedRisk
      maxSharesPosition
    }
  }
`;

const CALCULATE_DYNAMIC_STOP = gql`
  query CalculateDynamicStop(
    $entryPrice: Float!
    $atr: Float!
    $atrMultiplier: Float
    $supportLevel: Float
    $resistanceLevel: Float
    $signalType: String
  ) {
    calculateDynamicStop(
      entryPrice: $entryPrice
      atr: $atr
      atrMultiplier: $atrMultiplier
      supportLevel: $supportLevel
      resistanceLevel: $resistanceLevel
      signalType: $signalType
    ) {
      stopPrice
      stopDistance
      riskPercentage
      method
      atrStop
      srStop
      pctStop
    }
  }
`;

const CALCULATE_TARGET_PRICE = gql`
  query CalculateTargetPrice(
    $entryPrice: Float!
    $stopPrice: Float!
    $riskRewardRatio: Float
    $atr: Float
    $resistanceLevel: Float
    $supportLevel: Float
    $signalType: String
  ) {
    calculateTargetPrice(
      entryPrice: $entryPrice
      stopPrice: $stopPrice
      riskRewardRatio: $riskRewardRatio
      atr: $atr
      resistanceLevel: $resistanceLevel
      supportLevel: $supportLevel
      signalType: $signalType
    ) {
      targetPrice
      rewardDistance
      riskRewardRatio
      method
      rrTarget
      atrTarget
      srTarget
    }
  }
`;

/* ----------------------------- Helpers ----------------------------- */

const C = {
  bg: '#F9FAFB',
  card: '#FFFFFF',
  line: '#E5E7EB',
  text: '#111827',
  sub: '#6B7280',
  primary: '#3B82F6',
  green: '#10B981',
  red: '#EF4444',
  amber: '#F59E0B',
};

const safeFloat = (v: string) => {
  if (v === undefined || v === null) return NaN;
  // Allow "." while typing
  if (v.trim() === '' || v === '.') return NaN;
  const n = Number(v);
  return Number.isFinite(n) ? n : NaN;
};

const fmtMoney = (v?: number | null) =>
  typeof v === 'number' && isFinite(v)
    ? `$${v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    : '$0.00';

const fmtPct = (v?: number | null) => {
  if (typeof v !== 'number' || !isFinite(v)) return '—';
  const fraction = v > 1.5 ? v / 100 : v; // auto-detect percent vs fraction
  return `${(fraction * 100).toFixed(2)}%`;
};

const pctToFraction = (v: number) => (v > 1.5 ? v / 100 : v);

/* ----------------------------- Component ----------------------------- */

type TabKey = 'position' | 'stop' | 'target';

interface RiskCoachScreenProps {
  navigateTo?: (screen: string) => void;
}

const RiskCoachScreen: React.FC<RiskCoachScreenProps> = ({ navigateTo }) => {
  const [activeTab, setActiveTab] = useState<TabKey>('position');
  const [showAdvanced, setShowAdvanced] = useState(false);

  /* ------------------------- Inputs + Validation ------------------------- */

  const [autoCalc, setAutoCalc] = useState({
    position: true,
    stop: true,
    target: true,
  });

  // Position sizing inputs
  const [positionInputs, setPositionInputs] = useState({
    accountEquity: '10000',
    entryPrice: '100',
    stopPrice: '95',
    riskPerTrade: '0.01', // fraction (e.g., 0.01 = 1%)
    maxPositionPct: '0.1', // fraction (e.g., 0.1 = 10%)
    confidence: '0.8', // 0-1
    side: 'long' as 'long' | 'short',
  });

  // Stop loss inputs
  const [stopInputs, setStopInputs] = useState({
    entryPrice: '100',
    atr: '2.0',
    atrMultiplier: '1.5',
    supportLevel: '90',
    resistanceLevel: '110',
    signalType: 'long' as 'long' | 'short',
  });

  // Target price inputs
  const [targetInputs, setTargetInputs] = useState({
    entryPrice: '100',
    stopPrice: '95',
    riskRewardRatio: '2.0',
    atr: '2.0',
    resistanceLevel: '110',
    supportLevel: '90',
    signalType: 'long' as 'long' | 'short',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const updatePosition = useCallback((k: string, v: string) => {
    setPositionInputs((p) => ({ ...p, [k]: v }));
    setErrors((e) => ({ ...e, [`position.${k}`]: '' }));
  }, []);
  const updateStop = useCallback((k: string, v: string) => {
    setStopInputs((p) => ({ ...p, [k]: v }));
    setErrors((e) => ({ ...e, [`stop.${k}`]: '' }));
  }, []);
  const updateTarget = useCallback((k: string, v: string) => {
    setTargetInputs((p) => ({ ...p, [k]: v }));
    setErrors((e) => ({ ...e, [`target.${k}`]: '' }));
  }, []);

  const validatePosition = useCallback(() => {
    const e: Record<string, string> = {};
    const eq = safeFloat(positionInputs.accountEquity);
    const entry = safeFloat(positionInputs.entryPrice);
    const stop = safeFloat(positionInputs.stopPrice);
    const risk = safeFloat(positionInputs.riskPerTrade);
    const maxPos = safeFloat(positionInputs.maxPositionPct);
    const conf = safeFloat(positionInputs.confidence);

    if (!isFinite(eq) || eq <= 0) e['position.accountEquity'] = 'Enter equity > 0';
    if (!isFinite(entry) || entry <= 0) e['position.entryPrice'] = 'Enter valid entry';
    if (!isFinite(stop) || stop <= 0) e['position.stopPrice'] = 'Enter valid stop';
    if (!isFinite(risk) || risk <= 0 || risk > 1) e['position.riskPerTrade'] = 'Use a fraction (e.g., 0.01)';
    if (!isFinite(maxPos) || maxPos <= 0 || maxPos > 1) e['position.maxPositionPct'] = 'Use a fraction (e.g., 0.1)';
    if (!isFinite(conf) || conf <= 0 || conf > 1) e['position.confidence'] = '0–1';

    // Long/short directional check (align with stop)
    if (positionInputs.side === 'long' && isFinite(entry) && isFinite(stop) && !(stop < entry)) {
      e['position.stopPrice'] = 'For LONG, stop should be below entry';
    }
    if (positionInputs.side === 'short' && isFinite(entry) && isFinite(stop) && !(stop > entry)) {
      e['position.stopPrice'] = 'For SHORT, stop should be above entry';
    }
    setErrors((prev) => ({ ...prev, ...e }));
    return Object.keys(e).length === 0;
  }, [positionInputs]);

  const validateStop = useCallback(() => {
    const e: Record<string, string> = {};
    const entry = safeFloat(stopInputs.entryPrice);
    const atr = safeFloat(stopInputs.atr);
    const mult = safeFloat(stopInputs.atrMultiplier);

    if (!isFinite(entry) || entry <= 0) e['stop.entryPrice'] = 'Enter valid entry';
    if (!isFinite(atr) || atr <= 0) e['stop.atr'] = 'Enter ATR > 0';
    if (!isFinite(mult) || mult <= 0) e['stop.atrMultiplier'] = 'Enter multiplier > 0';

    setErrors((prev) => ({ ...prev, ...e }));
    return Object.keys(e).length === 0;
  }, [stopInputs]);

  const validateTarget = useCallback(() => {
    const e: Record<string, string> = {};
    const entry = safeFloat(targetInputs.entryPrice);
    const stop = safeFloat(targetInputs.stopPrice);
    const rr = safeFloat(targetInputs.riskRewardRatio);

    if (!isFinite(entry) || entry <= 0) e['target.entryPrice'] = 'Enter valid entry';
    if (!isFinite(stop) || stop <= 0) e['target.stopPrice'] = 'Enter valid stop';
    if (!isFinite(rr) || rr <= 0) e['target.riskRewardRatio'] = 'Ratio > 0';

    if (targetInputs.signalType === 'long' && isFinite(stop) && !(stop < entry)) {
      e['target.stopPrice'] = 'For LONG, stop should be below entry';
    }
    if (targetInputs.signalType === 'short' && isFinite(stop) && !(stop > entry)) {
      e['target.stopPrice'] = 'For SHORT, stop should be above entry';
    }

    setErrors((prev) => ({ ...prev, ...e }));
    return Object.keys(e).length === 0;
  }, [targetInputs]);

  /* --------------------------- Queries (lazy) --------------------------- */

  const [fetchPositionSize, {
    data: positionData, loading: positionLoading, error: positionError,
  }] = useLazyQuery(CALCULATE_POSITION_SIZE, { fetchPolicy: 'network-only', errorPolicy: 'all' });

  const [fetchStop, {
    data: stopData, loading: stopLoading, error: stopError,
  }] = useLazyQuery(CALCULATE_DYNAMIC_STOP, { fetchPolicy: 'network-only', errorPolicy: 'all' });

  const [fetchTarget, {
    data: targetData, loading: targetLoading, error: targetError,
  }] = useLazyQuery(CALCULATE_TARGET_PRICE, { fetchPolicy: 'network-only', errorPolicy: 'all' });

  /* --------------------------- Debounced auto calc --------------------------- */

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const debounce = useCallback((fn: () => void) => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(fn, 400);
  }, []);

  // Auto-calc handlers per tab
  useEffect(() => {
    if (!autoCalc.position) return;
    debounce(() => {
      if (!validatePosition()) return;
      fetchPositionSize({
        variables: {
          accountEquity: safeFloat(positionInputs.accountEquity),
          entryPrice: safeFloat(positionInputs.entryPrice),
          stopPrice: safeFloat(positionInputs.stopPrice),
          riskPerTrade: safeFloat(positionInputs.riskPerTrade),
          maxPositionPct: safeFloat(positionInputs.maxPositionPct),
          confidence: safeFloat(positionInputs.confidence),
        },
      });
    });
  }, [positionInputs, autoCalc.position, debounce, fetchPositionSize, validatePosition]);

  useEffect(() => {
    if (!autoCalc.stop) return;
    debounce(() => {
      if (!validateStop()) return;
      fetchStop({
        variables: {
          entryPrice: safeFloat(stopInputs.entryPrice),
          atr: safeFloat(stopInputs.atr),
          atrMultiplier: safeFloat(stopInputs.atrMultiplier),
          supportLevel: stopInputs.supportLevel ? safeFloat(stopInputs.supportLevel) : undefined,
          resistanceLevel: stopInputs.resistanceLevel ? safeFloat(stopInputs.resistanceLevel) : undefined,
          signalType: stopInputs.signalType,
        },
      });
    });
  }, [stopInputs, autoCalc.stop, debounce, fetchStop, validateStop]);

  useEffect(() => {
    if (!autoCalc.target) return;
    debounce(() => {
      if (!validateTarget()) return;
      fetchTarget({
        variables: {
          entryPrice: safeFloat(targetInputs.entryPrice),
          stopPrice: safeFloat(targetInputs.stopPrice),
          riskRewardRatio: safeFloat(targetInputs.riskRewardRatio),
          atr: targetInputs.atr ? safeFloat(targetInputs.atr) : undefined,
          resistanceLevel: targetInputs.resistanceLevel ? safeFloat(targetInputs.resistanceLevel) : undefined,
          supportLevel: targetInputs.supportLevel ? safeFloat(targetInputs.supportLevel) : undefined,
          signalType: targetInputs.signalType,
        },
      });
    });
  }, [targetInputs, autoCalc.target, debounce, fetchTarget, validateTarget]);

  /* ----------------------------- Renderers ----------------------------- */

  const Header = () => (
    <View style={styles.header}>
      <TouchableOpacity
        style={styles.backButton}
        onPress={() => navigateTo?.('swing-trading-test')}
      >
        <Icon name="arrow-left" size={24} color="#6B7280" />
      </TouchableOpacity>
      <Text style={styles.headerTitle}>Guardrails</Text>
      <TouchableOpacity
        style={styles.advancedToggle}
        onPress={() => setShowAdvanced((s) => !s)}
        testID="toggle-advanced"
      >
        <Text style={styles.advancedToggleText}>{showAdvanced ? 'Hide' : 'Show'} Advanced</Text>
      </TouchableOpacity>
    </View>
  );

  const AutoCalcToggle = ({ tab }: { tab: TabKey }) => (
    <View style={styles.autoRow}>
      <Text style={styles.autoLabel}>Auto-calc</Text>
      <Switch
        value={autoCalc[tab]}
        onValueChange={(v) => setAutoCalc((s) => ({ ...s, [tab]: v }))}
        thumbColor={autoCalc[tab] ? C.primary : '#fff'}
        trackColor={{ true: '#DBEAFE', false: '#E5E7EB' }}
        testID={`autocalc-${tab}`}
      />
    </View>
  );

  const ErrorBanner = ({ text }: { text?: string }) =>
    text ? (
      <View style={styles.errorBanner}>
        <Icon name="alert-triangle" size={16} color="#fff" />
        <Text style={styles.errorBannerText}>{text}</Text>
      </View>
    ) : null;

  const InputRow = React.memo(function InputRow({
    label, value, onChange, placeholder, error, keyboardType = 'decimal-pad', testID,
  }: {
    label: string;
    value: string;
    onChange: (v: string) => void;
    placeholder?: string;
    error?: string;
    keyboardType?: 'decimal-pad' | 'numeric' | 'default';
    testID?: string;
  }) {
    return (
      <View style={styles.inputGroup}>
        <Text style={styles.inputLabel}>{label}</Text>
        <TextInput
          style={[styles.input, !!error && { borderColor: C.red }]}
          value={value}
          onChangeText={onChange}
          placeholder={placeholder}
          keyboardType={keyboardType}
          testID={testID}
        />
        {!!error && <Text style={styles.inputError}>{error}</Text>}
      </View>
    );
  });

  const Segmented = ({
    value, onChange, options,
  }: {
    value: string;
    onChange: (v: string) => void;
    options: { value: string; label: string }[];
  }) => (
    <View style={styles.segmentedControl}>
      {options.map((opt) => {
        const active = value === opt.value;
        return (
          <TouchableOpacity
            key={opt.value}
            style={[styles.segmentButton, active && styles.segmentButtonActive]}
            onPress={() => onChange(opt.value)}
          >
            <Text style={[styles.segmentButtonText, active && styles.segmentButtonTextActive]}>
              {opt.label}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );

  /* ------------------------- Tabs: Position / Stop / Target ------------------------- */

  const renderPosition = () => {
    const err = (k: string) => errors[`position.${k}`];

    const runNow = () => {
      if (!validatePosition()) return;
      fetchPositionSize({
        variables: {
          accountEquity: safeFloat(positionInputs.accountEquity),
          entryPrice: safeFloat(positionInputs.entryPrice),
          stopPrice: safeFloat(positionInputs.stopPrice),
          riskPerTrade: safeFloat(positionInputs.riskPerTrade),
          maxPositionPct: safeFloat(positionInputs.maxPositionPct),
          confidence: safeFloat(positionInputs.confidence),
        },
      });
    };

    return (
      <View style={styles.tabContent}>
        <AutoCalcToggle tab="position" />
        <Text style={styles.sectionTitle}>Account & Trade</Text>

        <Segmented
          value={positionInputs.side}
          onChange={(v) => updatePosition('side', v)}
          options={[{ value: 'long', label: 'LONG' }, { value: 'short', label: 'SHORT' }]}
        />

        <InputRow label="Account Equity" value={positionInputs.accountEquity}
          onChange={(v) => updatePosition('accountEquity', v)} placeholder="10000" error={err('accountEquity')}
          testID="pos-equity" />

        <TwoCol>
          <InputRow label="Entry Price" value={positionInputs.entryPrice}
            onChange={(v) => updatePosition('entryPrice', v)} placeholder="100.00" error={err('entryPrice')}
            testID="pos-entry" />
          <InputRow label="Stop Price" value={positionInputs.stopPrice}
            onChange={(v) => updatePosition('stopPrice', v)} placeholder="95.00" error={err('stopPrice')}
            testID="pos-stop" />
        </TwoCol>

        <Text style={[styles.sectionTitle, { marginTop: 8 }]}>Risk Controls</Text>
        <TwoCol>
          <InputRow label="Risk / Trade (fraction)" value={positionInputs.riskPerTrade}
            onChange={(v) => updatePosition('riskPerTrade', v)} placeholder="0.01" error={err('riskPerTrade')}
            testID="pos-risk" />
          <InputRow label="Max Position (fraction)" value={positionInputs.maxPositionPct}
            onChange={(v) => updatePosition('maxPositionPct', v)} placeholder="0.10" error={err('maxPositionPct')}
            testID="pos-maxpos" />
        </TwoCol>
        <InputRow label="Signal Confidence (0–1)" value={positionInputs.confidence}
          onChange={(v) => updatePosition('confidence', v)} placeholder="0.80" error={err('confidence')}
          testID="pos-conf" />

        <PrimaryButton onPress={runNow} label="Calculate Position Size" loading={positionLoading} testID="pos-run" />

        <ErrorBanner text={positionError?.message} />

        {positionData?.calculatePositionSize && (
          <View style={styles.resultsSection}>
            <Text style={styles.sectionTitle}>Position Sizing Results</Text>
            <Card>
              <MetricRow label="Recommended Shares" value={positionData.calculatePositionSize.positionSize?.toLocaleString() ?? '—'} />
              <MetricRow label="Position Value" value={fmtMoney(positionData.calculatePositionSize.positionValue)} />
              <MetricRow label="Dollar Risk" value={fmtMoney(positionData.calculatePositionSize.dollarRisk)} />
              <MetricRow label="Position %" value={fmtPct(positionData.calculatePositionSize.positionPct)} />
              <MetricRow label="Risk / Trade %" value={fmtPct(positionData.calculatePositionSize.riskPerTradePct)} />
              <Divider />
              <MetricRow label="Method" value={positionData.calculatePositionSize.method || '—'} />
              <MetricRow label="Risk / Share" value={fmtMoney(positionData.calculatePositionSize.riskPerShare)} />
              <MetricRow label="Max Shares (Fixed Risk)" value={positionData.calculatePositionSize.maxSharesFixedRisk?.toLocaleString() ?? '—'} />
              <MetricRow label="Max Shares (Position Cap)" value={positionData.calculatePositionSize.maxSharesPosition?.toLocaleString() ?? '—'} />
            </Card>
          </View>
        )}
      </View>
    );
  };

  const renderStop = () => {
    const err = (k: string) => errors[`stop.${k}`];

    const runNow = () => {
      if (!validateStop()) return;
      fetchStop({
        variables: {
          entryPrice: safeFloat(stopInputs.entryPrice),
          atr: safeFloat(stopInputs.atr),
          atrMultiplier: safeFloat(stopInputs.atrMultiplier),
          supportLevel: stopInputs.supportLevel ? safeFloat(stopInputs.supportLevel) : undefined,
          resistanceLevel: stopInputs.resistanceLevel ? safeFloat(stopInputs.resistanceLevel) : undefined,
          signalType: stopInputs.signalType,
        },
      });
    };

    const useAsStopInPosition = () => {
      const v = stopData?.calculateDynamicStop?.stopPrice;
      if (typeof v === 'number' && isFinite(v)) {
        updatePosition('stopPrice', String(v.toFixed(2)));
        setActiveTab('position');
        Alert.alert('Applied', 'Stop price copied to Position tab.');
      }
    };

    return (
      <View style={styles.tabContent}>
        <AutoCalcToggle tab="stop" />
        <Text style={styles.sectionTitle}>Trade Inputs</Text>

        <Segmented
          value={stopInputs.signalType}
          onChange={(v) => updateStop('signalType', v)}
          options={[{ value: 'long', label: 'LONG' }, { value: 'short', label: 'SHORT' }]}
        />

        <TwoCol>
          <InputRow label="Entry Price" value={stopInputs.entryPrice}
            onChange={(v) => updateStop('entryPrice', v)} placeholder="100.00" error={err('entryPrice')}
            testID="stop-entry" />
          <InputRow label="ATR" value={stopInputs.atr}
            onChange={(v) => updateStop('atr', v)} placeholder="2.0" error={err('atr')}
            testID="stop-atr" />
        </TwoCol>

        <InputRow label="ATR Multiplier" value={stopInputs.atrMultiplier}
          onChange={(v) => updateStop('atrMultiplier', v)} placeholder="1.5" error={err('atrMultiplier')}
          testID="stop-mult" />

        {showAdvanced && (
          <>
            <Text style={[styles.sectionTitle, { marginTop: 8 }]}>Advanced</Text>
            <TwoCol>
              <InputRow label="Support (opt)" value={stopInputs.supportLevel}
                onChange={(v) => updateStop('supportLevel', v)} placeholder="90.00"
                testID="stop-support" />
              <InputRow label="Resistance (opt)" value={stopInputs.resistanceLevel}
                onChange={(v) => updateStop('resistanceLevel', v)} placeholder="110.00"
                testID="stop-resistance" />
            </TwoCol>
          </>
        )}

        <PrimaryButton onPress={runNow} label="Calculate Stop" loading={stopLoading} testID="stop-run" />
        <ErrorBanner text={stopError?.message} />

        {stopData?.calculateDynamicStop && (
          <View style={styles.resultsSection}>
            <Text style={styles.sectionTitle}>Stop Loss Analysis</Text>
            <Card>
              <MetricRow label="Recommended Stop" value={fmtMoney(stopData.calculateDynamicStop.stopPrice)} />
              <MetricRow label="Stop Distance" value={fmtMoney(stopData.calculateDynamicStop.stopDistance)} />
              <MetricRow
                label="Risk %"
                value={fmtPct(pctToFraction(stopData.calculateDynamicStop.riskPercentage))}
              />
              <Divider />
              <MetricRow label="Method" value={stopData.calculateDynamicStop.method || '—'} />
              <MetricRow label="ATR Stop" value={fmtMoney(stopData.calculateDynamicStop.atrStop)} />
              {typeof stopData.calculateDynamicStop.srStop === 'number' && (
                <MetricRow label="S/R Stop" value={fmtMoney(stopData.calculateDynamicStop.srStop)} />
              )}
              <MetricRow label="Pct Stop" value={fmtMoney(stopData.calculateDynamicStop.pctStop)} />
            </Card>

            <View style={{ marginTop: 8, flexDirection: 'row', gap: 10 }}>
              <SecondaryButton onPress={useAsStopInPosition} icon="corner-down-left" label="Use in Position" />
            </View>
          </View>
        )}
      </View>
    );
  };

  const renderTarget = () => {
    const err = (k: string) => errors[`target.${k}`];

    const runNow = () => {
      if (!validateTarget()) return;
      fetchTarget({
        variables: {
          entryPrice: safeFloat(targetInputs.entryPrice),
          stopPrice: safeFloat(targetInputs.stopPrice),
          riskRewardRatio: safeFloat(targetInputs.riskRewardRatio),
          atr: targetInputs.atr ? safeFloat(targetInputs.atr) : undefined,
          resistanceLevel: targetInputs.resistanceLevel ? safeFloat(targetInputs.resistanceLevel) : undefined,
          supportLevel: targetInputs.supportLevel ? safeFloat(targetInputs.supportLevel) : undefined,
          signalType: targetInputs.signalType,
        },
      });
    };

    const useAsTargetInPosition = () => {
      const v = targetData?.calculateTargetPrice?.targetPrice;
      if (typeof v === 'number' && isFinite(v)) {
        // not changing position sizing directly; just helpful action
        Alert.alert('Target Saved', `Suggested target: $${v.toFixed(2)}`);
      }
    };

    const applyStopFromStopTab = () => {
      const v = stopData?.calculateDynamicStop?.stopPrice;
      if (typeof v === 'number' && isFinite(v)) {
        updateTarget('stopPrice', String(v.toFixed(2)));
      }
    };

    return (
      <View style={styles.tabContent}>
        <AutoCalcToggle tab="target" />
        <Text style={styles.sectionTitle}>Trade Inputs</Text>

        <Segmented
          value={targetInputs.signalType}
          onChange={(v) => updateTarget('signalType', v)}
          options={[{ value: 'long', label: 'LONG' }, { value: 'short', label: 'SHORT' }]}
        />

        <TwoCol>
          <InputRow label="Entry Price" value={targetInputs.entryPrice}
            onChange={(v) => updateTarget('entryPrice', v)} placeholder="100.00" error={err('entryPrice')}
            testID="tgt-entry" />
          <InputRow label="Stop Price" value={targetInputs.stopPrice}
            onChange={(v) => updateTarget('stopPrice', v)} placeholder="95.00" error={err('stopPrice')}
            testID="tgt-stop" />
        </TwoCol>

        <InputRow label="Risk/Reward Ratio" value={targetInputs.riskRewardRatio}
          onChange={(v) => updateTarget('riskRewardRatio', v)} placeholder="2.0" error={err('riskRewardRatio')}
          testID="tgt-rr" />

        {showAdvanced && (
          <>
            <Text style={[styles.sectionTitle, { marginTop: 8 }]}>Advanced</Text>
            <TwoCol>
              <InputRow label="ATR (opt)" value={targetInputs.atr}
                onChange={(v) => updateTarget('atr', v)} placeholder="2.0"
                testID="tgt-atr" />
              <InputRow label="Resistance (opt)" value={targetInputs.resistanceLevel}
                onChange={(v) => updateTarget('resistanceLevel', v)} placeholder="110.00"
                testID="tgt-res" />
            </TwoCol>
            <InputRow label="Support (opt)" value={targetInputs.supportLevel}
              onChange={(v) => updateTarget('supportLevel', v)} placeholder="90.00"
              testID="tgt-sup" />
          </>
        )}

        <PrimaryButton onPress={runNow} label="Calculate Target" loading={targetLoading} testID="tgt-run" />
        <ErrorBanner text={targetError?.message} />

        {targetData?.calculateTargetPrice && (
          <View style={styles.resultsSection}>
            <Text style={styles.sectionTitle}>Target Price Analysis</Text>
            <Card>
              <MetricRow label="Recommended Target" value={fmtMoney(targetData.calculateTargetPrice.targetPrice)} />
              <MetricRow label="Reward Distance" value={fmtMoney(targetData.calculateTargetPrice.rewardDistance)} />
              <MetricRow label="Risk / Reward" value={targetData.calculateTargetPrice.riskRewardRatio?.toFixed(2) ?? '—'} />
              <Divider />
              <MetricRow label="Method" value={targetData.calculateTargetPrice.method || '—'} />
              <MetricRow label="RR Target" value={fmtMoney(targetData.calculateTargetPrice.rrTarget)} />
              {typeof targetData.calculateTargetPrice.atrTarget === 'number' && (
                <MetricRow label="ATR Target" value={fmtMoney(targetData.calculateTargetPrice.atrTarget)} />
              )}
              {typeof targetData.calculateTargetPrice.srTarget === 'number' && (
                <MetricRow label="S/R Target" value={fmtMoney(targetData.calculateTargetPrice.srTarget)} />
              )}
            </Card>

            <View style={{ marginTop: 8, flexDirection: 'row', gap: 10 }}>
              <SecondaryButton onPress={useAsTargetInPosition} icon="flag" label="Save Target" />
              <SecondaryButton onPress={applyStopFromStopTab} icon="download" label="Use Stop from Stop Tab" />
            </View>
          </View>
        )}
      </View>
    );
  };

  /* ----------------------------- Main Layout ----------------------------- */

  return (
    <SafeAreaView style={styles.container}>
      <Header />

      <View style={styles.tabBar}>
        {(['position', 'stop', 'target'] as const).map((k) => (
          <TouchableOpacity
            key={k}
            style={[styles.tab, activeTab === k && styles.activeTab]}
            onPress={() => setActiveTab(k)}
            testID={`tab-${k}`}
          >
            <Text style={[styles.tabText, activeTab === k && styles.activeTabText]}>
              {k === 'position' ? 'Position Size' : k === 'stop' ? 'Stop Loss' : 'Target Price'}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      <KeyboardAvoidingView behavior={Platform.select({ ios: 'padding', android: undefined })} style={{ flex: 1 }}>
        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {activeTab === 'position' && renderPosition()}
          {activeTab === 'stop' && renderStop()}
          {activeTab === 'target' && renderTarget()}

          <View style={styles.disclaimer}>
            <Icon name="info" size={14} color={C.sub} />
            <Text style={styles.disclaimerText}>
              Educational tool only. Not investment advice. Verify calculations before trading.
            </Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

/* -------------------------- UI subcomponents -------------------------- */

const Card = ({ children }: { children: React.ReactNode }) => (
  <View style={styles.resultCard}>{children}</View>
);

const Divider = () => <View style={styles.divider} />;

const MetricRow = ({ label, value }: { label: string; value: string }) => (
  <View style={styles.resultRow}>
    <Text style={styles.resultLabel}>{label}</Text>
    <Text style={styles.resultValue}>{value}</Text>
  </View>
);

const TwoCol = ({ children }: { children: React.ReactNode }) => {
  const arr = Array.isArray(children) ? children : [children];
  return (
    <View style={{ flexDirection: 'row', gap: 12 }}>
      <View style={{ flex: 1 }}>{arr[0]}</View>
      <View style={{ flex: 1 }}>{arr[1]}</View>
    </View>
  );
};

const PrimaryButton = ({
  onPress, label, loading, testID,
}: { onPress: () => void; label: string; loading?: boolean; testID?: string }) => (
  <TouchableOpacity
    onPress={onPress}
    disabled={loading}
    style={[styles.primaryBtn, loading && styles.disabledButton]}
    testID={testID}
  >
    {loading ? <ActivityIndicator color="#fff" /> : <Icon name="play" size={18} color="#fff" />}
    <Text style={styles.primaryBtnText}>{label}</Text>
  </TouchableOpacity>
);

const SecondaryButton = ({
  onPress, label, icon,
}: { onPress: () => void; label: string; icon: string }) => (
  <TouchableOpacity onPress={onPress} style={styles.secondaryBtn}>
    <Icon name={icon as any} size={16} color={C.primary} />
    <Text style={styles.secondaryBtnText}>{label}</Text>
  </TouchableOpacity>
);

/* ------------------------------- Styles ------------------------------- */

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },

  header: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 20, paddingVertical: 16, backgroundColor: C.card,
    borderBottomWidth: 1, borderBottomColor: C.line,
  },
  backButton: { padding: 8, marginRight: 8 },
  headerTitle: { fontSize: 24, fontWeight: '700', color: C.text },
  advancedToggle: { padding: 8 },
  advancedToggleText: { fontSize: 14, color: C.primary, fontWeight: '600' },

  tabBar: { flexDirection: 'row', backgroundColor: C.card, borderBottomWidth: 1, borderBottomColor: C.line },
  tab: { flex: 1, paddingVertical: 16, alignItems: 'center' },
  activeTab: { borderBottomWidth: 2, borderBottomColor: C.primary },
  tabText: { fontSize: 16, color: C.sub, fontWeight: '500' },
  activeTabText: { color: C.primary, fontWeight: '600' },

  content: { flex: 1 },

  tabContent: { padding: 20 },

  sectionTitle: { fontSize: 18, fontWeight: '600', color: C.text, marginBottom: 12 },

  inputGroup: { marginBottom: 16 },
  inputLabel: { fontSize: 14, fontWeight: '500', color: '#374151', marginBottom: 8 },
  input: {
    borderWidth: 1, borderColor: '#D1D5DB', borderRadius: 8,
    paddingHorizontal: 12, paddingVertical: 12, fontSize: 16, color: C.text, backgroundColor: C.card,
  },
  inputError: { marginTop: 6, color: C.red },

  segmentedControl: { flexDirection: 'row', backgroundColor: '#F3F4F6', borderRadius: 8, padding: 4, marginBottom: 8 },
  segmentButton: { flex: 1, paddingVertical: 8, paddingHorizontal: 16, borderRadius: 6, alignItems: 'center' },
  segmentButtonActive: { backgroundColor: C.primary },
  segmentButtonText: { fontSize: 14, fontWeight: '500', color: C.sub },
  segmentButtonTextActive: { color: '#FFFFFF' },

  autoRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'flex-end', marginBottom: 8, gap: 8 },
  autoLabel: { color: C.sub, fontSize: 12 },

  resultsSection: { marginTop: 16 },

  resultCard: {
    backgroundColor: C.card, borderRadius: 12, padding: 16,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1, shadowRadius: 3.84, elevation: 5,
  },
  resultRow: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingVertical: 8, borderBottomWidth: 1, borderBottomColor: '#F3F4F6',
  },
  divider: { height: 1, backgroundColor: '#F3F4F6', marginVertical: 6 },
  resultLabel: { fontSize: 14, color: C.sub },
  resultValue: { fontSize: 16, fontWeight: '600', color: C.text },

  primaryBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    backgroundColor: C.primary, paddingVertical: 14, borderRadius: 10, gap: 8, marginTop: 4,
  },
  primaryBtnText: { color: '#fff', fontWeight: '700' },
  disabledButton: { opacity: 0.7 },

  secondaryBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    paddingHorizontal: 12, paddingVertical: 8, borderRadius: 8, backgroundColor: '#EAF2FF',
  },
  secondaryBtnText: { color: C.primary, fontWeight: '700' },

  errorBanner: {
    flexDirection: 'row', alignItems: 'center', gap: 8, backgroundColor: '#DC2626',
    paddingVertical: 8, paddingHorizontal: 12, borderRadius: 8, marginTop: 10,
  },
  errorBannerText: { color: '#fff', flex: 1 },

  disclaimer: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    paddingHorizontal: 20, paddingVertical: 12,
  },
  disclaimerText: { color: C.sub, fontSize: 12, flex: 1 },
});

export default RiskCoachScreen;
