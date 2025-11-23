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
        <View style={{ flex: 1, marginRight: 16 }}>
          <Text style={[styles.title, { color: isDark ? '#fff' : '#111827' }]}>Signal Contribution</Text>
          <Text style={[styles.subtitle, { color: isDark ? '#999' : '#6B7280' }]}>What's driving the {symbol} prediction</Text>
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
              <View style={[styles.barBackground, { backgroundColor: isDark ? '#2a2a2a' : '#F3F4F6' }]}>
                <LinearGradient
                  colors={[signal.color, signal.color + 'DD']}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={[styles.barFill, { width: `${signal.normalized}%` }]}
                />
              </View>
              <Text style={[styles.contributionText, { color: isDark ? '#fff' : '#111827' }]}>
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
        <View style={[styles.reasoning, { backgroundColor: isDark ? '#2a2a2a' : '#F9FAFB' }]}>
          <Text style={[styles.reasoningLabel, { color: isDark ? '#999' : '#6B7280' }]}>AI Reasoning:</Text>
          <Text style={[styles.reasoningText, { color: isDark ? '#fff' : '#374151' }]}>{reasoning}</Text>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { 
    padding: 20, 
    borderRadius: 20, 
    marginVertical: 8, 
    shadowColor: '#000', 
    shadowOffset: { width: 0, height: 4 }, 
    shadowOpacity: 0.12, 
    shadowRadius: 16, 
    elevation: 5,
    borderWidth: 1,
    borderColor: '#F3F4F6',
  },
  header: { 
    flexDirection: 'row', 
    justifyContent: 'space-between', 
    alignItems: 'flex-start', 
    marginBottom: 28,
    paddingBottom: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  title: { 
    fontSize: 24, 
    fontWeight: '800', 
    marginBottom: 8,
    letterSpacing: -0.8,
    color: '#111827',
  },
  subtitle: { 
    fontSize: 14, 
    fontWeight: '500',
    color: '#6B7280',
    letterSpacing: -0.2,
  },
  scoreBadge: { 
    alignItems: 'center', 
    justifyContent: 'center', 
    paddingHorizontal: 20, 
    paddingVertical: 16, 
    borderRadius: 14, 
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    minWidth: 90,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  scoreLabel: { 
    fontSize: 10, 
    fontWeight: '700', 
    color: '#6B7280', 
    marginBottom: 6,
    textTransform: 'uppercase',
    letterSpacing: 1.2,
  },
  scoreValue: { 
    fontSize: 28, 
    fontWeight: '800', 
    color: '#111827',
    letterSpacing: -1,
  },
  barsContainer: { marginBottom: 24 },
  barRow: { marginBottom: 24 },
  barLabelContainer: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    marginBottom: 12,
  },
  colorIndicator: { 
    width: 20, 
    height: 20, 
    borderRadius: 10, 
    marginRight: 12,
    borderWidth: 2,
    borderColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 2,
  },
  labelTextContainer: { flex: 1 },
  signalName: { 
    fontSize: 16, 
    fontWeight: '700', 
    marginBottom: 3,
    letterSpacing: -0.3,
  },
  signalDescription: { 
    fontSize: 13, 
    fontWeight: '500',
    color: '#6B7280',
  },
  barContainer: { 
    flexDirection: 'row', 
    alignItems: 'center',
    marginTop: 10,
  },
  barBackground: { 
    flex: 1, 
    height: 32, 
    borderRadius: 16, 
    overflow: 'hidden', 
    marginRight: 16,
    backgroundColor: '#F3F4F6',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  barFill: { 
    height: '100%', 
    borderRadius: 16,
  },
  contributionText: { 
    fontSize: 15, 
    fontWeight: '700', 
    minWidth: 65, 
    textAlign: 'right',
    color: '#111827',
    letterSpacing: -0.3,
  },
  topSignal: { 
    padding: 14, 
    borderRadius: 16, 
    marginTop: 12, 
    borderWidth: 2,
  },
  topSignalText: { 
    fontSize: 14, 
    fontWeight: '700', 
    textAlign: 'center',
    letterSpacing: 0.3,
  },
  reasoning: { 
    padding: 18, 
    borderRadius: 14, 
    marginTop: 20,
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
    elevation: 2,
  },
  reasoningLabel: { 
    fontSize: 10, 
    fontWeight: '700', 
    marginBottom: 10, 
    textTransform: 'uppercase', 
    letterSpacing: 1.5,
    color: '#6B7280',
  },
  reasoningText: { 
    fontSize: 15, 
    fontWeight: '500', 
    lineHeight: 24,
    color: '#374151',
    letterSpacing: -0.2,
  },
});

