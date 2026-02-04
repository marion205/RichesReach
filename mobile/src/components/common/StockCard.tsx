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
  isGoodForIncomeProfile?: boolean;
  currentPrice?: number; // Add current price for affordability calculation
  onPressAdd: () => void;
  onPressAnalysis: () => void;
  onPressMetric: (k: 'marketCap' | 'peRatio' | 'dividendYield') => void;
  onPressBudgetImpact?: () => void;
  // onPressTrade removed - Trade button no longer exists
  onPress?: () => void;
  isSelected?: boolean;
};

function StockCard(props: StockCardProps) {
  const rec = getBuyRecommendation(props.beginnerFriendlyScore);
  
  // Calculate affordability based on price
  const getAffordabilityInfo = () => {
    if (!props.currentPrice) return null;
    
    const price = Number(props.currentPrice);
    if (price <= 50) return { label: 'Budget', color: '#4CAF50', icon: 'dollar-sign' };
    if (price <= 100) return { label: 'Affordable', color: '#8BC34A', icon: 'check-circle' };
    if (price <= 200) return { label: 'Moderate', color: '#FF9800', icon: 'minus-circle' };
    return { label: 'Premium', color: '#F44336', icon: 'trending-up' };
  };
  
  const affordability = getAffordabilityInfo();

  return (
    <View style={[styles.card, props.isSelected && styles.selectedCard]}>
      <View style={styles.header}>
        <View style={styles.headerRow}>
          <TouchableOpacity 
            style={styles.symbolContainer} 
            onPress={props.onPress || props.onPressAdd} 
            activeOpacity={0.7}
          >
            <Text style={styles.symbol}>{props.symbol}</Text>
          </TouchableOpacity>
          <View style={styles.badgesRow}>
            <View style={[styles.scoreBadge, { backgroundColor: getScoreColor(props.beginnerFriendlyScore) }]}>
              <Text style={styles.scoreText}>{props.beginnerFriendlyScore}</Text>
            </View>
            <View style={[styles.recBadge, { backgroundColor: rec.backgroundColor, borderColor: rec.color }]}>
              <Text style={[styles.recText, { color: rec.color }]}>{rec.text}</Text>
            </View>
            <View style={styles.budgetContainer}>
              <TouchableOpacity 
                style={styles.budgetBtn} 
                onPress={props.onPressBudgetImpact} 
                activeOpacity={0.85}
              >
                <Icon name="dollar-sign" size={14} color="#FF6B35" />
              </TouchableOpacity>
              {props.isGoodForIncomeProfile && affordability && (
                <TouchableOpacity 
                  style={[styles.affordabilityBadge, { backgroundColor: affordability.color }]}
                  onPress={props.onPressBudgetImpact}
                  activeOpacity={0.85}
                >
                  <Icon name={affordability.icon} size={10} color="#fff" />
                  <Text style={styles.affordabilityText}>{affordability.label}</Text>
                </TouchableOpacity>
              )}
            </View>
            <TouchableOpacity 
              style={styles.watchlistBtnTop} 
              onPress={props.onPressAdd} 
              activeOpacity={0.85}
            >
              <Icon name="plus" size={16} color="#007AFF" />
            </TouchableOpacity>
          </View>
        </View>
        <TouchableOpacity 
          style={styles.nameContainer} 
          onPress={props.onPress || props.onPressAdd} 
          activeOpacity={0.7}
        >
          <Text style={styles.name}>{props.companyName}</Text>
          <Text style={styles.sector}>{props.sector}</Text>
        </TouchableOpacity>
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
                ? `${((Number(props.dividendYield) || 0) * 100).toFixed(2)}%` 
                : 'N/A'}
            </Text>
            <Icon name="trending-up" size={16} color="#00cc99" style={styles.info} />
          </TouchableOpacity>
        )}
      </View>

      {/* Trade Button - Removed as requested */}

      {/* Advanced Analysis Button - Always visible */}
      <TouchableOpacity
        style={styles.analysisBtn}
        onPress={() => {
          if (props.onPressAnalysis) {
            props.onPressAnalysis();
          }
        }}
        activeOpacity={0.85}
      >
        <Icon name="bar-chart-2" size={16} color="#fff" style={{ marginRight: 8 }} />
        <Text style={styles.analysisText}>Advanced Analysis</Text>
      </TouchableOpacity>
    </View>
  );
}

export default memo(StockCard);

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#fff', borderRadius: 16, padding: 20, marginBottom: 16,
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.1, shadowRadius: 8, elevation: 3,
  },
  header: { marginBottom: 16 },
  headerRow: { 
    flexDirection: 'row', 
    alignItems: 'flex-start', 
    justifyContent: 'space-between',
    flexWrap: 'wrap',
    gap: 8,
  },
  badgesRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    flexShrink: 1,
    flexWrap: 'wrap',
  },
  symbolContainer: { 
    paddingVertical: 4, 
    paddingHorizontal: 2,
    flexShrink: 0,
  },
  symbol: { fontSize: 24, fontWeight: 'bold', color: '#333' },
  nameContainer: { paddingVertical: 4, paddingHorizontal: 2 },
  scoreBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12, minWidth: 32, alignItems: 'center', flexShrink: 0 },
  scoreText: { fontSize: 12, fontWeight: 'bold', color: '#fff' },
  recBadge: { paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12, borderWidth: 1, minWidth: 50, alignItems: 'center', flexShrink: 0 },
  recText: { fontSize: 9, fontWeight: 'bold', textAlign: 'center' },
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
    borderWidth: 1, borderColor: '#007AFF',
    flexShrink: 0,
    width: 32,
    height: 32,
  },
  budgetBtn: { 
    backgroundColor: '#FFF5F0', paddingHorizontal: 6, paddingVertical: 6, borderRadius: 8, 
    alignItems: 'center', justifyContent: 'center', 
    borderWidth: 1, borderColor: '#FF6B35',
    flexShrink: 0,
    width: 28,
    height: 28,
  },
  budgetContainer: {
    alignItems: 'center',
    flexShrink: 0,
  },
  affordabilityBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 5,
    paddingVertical: 3,
    borderRadius: 6,
    marginTop: 4,
    minWidth: 55,
    maxWidth: 80,
    justifyContent: 'center',
    flexShrink: 1,
  },
  affordabilityText: {
    fontSize: 9,
    fontWeight: 'bold',
    color: '#fff',
    marginLeft: 3,
  },
  // Trade button styles removed
  analysisBtn: {
    flexDirection: 'row', 
    alignItems: 'center', 
    justifyContent: 'center', 
    backgroundColor: '#6366f1',
    paddingVertical: 12, 
    borderRadius: 12, 
    marginTop: 12,
    shadowColor: '#6366f1',
    shadowOffset: { width: 0, height: 2 }, 
    shadowOpacity: 0.3, 
    shadowRadius: 4, 
    elevation: 3,
  },
  analysisText: { 
    fontSize: 14, 
    fontWeight: '600', 
    color: '#fff' 
  },
  selectedCard: {
    borderColor: '#007AFF',
    borderWidth: 2,
    backgroundColor: '#F0F8FF',
  },
});
