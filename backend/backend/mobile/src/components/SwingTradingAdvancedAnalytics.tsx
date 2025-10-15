import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';

const { width } = Dimensions.get('window');

interface CorrelationData {
  symbol1: string;
  symbol2: string;
  correlation: number;
  period: string;
  trend: 'increasing' | 'decreasing' | 'stable';
}

interface SectorRotation {
  sector: string;
  symbol: string;
  momentum: number;
  strength: number;
  trend: 'bullish' | 'bearish' | 'neutral';
  description: string;
}

interface MarketBreadth {
  index: string;
  advancing: number;
  declining: number;
  unchanged: number;
  newHighs: number;
  newLows: number;
  advDeclRatio: number;
  newHighLowRatio: number;
}

interface VolatilityAnalysis {
  symbol: string;
  currentVol: number;
  avgVol: number;
  volPercentile: number;
  impliedVol: number;
  historicalVol: number;
  volTrend: 'increasing' | 'decreasing' | 'stable';
}

const SwingTradingAdvancedAnalytics: React.FC = () => {
  const [selectedAnalysis, setSelectedAnalysis] = useState('correlation');

  const correlationData: CorrelationData[] = [
    {
      symbol1: 'SPY',
      symbol2: 'QQQ',
      correlation: 0.89,
      period: '30d',
      trend: 'stable'
    },
    {
      symbol1: 'SPY',
      symbol2: 'IWM',
      correlation: 0.76,
      period: '30d',
      trend: 'increasing'
    },
    {
      symbol1: 'QQQ',
      symbol2: 'XLK',
      correlation: 0.92,
      period: '30d',
      trend: 'stable'
    },
    {
      symbol1: 'SPY',
      symbol2: 'VIX',
      correlation: -0.78,
      period: '30d',
      trend: 'decreasing'
    },
    {
      symbol1: 'XLF',
      symbol2: 'XLE',
      correlation: 0.45,
      period: '30d',
      trend: 'increasing'
    },
    {
      symbol1: 'GLD',
      symbol2: 'TLT',
      correlation: 0.67,
      period: '30d',
      trend: 'stable'
    }
  ];

  const sectorRotation: SectorRotation[] = [
    {
      sector: 'Technology',
      symbol: 'XLK',
      momentum: 0.85,
      strength: 92,
      trend: 'bullish',
      description: 'Leading sector with strong earnings and AI adoption'
    },
    {
      sector: 'Healthcare',
      symbol: 'XLV',
      momentum: 0.45,
      strength: 68,
      trend: 'neutral',
      description: 'Stable performance with mixed earnings results'
    },
    {
      sector: 'Financials',
      symbol: 'XLF',
      momentum: 0.72,
      strength: 78,
      trend: 'bullish',
      description: 'Benefiting from higher interest rates and economic growth'
    },
    {
      sector: 'Energy',
      symbol: 'XLE',
      momentum: -0.15,
      strength: 35,
      trend: 'bearish',
      description: 'Under pressure from declining oil prices'
    },
    {
      sector: 'Consumer Discretionary',
      symbol: 'XLY',
      momentum: 0.58,
      strength: 72,
      trend: 'bullish',
      description: 'Strong consumer spending supporting retail stocks'
    },
    {
      sector: 'Utilities',
      symbol: 'XLU',
      momentum: -0.25,
      strength: 28,
      trend: 'bearish',
      description: 'Interest rate sensitivity weighing on performance'
    }
  ];

  const marketBreadth: MarketBreadth[] = [
    {
      index: 'NYSE',
      advancing: 2847,
      declining: 1234,
      unchanged: 456,
      newHighs: 89,
      newLows: 23,
      advDeclRatio: 2.31,
      newHighLowRatio: 3.87
    },
    {
      index: 'NASDAQ',
      advancing: 1892,
      declining: 1456,
      unchanged: 234,
      newHighs: 67,
      newLows: 45,
      advDeclRatio: 1.30,
      newHighLowRatio: 1.49
    },
    {
      index: 'S&P 500',
      advancing: 312,
      declining: 188,
      unchanged: 0,
      newHighs: 23,
      newLows: 8,
      advDeclRatio: 1.66,
      newHighLowRatio: 2.88
    }
  ];

  const volatilityAnalysis: VolatilityAnalysis[] = [
    {
      symbol: 'SPY',
      currentVol: 12.5,
      avgVol: 15.2,
      volPercentile: 35,
      impliedVol: 18.3,
      historicalVol: 12.5,
      volTrend: 'decreasing'
    },
    {
      symbol: 'QQQ',
      currentVol: 18.7,
      avgVol: 22.1,
      volPercentile: 28,
      impliedVol: 25.4,
      historicalVol: 18.7,
      volTrend: 'decreasing'
    },
    {
      symbol: 'IWM',
      currentVol: 24.3,
      avgVol: 26.8,
      volPercentile: 45,
      impliedVol: 28.9,
      historicalVol: 24.3,
      volTrend: 'stable'
    },
    {
      symbol: 'VIX',
      currentVol: 18.5,
      avgVol: 20.1,
      volPercentile: 42,
      impliedVol: 0,
      historicalVol: 18.5,
      volTrend: 'decreasing'
    }
  ];

  const analyses = [
    { key: 'correlation', label: 'Correlation', icon: 'link' },
    { key: 'sectors', label: 'Sector Rotation', icon: 'layers' },
    { key: 'breadth', label: 'Market Breadth', icon: 'bar-chart' },
    { key: 'volatility', label: 'Volatility', icon: 'activity' }
  ];

  const getCorrelationColor = (correlation: number) => {
    const abs = Math.abs(correlation);
    if (abs >= 0.8) return '#10B981';
    if (abs >= 0.6) return '#F59E0B';
    if (abs >= 0.4) return '#6B7280';
    return '#EF4444';
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'increasing': return '#10B981';
      case 'decreasing': return '#EF4444';
      case 'stable': return '#6B7280';
      default: return '#6B7280';
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'increasing': return 'trending-up';
      case 'decreasing': return 'trending-down';
      case 'stable': return 'minus';
      default: return 'minus';
    }
  };

  const getMomentumColor = (momentum: number) => {
    if (momentum >= 0.7) return '#10B981';
    if (momentum >= 0.3) return '#F59E0B';
    if (momentum >= -0.3) return '#6B7280';
    return '#EF4444';
  };

  const getVolPercentileColor = (percentile: number) => {
    if (percentile >= 80) return '#EF4444';
    if (percentile >= 60) return '#F59E0B';
    if (percentile >= 40) return '#6B7280';
    if (percentile >= 20) return '#10B981';
    return '#3B82F6';
  };

  const renderCorrelation = () => (
    <View style={styles.content}>
      <View style={styles.sectionHeader}>
        <Icon name="link" size={20} color="#3B82F6" />
        <Text style={styles.sectionTitle}>Asset Correlation Analysis</Text>
        <Text style={styles.sectionSubtitle}>30-Day Rolling Correlation</Text>
      </View>
      
      {correlationData.map((corr, index) => (
        <View key={index} style={styles.correlationCard}>
          <View style={styles.correlationHeader}>
            <Text style={styles.correlationPair}>
              {corr.symbol1} ↔ {corr.symbol2}
            </Text>
            <View style={styles.correlationTrend}>
              <Icon 
                name={getTrendIcon(corr.trend)} 
                size={14} 
                color={getTrendColor(corr.trend)} 
              />
              <Text style={[styles.trendText, { color: getTrendColor(corr.trend) }]}>
                {corr.trend.toUpperCase()}
              </Text>
            </View>
          </View>
          
          <View style={styles.correlationValue}>
            <Text style={[styles.correlationNumber, { color: getCorrelationColor(corr.correlation) }]}>
              {corr.correlation.toFixed(3)}
            </Text>
            <Text style={styles.correlationPeriod}>{corr.period}</Text>
          </View>
          
          <View style={styles.correlationBar}>
            <View 
              style={[
                styles.correlationFill, 
                { 
                  width: `${Math.abs(corr.correlation) * 100}%`,
                  backgroundColor: getCorrelationColor(corr.correlation)
                }
              ]} 
            />
          </View>
        </View>
      ))}
    </View>
  );

  const renderSectorRotation = () => (
    <View style={styles.content}>
      <View style={styles.sectionHeader}>
        <Icon name="layers" size={20} color="#10B981" />
        <Text style={styles.sectionTitle}>Sector Rotation Analysis</Text>
        <Text style={styles.sectionSubtitle}>Momentum & Strength</Text>
      </View>
      
      {sectorRotation.map((sector, index) => (
        <View key={index} style={styles.sectorCard}>
          <View style={styles.sectorHeader}>
            <View style={styles.sectorInfo}>
              <Text style={styles.sectorName}>{sector.sector}</Text>
              <Text style={styles.sectorSymbol}>{sector.symbol}</Text>
            </View>
            <View style={[styles.trendBadge, { backgroundColor: getMomentumColor(sector.momentum) }]}>
              <Icon 
                name={getTrendIcon(sector.trend)} 
                size={12} 
                color="#FFFFFF" 
              />
              <Text style={styles.badgeText}>{sector.trend.toUpperCase()}</Text>
            </View>
          </View>
          
          <View style={styles.sectorMetrics}>
            <View style={styles.metric}>
              <Text style={styles.metricLabel}>Momentum</Text>
              <Text style={[styles.metricValue, { color: getMomentumColor(sector.momentum) }]}>
                {(sector.momentum * 100).toFixed(0)}%
              </Text>
            </View>
            <View style={styles.metric}>
              <Text style={styles.metricLabel}>Strength</Text>
              <Text style={[styles.metricValue, { color: getMomentumColor(sector.strength / 100) }]}>
                {sector.strength}%
              </Text>
            </View>
          </View>
          
          <View style={styles.strengthBar}>
            <View 
              style={[
                styles.strengthFill, 
                { 
                  width: `${sector.strength}%`,
                  backgroundColor: getMomentumColor(sector.strength / 100)
                }
              ]} 
            />
          </View>
          
          <Text style={styles.sectorDescription}>{sector.description}</Text>
        </View>
      ))}
    </View>
  );

  const renderMarketBreadth = () => (
    <View style={styles.content}>
      <View style={styles.sectionHeader}>
        <Icon name="bar-chart" size={20} color="#F59E0B" />
        <Text style={styles.sectionTitle}>Market Breadth Analysis</Text>
        <Text style={styles.sectionSubtitle}>Advance/Decline Metrics</Text>
      </View>
      
      {marketBreadth.map((breadth, index) => (
        <View key={index} style={styles.breadthCard}>
          <Text style={styles.breadthIndex}>{breadth.index}</Text>
          
          <View style={styles.breadthStats}>
            <View style={styles.breadthStat}>
              <Text style={styles.breadthNumber}>{breadth.advancing.toLocaleString()}</Text>
              <Text style={styles.breadthLabel}>Advancing</Text>
            </View>
            <View style={styles.breadthStat}>
              <Text style={styles.breadthNumber}>{breadth.declining.toLocaleString()}</Text>
              <Text style={styles.breadthLabel}>Declining</Text>
            </View>
            <View style={styles.breadthStat}>
              <Text style={styles.breadthNumber}>{breadth.unchanged.toLocaleString()}</Text>
              <Text style={styles.breadthLabel}>Unchanged</Text>
            </View>
          </View>
          
          <View style={styles.breadthRatios}>
            <View style={styles.ratioItem}>
              <Text style={styles.ratioLabel}>A/D Ratio</Text>
              <Text style={[styles.ratioValue, { color: breadth.advDeclRatio > 1 ? '#10B981' : '#EF4444' }]}>
                {breadth.advDeclRatio.toFixed(2)}
              </Text>
            </View>
            <View style={styles.ratioItem}>
              <Text style={styles.ratioLabel}>New High/Low</Text>
              <Text style={[styles.ratioValue, { color: breadth.newHighLowRatio > 1 ? '#10B981' : '#EF4444' }]}>
                {breadth.newHighLowRatio.toFixed(2)}
              </Text>
            </View>
          </View>
        </View>
      ))}
    </View>
  );

  const renderVolatility = () => (
    <View style={styles.content}>
      <View style={styles.sectionHeader}>
        <Icon name="activity" size={20} color="#8B5CF6" />
        <Text style={styles.sectionTitle}>Volatility Analysis</Text>
        <Text style={styles.sectionSubtitle}>Current vs Historical</Text>
      </View>
      
      {volatilityAnalysis.map((vol, index) => (
        <View key={index} style={styles.volatilityCard}>
          <View style={styles.volatilityHeader}>
            <Text style={styles.volatilitySymbol}>{vol.symbol}</Text>
            <View style={styles.volatilityTrend}>
              <Icon 
                name={getTrendIcon(vol.volTrend)} 
                size={14} 
                color={getTrendColor(vol.volTrend)} 
              />
              <Text style={[styles.trendText, { color: getTrendColor(vol.volTrend) }]}>
                {vol.volTrend.toUpperCase()}
              </Text>
            </View>
          </View>
          
          <View style={styles.volatilityMetrics}>
            <View style={styles.volMetric}>
              <Text style={styles.volLabel}>Current Vol</Text>
              <Text style={styles.volValue}>{vol.currentVol.toFixed(1)}%</Text>
            </View>
            <View style={styles.volMetric}>
              <Text style={styles.volLabel}>Avg Vol</Text>
              <Text style={styles.volValue}>{vol.avgVol.toFixed(1)}%</Text>
            </View>
            <View style={styles.volMetric}>
              <Text style={styles.volLabel}>Percentile</Text>
              <Text style={[styles.volValue, { color: getVolPercentileColor(vol.volPercentile) }]}>
                {vol.volPercentile}%
              </Text>
            </View>
          </View>
          
          <View style={styles.volatilityComparison}>
            <View style={styles.comparisonItem}>
              <Text style={styles.comparisonLabel}>Implied Vol</Text>
              <Text style={styles.comparisonValue}>{vol.impliedVol.toFixed(1)}%</Text>
            </View>
            <View style={styles.comparisonItem}>
              <Text style={styles.comparisonLabel}>Historical Vol</Text>
              <Text style={styles.comparisonValue}>{vol.historicalVol.toFixed(1)}%</Text>
            </View>
          </View>
        </View>
      ))}
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Analysis Selector */}
      <View style={styles.analysisSelector}>
        {analyses.map((analysis) => (
          <TouchableOpacity
            key={analysis.key}
            style={[
              styles.analysisButton,
              selectedAnalysis === analysis.key && styles.analysisButtonActive
            ]}
            onPress={() => setSelectedAnalysis(analysis.key)}
          >
            <Icon 
              name={analysis.icon as any} 
              size={16} 
              color={selectedAnalysis === analysis.key ? '#FFFFFF' : '#6B7280'} 
            />
            <Text style={[
              styles.analysisText,
              selectedAnalysis === analysis.key && styles.analysisTextActive
            ]}>
              {analysis.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {selectedAnalysis === 'correlation' && renderCorrelation()}
        {selectedAnalysis === 'sectors' && renderSectorRotation()}
        {selectedAnalysis === 'breadth' && renderMarketBreadth()}
        {selectedAnalysis === 'volatility' && renderVolatility()}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  analysisSelector: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    marginHorizontal: 16,
    marginTop: 16,
    borderRadius: 12,
    padding: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  analysisButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 8,
  },
  analysisButtonActive: {
    backgroundColor: '#3B82F6',
  },
  analysisText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
    marginLeft: 4,
  },
  analysisTextActive: {
    color: '#FFFFFF',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 16,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginLeft: 8,
  },
  sectionSubtitle: {
    fontSize: 12,
    color: '#6B7280',
    marginLeft: 'auto',
  },
  correlationCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  correlationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  correlationPair: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  correlationTrend: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  trendText: {
    fontSize: 10,
    fontWeight: '700',
    marginLeft: 4,
  },
  correlationValue: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  correlationNumber: {
    fontSize: 24,
    fontWeight: '700',
    marginRight: 8,
  },
  correlationPeriod: {
    fontSize: 12,
    color: '#6B7280',
  },
  correlationBar: {
    width: '100%',
    height: 6,
    backgroundColor: '#F3F4F6',
    borderRadius: 3,
  },
  correlationFill: {
    height: '100%',
    borderRadius: 3,
  },
  sectorCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  sectorHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  sectorInfo: {
    flex: 1,
  },
  sectorName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  sectorSymbol: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  trendBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#FFFFFF',
    marginLeft: 2,
  },
  sectorMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  metric: {
    alignItems: 'center',
  },
  metricLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: '700',
  },
  strengthBar: {
    width: '100%',
    height: 4,
    backgroundColor: '#F3F4F6',
    borderRadius: 2,
    marginBottom: 8,
  },
  strengthFill: {
    height: '100%',
    borderRadius: 2,
  },
  sectorDescription: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
  breadthCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  breadthIndex: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 16,
    textAlign: 'center',
  },
  breadthStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  breadthStat: {
    alignItems: 'center',
  },
  breadthNumber: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  breadthLabel: {
    fontSize: 10,
    color: '#6B7280',
    marginTop: 2,
  },
  breadthRatios: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  ratioItem: {
    alignItems: 'center',
  },
  ratioLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  ratioValue: {
    fontSize: 16,
    fontWeight: '700',
  },
  volatilityCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  volatilityHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  volatilitySymbol: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  volatilityTrend: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  volatilityMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  volMetric: {
    alignItems: 'center',
  },
  volLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  volValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  volatilityComparison: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
  },
  comparisonItem: {
    alignItems: 'center',
  },
  comparisonLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  comparisonValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
});

export default SwingTradingAdvancedAnalytics;
