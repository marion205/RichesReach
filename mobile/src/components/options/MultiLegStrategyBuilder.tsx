import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, TextInput, Alert, ActivityIndicator } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useMutation } from '@apollo/client';
import logger from '../../utils/logger';
import { PLACE_MULTI_LEG_OPTIONS_ORDER } from '../../graphql/optionsMutations';
import StrategyPayoffChart from './StrategyPayoffChart';

type LegType = 'call' | 'put';
type LegAction = 'buy' | 'sell';

interface StrategyLeg {
  id: string;
  optionType: LegType;
  action: LegAction;
  strike: string;
  expiration: string;
  quantity: string;
}

interface MultiLegStrategyBuilderProps {
  symbol: string;
  underlyingPrice: number;
  onBuildStrategy: (strategy: {
    name: string;
    legs: StrategyLeg[];
    maxProfit?: number;
    maxLoss?: number;
    breakeven?: number[];
  }) => void;
  onClose: () => void;
}

const STRATEGY_TEMPLATES = [
  { name: 'Bull Call Spread', legs: [{ type: 'call', action: 'buy' }, { type: 'call', action: 'sell' }] },
  { name: 'Bear Put Spread', legs: [{ type: 'put', action: 'buy' }, { type: 'put', action: 'sell' }] },
  { name: 'Straddle', legs: [{ type: 'call', action: 'buy' }, { type: 'put', action: 'buy' }] },
  { name: 'Strangle', legs: [{ type: 'call', action: 'buy' }, { type: 'put', action: 'buy' }] },
  { name: 'Iron Condor', legs: [
    { type: 'call', action: 'sell' },
    { type: 'call', action: 'buy' },
    { type: 'put', action: 'sell' },
    { type: 'put', action: 'buy' },
  ]},
];

export default function MultiLegStrategyBuilder({
  symbol,
  underlyingPrice,
  onBuildStrategy,
  onClose,
}: MultiLegStrategyBuilderProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [legs, setLegs] = useState<StrategyLeg[]>([]);
  const [strategyName, setStrategyName] = useState('');
  const [placingOrder, setPlacingOrder] = useState(false);
  const [placeMultiLegOrder] = useMutation(PLACE_MULTI_LEG_OPTIONS_ORDER);

  const applyTemplate = (template: typeof STRATEGY_TEMPLATES[0]) => {
    setSelectedTemplate(template.name);
    setStrategyName(template.name);
    
    const newLegs: StrategyLeg[] = template.legs.map((leg, index) => ({
      id: `leg-${index}`,
      optionType: leg.type as LegType,
      action: leg.action as LegAction,
      strike: '',
      expiration: '',
      quantity: '1',
    }));
    
    setLegs(newLegs);
  };

  const updateLeg = (id: string, field: keyof StrategyLeg, value: string) => {
    setLegs(legs.map(leg => leg.id === id ? { ...leg, [field]: value } : leg));
  };

  const addLeg = () => {
    setLegs([...legs, {
      id: `leg-${legs.length}`,
      optionType: 'call',
      action: 'buy',
      strike: '',
      expiration: '',
      quantity: '1',
    }]);
  };

  const removeLeg = (id: string) => {
    setLegs(legs.filter(leg => leg.id !== id));
  };

  const validateAndBuild = async () => {
    // Validate all legs have required fields
    for (const leg of legs) {
      if (!leg.strike || !leg.expiration || !leg.quantity) {
        Alert.alert('Validation Error', 'Please fill in all fields for each leg.');
        return;
      }
    }

    if (legs.length < 2) {
      Alert.alert('Validation Error', 'Multi-leg strategies require at least 2 legs.');
      return;
    }

    setPlacingOrder(true);

    try {
      // Prepare legs for GraphQL mutation
      const legsForMutation = legs.map(leg => ({
        option_type: leg.optionType,
        side: leg.action.toUpperCase(),
        strike: parseFloat(leg.strike),
        expiration: leg.expiration,
        quantity: parseInt(leg.quantity) || 1,
        order_type: 'MARKET', // Could make this configurable
        time_in_force: 'DAY',
      }));

      const result = await placeMultiLegOrder({
        variables: {
          symbol: symbol.toUpperCase(),
          legs: legsForMutation,
          strategyName: strategyName || 'Custom Strategy',
        },
      });

      const response = result.data?.placeMultiLegOptionsOrder;

      if (response?.success) {
        Alert.alert(
          'Strategy Executed!',
          `${strategyName || 'Custom Strategy'} placed successfully.\n\nOrder IDs: ${response.orderIds?.join(', ')}`,
          [{ text: 'Done', onPress: onClose }]
        );
        onBuildStrategy({
          name: strategyName || 'Custom Strategy',
          legs,
          maxProfit: 0, // Would calculate from actual fills
          maxLoss: 0,
        });
      } else {
        Alert.alert('Order Failed', response?.error || 'Unknown error occurred');
      }
    } catch (error: any) {
      logger.error('Error placing multi-leg order:', error);
      Alert.alert('Error', error.message || 'Failed to place order. Please try again.');
    } finally {
      setPlacingOrder(false);
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={onClose} style={styles.closeButton}>
          <Icon name="x" size={24} color="#111827" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Build Multi-Leg Strategy</Text>
        <View style={styles.placeholder} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Strategy Templates */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quick Templates</Text>
          <View style={styles.templateGrid}>
            {STRATEGY_TEMPLATES.map((template) => (
              <TouchableOpacity
                key={template.name}
                style={[
                  styles.templateCard,
                  selectedTemplate === template.name && styles.templateCardSelected,
                ]}
                onPress={() => applyTemplate(template)}
              >
                <Text style={[
                  styles.templateName,
                  selectedTemplate === template.name && styles.templateNameSelected,
                ]}>
                  {template.name}
                </Text>
                <Text style={styles.templateLegs}>
                  {template.legs.length} leg{template.legs.length > 1 ? 's' : ''}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Strategy Name */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Strategy Name</Text>
          <TextInput
            style={styles.input}
            value={strategyName}
            onChangeText={setStrategyName}
            placeholder="e.g., Bull Call Spread"
          />
        </View>

        {/* Legs */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Legs ({legs.length})</Text>
            <TouchableOpacity style={styles.addButton} onPress={addLeg}>
              <Icon name="plus" size={16} color="#007AFF" />
              <Text style={styles.addButtonText}>Add Leg</Text>
            </TouchableOpacity>
          </View>

          {legs.map((leg, index) => (
            <View key={leg.id} style={styles.legCard}>
              <View style={styles.legHeader}>
                <Text style={styles.legNumber}>Leg {index + 1}</Text>
                {legs.length > 1 && (
                  <TouchableOpacity onPress={() => removeLeg(leg.id)}>
                    <Icon name="trash-2" size={16} color="#DC2626" />
                  </TouchableOpacity>
                )}
              </View>

              {/* Action & Type */}
              <View style={styles.legRow}>
                <TouchableOpacity
                  style={[styles.legButton, leg.action === 'buy' && styles.legButtonActive]}
                  onPress={() => updateLeg(leg.id, 'action', 'buy')}
                >
                  <Text style={[styles.legButtonText, leg.action === 'buy' && styles.legButtonTextActive]}>
                    Buy
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.legButton, leg.action === 'sell' && styles.legButtonActive]}
                  onPress={() => updateLeg(leg.id, 'action', 'sell')}
                >
                  <Text style={[styles.legButtonText, leg.action === 'sell' && styles.legButtonTextActive]}>
                    Sell
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.legButton, leg.optionType === 'call' && styles.legButtonActive]}
                  onPress={() => updateLeg(leg.id, 'optionType', 'call')}
                >
                  <Text style={[styles.legButtonText, leg.optionType === 'call' && styles.legButtonTextActive]}>
                    Call
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.legButton, leg.optionType === 'put' && styles.legButtonActive]}
                  onPress={() => updateLeg(leg.id, 'optionType', 'put')}
                >
                  <Text style={[styles.legButtonText, leg.optionType === 'put' && styles.legButtonTextActive]}>
                    Put
                  </Text>
                </TouchableOpacity>
              </View>

              {/* Strike, Expiration, Quantity */}
              <View style={styles.legInputs}>
                <View style={styles.inputGroup}>
                  <Text style={styles.inputLabel}>Strike</Text>
                  <TextInput
                    style={styles.input}
                    value={leg.strike}
                    onChangeText={(value) => updateLeg(leg.id, 'strike', value)}
                    keyboardType="numeric"
                    placeholder={`$${underlyingPrice.toFixed(2)}`}
                  />
                </View>
                <View style={styles.inputGroup}>
                  <Text style={styles.inputLabel}>Expiration</Text>
                  <TextInput
                    style={styles.input}
                    value={leg.expiration}
                    onChangeText={(value) => updateLeg(leg.id, 'expiration', value)}
                    placeholder="YYYY-MM-DD"
                  />
                </View>
                <View style={styles.inputGroup}>
                  <Text style={styles.inputLabel}>Quantity</Text>
                  <TextInput
                    style={styles.input}
                    value={leg.quantity}
                    onChangeText={(value) => updateLeg(leg.id, 'quantity', value)}
                    keyboardType="numeric"
                    placeholder="1"
                  />
                </View>
              </View>
            </View>
          ))}

          {legs.length === 0 && (
            <View style={styles.emptyLegs}>
              <Icon name="layers" size={32} color="#D1D5DB" />
              <Text style={styles.emptyLegsText}>No legs added yet</Text>
              <Text style={styles.emptyLegsSubtext}>Select a template or add legs manually</Text>
            </View>
          )}

          {/* Payoff Visualization */}
          {legs.length >= 2 && legs.every(leg => leg.strike && leg.expiration && leg.quantity) && (
            <View style={styles.payoffSection}>
              <StrategyPayoffChart
                legs={legs.map(leg => ({
                  optionType: leg.optionType,
                  action: leg.action,
                  strike: parseFloat(leg.strike) || 0,
                  quantity: parseInt(leg.quantity) || 1,
                }))}
                underlyingPrice={underlyingPrice}
                expirationDays={(() => {
                  try {
                    const expDate = new Date(legs[0].expiration);
                    const today = new Date();
                    return Math.ceil((expDate.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
                  } catch {
                    return 30;
                  }
                })()}
              />
            </View>
          )}
        </View>
      </ScrollView>

      {/* Bottom Actions */}
      <View style={styles.bottomActions}>
        <TouchableOpacity style={styles.cancelButton} onPress={onClose}>
          <Text style={styles.cancelButtonText}>Cancel</Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.buildButton, (legs.length < 2 || placingOrder) && styles.buildButtonDisabled]}
          onPress={validateAndBuild}
          disabled={legs.length < 2 || placingOrder}
        >
          {placingOrder ? (
            <ActivityIndicator size="small" color="#FFFFFF" />
          ) : (
            <Text style={[styles.buildButtonText, legs.length < 2 && styles.buildButtonTextDisabled]}>
              Build Strategy
            </Text>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  closeButton: {
    padding: 4,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
  },
  placeholder: {
    width: 32,
  },
  content: {
    flex: 1,
    paddingHorizontal: 20,
  },
  section: {
    paddingVertical: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 12,
  },
  templateGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  templateCard: {
    width: '48%',
    padding: 12,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: '#E5E7EB',
    backgroundColor: '#FFFFFF',
  },
  templateCardSelected: {
    borderColor: '#007AFF',
    backgroundColor: '#EFF6FF',
  },
  templateName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 4,
  },
  templateNameSelected: {
    color: '#007AFF',
  },
  templateLegs: {
    fontSize: 12,
    color: '#6B7280',
  },
  input: {
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 8,
    padding: 12,
    fontSize: 15,
    color: '#111827',
    backgroundColor: '#FFFFFF',
  },
  legCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  legHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  legNumber: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111827',
  },
  legRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 12,
  },
  legButton: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: '#E5E7EB',
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
  },
  legButtonActive: {
    borderColor: '#007AFF',
    backgroundColor: '#EFF6FF',
  },
  legButtonText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#6B7280',
  },
  legButtonTextActive: {
    color: '#007AFF',
  },
  legInputs: {
    gap: 12,
  },
  inputGroup: {
    gap: 6,
  },
  inputLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#374151',
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1.5,
    borderColor: '#007AFF',
  },
  addButtonText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#007AFF',
  },
  emptyLegs: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyLegsText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
    marginTop: 12,
    marginBottom: 4,
  },
  emptyLegsSubtext: {
    fontSize: 13,
    color: '#9CA3AF',
  },
  payoffSection: {
    marginTop: 20,
    marginBottom: 20,
  },
  bottomActions: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
    gap: 12,
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: '#E5E7EB',
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
  },
  buildButton: {
    flex: 2,
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: '#007AFF',
    alignItems: 'center',
  },
  buildButtonDisabled: {
    backgroundColor: '#E5E7EB',
  },
  buildButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  buildButtonTextDisabled: {
    color: '#9CA3AF',
  },
});

