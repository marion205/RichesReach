import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  TextInput,
  Alert,
  ActivityIndicator,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useMutation } from '@apollo/client';
import { CREATE_CUSTOM_STRATEGY } from '../../../graphql/raha';
import type {
  ExtendedMutation,
} from '../../../generated/graphql';

interface StrategyBuilderScreenProps {
  navigateTo?: (screen: string, params?: any) => void;
  onBack?: () => void;
}

interface StrategyLogic {
  indicators?: Array<{
    type: string;
    window?: number;
  }>;
  entry: {
    type: 'long' | 'short';
    require_all?: boolean;
    conditions: Array<{
      type: 'indicator' | 'price' | 'volume';
      indicator?: string;
      field?: string;
      operator: '>' | '>=' | '<' | '<=' | '==' | '!=';
      value: number | string;
    }>;
  };
  exit: {
    stop_loss?: number;
    take_profit?: number;
    time_stop?: number;
  };
}

export default function StrategyBuilderScreen({
  navigateTo,
  onBack,
}: StrategyBuilderScreenProps = {}) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('MOMENTUM');
  const [marketType, setMarketType] = useState('STOCKS');

  // Strategy logic state
  const [entryType, setEntryType] = useState<'long' | 'short'>('long');
  const [stopLoss, setStopLoss] = useState('2');
  const [takeProfit, setTakeProfit] = useState('4');

  // Conditions
  const [conditions, setConditions] = useState<StrategyLogic['entry']['conditions']>([
    {
      type: 'indicator',
      indicator: 'rsi',
      operator: '>',
      value: 70,
    },
  ]);

  // ✅ Typed mutation (now using generated types!)
  type CreateCustomStrategyMutation = Pick<ExtendedMutation, 'createCustomStrategy'>;
  
  const [createStrategy, { loading }] = useMutation<CreateCustomStrategyMutation>(CREATE_CUSTOM_STRATEGY);

  const handleBack = useCallback(() => {
    if (onBack) {
      onBack();
    } else if (navigateTo) {
      navigateTo('pro-labs');
    } else if (typeof window !== 'undefined') {
      if ((window as any).__navigateToGlobal) {
        (window as any).__navigateToGlobal('pro-labs');
      } else if ((window as any).__setCurrentScreen) {
        (window as any).__setCurrentScreen('pro-labs');
      }
    }
  }, [navigateTo, onBack]);

  const handleSave = useCallback(async () => {
    if (!name.trim() || !description.trim()) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    // Build custom logic
    const customLogic: StrategyLogic = {
      indicators: [{ type: 'rsi' }, { type: 'sma', window: 20 }, { type: 'sma', window: 50 }],
      entry: {
        type: entryType,
        require_all: true,
        conditions: conditions,
      },
      exit: {
        stop_loss: parseFloat(stopLoss) / 100, // Convert to decimal
        take_profit: parseFloat(takeProfit) / 100,
        time_stop: 240, // 4 hours
      },
    };

    try {
      const result = await createStrategy({
        variables: {
          name: name.trim(),
          description: description.trim(),
          category,
          marketType,
          timeframeSupported: ['5m', '15m', '1h'],
          customLogic: JSON.stringify(customLogic),
          configSchema: JSON.stringify({}),
        },
      });

      if (result.data?.createCustomStrategy?.success) {
        Alert.alert('Success', 'Custom strategy created successfully!', [
          {
            text: 'OK',
            onPress: () => handleBack(),
          },
        ]);
      } else {
        Alert.alert(
          'Error',
          result.data?.createCustomStrategy?.message || 'Failed to create strategy'
        );
      }
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to create strategy');
    }
  }, [
    name,
    description,
    category,
    marketType,
    entryType,
    stopLoss,
    takeProfit,
    conditions,
    createStrategy,
    handleBack,
  ]);

  const addCondition = useCallback(() => {
    setConditions([
      ...conditions,
      {
        type: 'indicator',
        indicator: 'rsi',
        operator: '>',
        value: 50,
      },
    ]);
  }, [conditions]);

  const removeCondition = useCallback(
    (index: number) => {
      setConditions(conditions.filter((_, i) => i !== index));
    },
    [conditions],
  );

  const updateCondition = useCallback(
    (index: number, field: string, value: any) => {
      const updated = [...conditions];
      updated[index] = { ...updated[index], [field]: value };
      setConditions(updated);
    },
    [conditions],
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={handleBack}>
          <Icon name="arrow-left" size={24} color="#111827" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Strategy Builder</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Basic Info */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Basic Information</Text>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Strategy Name *</Text>
            <TextInput
              style={styles.input}
              value={name}
              onChangeText={setName}
              placeholder="e.g., My Custom Momentum Strategy"
              placeholderTextColor="#9CA3AF"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Description *</Text>
            <TextInput
              style={[styles.input, styles.textArea]}
              value={description}
              onChangeText={setDescription}
              placeholder="Describe your strategy..."
              placeholderTextColor="#9CA3AF"
              multiline
              numberOfLines={4}
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Category</Text>
            <View style={styles.buttonRow}>
              {['MOMENTUM', 'REVERSAL', 'SWING'].map(cat => (
                <TouchableOpacity
                  key={cat}
                  style={[styles.categoryButton, category === cat && styles.categoryButtonActive]}
                  onPress={() => setCategory(cat)}
                >
                  <Text
                    style={[
                      styles.categoryButtonText,
                      category === cat && styles.categoryButtonTextActive,
                    ]}
                  >
                    {cat}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        </View>

        {/* Entry Conditions */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Entry Conditions</Text>
            <TouchableOpacity style={styles.addButton} onPress={addCondition}>
              <Icon name="plus" size={20} color="#3B82F6" />
              <Text style={styles.addButtonText}>Add Condition</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Entry Type</Text>
            <View style={styles.buttonRow}>
              <TouchableOpacity
                style={[styles.entryButton, entryType === 'long' && styles.entryButtonActive]}
                onPress={() => setEntryType('long')}
              >
                <Text
                  style={[
                    styles.entryButtonText,
                    entryType === 'long' && styles.entryButtonTextActive,
                  ]}
                >
                  Long
                </Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.entryButton, entryType === 'short' && styles.entryButtonActive]}
                onPress={() => setEntryType('short')}
              >
                <Text
                  style={[
                    styles.entryButtonText,
                    entryType === 'short' && styles.entryButtonTextActive,
                  ]}
                >
                  Short
                </Text>
              </TouchableOpacity>
            </View>
          </View>

          {conditions.map((condition, index) => (
            <View key={index} style={styles.conditionCard}>
              <View style={styles.conditionHeader}>
                <Text style={styles.conditionTitle}>Condition {index + 1}</Text>
                <TouchableOpacity onPress={() => removeCondition(index)}>
                  <Icon name="x" size={20} color="#EF4444" />
                </TouchableOpacity>
              </View>

              <View style={styles.conditionRow}>
                <Text style={styles.conditionLabel}>Type:</Text>
                <View style={styles.buttonRow}>
                  {['indicator', 'price', 'volume'].map(type => (
                    <TouchableOpacity
                      key={type}
                      style={[
                        styles.conditionTypeButton,
                        condition.type === type && styles.conditionTypeButtonActive,
                      ]}
                      onPress={() => updateCondition(index, 'type', type)}
                    >
                      <Text
                        style={[
                          styles.conditionTypeButtonText,
                          condition.type === type && styles.conditionTypeButtonTextActive,
                        ]}
                      >
                        {type}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>

              {condition.type === 'indicator' && (
                <View style={styles.conditionRow}>
                  <Text style={styles.conditionLabel}>Indicator:</Text>
                  <View style={styles.buttonRow}>
                    {['rsi', 'macd', 'sma_20', 'sma_50'].map(ind => (
                      <TouchableOpacity
                        key={ind}
                        style={[
                          styles.conditionValueButton,
                          condition.indicator === ind && styles.conditionValueButtonActive,
                        ]}
                        onPress={() => updateCondition(index, 'indicator', ind)}
                      >
                        <Text
                          style={[
                            styles.conditionValueButtonText,
                            condition.indicator === ind && styles.conditionValueButtonTextActive,
                          ]}
                        >
                          {ind.toUpperCase()}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                </View>
              )}

              <View style={styles.conditionRow}>
                <Text style={styles.conditionLabel}>Operator:</Text>
                <View style={styles.buttonRow}>
                  {['>', '>=', '<', '<='].map(op => (
                    <TouchableOpacity
                      key={op}
                      style={[
                        styles.conditionValueButton,
                        condition.operator === op && styles.conditionValueButtonActive,
                      ]}
                      onPress={() => updateCondition(index, 'operator', op)}
                    >
                      <Text
                        style={[
                          styles.conditionValueButtonText,
                          condition.operator === op && styles.conditionValueButtonTextActive,
                        ]}
                      >
                        {op}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </View>
              </View>

              <View style={styles.conditionRow}>
                <Text style={styles.conditionLabel}>Value:</Text>
                <TextInput
                  style={styles.conditionValueInput}
                  value={String(condition.value)}
                  onChangeText={text => {
                    const numValue = parseFloat(text);
                    updateCondition(index, 'value', isNaN(numValue) ? text : numValue);
                  }}
                  placeholder="Value"
                  placeholderTextColor="#9CA3AF"
                  keyboardType="numeric"
                />
              </View>
            </View>
          ))}
        </View>

        {/* Exit Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Exit Settings</Text>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Stop Loss (%)</Text>
            <TextInput
              style={styles.input}
              value={stopLoss}
              onChangeText={setStopLoss}
              placeholder="2"
              placeholderTextColor="#9CA3AF"
              keyboardType="numeric"
            />
          </View>

          <View style={styles.inputGroup}>
            <Text style={styles.label}>Take Profit (%)</Text>
            <TextInput
              style={styles.input}
              value={takeProfit}
              onChangeText={setTakeProfit}
              placeholder="4"
              placeholderTextColor="#9CA3AF"
              keyboardType="numeric"
            />
          </View>
        </View>

        {/* Save Button */}
        <TouchableOpacity
          style={[styles.saveButton, loading && styles.saveButtonDisabled]}
          onPress={handleSave}
          disabled={loading}
        >
          {loading ? (
            <ActivityIndicator color="#FFFFFF" />
          ) : (
            <>
              <Icon name="save" size={20} color="#FFFFFF" />
              <Text style={styles.saveButtonText}>Create Strategy</Text>
            </>
          )}
        </TouchableOpacity>

        <View style={{ height: 40 }} />
      </ScrollView>
    </SafeAreaView>
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
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  section: {
    marginBottom: 24,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  inputGroup: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: '#374151',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#111827',
    backgroundColor: '#FFFFFF',
  },
  textArea: {
    height: 100,
    textAlignVertical: 'top',
  },
  buttonRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  categoryButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    backgroundColor: '#FFFFFF',
  },
  categoryButtonActive: {
    backgroundColor: '#3B82F6',
    borderColor: '#3B82F6',
  },
  categoryButtonText: {
    fontSize: 14,
    color: '#6B7280',
  },
  categoryButtonTextActive: {
    color: '#FFFFFF',
  },
  entryButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    backgroundColor: '#FFFFFF',
    alignItems: 'center',
  },
  entryButtonActive: {
    backgroundColor: '#3B82F6',
    borderColor: '#3B82F6',
  },
  entryButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#6B7280',
  },
  entryButtonTextActive: {
    color: '#FFFFFF',
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: '#EFF6FF',
  },
  addButtonText: {
    fontSize: 14,
    color: '#3B82F6',
    marginLeft: 4,
  },
  conditionCard: {
    borderWidth: 1,
    borderColor: '#E5E7EB',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
    backgroundColor: '#F9FAFB',
  },
  conditionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  conditionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#111827',
  },
  conditionRow: {
    marginBottom: 12,
  },
  conditionLabel: {
    fontSize: 12,
    fontWeight: '500',
    color: '#6B7280',
    marginBottom: 8,
  },
  conditionTypeButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    backgroundColor: '#FFFFFF',
    marginRight: 8,
  },
  conditionTypeButtonActive: {
    backgroundColor: '#3B82F6',
    borderColor: '#3B82F6',
  },
  conditionTypeButtonText: {
    fontSize: 12,
    color: '#6B7280',
  },
  conditionTypeButtonTextActive: {
    color: '#FFFFFF',
  },
  conditionValueButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    backgroundColor: '#FFFFFF',
    marginRight: 8,
  },
  conditionValueButtonActive: {
    backgroundColor: '#3B82F6',
    borderColor: '#3B82F6',
  },
  conditionValueButtonText: {
    fontSize: 12,
    color: '#6B7280',
  },
  conditionValueButtonTextActive: {
    color: '#FFFFFF',
  },
  conditionValueInput: {
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 6,
    padding: 8,
    fontSize: 14,
    color: '#111827',
    backgroundColor: '#FFFFFF',
    minWidth: 100,
  },
  saveButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#3B82F6',
    paddingVertical: 16,
    borderRadius: 12,
    marginTop: 24,
  },
  saveButtonDisabled: {
    opacity: 0.6,
  },
  saveButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
    marginLeft: 8,
  },
});
