import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import EducationalTooltip from './EducationalTooltip';
import { getTermExplanation } from '../data/financialTerms';

interface Holding {
  symbol: string;
  companyName: string;
  shares: number;
  currentPrice: number;
  totalValue: number;
  costBasis: number;
  returnAmount: number;
  returnPercent: number;
  sector: string;
}

interface BasicRiskMetricsProps {
  holdings: Holding[];
  totalValue: number;
  totalReturn: number;
  totalReturnPercent: number;
}

const BasicRiskMetrics: React.FC<BasicRiskMetricsProps> = ({
  holdings,
  totalValue,
  totalReturn,
  totalReturnPercent,
}) => {
  // Calculate basic risk metrics
  const calculateDiversificationScore = () => {
    if (holdings.length === 0) return 0;
    
    // Count unique sectors
    const sectors = new Set(holdings.map(h => h.sector));
    const sectorCount = sectors.size;
    const totalHoldings = holdings.length;
    
    // Simple diversification score (0-100)
    // More sectors and more holdings = better diversification
    const sectorScore = Math.min(sectorCount * 20, 60); // Max 60 points for sectors
    const holdingsScore = Math.min(totalHoldings * 5, 40); // Max 40 points for holdings
    
    return Math.round(sectorScore + holdingsScore);
  };

  const calculateVolatility = () => {
    if (holdings.length === 0) return 0;
    
    // Simple volatility calculation based on return percentages
    const returns = holdings.map(h => h.returnPercent);
    const avgReturn = returns.reduce((sum, ret) => sum + ret, 0) / returns.length;
    
    // Calculate standard deviation
    const variance = returns.reduce((sum, ret) => sum + Math.pow(ret - avgReturn, 2), 0) / returns.length;
    const volatility = Math.sqrt(variance);
    
    return Math.round(volatility * 10) / 10; // Round to 1 decimal
  };

  const getRiskLevel = (volatility: number) => {
    if (volatility < 5) return { level: 'Low', color: '#34C759', icon: 'shield' };
    if (volatility < 15) return { level: 'Medium', color: '#FF9500', icon: 'alert-triangle' };
    return { level: 'High', color: '#FF3B30', icon: 'alert-circle' };
  };

  const getDiversificationLevel = (score: number) => {
    if (score >= 80) return { level: 'Excellent', color: '#34C759', icon: 'check-circle' };
    if (score >= 60) return { level: 'Good', color: '#32D74B', icon: 'thumbs-up' };
    if (score >= 40) return { level: 'Fair', color: '#FF9500', icon: 'minus-circle' };
    return { level: 'Poor', color: '#FF3B30', icon: 'x-circle' };
  };

  const diversificationScore = calculateDiversificationScore();
  const volatility = calculateVolatility();
  const riskLevel = getRiskLevel(volatility);
  const diversificationLevel = getDiversificationLevel(diversificationScore);

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.titleContainer}>
          <Icon name="bar-chart-2" size={20} color="#007AFF" />
          <Text style={styles.title}>Risk & Diversification</Text>
        </View>
        <Text style={styles.subtitle}>Free Analysis</Text>
      </View>

      <View style={styles.metricsContainer}>
        {/* Diversification Score */}
        <View style={styles.metricCard}>
          <EducationalTooltip
            term="Diversification"
            explanation={getTermExplanation('Diversification')}
            position="top"
          >
            <View style={styles.metricHeader}>
              <Icon name={diversificationLevel.icon} size={16} color={diversificationLevel.color} />
              <Text style={styles.metricTitle}>Diversification</Text>
            </View>
          </EducationalTooltip>
          
          <View style={styles.metricContent}>
            <Text style={[styles.metricValue, { color: diversificationLevel.color }]}>
              {diversificationScore}/100
            </Text>
            <Text style={[styles.metricLevel, { color: diversificationLevel.color }]}>
              {diversificationLevel.level}
            </Text>
          </View>
          
          <View style={styles.progressBar}>
            <View 
              style={[
                styles.progressFill, 
                { 
                  width: `${diversificationScore}%`,
                  backgroundColor: diversificationLevel.color 
                }
              ]} 
            />
          </View>
          
          <Text style={styles.metricDescription}>
            {holdings.length} holdings across {new Set(holdings.map(h => h.sector)).size} sectors
          </Text>
        </View>

        {/* Volatility */}
        <View style={styles.metricCard}>
          <EducationalTooltip
            term="Volatility"
            explanation={getTermExplanation('Volatility')}
            position="top"
          >
            <View style={styles.metricHeader}>
              <Icon name={riskLevel.icon} size={16} color={riskLevel.color} />
              <Text style={styles.metricTitle}>Volatility</Text>
            </View>
          </EducationalTooltip>
          
          <View style={styles.metricContent}>
            <Text style={[styles.metricValue, { color: riskLevel.color }]}>
              {volatility}%
            </Text>
            <Text style={[styles.metricLevel, { color: riskLevel.color }]}>
              {riskLevel.level} Risk
            </Text>
          </View>
          
          <View style={styles.riskBar}>
            <View style={[styles.riskIndicator, { 
              left: `${Math.min(volatility * 2, 100)}%`,
              backgroundColor: riskLevel.color 
            }]} />
          </View>
          
          <Text style={styles.metricDescription}>
            Based on your holdings' price movements
          </Text>
        </View>
      </View>

      {/* Upgrade Prompt */}
      <TouchableOpacity style={styles.upgradePrompt}>
        <View style={styles.upgradeContent}>
          <Icon name="star" size={16} color="#FFD60A" />
          <Text style={styles.upgradeText}>
            Unlock advanced analytics with Premium
          </Text>
        </View>
        <Icon name="chevron-right" size={16} color="#8E8E93" />
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  subtitle: {
    fontSize: 12,
    color: '#8E8E93',
    backgroundColor: '#F2F2F7',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
  },
  metricsContainer: {
    gap: 16,
  },
  metricCard: {
    backgroundColor: '#F8F9FA',
    borderRadius: 12,
    padding: 16,
  },
  metricHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  metricTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1C1C1E',
  },
  metricContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  metricValue: {
    fontSize: 24,
    fontWeight: '700',
  },
  metricLevel: {
    fontSize: 14,
    fontWeight: '600',
  },
  progressBar: {
    height: 6,
    backgroundColor: '#E5E5EA',
    borderRadius: 3,
    marginBottom: 8,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 3,
  },
  riskBar: {
    height: 6,
    backgroundColor: '#E5E5EA',
    borderRadius: 3,
    marginBottom: 8,
    position: 'relative',
  },
  riskIndicator: {
    position: 'absolute',
    top: -2,
    width: 10,
    height: 10,
    borderRadius: 5,
    borderWidth: 2,
    borderColor: '#FFFFFF',
  },
  metricDescription: {
    fontSize: 12,
    color: '#8E8E93',
    lineHeight: 16,
  },
  upgradePrompt: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#F2F2F7',
    borderRadius: 12,
    padding: 12,
    marginTop: 16,
  },
  upgradeContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  upgradeText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1C1C1E',
  },
});

export default BasicRiskMetrics;
