/**
 * Chart 3: "Signal Contribution"
 * Horizontal bar chart showing % contribution of each signal
 */
import React from 'react';
import { View, Text, StyleSheet, Dimensions } from 'react-native';
import { useColorScheme } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';

const { width } = Dimensions.get('window');

interface SignalContribution {
  name: string;
  contribution: number;
  color: string;
  description?: string;
}

interface SignalContributionChartProps {
  symbol: string;
  contributions: SignalContribution[];
  totalScore?: number;
  reasoning?: string;
}

export default function SignalContributionChart({
  symbol,
  contributions,
  totalScore,
  reasoning,
}: SignalContributionChartProps) {
  const colorScheme = useColorScheme();
  const isDark = colorScheme === 'dark';

  const sortedContributions = [...contributions].sort((a, b) => b.contribution - a.contribution);
  const total = contributions.reduce((sum, c) => sum + c.contribution, 0);
  const normalizedContributions = sortedContributions.map((c) => ({
    ...c,
    normalized: total > 0 ? (c.contribution / total) * 100 : 0,
  }));

  return (
    <View style={[styles.container, { backgroundColor: isDark ? '#1a1a1a' : '#fff' }]}>
      <View style={styles.header}>
        <View>
          <Text style={[styles.title, { color: isDark ? '#fff' : '#000' }]}>Signal Contribution</Text>
          <Text style={[styles.subtitle, { color: isDark ? '#999' : '#666' }]}>What's driving the {symbol} prediction</Text>
        </View>
        {totalScore !== undefined && (
          <View style={styles.scoreBadge}>
            <Text style={styles.scoreLabel}>Score</Text>
            <Text style={styles.scoreValue}>{(totalScore * 100).toFixed(0)}</Text>
          </View>
        )}
      </View>

      <View style={styles.barsContainer}>
        {normalizedContributions.map((signal, idx) => (
          <View key={idx} style={styles.barRow}>
            <View style={styles.barLabelContainer}>
              <View style={[styles.colorIndicator, { backgroundColor: signal.color }]} />
              <View style={styles.labelTextContainer}>
                <Text style={[styles.signalName, { color: isDark ? '#fff' : '#000' }]}>{signal.name}</Text>
                {signal.description && (
                  <Text style={[styles.signalDescription, { color: isDark ? '#999' : '#666' }]}>{signal.description}</Text>
                )}
              </View>
            </View>
            <View style={styles.barContainer}>
              <View style={[styles.barBackground, { backgroundColor: isDark ? '#2a2a2a' : '#f3f4f6' }]}>
                <LinearGradient
                  colors={[signal.color, signal.color + 'CC']}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={[styles.barFill, { width: `${signal.normalized}%` }]}
                />
              </View>
              <Text style={[styles.contributionText, { color: isDark ? '#fff' : '#000' }]}>
                {signal.contribution.toFixed(1)}%
              </Text>
            </View>
          </View>
        ))}
      </View>

      {normalizedContributions.length > 0 && normalizedContributions[0].normalized > 40 && (
        <View
          style={[
            styles.topSignal,
            {
              backgroundColor: isDark ? normalizedContributions[0].color + '20' : normalizedContributions[0].color + '10',
              borderColor: normalizedContributions[0].color + '40',
            },
          ]}
        >
          <Text style={[styles.topSignalText, { color: normalizedContributions[0].color }]}>
            🎯 Primary Driver: {normalizedContributions[0].name} ({normalizedContributions[0].contribution.toFixed(1)}%)
          </Text>
        </View>
      )}

      {reasoning && (
        <View style={[styles.reasoning, { backgroundColor: isDark ? '#2a2a2a' : '#f9fafb' }]}>
          <Text style={[styles.reasoningLabel, { color: isDark ? '#999' : '#666' }]}>AI Reasoning:</Text>
          <Text style={[styles.reasoningText, { color: isDark ? '#fff' : '#000' }]}>{reasoning}</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16, borderRadius: 16, marginVertical: 8, shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 8, elevation: 3 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 },
  title: { fontSize: 20, fontWeight: '700', marginBottom: 4 },
  subtitle: { fontSize: 14, fontWeight: '400' },
  scoreBadge: { alignItems: 'center', justifyContent: 'center', paddingHorizontal: 12, paddingVertical: 8, borderRadius: 12, backgroundColor: 'rgba(0, 0, 0, 0.05)' },
  scoreLabel: { fontSize: 10, fontWeight: '600', color: '#666', marginBottom: 2 },
  scoreValue: { fontSize: 20, fontWeight: '700', color: '#000' },
  barsContainer: { marginBottom: 16 },
  barRow: { marginBottom: 16 },
  barLabelContainer: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  colorIndicator: { width: 16, height: 16, borderRadius: 8, marginRight: 8 },
  labelTextContainer: { flex: 1 },
  signalName: { fontSize: 15, fontWeight: '600', marginBottom: 2 },
  signalDescription: { fontSize: 12, fontWeight: '400' },
  barContainer: { flexDirection: 'row', alignItems: 'center' },
  barBackground: { flex: 1, height: 24, borderRadius: 12, overflow: 'hidden', marginRight: 12 },
  barFill: { height: '100%', borderRadius: 12 },
  contributionText: { fontSize: 14, fontWeight: '700', minWidth: 50, textAlign: 'right' },
  topSignal: { padding: 12, borderRadius: 12, marginTop: 8, borderWidth: 1 },
  topSignalText: { fontSize: 13, fontWeight: '600', textAlign: 'center' },
  reasoning: { padding: 12, borderRadius: 12, marginTop: 12 },
  reasoningLabel: { fontSize: 12, fontWeight: '600', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 },
  reasoningText: { fontSize: 13, fontWeight: '400', lineHeight: 18 },
});

