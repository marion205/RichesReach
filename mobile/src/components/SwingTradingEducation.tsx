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

interface Strategy {
  id: string;
  name: string;
  description: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  timeHorizon: string;
  winRate: number;
  avgReturn: number;
  riskLevel: 'low' | 'medium' | 'high';
  tags: string[];
}

interface RiskTip {
  id: string;
  title: string;
  description: string;
  category: 'position' | 'stop' | 'diversification' | 'psychology';
  importance: 'critical' | 'important' | 'helpful';
}

interface MarketPsychology {
  id: string;
  concept: string;
  description: string;
  example: string;
  impact: 'positive' | 'negative' | 'neutral';
}

const SwingTradingEducation: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState('strategies');

  const strategies: Strategy[] = [
    {
      id: '1',
      name: 'RSI Mean Reversion',
      description: 'Buy oversold stocks (RSI < 30) and sell overbought (RSI > 70) with volume confirmation.',
      difficulty: 'beginner',
      timeHorizon: '3-7 days',
      winRate: 68,
      avgReturn: 4.2,
      riskLevel: 'medium',
      tags: ['RSI', 'Mean Reversion', 'Volume']
    },
    {
      id: '2',
      name: 'EMA Crossover',
      description: 'Enter long when EMA 12 crosses above EMA 26 with strong volume. Exit when trend reverses.',
      difficulty: 'beginner',
      timeHorizon: '5-14 days',
      winRate: 72,
      avgReturn: 6.8,
      riskLevel: 'medium',
      tags: ['EMA', 'Trend Following', 'Momentum']
    },
    {
      id: '3',
      name: 'Breakout Trading',
      description: 'Trade breakouts above resistance levels with volume confirmation and tight stops.',
      difficulty: 'intermediate',
      timeHorizon: '2-10 days',
      winRate: 58,
      avgReturn: 8.5,
      riskLevel: 'high',
      tags: ['Breakout', 'Support/Resistance', 'Volume']
    },
    {
      id: '4',
      name: 'Bollinger Band Squeeze',
      description: 'Trade the expansion after periods of low volatility (squeeze) with directional bias.',
      difficulty: 'intermediate',
      timeHorizon: '3-12 days',
      winRate: 65,
      avgReturn: 7.2,
      riskLevel: 'medium',
      tags: ['Bollinger Bands', 'Volatility', 'Squeeze']
    },
    {
      id: '5',
      name: 'Fibonacci Retracement',
      description: 'Buy at key Fibonacci levels (38.2%, 50%, 61.8%) with confluence from other indicators.',
      difficulty: 'advanced',
      timeHorizon: '5-21 days',
      winRate: 62,
      avgReturn: 9.1,
      riskLevel: 'medium',
      tags: ['Fibonacci', 'Support/Resistance', 'Confluence']
    },
    {
      id: '6',
      name: 'Gap Trading',
      description: 'Trade gap fills or gap continuations based on market context and volume patterns.',
      difficulty: 'advanced',
      timeHorizon: '1-5 days',
      winRate: 55,
      avgReturn: 12.3,
      riskLevel: 'high',
      tags: ['Gaps', 'Volume', 'Market Context']
    }
  ];

  const riskTips: RiskTip[] = [
    {
      id: '1',
      title: 'Never Risk More Than 2% Per Trade',
      description: 'Calculate position size so that if your stop loss is hit, you only lose 2% of your account.',
      category: 'position',
      importance: 'critical'
    },
    {
      id: '2',
      title: 'Use ATR-Based Stop Losses',
      description: 'Set stops at 1.5-2x ATR below entry for long positions to account for normal volatility.',
      category: 'stop',
      importance: 'critical'
    },
    {
      id: '3',
      title: 'Diversify Across Sectors',
      description: 'Never have more than 25% of your portfolio in one sector to reduce correlation risk.',
      category: 'diversification',
      importance: 'important'
    },
    {
      id: '4',
      title: 'Keep Emotions in Check',
      description: 'Stick to your trading plan. Don\'t let fear or greed override your risk management rules.',
      category: 'psychology',
      importance: 'critical'
    },
    {
      id: '5',
      title: 'Scale Out of Positions',
      description: 'Take partial profits at 1:1 and 2:1 risk-reward ratios to lock in gains.',
      category: 'position',
      importance: 'important'
    },
    {
      id: '6',
      title: 'Avoid Trading During News',
      description: 'High-impact news events can cause unpredictable price movements. Wait for clarity.',
      category: 'psychology',
      importance: 'important'
    },
    {
      id: '7',
      title: 'Use Trailing Stops',
      description: 'Move stops to breakeven once price moves 1:1 in your favor to protect capital.',
      category: 'stop',
      importance: 'helpful'
    },
    {
      id: '8',
      title: 'Monitor Market Conditions',
      description: 'Reduce position sizes during high volatility periods (VIX > 25) or market stress.',
      category: 'diversification',
      importance: 'important'
    }
  ];

  const marketPsychology: MarketPsychology[] = [
    {
      id: '1',
      concept: 'FOMO (Fear of Missing Out)',
      description: 'The anxiety that others are making money while you\'re not, leading to impulsive trades.',
      example: 'Buying a stock after it has already moved 20% because everyone is talking about it.',
      impact: 'negative'
    },
    {
      id: '2',
      concept: 'Confirmation Bias',
      description: 'Seeking information that confirms your existing beliefs while ignoring contradictory evidence.',
      example: 'Only reading bullish news about a stock you own, ignoring bearish signals.',
      impact: 'negative'
    },
    {
      id: '3',
      concept: 'Loss Aversion',
      description: 'The tendency to feel losses more strongly than equivalent gains, leading to poor risk management.',
      example: 'Holding losing positions too long while selling winners too quickly.',
      impact: 'negative'
    },
    {
      id: '4',
      concept: 'Patience',
      description: 'Waiting for high-probability setups rather than forcing trades in poor market conditions.',
      example: 'Skipping marginal setups and waiting for clear signals with strong risk-reward ratios.',
      impact: 'positive'
    },
    {
      id: '5',
      concept: 'Discipline',
      description: 'Following your trading plan consistently, regardless of emotions or market noise.',
      example: 'Always using stop losses and position sizing rules, even when you feel confident.',
      impact: 'positive'
    },
    {
      id: '6',
      concept: 'Overconfidence',
      description: 'Overestimating your trading abilities after a few successful trades.',
      example: 'Increasing position sizes after a winning streak, leading to larger losses.',
      impact: 'negative'
    }
  ];

  const categories = [
    { key: 'strategies', label: 'Strategies', icon: 'trending-up' },
    { key: 'risk', label: 'Risk Management', icon: 'shield' },
    { key: 'psychology', label: 'Psychology', icon: 'brain' }
  ];

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return '#10B981';
      case 'intermediate': return '#F59E0B';
      case 'advanced': return '#EF4444';
      default: return '#6B7280';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'low': return '#10B981';
      case 'medium': return '#F59E0B';
      case 'high': return '#EF4444';
      default: return '#6B7280';
    }
  };

  const getImportanceColor = (importance: string) => {
    switch (importance) {
      case 'critical': return '#EF4444';
      case 'important': return '#F59E0B';
      case 'helpful': return '#10B981';
      default: return '#6B7280';
    }
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'positive': return '#10B981';
      case 'negative': return '#EF4444';
      case 'neutral': return '#6B7280';
      default: return '#6B7280';
    }
  };

  const renderStrategies = () => (
    <View style={styles.content}>
      {strategies.map((strategy) => (
        <View key={strategy.id} style={styles.strategyCard}>
          <View style={styles.strategyHeader}>
            <Text style={styles.strategyName}>{strategy.name}</Text>
            <View style={styles.strategyBadges}>
              <View style={[styles.difficultyBadge, { backgroundColor: getDifficultyColor(strategy.difficulty) }]}>
                <Text style={styles.badgeText}>{strategy.difficulty.toUpperCase()}</Text>
              </View>
              <View style={[styles.riskBadge, { backgroundColor: getRiskColor(strategy.riskLevel) }]}>
                <Text style={styles.badgeText}>{strategy.riskLevel.toUpperCase()}</Text>
              </View>
            </View>
          </View>
          
          <Text style={styles.strategyDescription}>{strategy.description}</Text>
          
          <View style={styles.strategyMetrics}>
            <View style={styles.metric}>
              <Text style={styles.metricLabel}>Time Horizon</Text>
              <Text style={styles.metricValue}>{strategy.timeHorizon}</Text>
            </View>
            <View style={styles.metric}>
              <Text style={styles.metricLabel}>Win Rate</Text>
              <Text style={styles.metricValue}>{strategy.winRate}%</Text>
            </View>
            <View style={styles.metric}>
              <Text style={styles.metricLabel}>Avg Return</Text>
              <Text style={styles.metricValue}>{strategy.avgReturn}%</Text>
            </View>
          </View>
          
          <View style={styles.tagsContainer}>
            {strategy.tags.map((tag, index) => (
              <View key={index} style={styles.tag}>
                <Text style={styles.tagText}>{tag}</Text>
              </View>
            ))}
          </View>
        </View>
      ))}
    </View>
  );

  const renderRiskTips = () => (
    <View style={styles.content}>
      {riskTips.map((tip) => (
        <View key={tip.id} style={styles.tipCard}>
          <View style={styles.tipHeader}>
            <Text style={styles.tipTitle}>{tip.title}</Text>
            <View style={[styles.importanceBadge, { backgroundColor: getImportanceColor(tip.importance) }]}>
              <Text style={styles.badgeText}>{tip.importance.toUpperCase()}</Text>
            </View>
          </View>
          
          <Text style={styles.tipDescription}>{tip.description}</Text>
          
          <View style={styles.tipCategory}>
            <Icon name="tag" size={14} color="#6B7280" />
            <Text style={styles.categoryText}>{tip.category.replace('_', ' ').toUpperCase()}</Text>
          </View>
        </View>
      ))}
    </View>
  );

  const renderPsychology = () => (
    <View style={styles.content}>
      {marketPsychology.map((psych) => (
        <View key={psych.id} style={styles.psychologyCard}>
          <View style={styles.psychologyHeader}>
            <Text style={styles.psychologyConcept}>{psych.concept}</Text>
            <View style={[styles.impactBadge, { backgroundColor: getImpactColor(psych.impact) }]}>
              <Text style={styles.badgeText}>{psych.impact.toUpperCase()}</Text>
            </View>
          </View>
          
          <Text style={styles.psychologyDescription}>{psych.description}</Text>
          
          <View style={styles.exampleContainer}>
            <Text style={styles.exampleLabel}>Example:</Text>
            <Text style={styles.exampleText}>{psych.example}</Text>
          </View>
        </View>
      ))}
    </View>
  );

  return (
    <View style={styles.container}>
      {/* Category Selector */}
      <View style={styles.categorySelector}>
        {categories.map((category) => (
          <TouchableOpacity
            key={category.key}
            style={[
              styles.categoryButton,
              selectedCategory === category.key && styles.categoryButtonActive
            ]}
            onPress={() => setSelectedCategory(category.key)}
          >
            <Icon 
              name={category.icon as any} 
              size={16} 
              color={selectedCategory === category.key ? '#FFFFFF' : '#6B7280'} 
            />
            <Text style={[
              styles.categoryText,
              selectedCategory === category.key && styles.categoryTextActive
            ]}>
              {category.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {selectedCategory === 'strategies' && renderStrategies()}
        {selectedCategory === 'risk' && renderRiskTips()}
        {selectedCategory === 'psychology' && renderPsychology()}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  categorySelector: {
    flexDirection: 'row',
    backgroundColor: '#FFFFFF',
    marginHorizontal: 0,
    marginTop: 5,
    borderRadius: 12,
    padding: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  categoryButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 8,
    borderRadius: 8,
  },
  categoryButtonActive: {
    backgroundColor: '#3B82F6',
  },
  categoryText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
    marginLeft: 4,
  },
  categoryTextActive: {
    color: '#FFFFFF',
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 0,
  },
  strategyCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  strategyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  strategyName: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    flex: 1,
    marginRight: 12,
  },
  strategyBadges: {
    flexDirection: 'row',
    gap: 6,
  },
  difficultyBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  riskBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  strategyDescription: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
    marginBottom: 16,
  },
  strategyMetrics: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
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
    color: '#111827',
  },
  tagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  tag: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  tagText: {
    fontSize: 12,
    color: '#6B7280',
    fontWeight: '500',
  },
  tipCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  tipHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  tipTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    flex: 1,
    marginRight: 12,
  },
  importanceBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  tipDescription: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
    marginBottom: 12,
  },
  tipCategory: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  categoryTextSecondary: {
    fontSize: 12,
    color: '#6B7280',
    marginLeft: 4,
    fontWeight: '500',
  },
  psychologyCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginHorizontal: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3.84,
    elevation: 5,
  },
  psychologyHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  psychologyConcept: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    flex: 1,
    marginRight: 12,
  },
  impactBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  psychologyDescription: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
    marginBottom: 12,
  },
  exampleContainer: {
    backgroundColor: '#F9FAFB',
    padding: 12,
    borderRadius: 8,
  },
  exampleLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  exampleText: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 18,
  },
});

export default SwingTradingEducation;
