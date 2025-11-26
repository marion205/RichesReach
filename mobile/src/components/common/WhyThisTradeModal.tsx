import React from 'react';
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

interface TradeSignal {
  name: string;
  value: number | string;
  strength: 'strong' | 'moderate' | 'weak';
  explanation: string;
  color: string;
}

interface WhyThisTradeModalProps {
  visible: boolean;
  onClose: () => void;
  symbol: string;
  side: 'LONG' | 'SHORT' | 'BUY' | 'SELL';
  signals: TradeSignal[];
  confidenceScore?: number;
  riskRewardRatio?: number;
  entryPrice?: number;
  stopPrice?: number;
  targetPrice?: number;
}

export const WhyThisTradeModal: React.FC<WhyThisTradeModalProps> = ({
  visible,
  onClose,
  symbol,
  side,
  signals,
  confidenceScore,
  riskRewardRatio,
  entryPrice,
  stopPrice,
  targetPrice,
}) => {
  const getStrengthColor = (strength: string) => {
    switch (strength) {
      case 'strong':
        return '#22C55E';
      case 'moderate':
        return '#F59E0B';
      case 'weak':
        return '#EF4444';
      default:
        return '#6B7280';
    }
  };

  const getStrengthIcon = (strength: string) => {
    switch (strength) {
      case 'strong':
        return 'trending-up';
      case 'moderate':
        return 'activity';
      case 'weak':
        return 'alert-circle';
      default:
        return 'circle';
    }
  };

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
            <Text style={styles.title}>Why This Trade?</Text>
          </View>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Icon name="x" size={24} color="#6B7280" />
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {/* Trade Summary */}
          <View style={styles.summaryCard}>
            <View style={styles.summaryHeader}>
              <Text style={styles.symbol}>{symbol}</Text>
              <View
                style={[
                  styles.sideBadge,
                  { backgroundColor: side === 'LONG' || side === 'BUY' ? '#DCFCE7' : '#FEE2E2' },
                ]}
              >
                <Text
                  style={[
                    styles.sideText,
                    { color: side === 'LONG' || side === 'BUY' ? '#16A34A' : '#DC2626' },
                  ]}
                >
                  {side}
                </Text>
              </View>
            </View>
            {confidenceScore !== undefined && (
              <View style={styles.confidenceRow}>
                <Icon name="target" size={16} color="#007AFF" />
                <Text style={styles.confidenceLabel}>Confidence Score:</Text>
                <Text style={[styles.confidenceValue, { color: getStrengthColor('strong') }]}>
                  {confidenceScore.toFixed(1)}/10
                </Text>
              </View>
            )}
            {riskRewardRatio !== undefined && (
              <View style={styles.confidenceRow}>
                <Icon name="trending-up" size={16} color="#22C55E" />
                <Text style={styles.confidenceLabel}>Risk:Reward:</Text>
                <Text style={[styles.confidenceValue, { color: '#22C55E' }]}>
                  {riskRewardRatio.toFixed(2)}:1
                </Text>
              </View>
            )}
          </View>

          {/* Price Levels */}
          {(entryPrice || stopPrice || targetPrice) && (
            <View style={styles.priceCard}>
              <Text style={styles.sectionTitle}>Price Levels</Text>
              <View style={styles.priceRow}>
                {entryPrice && (
                  <View style={styles.priceItem}>
                    <Text style={styles.priceLabel}>Entry</Text>
                    <Text style={[styles.priceValue, { color: '#007AFF' }]}>
                      ${entryPrice.toFixed(2)}
                    </Text>
                  </View>
                )}
                {stopPrice && (
                  <View style={styles.priceItem}>
                    <Text style={styles.priceLabel}>Stop</Text>
                    <Text style={[styles.priceValue, { color: '#EF4444' }]}>
                      ${stopPrice.toFixed(2)}
                    </Text>
                  </View>
                )}
                {targetPrice && (
                  <View style={styles.priceItem}>
                    <Text style={styles.priceLabel}>Target</Text>
                    <Text style={[styles.priceValue, { color: '#22C55E' }]}>
                      ${targetPrice.toFixed(2)}
                    </Text>
                  </View>
                )}
              </View>
            </View>
          )}

          {/* Trade Signals */}
          <View style={styles.signalsCard}>
            <Text style={styles.sectionTitle}>Trade Signals</Text>
            <Text style={styles.sectionSubtitle}>
              Here's why this trade setup looks promising:
            </Text>
            {signals.map((signal, index) => (
              <View key={index} style={styles.signalItem}>
                <View style={styles.signalHeader}>
                  <View style={styles.signalLeft}>
                    <Icon
                      name={getStrengthIcon(signal.strength)}
                      size={18}
                      color={getStrengthColor(signal.strength)}
                    />
                    <Text style={styles.signalName}>{signal.name}</Text>
                  </View>
                  <View
                    style={[
                      styles.strengthBadge,
                      { backgroundColor: `${getStrengthColor(signal.strength)}20` },
                    ]}
                  >
                    <Text
                      style={[styles.strengthText, { color: getStrengthColor(signal.strength) }]}
                    >
                      {signal.strength.toUpperCase()}
                    </Text>
                  </View>
                </View>
                <Text style={styles.signalValue}>
                  {typeof signal.value === 'number' ? signal.value.toFixed(2) : signal.value}
                </Text>
                <Text style={styles.signalExplanation}>{signal.explanation}</Text>
              </View>
            ))}
          </View>

          {/* Trading Tip */}
          <View style={styles.tipCard}>
            <Icon name="info" size={20} color="#007AFF" />
            <Text style={styles.tipText}>
              Remember: Always use stop loss and never risk more than 1-2% of your account per
              trade. These signals are based on technical analysis and should be combined with
              your own research.
            </Text>
          </View>
        </ScrollView>
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
  summaryCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  summaryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  symbol: {
    fontSize: 28,
    fontWeight: '800',
    color: '#111827',
  },
  sideBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  sideText: {
    fontSize: 14,
    fontWeight: '700',
  },
  confidenceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginTop: 8,
  },
  confidenceLabel: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '500',
  },
  confidenceValue: {
    fontSize: 16,
    fontWeight: '700',
  },
  priceCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 12,
  },
  sectionSubtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 16,
    lineHeight: 20,
  },
  priceRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  priceItem: {
    alignItems: 'center',
  },
  priceLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  priceValue: {
    fontSize: 20,
    fontWeight: '700',
  },
  signalsCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  signalItem: {
    marginBottom: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  signalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  signalLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flex: 1,
  },
  signalName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  strengthBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  strengthText: {
    fontSize: 10,
    fontWeight: '700',
  },
  signalValue: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
  },
  signalExplanation: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
  tipCard: {
    flexDirection: 'row',
    backgroundColor: '#EFF6FF',
    borderRadius: 12,
    padding: 16,
    gap: 12,
    borderWidth: 1,
    borderColor: '#BFDBFE',
  },
  tipText: {
    flex: 1,
    fontSize: 13,
    color: '#1E40AF',
    lineHeight: 18,
  },
});

