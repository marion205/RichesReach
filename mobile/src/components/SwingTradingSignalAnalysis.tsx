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

interface TechnicalIndicator {
  name: string;
  value: number;
  signal: 'bullish' | 'bearish' | 'neutral';
  strength: number; // 0-100
  description: string;
}

interface PatternRecognition {
  name: string;
  type: 'bullish' | 'bearish' | 'neutral';
  confidence: number;
  description: string;
  timeframe: string;
}

interface MLMetrics {
  overallScore: number;
  featureImportance: Array<{
    feature: string;
    importance: number;
    value: number;
  }>;
  modelConfidence: number;
  predictionAccuracy: number;
}

const SwingTradingSignalAnalysis: React.FC = () => {
  const [selectedTimeframe, setSelectedTimeframe] = useState('1d');

  // Mock data - in real app, this would come from API
  const technicalIndicators: TechnicalIndicator[] = [
    {
      name: 'RSI (14)',
      value: 28.5,
      signal: 'bullish',
      strength: 85,
      description: 'Oversold condition, potential reversal signal'
    },
    {
      name: 'MACD',
      value: 2.34,
      signal: 'bullish',
      strength: 72,
      description: 'Bullish crossover above signal line'
    },
    {
      name: 'EMA 12/26',
      value: 176.2,
      signal: 'bullish',
      strength: 68,
      description: 'EMA 12 above EMA 26, bullish momentum'
    },
    {
      name: 'Bollinger Bands',
      value: 175.5,
      signal: 'bullish',
      strength: 75,
      description: 'Price near lower band, potential bounce'
    },
    {
      name: 'Volume',
      value: 1.8,
      signal: 'bullish',
      strength: 80,
      description: 'Volume surge confirms price movement'
    },
    {
      name: 'ATR',
      value: 2.1,
      signal: 'neutral',
      strength: 50,
      description: 'Normal volatility range'
    },
    {
      name: 'Stochastic',
      value: 25.3,
      signal: 'bullish',
      strength: 78,
      description: 'Oversold with bullish divergence'
    },
    {
      name: 'Williams %R',
      value: -74.2,
      signal: 'bullish',
      strength: 82,
      description: 'Oversold territory, reversal likely'
    }
  ];

  const patterns: PatternRecognition[] = [
    {
      name: 'Double Bottom',
      type: 'bullish',
      confidence: 88,
      description: 'Classic reversal pattern with strong volume confirmation',
      timeframe: '1d'
    },
    {
      name: 'Hammer Candlestick',
      type: 'bullish',
      confidence: 75,
      description: 'Single candlestick reversal pattern at support',
      timeframe: '4h'
    },
    {
      name: 'Bullish Divergence',
      type: 'bullish',
      confidence: 82,
      description: 'Price making lower lows while RSI makes higher lows',
      timeframe: '1d'
    },
    {
      name: 'Volume Breakout',
      type: 'bullish',
      confidence: 90,
      description: 'Price breaking above resistance with 2x average volume',
      timeframe: '1h'
    }
  ];

  const mlMetrics: MLMetrics = {
    overallScore: 0.78,
    featureImportance: [
      { feature: 'RSI_14', importance: 0.25, value: 28.5 },
      { feature: 'Volume_Surge', importance: 0.20, value: 1.8 },
      { feature: 'EMA_Crossover', importance: 0.18, value: 1.4 },
      { feature: 'MACD_Signal', importance: 0.15, value: 2.34 },
      { feature: 'Bollinger_Position', importance: 0.12, value: 0.15 },
      { feature: 'ATR_Volatility', importance: 0.10, value: 2.1 }
    ],
    modelConfidence: 0.85,
    predictionAccuracy: 0.72
  };

  const timeframes = ['1h', '4h', '1d', '1w'];

  const getSignalColor = (signal: string) => {
    switch (signal) {
      case 'bullish': return '#10B981';
      case 'bearish': return '#EF4444';
      default: return '#6B7280';
    }
  };

  const getSignalIcon = (signal: string) => {
    switch (signal) {
      case 'bullish': return 'trending-up';
      case 'bearish': return 'trending-down';
      default: return 'minus';
    }
  };

  const getStrengthColor = (strength: number) => {
    if (strength >= 80) return '#10B981';
    if (strength >= 60) return '#F59E0B';
    if (strength >= 40) return '#6B7280';
    return '#EF4444';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return '#10B981';
    if (confidence >= 60) return '#F59E0B';
    return '#EF4444';
  };

  return (
    <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Timeframe Selector */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Icon name="clock" size={20} color="#3B82F6" />
          <Text style={styles.sectionTitle}>Timeframe Analysis</Text>
        </View>
        
        <View style={styles.timeframeSelector}>
          {timeframes.map((timeframe) => (
            <TouchableOpacity
              key={timeframe}
              style={[
                styles.timeframeButton,
                selectedTimeframe === timeframe && styles.timeframeButtonActive
              ]}
              onPress={() => setSelectedTimeframe(timeframe)}
            >
              <Text style={[
                styles.timeframeText,
                selectedTimeframe === timeframe && styles.timeframeTextActive
              ]}>
                {timeframe}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {/* ML Score Overview */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Icon name="cpu" size={20} color="#8B5CF6" />
          <Text style={styles.sectionTitle}>ML Analysis</Text>
          <Text style={styles.sectionSubtitle}>AI-Powered Signal</Text>
        </View>
        
        <View style={styles.mlOverview}>
          <View style={styles.mlScoreCard}>
            <Text style={styles.mlScoreLabel}>Overall Score</Text>
            <Text style={[styles.mlScoreValue, { color: getConfidenceColor(mlMetrics.overallScore * 100) }]}>
              {((mlMetrics.overallScore || 0) * 100).toFixed(0)}%
            </Text>
            <View style={styles.mlScoreBar}>
              <View 
                style={[
                  styles.mlScoreFill, 
                  { 
                    width: `${mlMetrics.overallScore * 100}%`,
                    backgroundColor: getConfidenceColor(mlMetrics.overallScore * 100)
                  }
                ]} 
              />
            </View>
          </View>

          <View style={styles.mlMetrics}>
            <View style={styles.mlMetric}>
              <Text style={styles.mlMetricLabel}>Model Confidence</Text>
              <Text style={[styles.mlMetricValue, { color: getConfidenceColor(mlMetrics.modelConfidence * 100) }]}>
                {((mlMetrics.modelConfidence || 0) * 100).toFixed(0)}%
              </Text>
            </View>
            <View style={styles.mlMetric}>
              <Text style={styles.mlMetricLabel}>Prediction Accuracy</Text>
              <Text style={[styles.mlMetricValue, { color: getConfidenceColor(mlMetrics.predictionAccuracy * 100) }]}>
                {((mlMetrics.predictionAccuracy || 0) * 100).toFixed(0)}%
              </Text>
            </View>
          </View>
        </View>
      </View>

      {/* Feature Importance */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Icon name="bar-chart-2" size={20} color="#10B981" />
          <Text style={styles.sectionTitle}>Feature Importance</Text>
          <Text style={styles.sectionSubtitle}>ML Model Weights</Text>
        </View>
        
        <View style={styles.featureList}>
          {mlMetrics.featureImportance.map((feature, index) => (
            <View key={index} style={styles.featureItem}>
              <View style={styles.featureInfo}>
                <Text style={styles.featureName}>{feature.feature.replace(/_/g, ' ')}</Text>
                <Text style={styles.featureValue}>Value: {(feature.value || 0).toFixed(2)}</Text>
              </View>
              <View style={styles.featureImportance}>
                <Text style={styles.importanceValue}>{((feature.importance || 0) * 100).toFixed(0)}%</Text>
                <View style={styles.importanceBar}>
                  <View 
                    style={[
                      styles.importanceFill, 
                      { width: `${feature.importance * 100}%` }
                    ]} 
                  />
                </View>
              </View>
            </View>
          ))}
        </View>
      </View>

      {/* Technical Indicators */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Icon name="activity" size={20} color="#F59E0B" />
          <Text style={styles.sectionTitle}>Technical Indicators</Text>
          <Text style={styles.sectionSubtitle}>Multi-Timeframe Analysis</Text>
        </View>
        
        <View style={styles.indicatorsGrid}>
          {technicalIndicators.map((indicator, index) => (
            <View key={index} style={styles.indicatorCard}>
              <View style={styles.indicatorHeader}>
                <Text style={styles.indicatorName}>{indicator.name}</Text>
                <View style={styles.indicatorSignal}>
                  <Icon 
                    name={getSignalIcon(indicator.signal)} 
                    size={16} 
                    color={getSignalColor(indicator.signal)} 
                  />
                  <Text style={[styles.signalText, { color: getSignalColor(indicator.signal) }]}>
                    {indicator.signal.toUpperCase()}
                  </Text>
                </View>
              </View>
              
              <Text style={styles.indicatorValue}>{(indicator.value || 0).toFixed(2)}</Text>
              
              <View style={styles.strengthContainer}>
                <Text style={styles.strengthLabel}>Strength</Text>
                <View style={styles.strengthBar}>
                  <View 
                    style={[
                      styles.strengthFill, 
                      { 
                        width: `${indicator.strength}%`,
                        backgroundColor: getStrengthColor(indicator.strength)
                      }
                    ]} 
                  />
                </View>
                <Text style={[styles.strengthValue, { color: getStrengthColor(indicator.strength) }]}>
                  {indicator.strength}%
                </Text>
              </View>
              
              <Text style={styles.indicatorDescription}>{indicator.description}</Text>
            </View>
          ))}
        </View>
      </View>

      {/* Pattern Recognition */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Icon name="layers" size={20} color="#EC4899" />
          <Text style={styles.sectionTitle}>Pattern Recognition</Text>
          <Text style={styles.sectionSubtitle}>Chart Pattern Analysis</Text>
        </View>
        
        <View style={styles.patternsList}>
          {patterns.map((pattern, index) => (
            <View key={index} style={styles.patternCard}>
              <View style={styles.patternHeader}>
                <View style={styles.patternInfo}>
                  <Text style={styles.patternName}>{pattern.name}</Text>
                  <Text style={styles.patternTimeframe}>{pattern.timeframe}</Text>
                </View>
                <View style={styles.patternConfidence}>
                  <Text style={[styles.confidenceValue, { color: getConfidenceColor(pattern.confidence) }]}>
                    {pattern.confidence}%
                  </Text>
                  <Text style={styles.confidenceLabel}>Confidence</Text>
                </View>
              </View>
              
              <View style={styles.patternType}>
                <Icon 
                  name={getSignalIcon(pattern.type)} 
                  size={16} 
                  color={getSignalColor(pattern.type)} 
                />
                <Text style={[styles.patternTypeText, { color: getSignalColor(pattern.type) }]}>
                  {pattern.type.toUpperCase()}
                </Text>
              </View>
              
              <Text style={styles.patternDescription}>{pattern.description}</Text>
            </View>
          ))}
        </View>
      </View>

      {/* Market Context */}
      <View style={styles.section}>
        <View style={styles.sectionHeader}>
          <Icon name="globe" size={20} color="#06B6D4" />
          <Text style={styles.sectionTitle}>Market Context</Text>
          <Text style={styles.sectionSubtitle}>Broader Market Analysis</Text>
        </View>
        
        <View style={styles.contextGrid}>
          <View style={styles.contextCard}>
            <Text style={styles.contextTitle}>Sector Rotation</Text>
            <Text style={styles.contextValue}>Technology Leading</Text>
            <Text style={styles.contextDescription}>XLK up 2.3% today</Text>
          </View>
          
          <View style={styles.contextCard}>
            <Text style={styles.contextTitle}>Market Breadth</Text>
            <Text style={styles.contextValue}>Bullish</Text>
            <Text style={styles.contextDescription}>2.3:1 A/D ratio</Text>
          </View>
          
          <View style={styles.contextCard}>
            <Text style={styles.contextTitle}>Volatility</Text>
            <Text style={styles.contextValue}>Low</Text>
            <Text style={styles.contextDescription}>VIX at 18.5</Text>
          </View>
          
          <View style={styles.contextCard}>
            <Text style={styles.contextTitle}>Sentiment</Text>
            <Text style={styles.contextValue}>Greed</Text>
            <Text style={styles.contextDescription}>Fear & Greed: 65</Text>
          </View>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  section: {
    marginBottom: 24,
    paddingHorizontal: 16,
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
  timeframeSelector: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  timeframeButton: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  timeframeButtonActive: {
    backgroundColor: '#3B82F6',
  },
  timeframeText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
  },
  timeframeTextActive: {
    color: '#FFFFFF',
  },
  mlOverview: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  mlScoreCard: {
    alignItems: 'center',
    marginBottom: 20,
  },
  mlScoreLabel: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 8,
  },
  mlScoreValue: {
    fontSize: 36,
    fontWeight: '700',
    marginBottom: 12,
  },
  mlScoreBar: {
    width: '100%',
    height: 8,
    backgroundColor: '#F3F4F6',
    borderRadius: 4,
  },
  mlScoreFill: {
    height: '100%',
    borderRadius: 4,
  },
  mlMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  mlMetric: {
    alignItems: 'center',
  },
  mlMetricLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  mlMetricValue: {
    fontSize: 18,
    fontWeight: '700',
  },
  featureList: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  featureItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  featureInfo: {
    flex: 1,
  },
  featureName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
    textTransform: 'capitalize',
  },
  featureValue: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  featureImportance: {
    alignItems: 'flex-end',
    width: 80,
  },
  importanceValue: {
    fontSize: 14,
    fontWeight: '700',
    color: '#3B82F6',
    marginBottom: 4,
  },
  importanceBar: {
    width: '100%',
    height: 4,
    backgroundColor: '#F3F4F6',
    borderRadius: 2,
  },
  importanceFill: {
    height: '100%',
    backgroundColor: '#3B82F6',
    borderRadius: 2,
  },
  indicatorsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  indicatorCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    width: (width - 48) / 2,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  indicatorHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  indicatorName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  indicatorSignal: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  signalText: {
    fontSize: 10,
    fontWeight: '700',
    marginLeft: 4,
  },
  indicatorValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
  },
  strengthContainer: {
    marginBottom: 8,
  },
  strengthLabel: {
    fontSize: 10,
    color: '#6B7280',
    marginBottom: 4,
  },
  strengthBar: {
    width: '100%',
    height: 4,
    backgroundColor: '#F3F4F6',
    borderRadius: 2,
    marginBottom: 4,
  },
  strengthFill: {
    height: '100%',
    borderRadius: 2,
  },
  strengthValue: {
    fontSize: 12,
    fontWeight: '600',
  },
  indicatorDescription: {
    fontSize: 11,
    color: '#6B7280',
    lineHeight: 16,
  },
  patternsList: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  patternCard: {
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  patternHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  patternInfo: {
    flex: 1,
  },
  patternName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  patternTimeframe: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  patternConfidence: {
    alignItems: 'flex-end',
  },
  confidenceValue: {
    fontSize: 18,
    fontWeight: '700',
  },
  confidenceLabel: {
    fontSize: 10,
    color: '#6B7280',
  },
  patternType: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  patternTypeText: {
    fontSize: 12,
    fontWeight: '700',
    marginLeft: 4,
  },
  patternDescription: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
  contextGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  contextCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    width: (width - 48) / 2,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  contextTitle: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  contextValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 4,
  },
  contextDescription: {
    fontSize: 12,
    color: '#6B7280',
  },
});

export default SwingTradingSignalAnalysis;
