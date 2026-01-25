import React, { useState, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  ActivityIndicator,
  Alert,
  TextInput,
} from 'react-native';
import Slider from '@react-native-community/slider';
import Icon from 'react-native-vector-icons/Feather';
import { useQuery, useMutation } from '@apollo/client';
import {
  GET_STRATEGY_BLENDS,
  CREATE_STRATEGY_BLEND,
  UPDATE_STRATEGY_BLEND,
  DELETE_STRATEGY_BLEND,
} from '../../../graphql/raha';
import type {
  StrategyBlendType,
} from '../../../generated/graphql';
import { useStrategies, Strategy } from '../hooks/useStrategies';
import logger from '../../../utils/logger';

interface StrategyBlendBuilderScreenProps {
  navigateTo?: (screen: string, params?: any) => void;
  onBack?: () => void;
}

interface BlendComponent {
  strategyVersionId: string;
  weight: number;
  strategyName?: string;
}

interface StrategyBlend {
  id: string;
  name: string;
  description?: string;
  components: BlendComponent[];
  isActive: boolean;
  isDefault: boolean;
  createdAt: string;
  updatedAt: string;
}

export default function StrategyBlendBuilderScreen({
  navigateTo,
  onBack,
}: StrategyBlendBuilderScreenProps = {}) {
  const [editingBlend, setEditingBlend] = useState<StrategyBlend | null>(null);
  const [blendName, setBlendName] = useState('');
  const [blendDescription, setBlendDescription] = useState('');
  const [selectedStrategies, setSelectedStrategies] = useState<Map<string, number>>(new Map());
  const [isDefault, setIsDefault] = useState(false);

  const { strategies, loading: strategiesLoading } = useStrategies();
  
  const { data, loading, error, refetch } = useQuery<any>(GET_STRATEGY_BLENDS);
  const [createBlend] = useMutation<any>(CREATE_STRATEGY_BLEND);
  const [updateBlend] = useMutation<any>(UPDATE_STRATEGY_BLEND);
  const [deleteBlend] = useMutation<any>(DELETE_STRATEGY_BLEND);

  // ✅ Now using generated StrategyBlendType
  const blends: StrategyBlend[] = useMemo(() => {
    if (!data?.strategyBlends) {
      return [];
    }
    return data.strategyBlends
      .filter((blend): blend is StrategyBlendType => blend !== null && blend !== undefined)
      .map((blend) => ({
        id: blend.id,
        name: blend.name,
        description: blend.description || undefined,
        components: (blend.components || []).map((c) => ({
          strategyVersionId: c?.strategyVersionId || '',
          weight: c?.weight || 0,
          strategyName: c?.strategyName || undefined,
        })),
        isActive: blend.isActive || false,
        isDefault: blend.isDefault || false,
        createdAt: blend.createdAt,
        updatedAt: blend.updatedAt,
      }));
  }, [data]);

  const handleBack = () => {
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
  };

  const startCreating = () => {
    setEditingBlend(null);
    setBlendName('');
    setBlendDescription('');
    setSelectedStrategies(new Map());
    setIsDefault(false);
  };

  const startEditing = (blend: StrategyBlend) => {
    setEditingBlend(blend);
    setBlendName(blend.name);
    setBlendDescription(blend.description || '');
    setIsDefault(blend.isDefault);

    const weights = new Map<string, number>();
    blend.components.forEach(comp => {
      weights.set(comp.strategyVersionId, comp.weight);
    });
    setSelectedStrategies(weights);
  };

  const toggleStrategy = (strategy: Strategy) => {
    const versionId = strategy.defaultVersion?.id;
    if (!versionId) {
      return;
    }

    const newWeights = new Map(selectedStrategies);
    if (newWeights.has(versionId)) {
      newWeights.delete(versionId);
    } else {
      newWeights.set(versionId, 1.0 / (newWeights.size + 1)); // Equal weight initially
    }

    // Normalize weights
    normalizeWeights(newWeights);
    setSelectedStrategies(newWeights);
  };

  const updateWeight = (strategyVersionId: string, weight: number) => {
    const newWeights = new Map(selectedStrategies);
    newWeights.set(strategyVersionId, weight);
    normalizeWeights(newWeights);
    setSelectedStrategies(newWeights);
  };

  const normalizeWeights = (weights: Map<string, number>) => {
    const total = Array.from(weights.values()).reduce((sum, w) => sum + w, 0);
    if (total > 0) {
      weights.forEach((weight, key) => {
        weights.set(key, weight / total);
      });
    } else {
      // Equal weights if total is 0
      const equalWeight = 1.0 / weights.size;
      weights.forEach((_, key) => {
        weights.set(key, equalWeight);
      });
    }
  };

  const handleSave = async () => {
    if (!blendName.trim()) {
      Alert.alert('Error', 'Please enter a name for the blend');
      return;
    }

    if (selectedStrategies.size < 2) {
      Alert.alert('Error', 'A blend must contain at least 2 strategies');
      return;
    }

    const components = Array.from(selectedStrategies.entries()).map(
      ([strategyVersionId, weight]) => ({
        strategy_version_id: strategyVersionId,
        weight: weight,
      }),
    );

    try {
      if (editingBlend) {
        const result = await updateBlend({
          variables: {
            blendId: editingBlend.id,
            name: blendName,
            description: blendDescription || null,
            components: components.map(c => JSON.stringify(c)),
            isDefault: isDefault,
          },
        });

        if (result.data?.updateStrategyBlend?.success) {
          Alert.alert('Success', 'Strategy blend updated successfully');
          await refetch();
          startCreating();
        } else {
          Alert.alert('Error', result.data?.updateStrategyBlend?.message || 'Update failed');
        }
      } else {
        const result = await createBlend({
          variables: {
            name: blendName,
            description: blendDescription || null,
            components: components.map(c => JSON.stringify(c)),
            isDefault: isDefault,
          },
        });

        if (result.data?.createStrategyBlend?.success) {
          Alert.alert('Success', 'Strategy blend created successfully');
          await refetch();
          startCreating();
        } else {
          Alert.alert('Error', result.data?.createStrategyBlend?.message || 'Creation failed');
        }
      }
    } catch (error: any) {
      logger.error('Error saving strategy blend:', error);
      Alert.alert('Error', error.message || 'Failed to save strategy blend');
    }
  };

  const handleDelete = (blend: StrategyBlend) => {
    Alert.alert('Delete Blend', `Are you sure you want to delete "${blend.name}"?`, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            const result = await deleteBlend({
              variables: { blendId: blend.id },
            });

            if (result.data?.deleteStrategyBlend?.success) {
              Alert.alert('Success', 'Strategy blend deleted successfully');
              await refetch();
            } else {
              Alert.alert('Error', result.data?.deleteStrategyBlend?.message || 'Delete failed');
            }
          } catch (error: any) {
            logger.error('Error deleting strategy blend:', error);
            Alert.alert('Error', error.message || 'Failed to delete strategy blend');
          }
        },
      },
    ]);
  };

  const totalWeight = Array.from(selectedStrategies.values()).reduce((sum, w) => sum + w, 0);

  if (strategiesLoading || loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={handleBack}>
            <Icon name="arrow-left" size={24} color="#111827" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>Strategy Blends</Text>
          <View style={{ width: 24 }} />
        </View>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#3B82F6" />
          <Text style={styles.loadingText}>Loading...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity style={styles.backButton} onPress={handleBack}>
          <Icon name="arrow-left" size={24} color="#111827" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Strategy Blends</Text>
        <TouchableOpacity onPress={() => refetch()}>
          <Icon name="refresh-cw" size={24} color="#3B82F6" />
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Create/Edit Form */}
        {editingBlend || selectedStrategies.size > 0 ? (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>
              {editingBlend ? 'Edit Blend' : 'Create New Blend'}
            </Text>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Name *</Text>
              <TextInput
                style={styles.input}
                value={blendName}
                onChangeText={setBlendName}
                placeholder="e.g., Balanced Momentum"
                placeholderTextColor="#9CA3AF"
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Description</Text>
              <TextInput
                style={[styles.input, styles.textArea]}
                value={blendDescription}
                onChangeText={setBlendDescription}
                placeholder="Optional description..."
                placeholderTextColor="#9CA3AF"
                multiline
                numberOfLines={3}
              />
            </View>

            {/* Strategy Selection */}
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Select Strategies (min 2)</Text>
              <View style={styles.strategyList}>
                {(strategies || []).map((strategy: Strategy) => {
                  const versionId = strategy.defaultVersion?.id;
                  if (!versionId) {
                    return null;
                  }

                  const isSelected = selectedStrategies.has(versionId);
                  const weight = selectedStrategies.get(versionId) || 0;

                  return (
                    <View key={strategy.id} style={styles.strategyItem}>
                      <TouchableOpacity
                        style={[styles.strategyToggle, isSelected && styles.strategyToggleActive]}
                        onPress={() => toggleStrategy(strategy)}
                      >
                        <Icon
                          name={isSelected ? 'check-square' : 'square'}
                          size={20}
                          color={isSelected ? '#3B82F6' : '#9CA3AF'}
                        />
                        <Text
                          style={[styles.strategyName, isSelected && styles.strategyNameActive]}
                        >
                          {strategy.name}
                        </Text>
                      </TouchableOpacity>

                      {isSelected && (
                        <View style={styles.weightControl}>
                          <Text style={styles.weightLabel}>{(weight * 100).toFixed(1)}%</Text>
                          <Slider
                            style={styles.slider}
                            minimumValue={0}
                            maximumValue={1}
                            value={weight}
                            onValueChange={value => updateWeight(versionId, value)}
                            minimumTrackTintColor="#3B82F6"
                            maximumTrackTintColor="#E5E7EB"
                            thumbTintColor="#3B82F6"
                          />
                        </View>
                      )}
                    </View>
                  );
                })}
              </View>
            </View>

            {/* Weight Summary */}
            {selectedStrategies.size >= 2 && (
              <View style={styles.weightSummary}>
                <Text style={styles.weightSummaryLabel}>
                  Total Weight: {(totalWeight * 100).toFixed(1)}%
                </Text>
                {Math.abs(totalWeight - 1.0) > 0.01 && (
                  <Text style={styles.weightSummaryWarning}>
                    Weights will be normalized to 100%
                  </Text>
                )}
              </View>
            )}

            {/* Default Toggle */}
            <View style={styles.inputGroup}>
              <TouchableOpacity style={styles.checkboxRow} onPress={() => setIsDefault(!isDefault)}>
                <Icon
                  name={isDefault ? 'check-square' : 'square'}
                  size={20}
                  color={isDefault ? '#3B82F6' : '#9CA3AF'}
                />
                <Text style={styles.checkboxLabel}>
                  Set as default blend (used automatically for signal generation)
                </Text>
              </TouchableOpacity>
            </View>

            {/* Action Buttons */}
            <View style={styles.actionButtons}>
              <TouchableOpacity style={styles.cancelButton} onPress={startCreating}>
                <Text style={styles.cancelButtonText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[
                  styles.saveButton,
                  selectedStrategies.size < 2 && styles.saveButtonDisabled,
                ]}
                onPress={handleSave}
                disabled={selectedStrategies.size < 2}
              >
                <Text style={styles.saveButtonText}>
                  {editingBlend ? 'Update Blend' : 'Create Blend'}
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        ) : (
          <TouchableOpacity style={styles.createButton} onPress={startCreating}>
            <Icon name="plus" size={24} color="#FFFFFF" />
            <Text style={styles.createButtonText}>Create New Blend</Text>
          </TouchableOpacity>
        )}

        {/* Existing Blends */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Your Blends ({blends.length})</Text>

          {blends.length === 0 ? (
            <View style={styles.emptyState}>
              <Icon name="layers" size={48} color="#9CA3AF" />
              <Text style={styles.emptyTitle}>No Blends Created</Text>
              <Text style={styles.emptyText}>
                Create a blend to combine multiple strategies with custom weights.
              </Text>
            </View>
          ) : (
            blends.map(blend => (
              <View key={blend.id} style={styles.blendCard}>
                <View style={styles.blendHeader}>
                  <View style={styles.blendHeaderLeft}>
                    <Text style={styles.blendName}>{blend.name}</Text>
                    {blend.isDefault && (
                      <View style={styles.defaultBadge}>
                        <Text style={styles.defaultBadgeText}>Default</Text>
                      </View>
                    )}
                    {!blend.isActive && (
                      <View style={styles.inactiveBadge}>
                        <Text style={styles.inactiveBadgeText}>Inactive</Text>
                      </View>
                    )}
                  </View>
                  <View style={styles.blendActions}>
                    <TouchableOpacity
                      style={styles.actionButton}
                      onPress={() => startEditing(blend)}
                    >
                      <Icon name="edit-2" size={18} color="#3B82F6" />
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={styles.actionButton}
                      onPress={() => handleDelete(blend)}
                    >
                      <Icon name="trash-2" size={18} color="#EF4444" />
                    </TouchableOpacity>
                  </View>
                </View>

                {blend.description && (
                  <Text style={styles.blendDescription}>{blend.description}</Text>
                )}

                <View style={styles.blendComponents}>
                  {blend.components.map((comp, idx) => (
                    <View key={idx} style={styles.componentItem}>
                      <Text style={styles.componentName}>
                        {comp.strategyName || 'Unknown Strategy'}
                      </Text>
                      <Text style={styles.componentWeight}>{(comp.weight * 100).toFixed(1)}%</Text>
                    </View>
                  ))}
                </View>
              </View>
            ))
          )}
        </View>

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
  scrollView: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6B7280',
  },
  section: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginBottom: 16,
  },
  createButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#3B82F6',
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderRadius: 8,
    margin: 16,
    gap: 8,
  },
  createButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
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
    backgroundColor: '#F9FAFB',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 12,
    fontSize: 16,
    color: '#111827',
  },
  textArea: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  strategyList: {
    gap: 12,
  },
  strategyItem: {
    backgroundColor: '#F9FAFB',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  strategyToggle: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  strategyToggleActive: {
    // Additional styling if needed
  },
  strategyName: {
    fontSize: 16,
    color: '#6B7280',
  },
  strategyNameActive: {
    color: '#111827',
    fontWeight: '500',
  },
  weightControl: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  weightLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#3B82F6',
    marginBottom: 8,
  },
  slider: {
    width: '100%',
    height: 40,
  },
  weightSummary: {
    backgroundColor: '#F0F9FF',
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  weightSummaryLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1E40AF',
  },
  weightSummaryWarning: {
    fontSize: 12,
    color: '#F59E0B',
    marginTop: 4,
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  checkboxLabel: {
    fontSize: 14,
    color: '#374151',
    flex: 1,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  cancelButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#D1D5DB',
    alignItems: 'center',
  },
  cancelButtonText: {
    fontSize: 16,
    fontWeight: '500',
    color: '#6B7280',
  },
  saveButton: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 8,
    backgroundColor: '#3B82F6',
    alignItems: 'center',
  },
  saveButtonDisabled: {
    opacity: 0.5,
  },
  saveButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  emptyState: {
    alignItems: 'center',
    padding: 40,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
  },
  blendCard: {
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  blendHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  blendHeaderLeft: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    flexWrap: 'wrap',
  },
  blendName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  defaultBadge: {
    backgroundColor: '#D1FAE5',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  defaultBadgeText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#065F46',
  },
  inactiveBadge: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  inactiveBadgeText: {
    fontSize: 12,
    fontWeight: '500',
    color: '#6B7280',
  },
  blendActions: {
    flexDirection: 'row',
    gap: 8,
  },
  actionButton: {
    padding: 8,
  },
  blendDescription: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 12,
  },
  blendComponents: {
    gap: 8,
  },
  componentItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
    paddingHorizontal: 12,
    backgroundColor: '#FFFFFF',
    borderRadius: 6,
  },
  componentName: {
    fontSize: 14,
    color: '#374151',
  },
  componentWeight: {
    fontSize: 14,
    fontWeight: '600',
    color: '#3B82F6',
  },
});
