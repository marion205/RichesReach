import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  Dimensions,
  TouchableOpacity,
  ScrollView,
  Alert,
  Modal,
  StatusBar,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
// import { BlurView } from 'expo-blur'; // Removed for Expo Go compatibility
// import LottieView from 'lottie-react-native'; // Removed for Expo Go compatibility
import Svg, { Circle, Path, G, Text as SvgText } from 'react-native-svg';

const { width } = Dimensions.get('window');

interface WellnessScoreDashboardProps {
  portfolio: any;
  onActionPress: (action: string) => void;
  onClose: () => void;
}

export default function WellnessScoreDashboard({ portfolio, onActionPress, onClose }: WellnessScoreDashboardProps) {
  const [wellnessScore, setWellnessScore] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null);
  
  // Animation values
  const scoreAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const rotationAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    // Calculate wellness score based on portfolio metrics
    const score = calculateWellnessScore(portfolio);
    setWellnessScore(score);
    
    // Animate score increase
    setIsAnimating(true);
    Animated.timing(scoreAnim, {
      toValue: score,
      duration: 2000,
      useNativeDriver: false,
    }).start(() => {
      setIsAnimating(false);
    });

    // Start pulse animation
    startPulseAnimation();
  }, [portfolio]);

  const startPulseAnimation = () => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.1,
          duration: 1000,
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1000,
          useNativeDriver: true,
        }),
      ])
    ).start();
  };

  const calculateWellnessScore = (portfolio: any) => {
    // AI-powered wellness calculation
    const metrics = {
      diversification: calculateDiversificationScore(portfolio),
      riskManagement: calculateRiskScore(portfolio),
      taxEfficiency: calculateTaxEfficiencyScore(portfolio),
      performance: calculatePerformanceScore(portfolio),
      liquidity: calculateLiquidityScore(portfolio),
    };

    // Weighted average with AI insights
    const weights = {
      diversification: 0.25,
      riskManagement: 0.25,
      taxEfficiency: 0.20,
      performance: 0.20,
      liquidity: 0.10,
    };

    const score = Object.entries(metrics).reduce((total, [key, value]) => {
      return total + (value * weights[key as keyof typeof weights]);
    }, 0);

    return Math.round(score);
  };

  const calculateDiversificationScore = (portfolio: any) => {
    // Calculate based on asset allocation spread
    const assets = portfolio?.allocation || {};
    const assetCount = Object.keys(assets).length;
    const maxWeight = Math.max(...Object.values(assets) as number[]);
    
    // Penalize over-concentration
    const concentrationPenalty = maxWeight > 50 ? (maxWeight - 50) * 0.5 : 0;
    const diversificationBonus = Math.min(assetCount * 10, 30);
    
    return Math.round(Math.max(0, 70 + diversificationBonus - concentrationPenalty));
  };

  const calculateRiskScore = (portfolio: any) => {
    // Calculate based on risk metrics
    const volatility = portfolio?.volatility || 15;
    const maxDrawdown = portfolio?.maxDrawdown || 10;
    const sharpeRatio = portfolio?.sharpeRatio || 1.0;
    
    // Risk scoring algorithm
    const volatilityScore = Math.max(0, 100 - volatility * 2);
    const drawdownScore = Math.max(0, 100 - maxDrawdown * 3);
    const sharpeScore = Math.min(100, sharpeRatio * 30);
    
    return Math.round((volatilityScore + drawdownScore + sharpeScore) / 3);
  };

  const calculateTaxEfficiencyScore = (portfolio: any) => {
    // Calculate based on tax optimization
    const taxLossHarvesting = portfolio?.taxLossHarvesting || false;
    const taxAdvantagedAccounts = portfolio?.taxAdvantagedAccounts || 0;
    const capitalGainsRate = portfolio?.capitalGainsRate || 20;
    
    let score = 50; // Base score
    
    if (taxLossHarvesting) score += 20;
    if (taxAdvantagedAccounts > 0) score += 15;
    if (capitalGainsRate < 15) score += 15;
    
    return Math.round(Math.min(100, score));
  };

  const calculatePerformanceScore = (portfolio: any) => {
    // Calculate based on performance metrics
    const returns = portfolio?.returns || {};
    const ytdReturn = returns.ytd || 0;
    const benchmarkReturn = returns.benchmark || 8;
    
    const outperformance = ytdReturn - benchmarkReturn;
    const score = 50 + (outperformance * 2);
    
    return Math.round(Math.max(0, Math.min(100, score)));
  };

  const calculateLiquidityScore = (portfolio: any) => {
    // Calculate based on liquidity metrics
    const cashPercentage = portfolio?.allocation?.cash || 0;
    const liquidAssets = portfolio?.liquidAssets || 0;
    
    let score = 50;
    
    if (cashPercentage > 5 && cashPercentage < 20) score += 20;
    if (liquidAssets > 80) score += 20;
    if (cashPercentage > 20) score -= 10; // Too much cash
    
    return Math.round(Math.max(0, Math.min(100, score)));
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return '#34C759';
    if (score >= 60) return '#FF9500';
    if (score >= 40) return '#FF3B30';
    return '#8E8E93';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 90) return 'Exceptional';
    if (score >= 80) return 'Excellent';
    if (score >= 70) return 'Good';
    if (score >= 60) return 'Fair';
    if (score >= 40) return 'Needs Attention';
    return 'Critical';
  };

  const getScoreEmoji = (score: number) => {
    if (score >= 90) return '🏆';
    if (score >= 80) return '🌟';
    if (score >= 70) return '👍';
    if (score >= 60) return '⚠️';
    if (score >= 40) return '🔧';
    return '🚨';
  };

  const metrics = [
    {
      id: 'diversification',
      name: 'Diversification',
      score: calculateDiversificationScore(portfolio),
      icon: '🎯',
      description: 'Asset allocation spread',
      action: 'Rebalance Portfolio',
    },
    {
      id: 'risk',
      name: 'Risk Management',
      score: calculateRiskScore(portfolio),
      icon: '🛡️',
      description: 'Volatility & drawdown control',
      action: 'Adjust Risk',
    },
    {
      id: 'tax',
      name: 'Tax Efficiency',
      score: calculateTaxEfficiencyScore(portfolio),
      icon: '💰',
      description: 'Tax optimization strategies',
      action: 'Tax Harvest',
    },
    {
      id: 'performance',
      name: 'Performance',
      score: calculatePerformanceScore(portfolio),
      icon: '📈',
      description: 'Returns vs benchmark',
      action: 'Optimize Strategy',
    },
    {
      id: 'liquidity',
      name: 'Liquidity',
      score: calculateLiquidityScore(portfolio),
      icon: '💧',
      description: 'Cash & liquid assets',
      action: 'Adjust Cash',
    },
  ];

  return (
    <Modal
      visible={true}
      animationType="slide"
      presentationStyle="fullScreen"
      onRequestClose={onClose}
    >
      <StatusBar barStyle="light-content" backgroundColor="#1a1a1a" />
      <View style={styles.modalContainer}>
        <View style={styles.modalHeader}>
          <TouchableOpacity style={styles.closeButton} onPress={onClose}>
            <Text style={styles.closeButtonText}>✕</Text>
          </TouchableOpacity>
          <Text style={styles.modalTitle}>Portfolio Wellness</Text>
          <View style={styles.placeholder} />
        </View>
        <ScrollView style={styles.container} showsVerticalScrollIndicator={false}>
      {/* Main Wellness Score Card */}
      <View style={styles.mainCard}>
        <LinearGradient
          colors={[getScoreColor(wellnessScore), `${getScoreColor(wellnessScore)}80`]}
          style={styles.scoreGradient}
        >
          <View style={styles.scoreHeader}>
            <Text style={styles.scoreTitle}>Portfolio Wellness Score</Text>
            <TouchableOpacity style={styles.refreshButton}>
              <Text style={styles.refreshIcon}>🔄</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.scoreDisplay}>
            <Animated.View
              style={[
                styles.scoreCircle,
                {
                  transform: [{ scale: pulseAnim }],
                },
              ]}
            >
              <CircularProgress
                progress={wellnessScore}
                size={120}
                strokeWidth={8}
                color={getScoreColor(wellnessScore)}
              />
              <View style={styles.scoreTextContainer}>
                <Animated.Text style={styles.scoreNumber}>
                  {scoreAnim.interpolate({
                    inputRange: [0, 100],
                    outputRange: ['0', '100'],
                    extrapolate: 'clamp',
                  })}
                </Animated.Text>
                <Text style={styles.scoreLabel}>/ 100</Text>
              </View>
            </Animated.View>

            <View style={styles.scoreInfo}>
              <Text style={styles.scoreEmoji}>{getScoreEmoji(wellnessScore)}</Text>
              <Text style={styles.scoreStatus}>{getScoreLabel(wellnessScore)}</Text>
              <Text style={styles.scoreDescription}>
                {wellnessScore >= 80 
                  ? 'Your portfolio is in excellent health!'
                  : wellnessScore >= 60
                  ? 'Your portfolio is doing well with room for improvement.'
                  : 'Your portfolio needs attention to optimize performance.'
                }
              </Text>
            </View>
          </View>
        </LinearGradient>
      </View>

      {/* Metrics Breakdown */}
      <View style={styles.metricsContainer}>
        <Text style={styles.metricsTitle}>Health Breakdown</Text>
        {metrics.map((metric) => (
          <MetricCard
            key={metric.id}
            metric={metric}
            isSelected={selectedMetric === metric.id}
            onPress={() => setSelectedMetric(selectedMetric === metric.id ? null : metric.id)}
            onActionPress={() => onActionPress(metric.action)}
          />
        ))}
      </View>

      {/* AI Recommendations */}
      <AIRecommendationsCard wellnessScore={wellnessScore} onActionPress={onActionPress} />

      {/* Quick Actions */}
      <QuickActionsCard onActionPress={onActionPress} />
        </ScrollView>
      </View>
    </Modal>
  );
}

// Circular Progress Component
function CircularProgress({ progress, size, strokeWidth, color }: any) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  return (
    <Svg width={size} height={size} style={styles.circularProgress}>
      <Circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        stroke="rgba(255,255,255,0.2)"
        strokeWidth={strokeWidth}
        fill="transparent"
      />
      <Circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        stroke={color}
        strokeWidth={strokeWidth}
        fill="transparent"
        strokeDasharray={strokeDasharray}
        strokeDashoffset={strokeDashoffset}
        strokeLinecap="round"
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
      />
    </Svg>
  );
}

// Metric Card Component
function MetricCard({ metric, isSelected, onPress, onActionPress }: any) {
  const getScoreColor = (score: number) => {
    if (score >= 80) return '#34C759';
    if (score >= 60) return '#FF9500';
    return '#FF3B30';
  };

  return (
    <TouchableOpacity
      style={[styles.metricCard, isSelected && styles.metricCardSelected]}
      onPress={onPress}
    >
      <View style={styles.metricHeader}>
        <View style={styles.metricInfo}>
          <Text style={styles.metricIcon}>{metric.icon}</Text>
          <View>
            <Text style={styles.metricName}>{metric.name}</Text>
            <Text style={styles.metricDescription}>{metric.description}</Text>
          </View>
        </View>
        <View style={styles.metricScore}>
          <Text style={[styles.metricScoreText, { color: getScoreColor(metric.score) }]}>
            {metric.score}
          </Text>
          <Text style={styles.metricScoreLabel}>/ 100</Text>
        </View>
      </View>

      {isSelected && (
        <View style={styles.metricDetails}>
          <View style={styles.metricBar}>
            <View
              style={[
                styles.metricBarFill,
                {
                  width: `${metric.score}%`,
                  backgroundColor: getScoreColor(metric.score),
                },
              ]}
            />
          </View>
          <TouchableOpacity
            style={[styles.metricAction, { backgroundColor: getScoreColor(metric.score) }]}
            onPress={() => onActionPress(metric.action)}
          >
            <Text style={styles.metricActionText}>{metric.action}</Text>
          </TouchableOpacity>
        </View>
      )}
    </TouchableOpacity>
  );
}

// AI Recommendations Card
function AIRecommendationsCard({ wellnessScore, onActionPress }: any) {
  const recommendations = getAIRecommendations(wellnessScore);

  return (
    <View style={styles.recommendationsCard}>
      <View style={styles.recommendationsHeader}>
        <Text style={styles.recommendationsTitle}>🤖 AI Recommendations</Text>
        <Text style={styles.recommendationsSubtitle}>Personalized insights for your portfolio</Text>
      </View>

      {recommendations.map((rec, index) => (
        <TouchableOpacity
          key={index}
          style={styles.recommendationItem}
          onPress={() => onActionPress(rec.action)}
        >
          <View style={styles.recommendationIcon}>
            <Text style={styles.recommendationEmoji}>{rec.icon}</Text>
          </View>
          <View style={styles.recommendationContent}>
            <Text style={styles.recommendationTitle}>{rec.title}</Text>
            <Text style={styles.recommendationDescription}>{rec.description}</Text>
            <Text style={styles.recommendationImpact}>Impact: {rec.impact}</Text>
          </View>
          <Text style={styles.recommendationArrow}>→</Text>
        </TouchableOpacity>
      ))}
    </View>
  );
}

// Quick Actions Card
function QuickActionsCard({ onActionPress }: any) {
  const actions = [
    { id: 'rebalance', title: 'Auto-Rebalance', icon: '⚖️', color: '#667eea' },
    { id: 'tax-harvest', title: 'Tax Harvest', icon: '💰', color: '#764ba2' },
    { id: 'risk-adjust', title: 'Risk Adjust', icon: '🛡️', color: '#f093fb' },
    { id: 'optimize', title: 'AI Optimize', icon: '🤖', color: '#f5576c' },
  ];

  return (
    <View style={styles.quickActionsCard}>
      <Text style={styles.quickActionsTitle}>Quick Actions</Text>
      <View style={styles.quickActionsGrid}>
        {actions.map((action) => (
          <TouchableOpacity
            key={action.id}
            style={[styles.quickActionButton, { backgroundColor: action.color }]}
            onPress={() => onActionPress(action.title)}
          >
            <Text style={styles.quickActionIcon}>{action.icon}</Text>
            <Text style={styles.quickActionText}>{action.title}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

// Helper Functions
function getAIRecommendations(wellnessScore: number) {
  if (wellnessScore >= 80) {
    return [
      {
        icon: '🚀',
        title: 'Consider Growth Opportunities',
        description: 'Your portfolio is healthy. Explore emerging markets or alternative investments.',
        impact: '+5-10% potential returns',
        action: 'Explore Growth',
      },
      {
        icon: '💎',
        title: 'Tax Loss Harvesting',
        description: 'Optimize your tax position with strategic loss harvesting.',
        impact: 'Save 2-5% on taxes',
        action: 'Tax Harvest',
      },
    ];
  } else if (wellnessScore >= 60) {
    return [
      {
        icon: '⚖️',
        title: 'Rebalance Portfolio',
        description: 'Your allocation has drifted. Rebalance to maintain target weights.',
        impact: '+3-7% risk-adjusted returns',
        action: 'Rebalance',
      },
      {
        icon: '🛡️',
        title: 'Reduce Risk Exposure',
        description: 'Consider reducing position sizes in volatile assets.',
        impact: 'Lower volatility by 15%',
        action: 'Adjust Risk',
      },
    ];
  } else {
    return [
      {
        icon: '🚨',
        title: 'Emergency Portfolio Review',
        description: 'Your portfolio needs immediate attention. High risk detected.',
        impact: 'Critical risk reduction',
        action: 'Emergency Review',
      },
      {
        icon: '💰',
        title: 'Increase Cash Position',
        description: 'Build emergency fund and reduce market exposure.',
        impact: 'Improve liquidity by 20%',
        action: 'Increase Cash',
      },
    ];
  }
}

const styles = StyleSheet.create({
  modalContainer: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#1a1a1a',
    paddingTop: 50, // Account for status bar
  },
  closeButton: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  modalTitle: {
    color: 'white',
    fontSize: 18,
    fontWeight: '600',
  },
  placeholder: {
    width: 32,
  },
  container: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  mainCard: {
    margin: 16,
    borderRadius: 20,
    overflow: 'hidden',
    elevation: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
  },
  scoreGradient: {
    padding: 24,
  },
  scoreHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  scoreTitle: {
    color: 'white',
    fontSize: 20,
    fontWeight: 'bold',
  },
  refreshButton: {
    padding: 8,
  },
  refreshIcon: {
    fontSize: 20,
    color: 'white',
  },
  scoreDisplay: {
    alignItems: 'center',
  },
  scoreCircle: {
    position: 'relative',
    marginBottom: 24,
  },
  circularProgress: {
    position: 'absolute',
  },
  scoreTextContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
  },
  scoreNumber: {
    color: 'white',
    fontSize: 32,
    fontWeight: 'bold',
  },
  scoreLabel: {
    color: 'rgba(255,255,255,0.8)',
    fontSize: 16,
  },
  scoreInfo: {
    alignItems: 'center',
  },
  scoreEmoji: {
    fontSize: 32,
    marginBottom: 8,
  },
  scoreStatus: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  scoreDescription: {
    color: 'rgba(255,255,255,0.9)',
    fontSize: 14,
    textAlign: 'center',
    lineHeight: 20,
  },
  metricsContainer: {
    margin: 16,
  },
  metricsTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  metricCard: {
    backgroundColor: 'white',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  metricCardSelected: {
    elevation: 4,
    shadowOpacity: 0.15,
  },
  metricHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  metricInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  metricIcon: {
    fontSize: 24,
    marginRight: 12,
  },
  metricName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
  },
  metricDescription: {
    fontSize: 12,
    color: '#666',
    marginTop: 2,
  },
  metricScore: {
    alignItems: 'flex-end',
  },
  metricScoreText: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  metricScoreLabel: {
    fontSize: 12,
    color: '#666',
  },
  metricDetails: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#f0f0f0',
  },
  metricBar: {
    height: 6,
    backgroundColor: '#f0f0f0',
    borderRadius: 3,
    marginBottom: 12,
    overflow: 'hidden',
  },
  metricBarFill: {
    height: '100%',
    borderRadius: 3,
  },
  metricAction: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    alignSelf: 'flex-start',
  },
  metricActionText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
  recommendationsCard: {
    backgroundColor: 'white',
    margin: 16,
    borderRadius: 16,
    padding: 20,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  recommendationsHeader: {
    marginBottom: 20,
  },
  recommendationsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 4,
  },
  recommendationsSubtitle: {
    fontSize: 14,
    color: '#666',
  },
  recommendationItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  recommendationIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#f8f9fa',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  recommendationEmoji: {
    fontSize: 20,
  },
  recommendationContent: {
    flex: 1,
  },
  recommendationTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1a1a1a',
    marginBottom: 2,
  },
  recommendationDescription: {
    fontSize: 14,
    color: '#666',
    marginBottom: 4,
  },
  recommendationImpact: {
    fontSize: 12,
    color: '#34C759',
    fontWeight: '600',
  },
  recommendationArrow: {
    fontSize: 20,
    color: '#666',
    marginLeft: 8,
  },
  quickActionsCard: {
    backgroundColor: 'white',
    margin: 16,
    borderRadius: 16,
    padding: 20,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  quickActionsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1a1a1a',
    marginBottom: 16,
  },
  quickActionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  quickActionButton: {
    width: (width - 72) / 2,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 12,
  },
  quickActionIcon: {
    fontSize: 24,
    marginBottom: 8,
  },
  quickActionText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '600',
  },
});
