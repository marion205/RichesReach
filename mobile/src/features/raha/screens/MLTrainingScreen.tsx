import React, { useState, useMemo } from "react";
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
  Modal,
  FlatList,
  Pressable,
} from "react-native";
import Icon from "react-native-vector-icons/Feather";
import { useQuery, useMutation } from "@apollo/client";
import { GET_ML_MODELS, TRAIN_ML_MODEL } from "../../../graphql/raha";
import { useStrategies, Strategy } from "../hooks/useStrategies";
import logger from "../../../utils/logger";
import type {
  ExtendedQuery,
  ExtendedMutation,
} from "../../../generated/graphql";

interface MLTrainingScreenProps {
  navigateTo?: (screen: string, params?: any) => void;
  onBack?: () => void;
}

interface MLModel {
  id: string;
  strategy_version_id?: string;
  strategy_name: string;
  symbol?: string;
  model_type: string;
  lookback_days: number;
  training_samples: number;
  metrics: {
    accuracy?: number;
    precision?: number;
    recall?: number;
    f1_score?: number;
    roc_auc?: number;
    mse?: number;
    mae?: number;
    rmse?: number;
  };
  is_active: boolean;
  created_at: string;
  trained_at?: string;
}

export default function MLTrainingScreen({
  navigateTo,
  onBack,
}: MLTrainingScreenProps = {}) {
  const [selectedStrategy, setSelectedStrategy] = useState<string>("");
  const [selectedSymbol, setSelectedSymbol] = useState<string>("");
  const [lookbackDays, setLookbackDays] = useState<string>("90");
  const [selectedModelType, setSelectedModelType] = useState<
    "confidence_predictor" | "win_probability" | "pnl_predictor"
  >("confidence_predictor");
  const [isTraining, setIsTraining] = useState(false);
  const [strategyModalVisible, setStrategyModalVisible] = useState(false);

  const { strategies, loading: strategiesLoading } = useStrategies();
  
  // ✅ Typed queries and mutations (now using generated types!)
  type MLModelsQuery = Pick<ExtendedQuery, 'mlModels'>;
  type TrainMLModelMutation = Pick<ExtendedMutation, 'trainMlModel'>;
  
  const { data, loading, error, refetch } = useQuery<MLModelsQuery>(GET_ML_MODELS);
  const [trainModel] = useMutation<TrainMLModelMutation>(TRAIN_ML_MODEL);

  const models: MLModel[] = useMemo(() => {
    if (!data?.mlModels) {return [];}

    try {
      return data.mlModels.map((item: string) => JSON.parse(item));
    } catch (e) {
      logger.error("Error parsing ML models data:", e);
      return [];
    }
  }, [data]);

  const handleBack = () => {
    if (onBack) {
      onBack();
    } else if (navigateTo) {
      navigateTo("pro-labs");
    } else if (typeof window !== "undefined") {
      if ((window as any).__navigateToGlobal) {
        (window as any).__navigateToGlobal("pro-labs");
      } else if ((window as any).__setCurrentScreen) {
        (window as any).__setCurrentScreen("pro-labs");
      }
    }
  };

  const handleTrainModel = async () => {
    if (isTraining) {return;}

    const days = parseInt(lookbackDays, 10);
    if (isNaN(days) || days < 30 || days > 365) {
      Alert.alert("Invalid Input", "Lookback days must be between 30 and 365");
      return;
    }

    setIsTraining(true);

    try {
      const result = await trainModel({
        variables: {
          strategyVersionId: selectedStrategy || null,
          symbol: selectedSymbol || null,
          lookbackDays: days,
          modelType: selectedModelType,
        },
      });

      if (result.data?.trainMlModel?.success) {
        // Immediately refetch to show the new model
        await refetch();
        Alert.alert(
          "Success",
          `Model trained successfully!\n\nTraining samples: ${result.data.trainMlModel.trainingSamples}\n\nCheck the models list below.`,
          [{ text: "OK", onPress: () => refetch() }]
        );
      } else {
        Alert.alert(
          "Error",
          result.data?.trainMlModel?.message || "Training failed"
        );
      }
    } catch (error: any) {
      logger.error("Error training model:", error);
      Alert.alert("Error", error.message || "Failed to train model");
    } finally {
      setIsTraining(false);
    }
  };

  const formatMetric = (value?: number): string => {
    if (value === undefined || value === null) {return 'N/A';}
    return (value * 100).toFixed(1) + "%";
  };

  if (strategiesLoading || loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity style={styles.backButton} onPress={handleBack}>
            <Icon name="arrow-left" size={24} color="#111827" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>ML Model Training</Text>
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
        <Text style={styles.headerTitle}>ML Model Training</Text>
        <TouchableOpacity onPress={() => refetch()}>
          <Icon name="refresh-cw" size={24} color="#3B82F6" />
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.scrollView}
        showsVerticalScrollIndicator={false}
      >
        {/* Training Form */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Train New Model</Text>

          {/* Strategy Selection */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Strategy (Optional)</Text>
            <View style={styles.pickerContainer}>
              <TouchableOpacity
                style={styles.picker}
                onPress={() => setStrategyModalVisible(true)}
              >
                <Text style={styles.pickerText}>
                  {selectedStrategy
                    ? (strategies || []).find(
                        (s: Strategy) =>
                          s.defaultVersion?.id === selectedStrategy
                      )?.name || "Select Strategy"
                    : "All Strategies"}
                </Text>
                <Icon name="chevron-down" size={20} color="#6B7280" />
              </TouchableOpacity>
            </View>
          </View>

          {/* Strategy picker modal - scrollable list */}
          <Modal
            visible={strategyModalVisible}
            transparent
            animationType="fade"
            onRequestClose={() => setStrategyModalVisible(false)}
          >
            <Pressable
              style={styles.modalOverlay}
              onPress={() => setStrategyModalVisible(false)}
            >
              <Pressable style={styles.modalContent} onPress={(e) => e.stopPropagation()}>
                <Text style={styles.modalTitle}>Select Strategy</Text>
                <Text style={styles.modalSubtitle}>
                  Choose a strategy or leave blank for all strategies
                </Text>
                {(strategies || []).length === 0 && (
                  <Text style={styles.modalEmpty}>
                    No strategies in the catalog yet. Use &quot;All Strategies&quot; below to train on all data.
                  </Text>
                )}
                <FlatList
                  data={[
                    { id: "__all__", name: "All Strategies", versionId: "" },
                    ...(strategies || []).map((s) => ({
                      id: s.defaultVersion?.id || s.id,
                      name: s.name,
                      versionId: s.defaultVersion?.id || "",
                    })),
                  ]}
                  keyExtractor={(item) => item.id}
                  style={styles.strategyList}
                  ListEmptyComponent={null}
                  renderItem={({ item }) => (
                    <TouchableOpacity
                      style={[
                        styles.strategyRow,
                        selectedStrategy === item.versionId && styles.strategyRowSelected,
                      ]}
                      onPress={() => {
                        setSelectedStrategy(item.versionId);
                        setStrategyModalVisible(false);
                      }}
                    >
                      <Text style={styles.strategyRowText}>{item.name}</Text>
                      {selectedStrategy === item.versionId && (
                        <Icon name="check" size={20} color="#3B82F6" />
                      )}
                    </TouchableOpacity>
                  )}
                />
                <TouchableOpacity
                  style={styles.modalCancelButton}
                  onPress={() => setStrategyModalVisible(false)}
                >
                  <Text style={styles.modalCancelText}>Cancel</Text>
                </TouchableOpacity>
              </Pressable>
            </Pressable>
          </Modal>

          {/* Symbol Selection */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Symbol (Optional)</Text>
            <TextInput
              style={styles.input}
              value={selectedSymbol}
              onChangeText={setSelectedSymbol}
              placeholder="e.g., AAPL (leave blank for all symbols)"
              placeholderTextColor="#9CA3AF"
              autoCapitalize="characters"
              maxLength={10}
            />
          </View>

          {/* Model Type */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Model Type</Text>
            <View style={styles.buttonRow}>
              {(
                [
                  "confidence_predictor",
                  "win_probability",
                  "pnl_predictor",
                ] as const
              ).map((type) => (
                <TouchableOpacity
                  key={type}
                  style={[
                    styles.typeButton,
                    selectedModelType === type && styles.typeButtonActive,
                  ]}
                  onPress={() => setSelectedModelType(type)}
                >
                  <Text
                    style={[
                      styles.typeButtonText,
                      selectedModelType === type && styles.typeButtonTextActive,
                    ]}
                  >
                    {type === "confidence_predictor"
                      ? "Confidence"
                      : type === "win_probability"
                      ? "Win Prob"
                      : "P&L"}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          {/* Lookback Days */}
          <View style={styles.inputGroup}>
            <Text style={styles.label}>Lookback Days (30-365)</Text>
            <TextInput
              style={styles.input}
              value={lookbackDays}
              onChangeText={setLookbackDays}
              placeholder="90"
              placeholderTextColor="#9CA3AF"
              keyboardType="numeric"
            />
          </View>

          {/* Train Button */}
          <TouchableOpacity
            style={[
              styles.trainButton,
              isTraining && styles.trainButtonDisabled,
            ]}
            onPress={handleTrainModel}
            disabled={isTraining}
          >
            {isTraining ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <>
                <Icon name="cpu" size={20} color="#FFFFFF" />
                <Text style={styles.trainButtonText}>Train Model</Text>
              </>
            )}
          </TouchableOpacity>
        </View>

        {/* Trained Models List */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            Trained Models ({models.length})
          </Text>

          {models.length === 0 ? (
            <View style={styles.emptyState}>
              <Icon name="cpu" size={48} color="#9CA3AF" />
              <Text style={styles.emptyTitle}>No Models Trained</Text>
              <Text style={styles.emptyText}>
                Train a model using the form above to get started.
              </Text>
            </View>
          ) : (
            models.map((model) => (
              <View key={model.id} style={styles.modelCard}>
                <View style={styles.modelHeader}>
                  <View style={styles.modelHeaderLeft}>
                    <Text style={styles.modelName}>
                      {(model.model_type || "unknown")
                        .replace("_", " ")
                        .toUpperCase()}
                    </Text>
                    <Text style={styles.modelMeta}>
                      {model.strategy_name || "All Strategies"}
                      {model.symbol && ` • ${model.symbol}`}
                    </Text>
                  </View>
                  <View
                    style={[
                      styles.statusBadge,
                      model.is_active !== false && styles.statusBadgeActive,
                    ]}
                  >
                    <Text
                      style={[
                        styles.statusText,
                        model.is_active !== false && styles.statusTextActive,
                      ]}
                    >
                      {model.is_active !== false ? "Active" : "Inactive"}
                    </Text>
                  </View>
                </View>

                <View style={styles.modelMetrics}>
                  <View style={styles.metricRow}>
                    <View key="samples" style={styles.metricItem}>
                      <Text style={styles.metricLabel}>Samples</Text>
                      <Text style={styles.metricValue}>
                        {model.training_samples || 0}
                      </Text>
                    </View>
                    <View key="lookback" style={styles.metricItem}>
                      <Text style={styles.metricLabel}>Lookback</Text>
                      <Text style={styles.metricValue}>
                        {model.lookback_days || 0} days
                      </Text>
                    </View>
                    {model.metrics?.accuracy !== undefined && (
                      <View key="accuracy" style={styles.metricItem}>
                        <Text style={styles.metricLabel}>Accuracy</Text>
                        <Text style={styles.metricValue}>
                          {formatMetric(model.metrics.accuracy)}
                        </Text>
                      </View>
                    )}
                  </View>

                  {model.metrics?.f1_score !== undefined && (
                    <View style={styles.metricRow}>
                      {model.metrics?.precision !== undefined && (
                        <View key="precision" style={styles.metricItem}>
                          <Text style={styles.metricLabel}>Precision</Text>
                          <Text style={styles.metricValue}>
                            {formatMetric(model.metrics.precision)}
                          </Text>
                        </View>
                      )}
                      {model.metrics?.recall !== undefined && (
                        <View key="recall" style={styles.metricItem}>
                          <Text style={styles.metricLabel}>Recall</Text>
                          <Text style={styles.metricValue}>
                            {formatMetric(model.metrics.recall)}
                          </Text>
                        </View>
                      )}
                      <View key="f1-score" style={styles.metricItem}>
                        <Text style={styles.metricLabel}>F1 Score</Text>
                        <Text style={styles.metricValue}>
                          {formatMetric(model.metrics.f1_score)}
                        </Text>
                      </View>
                    </View>
                  )}

                  {model.metrics?.rmse !== undefined && (
                    <View style={styles.metricRow}>
                      <View key="rmse" style={styles.metricItem}>
                        <Text style={styles.metricLabel}>RMSE</Text>
                        <Text style={styles.metricValue}>
                          {model.metrics.rmse?.toFixed(4)}
                        </Text>
                      </View>
                      {model.metrics?.mae !== undefined && (
                        <View key="mae" style={styles.metricItem}>
                          <Text style={styles.metricLabel}>MAE</Text>
                          <Text style={styles.metricValue}>
                            {model.metrics.mae?.toFixed(4)}
                          </Text>
                        </View>
                      )}
                    </View>
                  )}
                </View>

                {model.trained_at && (
                  <Text style={styles.modelDate}>
                    Trained: {new Date(model.trained_at).toLocaleDateString()}
                  </Text>
                )}
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
    backgroundColor: "#FFFFFF",
  },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: "#E5E7EB",
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#111827",
  },
  scrollView: {
    flex: 1,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    padding: 40,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: "#6B7280",
  },
  section: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#E5E7EB",
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 16,
  },
  inputGroup: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: "500",
    color: "#374151",
    marginBottom: 8,
  },
  input: {
    backgroundColor: "#F9FAFB",
    borderWidth: 1,
    borderColor: "#D1D5DB",
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 12,
    fontSize: 16,
    color: "#111827",
  },
  pickerContainer: {
    backgroundColor: "#F9FAFB",
    borderWidth: 1,
    borderColor: "#D1D5DB",
    borderRadius: 8,
  },
  picker: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 12,
    paddingVertical: 12,
  },
  pickerText: {
    fontSize: 16,
    color: "#111827",
  },
  buttonRow: {
    flexDirection: "row",
    gap: 8,
  },
  typeButton: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#D1D5DB",
    backgroundColor: "#FFFFFF",
    alignItems: "center",
  },
  typeButtonActive: {
    backgroundColor: "#3B82F6",
    borderColor: "#3B82F6",
  },
  typeButtonText: {
    fontSize: 14,
    fontWeight: "500",
    color: "#6B7280",
  },
  typeButtonTextActive: {
    color: "#FFFFFF",
  },
  trainButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#3B82F6",
    paddingVertical: 14,
    borderRadius: 8,
    gap: 8,
    marginTop: 8,
  },
  trainButtonDisabled: {
    opacity: 0.6,
  },
  trainButtonText: {
    fontSize: 16,
    fontWeight: "600",
    color: "#FFFFFF",
  },
  emptyState: {
    alignItems: "center",
    padding: 40,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#111827",
    marginTop: 16,
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: "#6B7280",
    textAlign: "center",
  },
  modelCard: {
    backgroundColor: "#F9FAFB",
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  modelHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: 12,
  },
  modelHeaderLeft: {
    flex: 1,
  },
  modelName: {
    fontSize: 16,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 4,
  },
  modelMeta: {
    fontSize: 12,
    color: "#6B7280",
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    backgroundColor: "#F3F4F6",
  },
  statusBadgeActive: {
    backgroundColor: "#D1FAE5",
  },
  statusText: {
    fontSize: 12,
    fontWeight: "500",
    color: "#6B7280",
  },
  statusTextActive: {
    color: "#065F46",
  },
  modelMetrics: {
    marginTop: 12,
  },
  metricRow: {
    flexDirection: "row",
    marginBottom: 12,
    gap: 12,
  },
  metricItem: {
    flex: 1,
  },
  metricLabel: {
    fontSize: 12,
    color: "#6B7280",
    marginBottom: 4,
  },
  metricValue: {
    fontSize: 16,
    fontWeight: "600",
    color: "#111827",
  },
  modelDate: {
    fontSize: 12,
    color: "#6B7280",
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: "#E5E7EB",
  },
  // Strategy picker modal
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  modalContent: {
    backgroundColor: "#FFFFFF",
    borderRadius: 12,
    padding: 20,
    width: "100%",
    maxWidth: 340,
    maxHeight: "80%",
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: "600",
    color: "#111827",
    marginBottom: 8,
  },
  modalSubtitle: {
    fontSize: 14,
    color: "#6B7280",
    marginBottom: 16,
  },
  strategyList: {
    maxHeight: 280,
    marginBottom: 16,
  },
  strategyRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 8,
    marginBottom: 4,
    backgroundColor: "#F9FAFB",
  },
  strategyRowSelected: {
    backgroundColor: "#EFF6FF",
    borderWidth: 1,
    borderColor: "#3B82F6",
  },
  strategyRowText: {
    fontSize: 16,
    color: "#111827",
    flex: 1,
  },
  modalEmpty: {
    fontSize: 14,
    color: "#6B7280",
    textAlign: "center",
    paddingVertical: 16,
  },
  modalCancelButton: {
    paddingVertical: 12,
    alignItems: "center",
  },
  modalCancelText: {
    fontSize: 16,
    color: "#3B82F6",
    fontWeight: "500",
  },
});
