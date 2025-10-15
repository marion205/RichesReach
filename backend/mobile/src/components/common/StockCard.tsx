import React, { memo } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { getScoreColor, getBuyRecommendation, formatMarketCap, n } from '../../shared/utils/score';

export type StockCardProps = {
  id: string;
  symbol: string;
  companyName: string;
  sector: string;
  marketCap?: number | string | null;
  peRatio?: number | null;
  dividendYield?: number | null;
  beginnerFriendlyScore: number;
  beginnerScoreBreakdown?: {
    score: number;
    factors: Array<{
      name: string;
      weight: number;
      value: number;
      contrib: number;
      detail: string;
    }>;
    notes: string[];
  };
  onPressAdd: () => void;
  onPressAnalysis: () => void;
  onPressMetric: (k: 'marketCap' | 'peRatio' | 'dividendYield') => void;
  onPressBudgetImpact?: () => void;
  onPress?: () => void;
  isSelected?: boolean;
};

function StockCard(props: StockCardProps) {
  const rec = getBuyRecommendation(props.beginnerFriendlyScore);

  return (
    <TouchableOpacity 
      style={[styles.card, props.isSelected && styles.selectedCard]} 
      onPress={props.onPress || props.onPressAdd} 
      activeOpacity={0.9}
    >
      <View style={styles.header}>
        <View style={styles.row}>
          <Text style={styles.symbol}>{props.symbol}</Text>
          <View style={styles.row}>
            <View style={[styles.scoreBadge, { backgroundColor: getScoreColor(props.beginnerFriendlyScore) }]}>
              <Text style={styles.scoreText}>{props.beginnerFriendlyScore}</Text>
            </View>
            <View style={[styles.recBadge, { backgroundColor: rec.backgroundColor, borderColor: rec.color }]}>
              <Text style={[styles.recText, { color: rec.color }]}>{rec.text}</Text>
            </View>
            <TouchableOpacity style={styles.watchlistBtnTop} onPress={props.onPressAdd} activeOpacity={0.85}>
              <Icon name="plus" size={16} color="#007AFF" />
            </TouchableOpacity>
            {props.beginnerScoreBreakdown && (
              <TouchableOpacity style={styles.budgetBtn} onPress={props.onPressBudgetImpact} activeOpacity={0.85}>
                <Icon name="dollar-sign" size={14} color="#FF6B35" />
              </TouchableOpacity>
            )}
          </View>
        </View>
        <Text style={styles.name}>{props.companyName}</Text>
        <Text style={styles.sector}>{props.sector}</Text>
      </View>

      <View style={styles.metrics}>
        {props.marketCap != null && (
          <TouchableOpacity style={styles.metric} onPress={() => props.onPressMetric('marketCap')} activeOpacity={0.7}>
            <Text style={styles.metricLabel}>Market Cap</Text>
            <Text style={styles.metricValue}>{formatMarketCap(props.marketCap)}</Text>
            <Icon name="info" size={16} color="#00cc99" style={styles.info} />
          </TouchableOpacity>
        )}
        {props.peRatio != null && (
          <TouchableOpacity style={styles.metric} onPress={() => props.onPressMetric('peRatio')} activeOpacity={0.7}>
            <Text style={styles.metricLabel}>P/E Ratio</Text>
            <Text style={styles.metricValue}>{n(props.peRatio, 1)}</Text>
            <Icon name="info" size={16} color="#00cc99" style={styles.info} />
          </TouchableOpacity>
        )}
        {props.dividendYield != null && (
          <TouchableOpacity style={styles.metric} onPress={() => props.onPressMetric('dividendYield')} activeOpacity={0.7}>
            <Text style={styles.metricLabel}>Dividend</Text>
            <Text style={styles.metricValue}>
              {Number.isFinite(Number(props.dividendYield)) 
                ? `${(Number(props.dividendYield) * 100).toFixed(2)}%` 
                : 'N/A'}
            </Text>
            <Icon name="info" size={16} color="#00cc99" style={styles.info} />
          </TouchableOpacity>
        )}
      </View>

      <TouchableOpacity style={styles.analysisBtn} onPress={props.onPressAnalysis} activeOpacity={0.85}>
        <Icon name="bar-chart-2" size={16} color="#fff" style={{ marginRight: 8 }} />
        <Text style={styles.analysisText}>Advanced Analysis</Text>
      </TouchableOpacity>
    </TouchableOpacity>
  );
}

export default memo(StockCard);

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff', borderRadius: 16, padding: 20, marginBottom: 16,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 8, elevation: 3,
  },
  header: { marginBottom: 16 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  symbol: { fontSize: 24, fontWeight: 'bold', color: '#333', marginRight: 12 },
  scoreBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12, minWidth: 32, alignItems: 'center' },
  scoreText: { fontSize: 12, fontWeight: 'bold', color: '#fff' },
  recBadge: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12, borderWidth: 1, minWidth: 60, alignItems: 'center' },
  recText: { fontSize: 10, fontWeight: 'bold', textAlign: 'center' },
  name: { fontSize: 16, fontWeight: '600', color: '#333', marginBottom: 4 },
  sector: { fontSize: 14, color: '#666' },
  metrics: { flexDirection: 'row', justifyContent: 'space-between' },
  metric: { alignItems: 'center' },
  metricLabel: { fontSize: 12, color: '#999', marginBottom: 4 },
  metricValue: { fontSize: 14, fontWeight: '600', color: '#333' },
  info: { marginLeft: 8 },
  watchlistBtnTop: { 
    backgroundColor: '#F0F8FF', paddingHorizontal: 8, paddingVertical: 6, borderRadius: 8, 
    alignItems: 'center', justifyContent: 'center', 
    borderWidth: 1, borderColor: '#007AFF', marginLeft: 8
  },
  budgetBtn: { 
    backgroundColor: '#FFF5F0', paddingHorizontal: 8, paddingVertical: 6, borderRadius: 8, 
    alignItems: 'center', justifyContent: 'center', 
    borderWidth: 1, borderColor: '#FF6B35', marginLeft: 8
  },
  analysisBtn: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center', backgroundColor: '#6366f1',
    paddingVertical: 12, borderRadius: 12, marginTop: 16, shadowColor: '#6366f1',
    shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.3, shadowRadius: 4, elevation: 3,
  },
  analysisText: { fontSize: 14, fontWeight: '600', color: '#fff' },
  selectedCard: {
    borderColor: '#007AFF',
    borderWidth: 2,
    backgroundColor: '#F0F8FF',
  },
});
