import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Modal,
  ActivityIndicator,
  Alert,
  Platform,
} from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useQuery, useMutation } from '@apollo/client';
import LottieView from 'lottie-react-native';

import { RepairShield, GreeksRadarChart, PositionCardWithRepair, ShieldStatusBar } from '../../components/options/RepairShield';
import {
  GET_PORTFOLIO_WITH_REPAIRS,
  GET_POSITION_WITH_REPAIR,
  ACCEPT_REPAIR_PLAN,
  EXECUTE_BULK_REPAIRS,
  GET_PORTFOLIO_HEALTH,
  GET_REPAIR_HISTORY,
  GET_FLIGHT_MANUAL_FOR_REPAIR,
  REPAIR_PLAN_UPDATES,
} from '../../graphql/repairs.graphql';

interface Position {
  id: string;
  ticker: string;
  strategyType: string;
  unrealizedPnl: number;
  daysToExpiration: number;
  greeks: {
    delta: number;
    gamma: number;
    theta: number;
    vega: number;
    rho: number;
  };
  maxLoss: number;
  probabilityOfProfit: number;
}

interface RepairPlan {
  positionId: string;
  ticker: string;
  originalStrategy: string;
  currentDelta: number;
  deltaDriftPct: number;
  currentMaxLoss: number;
  repairType: string;
  repairStrikes: string;
  repairCredit: number;
  newMaxLoss: number;
  newBreakEven: number;
  confidenceBoost: number;
  headline: string;
  reason: string;
  actionDescription: string;
  priority: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
}

interface PortfolioState {
  totalDelta: number;
  totalGamma: number;
  totalTheta: number;
  totalVega: number;
  portfolioHealthStatus: 'healthy' | 'warning' | 'critical';
  repairsAvailable: number;
  totalMaxLoss: number;
}

interface ActiveRepairWorkflowProps {
  userId?: string;
  accountId?: string;
  onRefresh?: () => void;
}

/**
 * Active Repair Workflow
 * 
 * Complete user flow:
 * 1. Load portfolio and repair plans
 * 2. Show portfolio health overview
 * 3. Display positions with repair badges
 * 4. Modal: Show repair plan details with Greeks comparison
 * 5. Action: Accept/Reject with confirmation
 * 6. Success: Show trade execution confirmation
 */
export const ActiveRepairWorkflow: React.FC<ActiveRepairWorkflowProps> = ({
  userId = 'default-user',
  accountId = 'default-account',
  onRefresh,
}) => {
  const insets = useSafeAreaInsets();
  const [selectedRepair, setSelectedRepair] = useState<RepairPlan | null>(null);
  const [showRepairModal, setShowRepairModal] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [repairAccepted, setRepairAccepted] = useState<RepairPlan | null>(null);

  // GraphQL Queries
  const { data: portfolioData, loading: portfolioLoading, error: portfolioError, refetch: refetchPortfolio } = useQuery(
    GET_PORTFOLIO_WITH_REPAIRS,
    {
      variables: { user_id: userId, account_id: accountId },
      pollInterval: 30000, // Poll every 30 seconds
      errorPolicy: 'all', // Continue even if there are errors
    }
  );

  // GraphQL Mutations
  const [acceptRepairMutation, { loading: acceptLoading }] = useMutation(
    ACCEPT_REPAIR_PLAN,
    {
      onCompleted: (data) => {
        setIsProcessing(false);
        setSuccessMessage(`✓ Repair deployed! ${data.acceptRepairPlan.execution_message}`);
        setShowSuccessModal(true);
        setTimeout(() => {
          setShowRepairModal(false);
          setShowSuccessModal(false);
          refetchPortfolio();
        }, 2000);
      },
      onError: (error) => {
        setIsProcessing(false);
        Alert.alert('Repair Failed', error.message);
      },
    }
  );

  if (portfolioLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#3B82F6" />
        <Text style={styles.loadingText}>Loading your portfolio...</Text>
      </View>
    );
  }

  if (portfolioError) {
    return (
      <View style={styles.loadingContainer}>
        <Text style={styles.errorText}>Unable to load portfolio</Text>
        <Text style={styles.errorSubtext}>{portfolioError.message}</Text>
        <TouchableOpacity 
          style={styles.retryButton}
          onPress={() => refetchPortfolio()}
        >
          <Text style={styles.retryText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const portfolio: PortfolioState = portfolioData?.portfolio || {};
  const positions: Position[] = portfolioData?.positions || [];
  const repairPlans: RepairPlan[] = portfolioData?.repair_plans || [];

  // Map repair plans to positions
  const positionsWithRepairs = positions.map((pos) => ({
    position: pos,
    repair: repairPlans.find((rp) => rp.positionId === pos.id),
  }));

  const handleSelectRepair = (repair: RepairPlan) => {
    setSelectedRepair(repair);
    setShowRepairModal(true);
  };

  const handleAcceptRepair = async () => {
    if (!selectedRepair) return;

    setIsProcessing(true);
    setRepairAccepted(selectedRepair);

    try {
      await acceptRepairMutation({
        variables: {
          position_id: selectedRepair.positionId,
          repair_plan_id: selectedRepair.positionId, // Assuming this ID structure
          user_id: userId,
        },
      });
    } catch (error) {
      console.error('Error accepting repair:', error);
    }
  };

  const handleRejectRepair = () => {
    setSelectedRepair(null);
    setShowRepairModal(false);
  };

  // Get portfolio health status
  const getHealthStatus = () => {
    switch (portfolio.portfolioHealthStatus) {
      case 'critical':
        return 'critical';
      case 'warning':
        return 'warning';
      default:
        return 'healthy';
    }
  };

  return (
    <View style={[styles.container, { paddingTop: insets.top, paddingBottom: insets.bottom }]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>🛡️ Active Repairs</Text>
        <TouchableOpacity onPress={() => refetchPortfolio()}>
          <Text style={styles.refreshButton}>↻</Text>
        </TouchableOpacity>
      </View>

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
        {/* Health Status Bar */}
        <ShieldStatusBar
          status={getHealthStatus()}
          priority={
            repairPlans.length > 0
              ? repairPlans.reduce((max, rp) => {
                  const priorityOrder = { CRITICAL: 3, HIGH: 2, MEDIUM: 1, LOW: 0 };
                  return priorityOrder[rp.priority] > priorityOrder[max] ? rp.priority : max;
                }, repairPlans[0].priority)
              : undefined
          }
        />

        {/* Portfolio Overview Cards */}
        <View style={styles.overviewGrid}>
          <View style={styles.overviewCard}>
            <Text style={styles.overviewLabel}>Portfolio Delta</Text>
            <Text style={[styles.overviewValue, { color: Math.abs(portfolio.totalDelta) > 0.5 ? '#EF4444' : '#10B981' }]}>
              {portfolio.totalDelta.toFixed(2)}
            </Text>
          </View>

          <View style={styles.overviewCard}>
            <Text style={styles.overviewLabel}>Max Daily Loss</Text>
            <Text style={styles.overviewValue}>
              ${Math.abs(portfolio.totalMaxLoss).toFixed(0)}
            </Text>
          </View>

          <View style={styles.overviewCard}>
            <Text style={styles.overviewLabel}>Active Repairs</Text>
            <Text style={[styles.overviewValue, { color: portfolio.repairsAvailable > 0 ? '#DC2626' : '#10B981' }]}>
              {portfolio.repairsAvailable}
            </Text>
          </View>

          <View style={styles.overviewCard}>
            <Text style={styles.overviewLabel}>Theta Decay</Text>
            <Text style={[styles.overviewValue, { color: portfolio.totalTheta > 0 ? '#10B981' : '#EF4444' }]}>
              ${portfolio.totalTheta.toFixed(0)}/day
            </Text>
          </View>
        </View>

        {/* Portfolio Greeks Radar */}
        {portfolio.totalDelta !== undefined && (
          <View style={styles.radarSection}>
            <GreeksRadarChart
              greeks={{
                delta: portfolio.totalDelta,
                gamma: portfolio.totalGamma,
                theta: portfolio.totalTheta,
                vega: portfolio.totalVega,
                rho: 0, // Often omitted from portfolio view
              }}
              title="Portfolio Greeks Profile"
            />
          </View>
        )}

        {/* Active Repairs Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            Active Repairs ({repairPlans.length})
          </Text>

          {repairPlans.length === 0 ? (
            <View style={styles.emptyState}>
              <Text style={styles.emptyEmoji}>✓</Text>
              <Text style={styles.emptyTitle}>All Positions Healthy</Text>
              <Text style={styles.emptySubtitle}>
                No repairs needed. Your portfolio is well-balanced.
              </Text>
            </View>
          ) : (
            repairPlans.map((repair) => (
              <TouchableOpacity
                key={repair.positionId}
                onPress={() => handleSelectRepair(repair)}
                activeOpacity={0.7}
              >
                <RepairShield
                  repairPlan={repair}
                  onAccept={() => handleSelectRepair(repair)}
                  onReject={() => {}}
                  loading={isProcessing && repairAccepted?.positionId === repair.positionId}
                />
              </TouchableOpacity>
            ))
          )}
        </View>

        {/* Open Positions Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            Open Positions ({positions.length})
          </Text>

          {positions.map((position) => {
            const posWithRepair = positionsWithRepairs.find((pwr) => pwr.position.id === position.id);
            return (
              <PositionCardWithRepair
                key={position.id}
                position={position}
                repairPlan={posWithRepair?.repair}
                onShowRepair={() => posWithRepair?.repair && handleSelectRepair(posWithRepair.repair)}
              />
            );
          })}
        </View>
      </ScrollView>

      {/* Repair Detail Modal */}
      <Modal
        visible={showRepairModal}
        animationType="slide"
        transparent={false}
        onRequestClose={handleRejectRepair}
      >
        <View style={[styles.modal, { paddingTop: insets.top }]}>
          {/* Modal Header */}
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={handleRejectRepair}>
              <Text style={styles.modalCloseButton}>✕</Text>
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Repair Plan Details</Text>
            <View style={{ width: 24 }} />
          </View>

          <ScrollView contentContainerStyle={styles.modalContent}>
            {selectedRepair && (
              <>
                {/* Repair Headline */}
                <View style={styles.detailSection}>
                  <Text style={styles.detailHeadline}>{selectedRepair.headline}</Text>
                  <Text style={styles.detailReason}>{selectedRepair.reason}</Text>
                </View>

                {/* Current vs Repaired Greeks Comparison */}
                <View style={styles.comparisonSection}>
                  <Text style={styles.comparisonTitle}>Greeks Comparison</Text>

                  <View style={styles.comparisonGrid}>
                    {/* Delta Comparison */}
                    <View style={styles.comparisonItem}>
                      <Text style={styles.comparisonLabel}>Delta Drift</Text>
                      <Text style={styles.comparisonBefore}>
                        Current: {selectedRepair.currentDelta.toFixed(2)}
                      </Text>
                      <Text style={styles.comparisonAfter}>
                        Target: ~0.10 (Neutral)
                      </Text>
                    </View>
                  </View>
                </View>

                {/* Repair Details */}
                <View style={styles.detailSection}>
                  <Text style={styles.sectionTitle}>Recommended Action</Text>

                  <View style={styles.actionDetail}>
                    <View style={styles.actionRow}>
                      <Text style={styles.actionRowLabel}>Strategy</Text>
                      <Text style={styles.actionRowValue}>{selectedRepair.repairType}</Text>
                    </View>
                    <View style={styles.actionRow}>
                      <Text style={styles.actionRowLabel}>Strikes</Text>
                      <Text style={styles.actionRowValue}>{selectedRepair.repairStrikes}</Text>
                    </View>
                    <View style={styles.actionRow}>
                      <Text style={styles.actionRowLabel}>Credit</Text>
                      <Text style={[styles.actionRowValue, { color: '#10B981' }]}>
                        +${selectedRepair.repairCredit.toFixed(0)}
                      </Text>
                    </View>
                  </View>
                </View>

                {/* Risk Reduction */}
                <View style={styles.detailSection}>
                  <Text style={styles.sectionTitle}>Risk Reduction</Text>

                  <View style={styles.riskReductionBox}>
                    <View style={styles.riskRow}>
                      <Text style={styles.riskLabel}>Current Max Loss</Text>
                      <Text style={styles.riskValue}>
                        ${selectedRepair.currentMaxLoss.toFixed(0)}
                      </Text>
                    </View>
                    <View style={styles.riskArrow}>
                      <Text style={styles.riskArrowText}>→</Text>
                    </View>
                    <View style={styles.riskRow}>
                      <Text style={styles.riskLabel}>After Repair</Text>
                      <Text style={[styles.riskValue, { color: '#10B981' }]}>
                        ${selectedRepair.newMaxLoss.toFixed(0)}
                      </Text>
                    </View>
                  </View>

                  <Text style={styles.riskSubtext}>
                    Reduces max loss by ${(selectedRepair.currentMaxLoss - selectedRepair.newMaxLoss).toFixed(0)}
                  </Text>
                </View>

                {/* Confidence Boost */}
                <View
                  style={[
                    styles.detailSection,
                    {
                      backgroundColor: '#ECFDF5',
                      borderRadius: 8,
                      padding: 12,
                    },
                  ]}
                >
                  <Text style={styles.sectionTitle}>Edge Boost</Text>
                  <Text style={{ fontSize: 14, color: '#047857', marginTop: 8 }}>
                    This repair increases your statistical edge by{' '}
                    <Text style={{ fontWeight: '700' }}>+{(selectedRepair.confidenceBoost * 100).toFixed(0)}%</Text>.
                  </Text>
                </View>

                {/* Flight Manual Link */}
                <TouchableOpacity style={styles.flightManualButton}>
                  <Text style={styles.flightManualButtonText}>📖 Read Flight Manual for {selectedRepair.repairType}</Text>
                </TouchableOpacity>
              </>
            )}
          </ScrollView>

          {/* Modal Footer Buttons */}
          <View style={[styles.modalFooter, { paddingBottom: insets.bottom + 16 }]}>
            <TouchableOpacity
              style={styles.rejectButton}
              onPress={handleRejectRepair}
              disabled={isProcessing}
            >
              <Text style={styles.rejectButtonText}>Review Later</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.acceptButtonLarge}
              onPress={handleAcceptRepair}
              disabled={isProcessing}
            >
              {isProcessing ? (
                <ActivityIndicator color="white" />
              ) : (
                <Text style={styles.acceptButtonText}>✓ ACCEPT & DEPLOY</Text>
              )}
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* Success Modal */}
      <Modal
        visible={showSuccessModal}
        animationType="fade"
        transparent={true}
        onRequestClose={() => setShowSuccessModal(false)}
      >
        <View style={styles.successOverlay}>
          <View style={styles.successBox}>
            <View style={styles.successAnimation}>
              <Text style={styles.successEmoji}>✓</Text>
            </View>
            <Text style={styles.successTitle}>{successMessage}</Text>
            <Text style={styles.successSubtitle}>
              Your repair plan has been executed. Position is now delta-neutral.
            </Text>
          </View>
        </View>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },

  // Header
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1F2937',
  },
  refreshButton: {
    fontSize: 20,
    color: '#3B82F6',
    padding: 8,
  },

  // Loading
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F9FAFB',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#6B7280',
  },
  errorText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#EF4444',
    marginBottom: 8,
  },
  errorSubtext: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 16,
    textAlign: 'center',
  },
  retryButton: {
    backgroundColor: '#3B82F6',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
  },
  retryText: {
    color: 'white',
    fontWeight: '600',
    fontSize: 14,
  },

  // Scroll Content
  scrollContent: {
    paddingBottom: 32,
  },

  // Overview Grid
  overviewGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 8,
    paddingVertical: 12,
  },
  overviewCard: {
    width: '50%',
    paddingHorizontal: 8,
    marginBottom: 12,
  },
  overviewCardContent: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  overviewLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 6,
  },
  overviewValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1F2937',
  },

  // Sections
  section: {
    marginHorizontal: 16,
    marginTop: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 12,
  },

  // Radar Section
  radarSection: {
    marginHorizontal: 16,
    marginVertical: 16,
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
  },

  // Empty State
  emptyState: {
    alignItems: 'center',
    paddingVertical: 32,
    backgroundColor: 'white',
    borderRadius: 12,
  },
  emptyEmoji: {
    fontSize: 48,
    marginBottom: 12,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 4,
  },
  emptySubtitle: {
    fontSize: 13,
    color: '#6B7280',
    textAlign: 'center',
  },

  // Modal Styles
  modal: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1F2937',
  },
  modalCloseButton: {
    fontSize: 24,
    color: '#6B7280',
    padding: 4,
  },
  modalContent: {
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 120,
  },

  // Detail Sections
  detailSection: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  detailHeadline: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 8,
  },
  detailReason: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },

  // Comparison Section
  comparisonSection: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  comparisonTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 12,
  },
  comparisonGrid: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  comparisonItem: {
    flex: 1,
    alignItems: 'center',
  },
  comparisonLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 8,
  },
  comparisonBefore: {
    fontSize: 13,
    color: '#EF4444',
    marginBottom: 4,
  },
  comparisonAfter: {
    fontSize: 13,
    color: '#10B981',
    fontWeight: '600',
  },

  // Action Detail
  actionDetail: {
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    padding: 12,
    marginTop: 12,
  },
  actionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 8,
  },
  actionRowLabel: {
    fontSize: 13,
    color: '#6B7280',
  },
  actionRowValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1F2937',
  },

  // Risk Reduction
  riskReductionBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    padding: 12,
    marginTop: 12,
  },
  riskRow: {
    flex: 1,
  },
  riskLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
  },
  riskValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1F2937',
  },
  riskArrow: {
    alignItems: 'center',
    marginHorizontal: 8,
  },
  riskArrowText: {
    fontSize: 18,
    color: '#D1D5DB',
  },
  riskSubtext: {
    fontSize: 12,
    color: '#10B981',
    marginTop: 8,
    fontWeight: '500',
  },

  // Flight Manual Button
  flightManualButton: {
    backgroundColor: 'white',
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    alignItems: 'center',
  },
  flightManualButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#3B82F6',
  },

  // Modal Footer
  modalFooter: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    gap: 12,
    paddingHorizontal: 16,
    paddingTop: 12,
    backgroundColor: 'white',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  rejectButton: {
    flex: 1,
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
  },
  rejectButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6B7280',
  },
  acceptButtonLarge: {
    flex: 1,
    backgroundColor: '#3B82F6',
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  acceptButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: 'white',
  },

  // Success Modal
  successOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 32,
  },
  successBox: {
    backgroundColor: 'white',
    borderRadius: 16,
    paddingVertical: 32,
    paddingHorizontal: 24,
    alignItems: 'center',
  },
  successAnimation: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#ECFDF5',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  successEmoji: {
    fontSize: 40,
    color: '#10B981',
  },
  successTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1F2937',
    marginBottom: 8,
    textAlign: 'center',
  },
  successSubtitle: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 20,
  },
});

export default ActiveRepairWorkflow;
