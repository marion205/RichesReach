// components/quant/QuantThinkingExplainer.tsx
/**
 * Quant Thinking Explainer
 * 
 * Educational component that explains Chan's quantitative concepts
 * in accessible, human-readable terms.
 * 
 * Philosophy: "Don't copy trades → Understand the logic landscape"
 */

import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { LinearGradient } from 'expo-linear-gradient';

interface QuantConcept {
  id: string;
  title: string;
  subtitle: string;
  explanation: string;
  richesReachTranslation: string;
  example: string;
  icon: string;
  color: string;
}

const QUANT_CONCEPTS: QuantConcept[] = [
  {
    id: 'mean_reversion',
    title: 'Mean Reversion',
    subtitle: 'Prices return to equilibrium',
    explanation: 'Prices tend to return to their statistical average over time. Extreme deviations (2+ standard deviations) often revert within 10-20 trading days.',
    richesReachTranslation: 'We don\'t auto-trade this. Instead, we calculate a Reversion Probability Score that tells you: "This asset is Xσ from its mean, with Y% probability of reversion within Z days."',
    example: 'AAPL drops 8% in 3 days while the market is flat. Mean reversion probability: 71% within 10 days. Expected max drawdown before reversion: -3.1%.',
    icon: 'trending-down',
    color: '#3B82F6',
  },
  {
    id: 'momentum',
    title: 'Momentum',
    subtitle: 'Trends persist longer than intuition',
    explanation: 'Strong price trends often continue longer than most traders expect. Multi-timeframe confirmation (daily, weekly, monthly) increases confidence.',
    richesReachTranslation: 'Momentum becomes a Timing Confidence Indicator. We show: "Momentum alignment: Daily ✅ Weekly ✅ Monthly ❌" with trend persistence half-life and decay probability.',
    example: 'TSLA shows strong momentum across daily and weekly timeframes, but monthly is negative. Trend persistence half-life: 18 days. Momentum decay probability next 7 days: 22%.',
    icon: 'trending-up',
    color: '#10B981',
  },
  {
    id: 'kelly',
    title: 'Kelly Criterion',
    subtitle: 'Optimal position sizing',
    explanation: 'The Kelly Criterion calculates the optimal position size based on win rate and risk/reward ratio. Formula: f = (p × b - q) / b, where p = win rate, q = loss rate, b = avg win / avg loss.',
    richesReachTranslation: 'We never show raw Kelly. Instead, we translate it into Capital Safety Score, Overexposure Warnings, and Position Size Guardrails that protect you from blowing up.',
    example: 'Based on 65% win rate and 2:1 risk/reward, optimal Kelly is 15%. Conservative recommendation: 3.75% of equity. Expected max drawdown risk: 2.1%.',
    icon: 'target',
    color: '#F59E0B',
  },
  {
    id: 'regime_robustness',
    title: 'Regime Robustness',
    subtitle: 'Signals that work across market conditions',
    explanation: 'A good signal should work in bull markets, bear markets, and sideways markets. Walk-forward testing across multiple regimes prevents overfitting.',
    richesReachTranslation: 'We calculate a Regime Robustness Score that shows: "This signal has remained predictive across 3 market regimes, including 2020 & 2022." This supports our Atomic Verification and anti-hallucination stance.',
    example: 'Mean reversion signal tested across Expansion, Crisis, and Deflation regimes. Performance range: -0.15 to 0.42 Sharpe. Robustness score: 78% (High consistency).',
    icon: 'shield',
    color: '#8B5CF6',
  },
  {
    id: 'execution_risk',
    title: 'Execution Risk',
    subtitle: 'The gap between theory and reality',
    explanation: 'Slippage, liquidity constraints, and psychological pressure during drawdowns can destroy theoretical edge. Real execution often underperforms backtests.',
    richesReachTranslation: 'We turn execution risk into education + protection. Example: "This setup looks attractive, but low liquidity increases slippage risk by ~0.8%. Historical edge may not survive execution."',
    example: 'A mean reversion signal shows 2.4σ deviation with 71% reversion probability. However, average daily volume is only $2M, suggesting 0.6% slippage risk. Net edge after costs: marginal.',
    icon: 'alert-triangle',
    color: '#EF4444',
  },
];

interface QuantThinkingExplainerProps {
  symbol?: string;
  onClose?: () => void;
  initialConcept?: string;
}

export default function QuantThinkingExplainer({
  symbol,
  onClose,
  initialConcept,
}: QuantThinkingExplainerProps) {
  const [selectedConcept, setSelectedConcept] = useState<string | null>(
    initialConcept || null
  );
  
  const selected = selectedConcept
    ? QUANT_CONCEPTS.find(c => c.id === selectedConcept)
    : null;
  
  return (
    <View style={styles.container}>
      {/* Header */}
      <LinearGradient
        colors={['#111827', '#1F2937']}
        style={styles.header}
      >
        <View style={styles.headerContent}>
          <View>
            <Text style={styles.headerTitle}>Quant Thinking</Text>
            <Text style={styles.headerSubtitle}>
              {symbol ? `Understanding ${symbol}` : 'The logic landscape behind signals'}
            </Text>
          </View>
          {onClose && (
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Icon name="x" size={24} color="#FFFFFF" />
            </TouchableOpacity>
          )}
        </View>
      </LinearGradient>
      
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Concept Grid */}
        {!selected && (
          <View style={styles.conceptGrid}>
            {QUANT_CONCEPTS.map((concept) => (
              <TouchableOpacity
                key={concept.id}
                style={styles.conceptCard}
                onPress={() => setSelectedConcept(concept.id)}
                activeOpacity={0.8}
              >
                <LinearGradient
                  colors={[concept.color, concept.color + '80']}
                  style={styles.conceptCardGradient}
                >
                  <Icon name={concept.icon} size={32} color="#FFFFFF" />
                  <Text style={styles.conceptCardTitle}>{concept.title}</Text>
                  <Text style={styles.conceptCardSubtitle}>{concept.subtitle}</Text>
                </LinearGradient>
              </TouchableOpacity>
            ))}
          </View>
        )}
        
        {/* Selected Concept Detail */}
        {selected && (
          <View style={styles.detailView}>
            <TouchableOpacity
              style={styles.backButton}
              onPress={() => setSelectedConcept(null)}
            >
              <Icon name="arrow-left" size={20} color="#111827" />
              <Text style={styles.backButtonText}>Back to Concepts</Text>
            </TouchableOpacity>
            
            <View style={styles.detailCard}>
              <View style={[styles.detailIconContainer, { backgroundColor: selected.color + '20' }]}>
                <Icon name={selected.icon} size={48} color={selected.color} />
              </View>
              
              <Text style={styles.detailTitle}>{selected.title}</Text>
              <Text style={styles.detailSubtitle}>{selected.subtitle}</Text>
              
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>The Concept</Text>
                <Text style={styles.sectionText}>{selected.explanation}</Text>
              </View>
              
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>RichesReach Translation</Text>
                <Text style={styles.sectionText}>{selected.richesReachTranslation}</Text>
              </View>
              
              <View style={[styles.section, styles.exampleSection]}>
                <View style={styles.exampleHeader}>
                  <Icon name="lightbulb" size={16} color={selected.color} />
                  <Text style={[styles.sectionTitle, { marginLeft: 8 }]}>Example</Text>
                </View>
                <Text style={styles.exampleText}>{selected.example}</Text>
              </View>
            </View>
          </View>
        )}
        
        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            RichesReach doesn't copy trades. We extract algorithmic primitives
            and turn them into productized intelligence.
          </Text>
          <Text style={styles.footerCredit}>
            Based on "Quantitative Trading" by Ernest P. Chan
          </Text>
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    paddingTop: 60,
    paddingBottom: 24,
    paddingHorizontal: 24,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 32,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: -1,
  },
  headerSubtitle: {
    fontSize: 16,
    color: '#D1D5DB',
    marginTop: 4,
    fontWeight: '500',
  },
  closeButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  scrollView: {
    flex: 1,
  },
  conceptGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 16,
    gap: 16,
  },
  conceptCard: {
    width: '47%',
    height: 160,
    borderRadius: 20,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  conceptCardGradient: {
    flex: 1,
    padding: 16,
    justifyContent: 'space-between',
  },
  conceptCardTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    letterSpacing: -0.3,
  },
  conceptCardSubtitle: {
    fontSize: 12,
    color: '#FFFFFF',
    opacity: 0.9,
    fontWeight: '500',
    marginTop: 4,
  },
  detailView: {
    padding: 16,
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    paddingVertical: 8,
  },
  backButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginLeft: 8,
  },
  detailCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 4,
  },
  detailIconContainer: {
    width: 80,
    height: 80,
    borderRadius: 40,
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
    marginBottom: 16,
  },
  detailTitle: {
    fontSize: 28,
    fontWeight: '800',
    color: '#111827',
    textAlign: 'center',
    letterSpacing: -0.5,
    marginBottom: 4,
  },
  detailSubtitle: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
    fontWeight: '500',
    marginBottom: 24,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
    letterSpacing: -0.2,
  },
  sectionText: {
    fontSize: 15,
    color: '#374151',
    lineHeight: 24,
    fontWeight: '400',
  },
  exampleSection: {
    backgroundColor: '#F9FAFB',
    padding: 16,
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#3B82F6',
  },
  exampleHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  exampleText: {
    fontSize: 14,
    color: '#4B5563',
    lineHeight: 22,
    fontStyle: 'italic',
  },
  footer: {
    padding: 24,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 22,
    marginBottom: 8,
    fontWeight: '500',
  },
  footerCredit: {
    fontSize: 12,
    color: '#9CA3AF',
    fontStyle: 'italic',
  },
});

