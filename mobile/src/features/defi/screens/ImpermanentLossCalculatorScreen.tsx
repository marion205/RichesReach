/**
 * Impermanent Loss Calculator
 *
 * Interactive tool that helps users understand IL risk before
 * entering a liquidity pool. Users input a token pair and price
 * change scenario; the calculator shows IL impact vs. holding.
 *
 * Part of Phase 3: Community Vanguard
 */
import React, { useState, useMemo } from 'react';
import {
  View,
  Text,
  ScrollView,
  Pressable,
  TextInput,
  StyleSheet,
  Platform,
} from 'react-native';
import Feather from '@expo/vector-icons/Feather';
import { useNavigation } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';
import Slider from '@react-native-community/slider';

// ---------- IL Math ----------

/**
 * Calculate impermanent loss percentage.
 * Formula: IL = 2 * sqrt(priceRatio) / (1 + priceRatio) - 1
 *
 * @param priceRatio - ratio of new price to initial price (e.g., 2.0 = 2x price increase)
 * @returns IL as a negative percentage (e.g., -0.0566 = -5.66%)
 */
function calculateIL(priceRatio: number): number {
  if (priceRatio <= 0) return 0;
  return (2 * Math.sqrt(priceRatio)) / (1 + priceRatio) - 1;
}

/**
 * Calculate full position comparison: LP vs. HODL
 */
function calculatePositionValue(
  initialInvestment: number,
  priceChangeA: number, // as percentage, e.g., 50 = +50%
  priceChangeB: number,
  poolApy: number,      // annual APY as percentage
  holdDays: number,
) {
  const ratioA = 1 + priceChangeA / 100;
  const ratioB = 1 + priceChangeB / 100;

  // For a 50/50 pool, IL depends on the ratio between the two assets
  const priceRatio = ratioA / ratioB;
  const ilPercent = calculateIL(priceRatio);

  // HODL value: 50% in A, 50% in B
  const hodlValue = initialInvestment * (0.5 * ratioA + 0.5 * ratioB);

  // LP value: HODL adjusted for IL
  const lpValueBeforeFees = hodlValue * (1 + ilPercent);

  // Yield earned over hold period
  const dailyRate = poolApy / 100 / 365;
  const yieldEarned = initialInvestment * dailyRate * holdDays;

  const lpValueAfterFees = lpValueBeforeFees + yieldEarned;

  return {
    ilPercent: ilPercent * 100,
    hodlValue,
    lpValueBeforeFees,
    lpValueAfterFees,
    yieldEarned,
    priceRatio,
    netGainVsHodl: lpValueAfterFees - hodlValue,
    breakEvenDays: ilPercent !== 0
      ? Math.abs(hodlValue * ilPercent / (initialInvestment * dailyRate || 1))
      : 0,
  };
}

// ---------- Preset Scenarios ----------

const PRESETS = [
  { label: 'Stablecoin Pair', tokenA: 'USDC', tokenB: 'USDT', changeA: 0, changeB: 0, apy: 5 },
  { label: 'ETH/USDC Bull', tokenA: 'ETH', tokenB: 'USDC', changeA: 50, changeB: 0, apy: 15 },
  { label: 'ETH/USDC Bear', tokenA: 'ETH', tokenB: 'USDC', changeA: -30, changeB: 0, apy: 15 },
  { label: 'BTC/ETH Flat', tokenA: 'BTC', tokenB: 'ETH', changeA: 10, changeB: 12, apy: 8 },
];

// ---------- Components ----------

function ResultCard({
  label,
  value,
  color,
  subtext,
}: {
  label: string;
  value: string;
  color: string;
  subtext?: string;
}) {
  return (
    <View style={styles.resultCard}>
      <Text style={styles.resultLabel}>{label}</Text>
      <Text style={[styles.resultValue, { color }]}>{value}</Text>
      {subtext ? <Text style={styles.resultSubtext}>{subtext}</Text> : null}
    </View>
  );
}

// ---------- Main Screen ----------

export default function ImpermanentLossCalculatorScreen() {
  const navigation = useNavigation<any>();

  const [tokenA, setTokenA] = useState('ETH');
  const [tokenB, setTokenB] = useState('USDC');
  const [investment, setInvestment] = useState('1000');
  const [priceChangeA, setPriceChangeA] = useState(50);
  const [priceChangeB, setPriceChangeB] = useState(0);
  const [poolApy, setPoolApy] = useState(15);
  const [holdDays, setHoldDays] = useState(90);

  const result = useMemo(() => {
    const inv = parseFloat(investment) || 1000;
    return calculatePositionValue(inv, priceChangeA, priceChangeB, poolApy, holdDays);
  }, [investment, priceChangeA, priceChangeB, poolApy, holdDays]);

  const applyPreset = (preset: typeof PRESETS[0]) => {
    setTokenA(preset.tokenA);
    setTokenB(preset.tokenB);
    setPriceChangeA(preset.changeA);
    setPriceChangeB(preset.changeB);
    setPoolApy(preset.apy);
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <LinearGradient
        colors={['#7C3AED', '#6D28D9']}
        style={styles.header}
      >
        <View style={styles.headerRow}>
          <Pressable
            style={({ pressed }) => [styles.backBtn, pressed && { opacity: 0.7 }]}
            onPress={() => navigation.goBack()}
          >
            <Feather name="arrow-left" size={22} color="#FFFFFF" />
          </Pressable>
          <Text style={styles.headerTitle}>IL Calculator</Text>
          <View style={{ width: 36 }} />
        </View>
        <Text style={styles.headerSubtitle}>
          Understand impermanent loss before you LP
        </Text>
      </LinearGradient>

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Presets */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quick Scenarios</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {PRESETS.map((preset, i) => (
              <Pressable
                key={i}
                style={({ pressed }) => [styles.presetPill, pressed && { opacity: 0.8 }]}
                onPress={() => applyPreset(preset)}
              >
                <Text style={styles.presetText}>{preset.label}</Text>
              </Pressable>
            ))}
          </ScrollView>
        </View>

        {/* Inputs */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Your Position</Text>

          {/* Token Pair */}
          <View style={styles.tokenRow}>
            <View style={styles.tokenInput}>
              <Text style={styles.inputLabel}>Token A</Text>
              <TextInput
                style={styles.textInput}
                value={tokenA}
                onChangeText={setTokenA}
                placeholder="ETH"
                placeholderTextColor="#9CA3AF"
              />
            </View>
            <Feather name="slash" size={20} color="#9CA3AF" style={{ marginTop: 28 }} />
            <View style={styles.tokenInput}>
              <Text style={styles.inputLabel}>Token B</Text>
              <TextInput
                style={styles.textInput}
                value={tokenB}
                onChangeText={setTokenB}
                placeholder="USDC"
                placeholderTextColor="#9CA3AF"
              />
            </View>
          </View>

          {/* Investment Amount */}
          <View style={styles.inputGroup}>
            <Text style={styles.inputLabel}>Investment Amount ($)</Text>
            <TextInput
              style={styles.textInput}
              value={investment}
              onChangeText={setInvestment}
              keyboardType="numeric"
              placeholder="1000"
              placeholderTextColor="#9CA3AF"
            />
          </View>

          {/* Pool APY */}
          <View style={styles.inputGroup}>
            <View style={styles.sliderLabelRow}>
              <Text style={styles.inputLabel}>Pool APY</Text>
              <Text style={styles.sliderValue}>{poolApy.toFixed(1)}%</Text>
            </View>
            <Slider
              style={styles.slider}
              minimumValue={0}
              maximumValue={100}
              step={0.5}
              value={poolApy}
              onValueChange={setPoolApy}
              minimumTrackTintColor="#7C3AED"
              maximumTrackTintColor="#E5E7EB"
              thumbTintColor="#7C3AED"
            />
          </View>

          {/* Hold Period */}
          <View style={styles.inputGroup}>
            <View style={styles.sliderLabelRow}>
              <Text style={styles.inputLabel}>Hold Period</Text>
              <Text style={styles.sliderValue}>{holdDays} days</Text>
            </View>
            <Slider
              style={styles.slider}
              minimumValue={1}
              maximumValue={365}
              step={1}
              value={holdDays}
              onValueChange={setHoldDays}
              minimumTrackTintColor="#7C3AED"
              maximumTrackTintColor="#E5E7EB"
              thumbTintColor="#7C3AED"
            />
          </View>
        </View>

        {/* Price Change Scenarios */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Price Scenario</Text>

          <View style={styles.inputGroup}>
            <View style={styles.sliderLabelRow}>
              <Text style={styles.inputLabel}>{tokenA} Price Change</Text>
              <Text style={[styles.sliderValue, { color: priceChangeA >= 0 ? '#10B981' : '#EF4444' }]}>
                {priceChangeA >= 0 ? '+' : ''}{priceChangeA.toFixed(0)}%
              </Text>
            </View>
            <Slider
              style={styles.slider}
              minimumValue={-90}
              maximumValue={500}
              step={1}
              value={priceChangeA}
              onValueChange={setPriceChangeA}
              minimumTrackTintColor="#10B981"
              maximumTrackTintColor="#E5E7EB"
              thumbTintColor="#10B981"
            />
          </View>

          <View style={styles.inputGroup}>
            <View style={styles.sliderLabelRow}>
              <Text style={styles.inputLabel}>{tokenB} Price Change</Text>
              <Text style={[styles.sliderValue, { color: priceChangeB >= 0 ? '#10B981' : '#EF4444' }]}>
                {priceChangeB >= 0 ? '+' : ''}{priceChangeB.toFixed(0)}%
              </Text>
            </View>
            <Slider
              style={styles.slider}
              minimumValue={-90}
              maximumValue={500}
              step={1}
              value={priceChangeB}
              onValueChange={setPriceChangeB}
              minimumTrackTintColor="#10B981"
              maximumTrackTintColor="#E5E7EB"
              thumbTintColor="#10B981"
            />
          </View>
        </View>

        {/* Results */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Results</Text>

          {/* IL Highlight */}
          <View style={[
            styles.ilHighlight,
            { backgroundColor: result.ilPercent < -5 ? '#FEE2E2' : result.ilPercent < -1 ? '#FEF3C7' : '#ECFDF5' },
          ]}>
            <Text style={styles.ilHighlightLabel}>Impermanent Loss</Text>
            <Text style={[
              styles.ilHighlightValue,
              { color: result.ilPercent < -5 ? '#DC2626' : result.ilPercent < -1 ? '#D97706' : '#059669' },
            ]}>
              {result.ilPercent.toFixed(2)}%
            </Text>
            <Text style={styles.ilHighlightDesc}>
              {result.ilPercent < -5
                ? 'High IL risk. Consider stablecoin pairs or shorter holding periods.'
                : result.ilPercent < -1
                ? 'Moderate IL. Pool fees may compensate over time.'
                : 'Minimal IL. This pair has low divergence risk.'}
            </Text>
          </View>

          {/* Comparison Cards */}
          <View style={styles.resultGrid}>
            <ResultCard
              label="If you HODL"
              value={`$${result.hodlValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
              color="#3B82F6"
              subtext="50/50 hold without LP"
            />
            <ResultCard
              label="LP (before fees)"
              value={`$${result.lpValueBeforeFees.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
              color={result.lpValueBeforeFees < result.hodlValue ? '#EF4444' : '#10B981'}
              subtext="Pool value minus IL"
            />
          </View>

          <View style={styles.resultGrid}>
            <ResultCard
              label="Yield Earned"
              value={`+$${result.yieldEarned.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
              color="#10B981"
              subtext={`${poolApy}% APY over ${holdDays}d`}
            />
            <ResultCard
              label="LP (after fees)"
              value={`$${result.lpValueAfterFees.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
              color={result.lpValueAfterFees >= result.hodlValue ? '#10B981' : '#EF4444'}
              subtext="Net position value"
            />
          </View>

          {/* Net vs HODL */}
          <View style={[
            styles.netCard,
            { backgroundColor: result.netGainVsHodl >= 0 ? '#ECFDF5' : '#FEE2E2' },
          ]}>
            <Text style={styles.netLabel}>Net vs. HODLing</Text>
            <Text style={[
              styles.netValue,
              { color: result.netGainVsHodl >= 0 ? '#059669' : '#DC2626' },
            ]}>
              {result.netGainVsHodl >= 0 ? '+' : ''}
              ${result.netGainVsHodl.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </Text>
            {result.breakEvenDays > 0 && result.netGainVsHodl < 0 && (
              <Text style={styles.netSubtext}>
                Break-even in ~{Math.ceil(result.breakEvenDays)} days at current APY
              </Text>
            )}
          </View>
        </View>

        {/* Education Card */}
        <View style={styles.section}>
          <Pressable
            style={({ pressed }) => [styles.eduCard, pressed && { opacity: 0.9 }]}
            onPress={() => navigation.navigate('Learn')}
          >
            <Feather name="book-open" size={20} color="#7C3AED" />
            <View style={{ flex: 1 }}>
              <Text style={styles.eduTitle}>What is Impermanent Loss?</Text>
              <Text style={styles.eduDesc}>
                Learn how price divergence affects your LP position and strategies to minimize risk.
              </Text>
            </View>
            <Feather name="chevron-right" size={18} color="#9CA3AF" />
          </Pressable>
        </View>

        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}

// ---------- Styles ----------

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },

  // Header
  header: {
    paddingTop: 56,
    paddingBottom: 20,
    paddingHorizontal: 20,
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  backBtn: { padding: 6 },
  headerTitle: { fontSize: 20, fontWeight: '700', color: '#FFFFFF' },
  headerSubtitle: { fontSize: 14, color: '#DDD6FE', textAlign: 'center', marginTop: 6 },

  // Scroll
  scrollView: { flex: 1 },
  scrollContent: { paddingTop: 16 },

  // Section
  section: { paddingHorizontal: 16, marginBottom: 20 },
  sectionTitle: { fontSize: 17, fontWeight: '700', color: '#111827', marginBottom: 10 },

  // Presets
  presetPill: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    backgroundColor: '#EDE9FE',
    borderRadius: 20,
    marginRight: 8,
  },
  presetText: { fontSize: 13, fontWeight: '600', color: '#7C3AED' },

  // Inputs
  tokenRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  tokenInput: { flex: 1 },
  inputGroup: { marginBottom: 14 },
  inputLabel: { fontSize: 13, fontWeight: '600', color: '#6B7280', marginBottom: 6 },
  textInput: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: Platform.OS === 'ios' ? 12 : 10,
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  sliderLabelRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  sliderValue: { fontSize: 16, fontWeight: '700', color: '#111827' },
  slider: { width: '100%', height: 40 },

  // Results
  ilHighlight: {
    padding: 16,
    borderRadius: 16,
    alignItems: 'center',
    marginBottom: 14,
  },
  ilHighlightLabel: { fontSize: 13, fontWeight: '600', color: '#6B7280', marginBottom: 4 },
  ilHighlightValue: { fontSize: 36, fontWeight: '900', letterSpacing: -1 },
  ilHighlightDesc: { fontSize: 12, color: '#6B7280', textAlign: 'center', marginTop: 6, lineHeight: 16 },

  resultGrid: { flexDirection: 'row', gap: 10, marginBottom: 10 },
  resultCard: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    padding: 14,
    borderRadius: 14,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
  },
  resultLabel: { fontSize: 12, fontWeight: '500', color: '#6B7280', marginBottom: 4 },
  resultValue: { fontSize: 18, fontWeight: '800' },
  resultSubtext: { fontSize: 11, color: '#9CA3AF', marginTop: 2 },

  netCard: {
    padding: 16,
    borderRadius: 16,
    alignItems: 'center',
    marginTop: 4,
  },
  netLabel: { fontSize: 13, fontWeight: '600', color: '#6B7280', marginBottom: 4 },
  netValue: { fontSize: 28, fontWeight: '900', letterSpacing: -0.5 },
  netSubtext: { fontSize: 12, color: '#6B7280', marginTop: 6 },

  // Education
  eduCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    padding: 14,
    backgroundColor: '#F5F3FF',
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#DDD6FE',
  },
  eduTitle: { fontSize: 14, fontWeight: '700', color: '#5B21B6', marginBottom: 2 },
  eduDesc: { fontSize: 12, color: '#7C3AED', lineHeight: 16 },
});
