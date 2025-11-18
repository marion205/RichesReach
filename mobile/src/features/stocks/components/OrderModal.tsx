import React from 'react';
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
  const validationError = form.validate();
  const disabled = Boolean(validationError) || isSubmitting;

  const handleSubmit = async () => {
    if (!disabled) {
      await onSubmit();
    }
  };

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

          <View style={{ height: 24 }} />
        </ScrollView>
      </SafeAreaView>
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
});

