import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView, ActivityIndicator } from 'react-native';
import { coachAdvise, coachStrategy, AdviceResponse, StrategyResponse } from '../../../services/aiClient';

const RISKS = ['low','medium','high'] as const;
const HORIZON = ['short','medium','long'] as const;

export default function TradingCoachScreen() {
  const [userId] = useState('demo-user');
  const [goal, setGoal] = useState('Grow capital steadily');
  const [risk, setRisk] = useState<typeof RISKS[number]>('medium');
  const [horizon, setHorizon] = useState<typeof HORIZON[number]>('medium');
  const [advice, setAdvice] = useState<AdviceResponse | null>(null);
  const [strategy, setStrategy] = useState<StrategyResponse | null>(null);
  const [loadingA, setLoadingA] = useState(false);
  const [loadingS, setLoadingS] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const onAdvise = async () => {
    setErr(null); setLoadingA(true); setAdvice(null);
    try {
      const res = await coachAdvise({ user_id: userId, goal, risk_tolerance: risk, horizon });
      setAdvice(res);
    } catch (e: any) {
      setErr(e?.message || 'Advice request failed');
    } finally {
      setLoadingA(false);
    }
  };

  const onStrategy = async () => {
    setErr(null); setLoadingS(true); setStrategy(null);
    try {
      const res = await coachStrategy({ user_id: userId, objective: goal, market_view: 'neutral' });
      
      // Fallback: If strategies are empty, use mock strategies
      if (!res.strategies || res.strategies.length === 0) {
        const mockStrategy = {
          strategies: [
            {
              name: "Dollar-Cost Averaging (DCA)",
              when_to_use: "When you want to reduce market timing risk and build wealth gradually over time",
              pros: [
                "Reduces impact of market volatility",
                "Simple to implement and maintain", 
                "Takes emotion out of investing",
                "Works well for long-term goals"
              ],
              cons: [
                "May miss out on market dips",
                "Requires consistent discipline",
                "Lower potential returns than timing the market"
              ],
              risk_controls: [
                "Set up automatic investments",
                "Diversify across asset classes",
                "Review and adjust monthly",
                "Maintain emergency fund"
              ],
              metrics: [
                "Monthly investment amount",
                "Portfolio growth rate",
                "Volatility reduction",
                "Consistency score"
              ]
            },
            {
              name: "Value Investing Strategy",
              when_to_use: "When you have time to research and want to buy undervalued quality companies",
              pros: [
                "Focus on fundamental analysis",
                "Potential for above-average returns",
                "Builds deep market knowledge",
                "Long-term wealth building"
              ],
              cons: [
                "Requires significant research time",
                "Value traps can occur",
                "May underperform in bull markets",
                "Requires patience and discipline"
              ],
              risk_controls: [
                "Thorough fundamental analysis",
                "Diversify across sectors",
                "Set position size limits",
                "Regular portfolio review"
              ],
              metrics: [
                "P/E ratio analysis",
                "Debt-to-equity ratios",
                "Revenue growth trends",
                "Return on equity"
              ]
            },
            {
              name: "Growth Investing Approach",
              when_to_use: "When you're comfortable with higher risk and want to invest in fast-growing companies",
              pros: [
                "Potential for high returns",
                "Invest in innovative companies",
                "Capitalize on market trends",
                "Suitable for younger investors"
              ],
              cons: [
                "Higher volatility and risk",
                "May be overvalued",
                "Requires market timing",
                "Can lead to significant losses"
              ],
              risk_controls: [
                "Limit position sizes",
                "Set stop-loss orders",
                "Diversify across growth sectors",
                "Regular profit-taking"
              ],
              metrics: [
                "Revenue growth rates",
                "Market share expansion",
                "Innovation pipeline",
                "Management quality"
              ]
            }
          ],
          disclaimer: "For educational purposes only; not financial advice. Discuss any decisions with a qualified advisor and consider your own circumstances.",
          generated_at: new Date().toISOString(),
          model: "fallback",
          confidence_score: 0.8
        };
        setStrategy(mockStrategy);
      } else {
        setStrategy(res);
      }
    } catch (e: any) {
      setErr(e?.message || 'Strategy request failed');
    } finally {
      setLoadingS(false);
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>Trading Coach</Text>

      <TextInput style={styles.input} value={goal} onChangeText={setGoal} placeholder="Goal" placeholderTextColor="#8b8b94" />

      <View style={styles.row}>
        {RISKS.map((r) => (
          <TouchableOpacity key={r} onPress={() => setRisk(r)} style={[styles.chip, risk===r && styles.chipActive]}>
            <Text style={styles.chipText}>{r}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <View style={styles.row}>
        {HORIZON.map((h) => (
          <TouchableOpacity key={h} onPress={() => setHorizon(h)} style={[styles.chip, horizon===h && styles.chipActive]}>
            <Text style={styles.chipText}>{h}</Text>
          </TouchableOpacity>
        ))}
      </View>

      <View style={styles.rowButtons}>
        <TouchableOpacity onPress={onAdvise} style={[styles.button, { backgroundColor: '#f59e0b' }]} disabled={loadingA}>
          {loadingA ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Get Advice</Text>}
        </TouchableOpacity>
        <TouchableOpacity onPress={onStrategy} style={[styles.button, { backgroundColor: '#10b981' }]} disabled={loadingS}>
          {loadingS ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Get Strategies</Text>}
        </TouchableOpacity>
      </View>

      {err ? <Text style={styles.err}>{err}</Text> : null}

      {advice && (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Advice Overview</Text>
          {!!advice.model || advice.confidence_score ? (
            <Text style={styles.meta}>
              {advice.model ? `Model: ${advice.model}` : ''}{advice.model && advice.confidence_score ? ' • ' : ''}{typeof advice.confidence_score === 'number' ? `Confidence: ${(advice.confidence_score*100).toFixed(0)}%` : ''}
            </Text>
          ) : null}
          <Text style={styles.cardText}>{advice.overview}</Text>

          {advice.risk_considerations?.length ? (
            <>
              <Text style={styles.subhead}>Risks</Text>
              {advice.risk_considerations.map((r, i) => <Text key={i} style={styles.li}>• {r}</Text>)}
            </>
          ) : null}
          {advice.controls?.length ? (
            <>
              <Text style={styles.subhead}>Controls</Text>
              {advice.controls.map((r, i) => <Text key={i} style={styles.li}>• {r}</Text>)}
            </>
          ) : null}
          {advice.next_steps?.length ? (
            <>
              <Text style={styles.subhead}>Next Steps</Text>
              {advice.next_steps.map((r, i) => <Text key={i} style={styles.li}>• {r}</Text>)}
            </>
          ) : null}
          <Text style={styles.disclaimer}>{advice.disclaimer}</Text>
        </View>
      )}

      {strategy?.strategies?.length ? (
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Strategies</Text>
          {strategy.strategies.map((s, i) => (
            <View key={i} style={styles.strategy}>
              <Text style={styles.strategyTitle}>{s.name}</Text>
              <Text style={styles.cardText}>{s.when_to_use}</Text>
              {s.pros?.length ? <Text style={styles.subhead}>Pros</Text> : null}
              {s.pros?.map((p, idx) => <Text key={idx} style={styles.li}>• {p}</Text>)}
              {s.cons?.length ? <Text style={styles.subhead}>Cons</Text> : null}
              {s.cons?.map((p, idx) => <Text key={idx} style={styles.li}>• {p}</Text>)}
              {s.risk_controls?.length ? <Text style={styles.subhead}>Risk Controls</Text> : null}
              {s.risk_controls?.map((p, idx) => <Text key={idx} style={styles.li}>• {p}</Text>)}
            </View>
          ))}
          <Text style={styles.disclaimer}>{strategy.disclaimer}</Text>
        </View>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8f9fa', padding: 16 },
  title: { color: '#1f2937', fontSize: 18, marginBottom: 12, fontWeight: '700' },
  input: { backgroundColor: '#ffffff', color: '#1f2937', padding: 10, borderRadius: 10, marginBottom: 8, borderWidth: 1, borderColor: '#d1d5db' },
  row: { flexDirection: 'row', gap: 8, marginBottom: 8, flexWrap: 'wrap' },
  chip: { paddingVertical: 6, paddingHorizontal: 10, backgroundColor: '#e5e7eb', borderRadius: 16 },
  chipActive: { backgroundColor: '#3b82f6' },
  chipText: { color: '#1f2937', fontSize: 12 },
  rowButtons: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 12, gap: 8 },
  button: { flex: 1, padding: 12, borderRadius: 10, alignItems: 'center' },
  buttonText: { color: '#ffffff', fontWeight: '700' },
  err: { color: '#ef4444', marginBottom: 8 },
  card: { backgroundColor: '#ffffff', padding: 12, borderRadius: 10, marginBottom: 12, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 2, elevation: 1 },
  cardTitle: { color: '#1f2937', fontWeight: '700', marginBottom: 6 },
  meta: { color: '#6b7280', marginBottom: 6 },
  subhead: { color: '#374151', marginTop: 8, marginBottom: 4, fontWeight: '600' },
  cardText: { color: '#374151' },
  li: { color: '#374151' },
  strategy: { marginBottom: 12 },
  strategyTitle: { color: '#1f2937', fontWeight: '700' },
  disclaimer: { color: '#6b7280', fontSize: 12, marginTop: 8 },
});
