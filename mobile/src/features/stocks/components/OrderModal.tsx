import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  SafeAreaView,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { OrderForm } from './OrderForm';
import { OrderFormState, OrderFormActions } from '../hooks/useOrderForm';
import { PreExecutionRiskCheckModal } from '../../../components/common/PreExecutionRiskCheckModal';
import { LearnWhileTradingModal } from '../../../components/common/LearnWhileTradingModal';

const C = {
  bg: '#F5F6FA',
  card: '#FFFFFF',
  line: '#E9EAF0',
  text: '#111827',
  sub: '#6B7280',
  primary: '#007AFF',
};

interface OrderModalProps {
  visible: boolean;
  onClose: () => void;
  onSubmit: () => Promise<void>;
  isSubmitting?: boolean;
  quoteData?: any;
  quoteLoading?: boolean;
  onSBLOCPress?: () => void;
  form: OrderFormState & OrderFormActions;
}

export const OrderModal: React.FC<OrderModalProps> = ({
  visible,
  onClose,
  onSubmit,
  isSubmitting = false,
  quoteData,
  quoteLoading,
  onSBLOCPress,
  form,
}) => {
  const [showRiskCheck, setShowRiskCheck] = useState(false);
  const [showLearnModal, setShowLearnModal] = useState(false);
  
  const validationError = form.validate();
  const disabled = Boolean(validationError) || isSubmitting;

  const handleSubmit = async () => {
    if (!disabled) {
      // Show risk check if stop loss is set
      if (form.orderType === 'stop_loss' && form.stopPrice) {
        setShowRiskCheck(true);
      } else {
        await onSubmit();
      }
    }
  };
  
  const handleRiskCheckConfirm = async () => {
    setShowRiskCheck(false);
    await onSubmit();
  };
  
  const currentPrice = quoteData?.tradingQuote
    ? (form.orderSide === 'buy' ? quoteData.tradingQuote.ask : quoteData.tradingQuote.bid)
    : 0;
  const stopPrice = form.stopPrice ? parseFloat(form.stopPrice) : undefined;
  const quantity = form.quantity ? parseFloat(form.quantity) : 0;
  const totalRisk = stopPrice && quantity && currentPrice
    ? Math.abs(currentPrice - stopPrice) * quantity
    : undefined;

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <SafeAreaView style={styles.modal}>
        <View style={styles.modalBar} />
        <View style={styles.modalHeader}>
          <Text style={styles.modalTitle}>Place Order</Text>
          <TouchableOpacity onPress={onClose}>
            <Icon name="x" size={24} color={C.text} />
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.scrollContent} showsVerticalScrollIndicator={false}>
          <OrderForm
            form={form}
            quoteData={quoteData}
            quoteLoading={quoteLoading}
            onSBLOCPress={onSBLOCPress}
          />

          <TouchableOpacity
            style={[styles.primaryBtn, disabled && styles.primaryBtnDisabled]}
            onPress={handleSubmit}
            disabled={disabled}
          >
            {isSubmitting ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.primaryBtnText}>Place Order</Text>
            )}
          </TouchableOpacity>

          {/* Help Button */}
          <TouchableOpacity
            style={styles.helpButton}
            onPress={() => setShowLearnModal(true)}
          >
            <Icon name="book-open" size={16} color="#007AFF" />
            <Text style={styles.helpButtonText}>Learn About Trading</Text>
          </TouchableOpacity>

          <View style={{ height: 24 }} />
        </ScrollView>
      </SafeAreaView>
      
      {/* Pre-Execution Risk Check Modal */}
      {form.orderType === 'stop_loss' && stopPrice && (
        <PreExecutionRiskCheckModal
          visible={showRiskCheck}
          onClose={() => setShowRiskCheck(false)}
          onConfirm={handleRiskCheckConfirm}
          symbol={form.symbol.toUpperCase()}
          side={form.orderSide.toUpperCase() as 'BUY' | 'SELL'}
          quantity={quantity}
          entryPrice={currentPrice || (form.price ? parseFloat(form.price) : 0)}
          stopPrice={stopPrice}
          totalRisk={totalRisk}
          onLearnMore={() => {
            setShowRiskCheck(false);
            setShowLearnModal(true);
          }}
        />
      )}
      
      {/* Learn While Trading Modal */}
      <LearnWhileTradingModal
        visible={showLearnModal}
        onClose={() => setShowLearnModal(false)}
        topic={form.orderType === 'stop_loss' ? 'stop_loss' : undefined}
      />
    </Modal>
  );
};

const styles = StyleSheet.create({
  modal: {
    flex: 1,
    backgroundColor: C.bg,
  },
  modalBar: {
    alignSelf: 'center',
    width: 40,
    height: 4,
    backgroundColor: '#D1D5DB',
    borderRadius: 999,
    marginTop: 8,
    marginBottom: 4,
  },
  modalHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 12,
    backgroundColor: C.card,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: C.line,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: C.text,
  },
  scrollContent: {
    paddingHorizontal: 20,
  },
  primaryBtn: {
    backgroundColor: C.primary,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 16,
  },
  primaryBtnDisabled: {
    opacity: 0.6,
  },
  primaryBtnText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '800',
  },
  helpButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
    backgroundColor: '#EFF6FF',
    marginTop: 16,
    gap: 8,
    borderWidth: 1,
    borderColor: '#BFDBFE',
  },
  helpButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
  },
});

