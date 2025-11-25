import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  ScrollView,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { LinearGradient } from 'expo-linear-gradient';

const { width: screenWidth } = Dimensions.get('window');

interface LearningTopic {
  id: string;
  title: string;
  icon: string;
  description: string;
  content: string;
  examples?: string[];
}

interface LearnWhileTradingModalProps {
  visible: boolean;
  onClose: () => void;
  topic?: 'stop_loss' | 'macd' | 'atr' | 'risk_reward' | 'position_sizing' | null;
  onNavigateToRiskCoach?: () => void;
}

const learningTopics: Record<string, LearningTopic> = {
  stop_loss: {
    id: 'stop_loss',
    title: 'Stop Loss',
    icon: 'shield',
    description: 'Learn how to protect your trades with stop losses',
    content:
      'A stop loss is an order that automatically closes your position when the price reaches a certain level. This limits your maximum loss on a trade.\n\n**Why Use Stop Loss?**\n\n1. **Protects Capital**: Limits losses to a predetermined amount\n2. **Removes Emotion**: Takes the decision out of your hands\n3. **Enables Position Sizing**: Lets you calculate exactly how much to risk\n\n**How to Set Stop Loss:**\n\n- **Day Trading**: Use 1.5-2x ATR (Average True Range)\n- **Swing Trading**: Use 2-3x ATR\n- **Place below support** for long positions\n- **Place above resistance** for short positions\n\n**Common Mistakes:**\n\n- Setting stop too tight (gets stopped out by noise)\n- Setting stop too wide (risks too much)\n- Moving stop further away when losing (hoping for recovery)',
    examples: [
      'Buying AAPL at $150, set stop at $145 (3.3% risk)',
      'Using ATR of $2, set stop at $146 for a $150 entry (2x ATR)',
      'Risking $100 on a trade, stop should limit loss to $100',
    ],
  },
  macd: {
    id: 'macd',
    title: 'MACD Indicator',
    icon: 'activity',
    description: 'Understand Moving Average Convergence Divergence',
    content:
      'MACD (Moving Average Convergence Divergence) is a momentum indicator that shows the relationship between two moving averages of a stock\'s price.\n\n**How to Read MACD:**\n\n- **MACD Line**: The difference between 12-period and 26-period EMAs\n- **Signal Line**: 9-period EMA of the MACD line\n- **Histogram**: The difference between MACD and Signal lines\n\n**Trading Signals:**\n\n1. **Bullish Signal**: MACD crosses above signal line (buy signal)\n2. **Bearish Signal**: MACD crosses below signal line (sell signal)\n3. **Divergence**: Price makes new high but MACD doesn\'t = warning\n\n**Best Practices:**\n\n- Use with price action confirmation\n- Stronger signals when MACD crosses in direction of trend\n- Look for histogram increasing (momentum building)',
    examples: [
      'MACD crosses above signal while price is in uptrend = strong buy',
      'Price makes new high, MACD makes lower high = bearish divergence',
      'Histogram bars getting taller = momentum increasing',
    ],
  },
  atr: {
    id: 'atr',
    title: 'ATR (Average True Range)',
    icon: 'trending-up',
    description: 'Measure volatility to set better stops',
    content:
      'ATR (Average True Range) measures market volatility by calculating the average of true ranges over a period.\n\n**What is True Range?**\n\nThe greatest of:\n- Current high minus current low\n- Absolute value of current high minus previous close\n- Absolute value of current low minus previous close\n\n**How to Use ATR:**\n\n1. **Set Stop Loss Distance**: 1.5-2x ATR for day trading, 2-3x ATR for swing trading\n2. **Position Sizing**: Higher ATR = wider stops = smaller position size\n3. **Volatility Filter**: Avoid trading when ATR is extremely high\n\n**Example:**\n\nIf ATR is $2 and you\'re buying at $100:\n- Day trading stop: $100 - (1.5 × $2) = $97\n- Swing trading stop: $100 - (2.5 × $2) = $95',
    examples: [
      'ATR of $2 means stock moves $2 on average → set stop $3-4 away',
      'High ATR ($5+) = very volatile = use wider stops or avoid',
      'Low ATR ($0.50) = stable = can use tighter stops',
    ],
  },
  risk_reward: {
    id: 'risk_reward',
    title: 'Risk/Reward Ratio',
    icon: 'target',
    description: 'Calculate potential profit vs. potential loss',
    content:
      'The risk/reward ratio compares the potential profit of a trade to the potential loss.\n\n**How to Calculate:**\n\nRisk/Reward = (Target Price - Entry Price) / (Entry Price - Stop Price)\n\n**Example:**\n\n- Entry: $100\n- Stop: $95 (risk $5)\n- Target: $110 (reward $10)\n- R:R = $10 / $5 = 2:1\n\n**Why It Matters:**\n\n- **2:1 Ratio**: You can be wrong 50% of the time and still break even\n- **3:1 Ratio**: You can be wrong 66% of the time and still profit\n- Better ratios = more profitable over time\n\n**Best Practices:**\n\n- Aim for at least 2:1 ratio\n- Never take trades with less than 1:1 ratio\n- Higher ratios allow for lower win rates',
    examples: [
      'Risk $100 to make $200 = 2:1 ratio (need 33% win rate)',
      'Risk $50 to make $150 = 3:1 ratio (need 25% win rate)',
      'Risk $200 to make $100 = 0.5:1 ratio (avoid this!)',
    ],
  },
  position_sizing: {
    id: 'position_sizing',
    title: 'Position Sizing',
    icon: 'layers',
    description: 'Calculate how many shares to trade',
    content:
      'Position sizing determines how many shares to trade based on your risk tolerance and account size.\n\n**The Formula:**\n\nShares = (Account Risk %) × Account Value / (Entry Price - Stop Price)\n\n**Example:**\n\n- Account: $10,000\n- Risk per trade: 1% = $100\n- Entry: $100\n- Stop: $95 (risk $5 per share)\n- Shares: $100 / $5 = 20 shares\n\n**Risk Management Rules:**\n\n1. **Never risk more than 1-2% per trade**\n2. **Adjust position size based on stop distance**\n3. **Smaller positions for wider stops**\n4. **Larger positions for tighter stops**\n\n**Why It Matters:**\n\n- Proper position sizing keeps you in the game\n- Allows you to survive losing streaks\n- Prevents emotional trading',
    examples: [
      '$10k account, risk 1% = $100 risk per trade',
      'Stop $5 away, risk $100 → buy 20 shares max',
      'Stop $2 away, risk $100 → buy 50 shares max',
    ],
  },
};

export const LearnWhileTradingModal: React.FC<LearnWhileTradingModalProps> = ({
  visible,
  onClose,
  topic,
  onNavigateToRiskCoach,
}) => {
  const [selectedTopic, setSelectedTopic] = useState<string | null>(topic || null);

  const currentTopic = selectedTopic ? learningTopics[selectedTopic] : null;

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <View style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerContent}>
            <Icon name="book-open" size={24} color="#007AFF" />
            <Text style={styles.title}>Learn While Trading</Text>
          </View>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Icon name="x" size={24} color="#6B7280" />
          </TouchableOpacity>
        </View>

        {!currentTopic ? (
          /* Topic Selection */
          <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
            <Text style={styles.subtitle}>Choose a topic to learn about:</Text>
            {Object.values(learningTopics).map((topic) => (
              <TouchableOpacity
                key={topic.id}
                style={styles.topicCard}
                onPress={() => setSelectedTopic(topic.id)}
              >
                <View style={styles.topicIcon}>
                  <Icon name={topic.icon as any} size={24} color="#007AFF" />
                </View>
                <View style={styles.topicContent}>
                  <Text style={styles.topicTitle}>{topic.title}</Text>
                  <Text style={styles.topicDescription}>{topic.description}</Text>
                </View>
                <Icon name="chevron-right" size={20} color="#9CA3AF" />
              </TouchableOpacity>
            ))}
            {onNavigateToRiskCoach && (
              <TouchableOpacity
                style={styles.riskCoachButton}
                onPress={() => {
                  onClose();
                  onNavigateToRiskCoach();
                }}
              >
                <LinearGradient
                  colors={['#007AFF', '#0056CC']}
                  style={styles.riskCoachGradient}
                >
                  <Icon name="calculator" size={20} color="#FFFFFF" />
                  <Text style={styles.riskCoachText}>Open Risk Coach</Text>
                </LinearGradient>
              </TouchableOpacity>
            )}
          </ScrollView>
        ) : (
          /* Topic Content */
          <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
            <TouchableOpacity
              style={styles.backButton}
              onPress={() => setSelectedTopic(null)}
            >
              <Icon name="arrow-left" size={20} color="#007AFF" />
              <Text style={styles.backText}>Back to Topics</Text>
            </TouchableOpacity>

            <View style={styles.topicHeader}>
              <View style={[styles.topicIcon, { backgroundColor: '#EFF6FF' }]}>
                <Icon name={currentTopic.icon as any} size={32} color="#007AFF" />
              </View>
              <Text style={styles.topicTitleLarge}>{currentTopic.title}</Text>
            </View>

            <View style={styles.contentCard}>
              <Text style={styles.contentText}>{currentTopic.content}</Text>
            </View>

            {currentTopic.examples && currentTopic.examples.length > 0 && (
              <View style={styles.examplesCard}>
                <Text style={styles.examplesTitle}>Examples:</Text>
                {currentTopic.examples.map((example, index) => (
                  <View key={index} style={styles.exampleItem}>
                    <Icon name="check-circle" size={16} color="#22C55E" />
                    <Text style={styles.exampleText}>{example}</Text>
                  </View>
                ))}
              </View>
            )}

            {onNavigateToRiskCoach && (
              <TouchableOpacity
                style={styles.riskCoachButton}
                onPress={() => {
                  onClose();
                  onNavigateToRiskCoach();
                }}
              >
                <LinearGradient
                  colors={['#007AFF', '#0056CC']}
                  style={styles.riskCoachGradient}
                >
                  <Icon name="calculator" size={20} color="#FFFFFF" />
                  <Text style={styles.riskCoachText}>Try Risk Coach Calculator</Text>
                </LinearGradient>
              </TouchableOpacity>
            )}
          </ScrollView>
        )}
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    paddingTop: 60,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#111827',
  },
  closeButton: {
    padding: 4,
  },
  content: {
    flex: 1,
    padding: 20,
  },
  subtitle: {
    fontSize: 16,
    color: '#6B7280',
    marginBottom: 20,
  },
  topicCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  topicIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#EFF6FF',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  topicContent: {
    flex: 1,
  },
  topicTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  topicDescription: {
    fontSize: 13,
    color: '#6B7280',
  },
  backButton: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    gap: 8,
  },
  backText: {
    fontSize: 16,
    color: '#007AFF',
    fontWeight: '600',
  },
  topicHeader: {
    alignItems: 'center',
    marginBottom: 24,
  },
  topicTitleLarge: {
    fontSize: 28,
    fontWeight: '700',
    color: '#111827',
    marginTop: 12,
  },
  contentCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  contentText: {
    fontSize: 15,
    color: '#374151',
    lineHeight: 24,
  },
  examplesCard: {
    backgroundColor: '#F0FDF4',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#BBF7D0',
  },
  examplesTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#166534',
    marginBottom: 12,
  },
  exampleItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
    gap: 8,
  },
  exampleText: {
    flex: 1,
    fontSize: 14,
    color: '#166534',
    lineHeight: 20,
  },
  riskCoachButton: {
    marginTop: 8,
    marginBottom: 20,
  },
  riskCoachGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 12,
    gap: 8,
  },
  riskCoachText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});

