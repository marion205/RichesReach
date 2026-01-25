import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  ScrollView,
  TouchableOpacity,
  Switch,
  Alert,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { LinearGradient } from 'expo-linear-gradient';
import { RiskRewardDiagram } from './RiskRewardDiagram';

interface PreExecutionRiskCheckModalProps {
  visible: boolean;
  onClose: () => void;
  onConfirm: () => void;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  entryPrice: number;
  stopPrice?: number;
  targetPrice?: number;
  totalRisk?: number;
  riskPercent?: number;
  onLearnMore?: () => void;
}

export const PreExecutionRiskCheckModal: React.FC<PreExecutionRiskCheckModalProps> = ({
  visible,
  onClose,
  onConfirm,
  symbol,
  side,
  quantity,
  entryPrice,
  stopPrice,
  targetPrice,
  totalRisk,
  riskPercent,
  onLearnMore,
}) => {
  const [understoodStopLoss, setUnderstoodStopLoss] = useState(false);
  const [understoodRisk, setUnderstoodRisk] = useState(false);

  const canProceed = understoodStopLoss && understoodRisk;

  const handleConfirm = () => {
    if (!canProceed) {
      Alert.alert(
        'Please Confirm',
        'Please confirm that you understand your stop loss and risk before proceeding.',
        [{ text: 'OK' }]
      );
      return;
    }
    onConfirm();
  };

  const calculatedTarget = targetPrice || (stopPrice ? entryPrice + Math.abs(entryPrice - stopPrice) * 2 : entryPrice * 1.05);
  const calculatedStop = stopPrice || entryPrice * 0.95;
  const riskAmount = Math.abs(entryPrice - calculatedStop) * quantity;
  const rewardAmount = Math.abs(calculatedTarget - entryPrice) * quantity;

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
            <Icon name="shield" size={24} color="#EF4444" />
            <Text style={styles.title}>Risk Check</Text>
          </View>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Icon name="x" size={24} color="#6B7280" />
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {/* Warning Banner */}
          <View style={styles.warningBanner}>
            <Icon name="alert-triangle" size={20} color="#DC2626" />
            <Text style={styles.warningText}>
              Please review your risk before executing this trade
            </Text>
          </View>

          {/* Trade Summary */}
          <View style={styles.summaryCard}>
            <Text style={styles.summaryTitle}>Trade Summary</Text>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Symbol:</Text>
              <Text style={styles.summaryValue}>{symbol}</Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Side:</Text>
              <Text
                style={[
                  styles.summaryValue,
                  { color: side === 'BUY' ? '#22C55E' : '#EF4444' },
                ]}
              >
                {side}
              </Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Quantity:</Text>
              <Text style={styles.summaryValue}>{quantity} shares</Text>
            </View>
            <View style={styles.summaryRow}>
              <Text style={styles.summaryLabel}>Entry Price:</Text>
              <Text style={styles.summaryValue}>${entryPrice.toFixed(2)}</Text>
            </View>
            {stopPrice && (
              <View style={styles.summaryRow}>
                <Text style={styles.summaryLabel}>Stop Loss:</Text>
                <Text style={[styles.summaryValue, { color: '#EF4444' }]}>
                  ${stopPrice.toFixed(2)}
                </Text>
              </View>
            )}
            {targetPrice && (
              <View style={styles.summaryRow}>
                <Text style={styles.summaryLabel}>Target:</Text>
                <Text style={[styles.summaryValue, { color: '#22C55E' }]}>
                  ${targetPrice.toFixed(2)}
                </Text>
              </View>
            )}
          </View>

          {/* Risk/Reward Diagram */}
          <View style={styles.diagramCard}>
            <RiskRewardDiagram
              entryPrice={entryPrice}
              stopPrice={calculatedStop}
              targetPrice={calculatedTarget}
              riskAmount={riskAmount}
              rewardAmount={rewardAmount}
            />
          </View>

          {/* Risk Breakdown */}
          {totalRisk !== undefined && (
            <View style={styles.riskCard}>
              <Text style={styles.riskTitle}>Risk Breakdown</Text>
              <View style={styles.riskRow}>
                <View style={styles.riskItem}>
                  <Icon name="alert-circle" size={20} color="#EF4444" />
                  <View style={styles.riskItemContent}>
                    <Text style={styles.riskItemLabel}>Total Risk</Text>
                    <Text style={[styles.riskItemValue, { color: '#EF4444' }]}>
                      ${totalRisk.toFixed(2)}
                    </Text>
                  </View>
                </View>
                {riskPercent !== undefined && (
                  <View style={styles.riskItem}>
                    <Icon name="percent" size={20} color="#F59E0B" />
                    <View style={styles.riskItemContent}>
                      <Text style={styles.riskItemLabel}>Risk %</Text>
                      <Text style={[styles.riskItemValue, { color: '#F59E0B' }]}>
                        {riskPercent.toFixed(2)}%
                      </Text>
                    </View>
                  </View>
                )}
              </View>
            </View>
          )}

          {/* Confirmations */}
          <View style={styles.confirmationsCard}>
            <Text style={styles.confirmationsTitle}>Confirmations</Text>
            
            <View style={styles.confirmationItem}>
              <Switch
                value={understoodStopLoss}
                onValueChange={setUnderstoodStopLoss}
                trackColor={{ false: '#D1D5DB', true: '#EF4444' }}
                thumbColor={understoodStopLoss ? '#FFFFFF' : '#F3F4F6'}
              />
              <View style={styles.confirmationContent}>
                <Text style={styles.confirmationLabel}>
                  I understand my stop loss will limit my maximum loss
                </Text>
                <Text style={styles.confirmationHint}>
                  If price reaches ${calculatedStop.toFixed(2)}, my position will be closed
                  automatically
                </Text>
              </View>
            </View>

            <View style={styles.confirmationItem}>
              <Switch
                value={understoodRisk}
                onValueChange={setUnderstoodRisk}
                trackColor={{ false: '#D1D5DB', true: '#EF4444' }}
                thumbColor={understoodRisk ? '#FFFFFF' : '#F3F4F6'}
              />
              <View style={styles.confirmationContent}>
                <Text style={styles.confirmationLabel}>
                  I understand the total risk of this trade
                </Text>
                <Text style={styles.confirmationHint}>
                  {totalRisk !== undefined
                    ? `I could lose up to $${totalRisk.toFixed(2)} if my stop loss is hit`
                    : 'I understand the potential loss if my stop loss is hit'}
                </Text>
              </View>
            </View>
          </View>

          {/* Educational Link */}
          {onLearnMore && (
            <TouchableOpacity style={styles.learnMoreButton} onPress={onLearnMore}>
              <Icon name="book-open" size={16} color="#007AFF" />
              <Text style={styles.learnMoreText}>Learn more about risk management</Text>
              <Icon name="chevron-right" size={16} color="#007AFF" />
            </TouchableOpacity>
          )}
        </ScrollView>

        {/* Footer Actions */}
        <View style={styles.footer}>
          <TouchableOpacity style={styles.cancelButton} onPress={onClose}>
            <Text style={styles.cancelButtonText}>Cancel</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.confirmButton, !canProceed && styles.confirmButtonDisabled]}
            onPress={handleConfirm}
            disabled={!canProceed}
          >
            <LinearGradient
              colors={canProceed ? ['#EF4444', '#DC2626'] : ['#D1D5DB', '#9CA3AF']}
              style={styles.confirmButtonGradient}
            >
              <Icon name="check" size={20} color="#FFFFFF" />
              <Text style={styles.confirmButtonText}>Confirm & Execute</Text>
            </LinearGradient>
          </TouchableOpacity>
        </View>
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
  warningBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FEE2E2',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
    gap: 12,
    borderWidth: 1,
    borderColor: '#FECACA',
  },
  warningText: {
    flex: 1,
    fontSize: 14,
    color: '#DC2626',
    fontWeight: '600',
  },
  summaryCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  summaryTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 12,
  },
  summaryRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  summaryLabel: {
    fontSize: 14,
    color: '#6B7280',
  },
  summaryValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  diagramCard: {
    marginBottom: 16,
  },
  riskCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  riskTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 12,
  },
  riskRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  riskItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  riskItemContent: {
    alignItems: 'flex-start',
  },
  riskItemLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  riskItemValue: {
    fontSize: 20,
    fontWeight: '700',
  },
  confirmationsCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  confirmationsTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 16,
  },
  confirmationItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 16,
    gap: 12,
  },
  confirmationContent: {
    flex: 1,
  },
  confirmationLabel: {
    fontSize: 15,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  confirmationHint: {
    fontSize: 13,
    color: '#6B7280',
    lineHeight: 18,
  },
  learnMoreButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#EFF6FF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    gap: 8,
    borderWidth: 1,
    borderColor: '#BFDBFE',
  },
  learnMoreText: {
    flex: 1,
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
  },
  footer: {
    flexDirection: 'row',
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    gap: 12,
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#6B7280',
  },
  confirmButton: {
    flex: 2,
    borderRadius: 12,
    overflow: 'hidden',
  },
  confirmButtonDisabled: {
    opacity: 0.6,
  },
  confirmButtonGradient: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    gap: 8,
  },
  confirmButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});

