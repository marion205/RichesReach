import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import intelligentPriceAlertService, { IntelligentAlert, StockPrice, MarketConditions } from '../services/IntelligentPriceAlertService';

const IntelligentAlertDemo: React.FC = () => {
  const [alerts, setAlerts] = useState<IntelligentAlert[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Sample data for demonstration
  const sampleStocks: { [key: string]: StockPrice[] } = {
    'AAPL': [
      { symbol: 'AAPL', price: 150.00, change: -2.50, change_percent: -1.64, volume: 45000000, timestamp: Date.now() - 86400000 * 5 },
      { symbol: 'AAPL', price: 148.50, change: -1.50, change_percent: -1.00, volume: 42000000, timestamp: Date.now() - 86400000 * 4 },
      { symbol: 'AAPL', price: 147.00, change: -1.50, change_percent: -1.01, volume: 48000000, timestamp: Date.now() - 86400000 * 3 },
      { symbol: 'AAPL', price: 145.50, change: -1.50, change_percent: -1.02, volume: 52000000, timestamp: Date.now() - 86400000 * 2 },
      { symbol: 'AAPL', price: 144.00, change: -1.50, change_percent: -1.03, volume: 55000000, timestamp: Date.now() - 86400000 * 1 },
      { symbol: 'AAPL', price: 142.50, change: -1.50, change_percent: -1.04, volume: 60000000, timestamp: Date.now() },
    ],
    'TSLA': [
      { symbol: 'TSLA', price: 200.00, change: 5.00, change_percent: 2.56, volume: 80000000, timestamp: Date.now() - 86400000 * 5 },
      { symbol: 'TSLA', price: 205.00, change: 5.00, change_percent: 2.50, volume: 85000000, timestamp: Date.now() - 86400000 * 4 },
      { symbol: 'TSLA', price: 210.00, change: 5.00, change_percent: 2.44, volume: 90000000, timestamp: Date.now() - 86400000 * 3 },
      { symbol: 'TSLA', price: 215.00, change: 5.00, change_percent: 2.38, volume: 95000000, timestamp: Date.now() - 86400000 * 2 },
      { symbol: 'TSLA', price: 220.00, change: 5.00, change_percent: 2.33, volume: 100000000, timestamp: Date.now() - 86400000 * 1 },
      { symbol: 'TSLA', price: 225.00, change: 5.00, change_percent: 2.27, volume: 110000000, timestamp: Date.now() },
    ],
  };

  const sampleMarketConditions: MarketConditions = {
    marketTrend: 'bullish',
    volatility: 'medium',
    volume: 'normal',
    sectorPerformance: 2.5,
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  const loadAlerts = async () => {
    try {
      const activeAlerts = await intelligentPriceAlertService.getActiveAlerts();
      setAlerts(activeAlerts);
    } catch (error) {
      console.error('Error loading alerts:', error);
    }
  };

  const runAnalysis = async () => {
    setIsAnalyzing(true);
    
    try {
      const newAlerts: IntelligentAlert[] = [];
      
      // Analyze each stock
      for (const [symbol, historicalData] of Object.entries(sampleStocks)) {
        const currentPrice = historicalData[historicalData.length - 1];
        const stockAlerts = await intelligentPriceAlertService.analyzeStock(
          symbol,
          currentPrice,
          historicalData,
          sampleMarketConditions
        );
        newAlerts.push(...stockAlerts);
      }
      
      setAlerts(newAlerts);
      
      if (newAlerts.length > 0) {
        Alert.alert(
          'Analysis Complete',
          `Found ${newAlerts.length} intelligent trading opportunities!`,
          [{ text: 'OK' }]
        );
      } else {
        Alert.alert(
          'Analysis Complete',
          'No strong opportunities found at this time. The AI is being selective!',
          [{ text: 'OK' }]
        );
      }
    } catch (error) {
      Alert.alert('Error', 'Failed to run analysis. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'buy_opportunity':
        return 'trending-up';
      case 'sell_signal':
        return 'trending-down';
      case 'technical_breakout':
        return 'zap';
      default:
        return 'alert-circle';
    }
  };

  const getAlertColor = (type: string) => {
    switch (type) {
      case 'buy_opportunity':
        return '#34C759';
      case 'sell_signal':
        return '#FF3B30';
      case 'technical_breakout':
        return '#FF9500';
      default:
        return '#007AFF';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return '#34C759';
    if (confidence >= 60) return '#FF9500';
    return '#FF3B30';
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.header}>
        <Icon name="cpu" size={32} color="#007AFF" />
        <Text style={styles.title}>AI Stock Analysis</Text>
        <Text style={styles.subtitle}>
          Intelligent algorithms analyze technical indicators, market conditions, and your profile
        </Text>
      </View>

      <TouchableOpacity
        style={[styles.analyzeButton, isAnalyzing && styles.analyzeButtonDisabled]}
        onPress={runAnalysis}
        disabled={isAnalyzing}
      >
        <Icon name={isAnalyzing ? "loader" : "play"} size={20} color="#FFFFFF" />
        <Text style={styles.analyzeButtonText}>
          {isAnalyzing ? 'Analyzing...' : 'Run AI Analysis'}
        </Text>
      </TouchableOpacity>

      {alerts.length > 0 && (
        <View style={styles.alertsContainer}>
          <Text style={styles.alertsTitle}>AI Recommendations</Text>
          {alerts.map((alert) => (
            <View key={alert.id} style={styles.alertCard}>
              <View style={styles.alertHeader}>
                <View style={styles.alertIconContainer}>
                  <Icon
                    name={getAlertIcon(alert.alertType)}
                    size={24}
                    color={getAlertColor(alert.alertType)}
                  />
                </View>
                <View style={styles.alertInfo}>
                  <Text style={styles.alertSymbol}>{alert.symbol}</Text>
                  <Text style={styles.alertType}>
                    {alert.alertType.replace('_', ' ').toUpperCase()}
                  </Text>
                </View>
                <View style={styles.confidenceContainer}>
                  <Text style={[
                    styles.confidenceText,
                    { color: getConfidenceColor(alert.confidence) }
                  ]}>
                    {alert.confidence}%
                  </Text>
                  <Text style={styles.confidenceLabel}>Confidence</Text>
                </View>
              </View>

              <Text style={styles.alertReason}>{alert.reason}</Text>

              <View style={styles.scoresContainer}>
                <View style={styles.scoreItem}>
                  <Text style={styles.scoreLabel}>Technical</Text>
                  <Text style={styles.scoreValue}>{alert.technicalScore}%</Text>
                </View>
                <View style={styles.scoreItem}>
                  <Text style={styles.scoreLabel}>Market</Text>
                  <Text style={styles.scoreValue}>{alert.marketScore}%</Text>
                </View>
                <View style={styles.scoreItem}>
                  <Text style={styles.scoreLabel}>Profile</Text>
                  <Text style={styles.scoreValue}>{alert.userScore}%</Text>
                </View>
              </View>

              {alert.targetPrice && (
                <View style={styles.priceInfo}>
                  <Text style={styles.priceLabel}>Target Price:</Text>
                  <Text style={styles.priceValue}>${alert.targetPrice.toFixed(2)}</Text>
                </View>
              )}

              {alert.stopLoss && (
                <View style={styles.priceInfo}>
                  <Text style={styles.priceLabel}>Stop Loss:</Text>
                  <Text style={styles.priceValue}>${alert.stopLoss.toFixed(2)}</Text>
                </View>
              )}

              <View style={styles.alertActions}>
                <TouchableOpacity style={styles.actionButton}>
                  <Icon name="eye" size={16} color="#007AFF" />
                  <Text style={styles.actionButtonText}>View Details</Text>
                </TouchableOpacity>
                <TouchableOpacity style={styles.actionButton}>
                  <Icon name="bell" size={16} color="#007AFF" />
                  <Text style={styles.actionButtonText}>Set Alert</Text>
                </TouchableOpacity>
              </View>
            </View>
          ))}
        </View>
      )}

      <View style={styles.algorithmExplanation}>
        <Text style={styles.explanationTitle}>How the AI Algorithm Works</Text>
        
        <View style={styles.algorithmStep}>
          <Text style={styles.stepNumber}>1</Text>
          <View style={styles.stepContent}>
            <Text style={styles.stepTitle}>Technical Analysis</Text>
            <Text style={styles.stepDescription}>
              Analyzes RSI, MACD, Bollinger Bands, moving averages, and volume patterns
            </Text>
          </View>
        </View>

        <View style={styles.algorithmStep}>
          <Text style={styles.stepNumber}>2</Text>
          <View style={styles.stepContent}>
            <Text style={styles.stepTitle}>Market Conditions</Text>
            <Text style={styles.stepDescription}>
              Evaluates market trend, volatility, and sector performance
            </Text>
          </View>
        </View>

        <View style={styles.algorithmStep}>
          <Text style={styles.stepNumber}>3</Text>
          <View style={styles.stepContent}>
            <Text style={styles.stepTitle}>Personal Profile</Text>
            <Text style={styles.stepDescription}>
              Matches opportunities to your risk tolerance and investment style
            </Text>
          </View>
        </View>

        <View style={styles.algorithmStep}>
          <Text style={styles.stepNumber}>4</Text>
          <View style={styles.stepContent}>
            <Text style={styles.stepTitle}>Confidence Scoring</Text>
            <Text style={styles.stepDescription}>
              Combines all factors into a confidence score (0-100%)
            </Text>
          </View>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  header: {
    alignItems: 'center',
    padding: 24,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
    marginTop: 12,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#6C757D',
    textAlign: 'center',
    lineHeight: 24,
  },
  analyzeButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    padding: 16,
    margin: 20,
    borderRadius: 12,
  },
  analyzeButtonDisabled: {
    backgroundColor: '#8E8E93',
  },
  analyzeButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  alertsContainer: {
    padding: 20,
  },
  alertsTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 16,
  },
  alertCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  alertHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  alertIconContainer: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#F0F8FF',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  alertInfo: {
    flex: 1,
  },
  alertSymbol: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  alertType: {
    fontSize: 12,
    color: '#6C757D',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  confidenceContainer: {
    alignItems: 'center',
  },
  confidenceText: {
    fontSize: 20,
    fontWeight: '700',
  },
  confidenceLabel: {
    fontSize: 10,
    color: '#6C757D',
    textTransform: 'uppercase',
  },
  alertReason: {
    fontSize: 14,
    color: '#1C1C1E',
    lineHeight: 20,
    marginBottom: 12,
  },
  scoresContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 12,
    paddingVertical: 12,
    backgroundColor: '#F8F9FA',
    borderRadius: 8,
  },
  scoreItem: {
    alignItems: 'center',
  },
  scoreLabel: {
    fontSize: 12,
    color: '#6C757D',
    marginBottom: 4,
  },
  scoreValue: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  priceInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  priceLabel: {
    fontSize: 14,
    color: '#6C757D',
  },
  priceValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  alertActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#007AFF',
  },
  actionButtonText: {
    fontSize: 14,
    color: '#007AFF',
    marginLeft: 4,
  },
  algorithmExplanation: {
    backgroundColor: '#FFFFFF',
    margin: 20,
    padding: 20,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  explanationTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 16,
  },
  algorithmStep: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  stepNumber: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#007AFF',
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
    textAlign: 'center',
    lineHeight: 24,
    marginRight: 12,
  },
  stepContent: {
    flex: 1,
  },
  stepTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  stepDescription: {
    fontSize: 14,
    color: '#6C757D',
    lineHeight: 20,
  },
});

export default IntelligentAlertDemo;
