import React, { useMemo, useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Switch,
  Modal,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { gql, useQuery, useMutation } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import UI from '../../../shared/constants';
import logger from '../../../utils/logger';

const AUTOPILOT_QUERY = gql`
  query AutopilotCommand {
    autopilotStatus {
      enabled
      lastEvaluatedAt
      lastMove {
        id
        fromVault
        toVault
        executedAt
        canRevert
        revertDeadline
      }
      policy {
        targetApy
        maxDrawdown
        riskLevel
        level
        spendLimit24h
      }
    }
    pendingRepairs {
      id
      fromVault
      toVault
      estimatedApyDelta
      gasEstimate
      proof {
        calmarImprovement
        tvlStabilityCheck
        policyAlignment
        explanation
        policyVersion
        guardrails
        integrityCheck {
          altmanZScore
          beneishMScore
          isErc4626Compliant
        }
      }
    }
  }
`;

const UPDATE_POLICY = gql`
  mutation UpdateAutopilotPolicy($input: AutopilotPolicyInput!) {
    updateAutopilotPolicy(input: $input) {
      policy {
        targetApy
        maxDrawdown
        riskLevel
        level
        spendLimit24h
      }
    }
  }
`;

const TOGGLE_AUTOPILOT = gql`
  mutation ToggleAutopilot($enabled: Boolean!) {
    toggleAutopilot(enabled: $enabled) {
      ok
    }
  }
`;

const EXECUTE_REPAIR = gql`
  mutation ExecuteRepair($repairId: String!) {
    executeRepair(repairId: $repairId) {
      receipt {
        success
        txHash
        message
      }
    }
  }
`;

const REVERT_MOVE = gql`
  mutation RevertAutopilotMove {
    revertAutopilotMove {
      receipt {
        success
        txHash
        message
      }
    }
  }
`;

const GOALS = [
  { id: 'FORTRESS', label: 'Steady Growth (Fortress)' },
  { id: 'BALANCED', label: 'Balanced' },
  { id: 'SPECULATIVE', label: 'Yield Max' },
];

const LEVELS = [
  { id: 'NOTIFY_ONLY', label: 'Notify Only' },
  { id: 'APPROVE_REPAIRS', label: 'Approve Repairs' },
  { id: 'AUTO_BOUNDED', label: 'Auto Within Limits' },
];

export default function DeFiAutopilotScreen() {
  const navigation = useNavigation<any>();
  const { data, loading, refetch } = useQuery(AUTOPILOT_QUERY, {
    fetchPolicy: 'network-only',
  });
  const [updatePolicy] = useMutation(UPDATE_POLICY);
  const [toggleAutopilot] = useMutation(TOGGLE_AUTOPILOT);
  const [executeRepair, { loading: executingRepair }] = useMutation(EXECUTE_REPAIR);
  const [revertAutopilotMove, { loading: revertingMove }] = useMutation(REVERT_MOVE);

  const status = data?.autopilotStatus;
  const policy = status?.policy;
  const lastMove = status?.lastMove;

  const [enabled, setEnabled] = useState(false);
  const [riskLevel, setRiskLevel] = useState('FORTRESS');
  const [drawdown, setDrawdown] = useState(5);
  const [targetApy, setTargetApy] = useState(8);
  const [autonomyLevel, setAutonomyLevel] = useState('NOTIFY_ONLY');
  const [proofOpen, setProofOpen] = useState(false);
  const [activeProof, setActiveProof] = useState<any>(null);

  useEffect(() => {
    if (status) {
      setEnabled(!!status.enabled);
    }
    if (policy) {
      setRiskLevel(policy.riskLevel || 'FORTRESS');
      setDrawdown(Math.round((policy.maxDrawdown || 0.05) * 100));
      setTargetApy(Math.round((policy.targetApy || 0.08) * 100));
      setAutonomyLevel(policy.level || 'NOTIFY_ONLY');
    }
  }, [status, policy]);

  const pendingRepairs = data?.pendingRepairs || [];

  const formattedDrawdown = `${drawdown}%`;
  const formattedTarget = `${targetApy}% APY`;

  const handleToggle = async (value: boolean) => {
    setEnabled(value);
    try {
      await toggleAutopilot({ variables: { enabled: value } });
      await refetch();
    } catch (error) {
      logger.error('Toggle autopilot error:', error);
    }
  };

  const handleSavePolicy = async () => {
    try {
      await updatePolicy({
        variables: {
          input: {
            targetApy: targetApy / 100,
            maxDrawdown: drawdown / 100,
            riskLevel,
            level: autonomyLevel,
            spendLimit24h: 500,
          },
        },
      });
      await refetch();
    } catch (error) {
      logger.error('Update policy error:', error);
    }
  };

  const handleExecuteRepair = async (repairId: string) => {
    try {
      await executeRepair({ variables: { repairId } });
      await refetch();
    } catch (error) {
      logger.error('Execute repair error:', error);
    }
  };

  const openProof = (proof: any) => {
    setActiveProof(proof);
    setProofOpen(true);
  };

  const handleRevertMove = async () => {
    try {
      await revertAutopilotMove();
      await refetch();
    } catch (error) {
      logger.error('Revert move error:', error);
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={UI.colors.primary} />
        <Text style={styles.loadingText}>Loading Auto-Pilot...</Text>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Auto-Pilot</Text>
          <Text style={styles.subtitle}>Protecting your wealth in real-time.</Text>
        </View>
        <Switch value={enabled} onValueChange={handleToggle} />
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>The Intent</Text>

        <Text style={styles.label}>What is your goal?</Text>
        <View style={styles.chipRow}>
          {GOALS.map((goal) => (
            <TouchableOpacity
              key={goal.id}
              style={[styles.chip, riskLevel === goal.id && styles.chipActive]}
              onPress={() => setRiskLevel(goal.id)}
            >
              <Text style={[styles.chipText, riskLevel === goal.id && styles.chipTextActive]}>
                {goal.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <Text style={styles.label}>Maximum Tolerance</Text>
        <View style={styles.stepperRow}>
          <TouchableOpacity
            style={styles.stepperButton}
            onPress={() => setDrawdown(Math.max(2, drawdown - 1))}
          >
            <Icon name="minus" size={16} color={UI.colors.text} />
          </TouchableOpacity>
          <Text style={styles.stepperValue}>{formattedDrawdown}</Text>
          <TouchableOpacity
            style={styles.stepperButton}
            onPress={() => setDrawdown(Math.min(15, drawdown + 1))}
          >
            <Icon name="plus" size={16} color={UI.colors.text} />
          </TouchableOpacity>
        </View>
        <Text style={styles.subtext}>
          If a pool drops more than {formattedDrawdown} from its peak, we trigger an immediate repair.
        </Text>

        <Text style={styles.label}>Target Yield</Text>
        <View style={styles.stepperRow}>
          <TouchableOpacity
            style={styles.stepperButton}
            onPress={() => setTargetApy(Math.max(2, targetApy - 1))}
          >
            <Icon name="minus" size={16} color={UI.colors.text} />
          </TouchableOpacity>
          <Text style={styles.stepperValue}>{formattedTarget}</Text>
          <TouchableOpacity
            style={styles.stepperButton}
            onPress={() => setTargetApy(Math.min(20, targetApy + 1))}
          >
            <Icon name="plus" size={16} color={UI.colors.text} />
          </TouchableOpacity>
        </View>

        <Text style={styles.label}>Autonomy Level</Text>
        <View style={styles.chipRow}>
          {LEVELS.map((level) => (
            <TouchableOpacity
              key={level.id}
              style={[styles.chip, autonomyLevel === level.id && styles.chipActive]}
              onPress={() => setAutonomyLevel(level.id)}
            >
              <Text style={[styles.chipText, autonomyLevel === level.id && styles.chipTextActive]}>
                {level.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <TouchableOpacity style={styles.primaryButton} onPress={handleSavePolicy}>
          <Text style={styles.primaryButtonText}>Save Intent</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Active Repair Queue</Text>

        {pendingRepairs.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyTitle}>All clear.</Text>
            <Text style={styles.emptyText}>Your positions are within your policy.</Text>
          </View>
        ) : (
          pendingRepairs.map((repair: any) => (
            <View key={repair.id} style={styles.repairCard}>
              <Text style={styles.repairTitle}>⚠️ Action Required</Text>
              <Text style={styles.repairSubtitle}>
                {repair.fromVault} → {repair.toVault}
              </Text>
              <Text style={styles.repairDesc}>{repair.proof?.explanation}</Text>
              <View style={styles.repairActions}>
                <TouchableOpacity
                  style={styles.secondaryButton}
                  onPress={() => openProof(repair.proof)}
                >
                  <Text style={styles.secondaryButtonText}>Why this move?</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.primaryButton}
                  onPress={() => handleExecuteRepair(repair.id)}
                  disabled={executingRepair}
                >
                  <Text style={styles.primaryButtonText}>
                    {executingRepair ? 'Executing...' : 'Execute 1‑Tap Repair'}
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          ))
        )}
      </View>

      {lastMove ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Last Move</Text>
          <Text style={styles.repairSubtitle}>{lastMove.fromVault} → {lastMove.toVault}</Text>
          <Text style={styles.repairDesc}>Executed at {lastMove.executedAt}</Text>
          <View style={styles.repairActions}>
            <TouchableOpacity
              style={styles.secondaryButton}
              onPress={handleRevertMove}
              disabled={!lastMove.canRevert || revertingMove}
            >
              <Text style={styles.secondaryButtonText}>
                {lastMove.canRevert ? (revertingMove ? 'Reverting...' : 'Revert This Move') : 'Revert Unavailable'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      ) : null}

      <Modal visible={proofOpen} transparent animationType="slide">
        <View style={styles.modalOverlay}>
          <View style={styles.modalCard}>
            <Text style={styles.modalTitle}>Proof Drawer</Text>
            {activeProof ? (
              <View>
                <Text style={styles.modalItem}>
                  Calmar Improvement: {activeProof.calmarImprovement?.toFixed(2) || '0.00'}
                </Text>
                <Text style={styles.modalItem}>
                  TVL Stability: {activeProof.tvlStabilityCheck ? 'Stable ✅' : 'Unstable'}
                </Text>
                <Text style={styles.modalItem}>
                  Policy Match: {activeProof.policyAlignment ? 'Within limits ✅' : 'Outside limits'}
                </Text>
                <Text style={styles.modalItem}>
                  Integrity: {activeProof.integrityCheck?.isErc4626Compliant ? 'ERC‑4626 ✅' : 'Unknown'}
                </Text>
                {activeProof.policyVersion ? (
                  <Text style={styles.modalItem}>Policy version: {activeProof.policyVersion}</Text>
                ) : null}
                {activeProof.guardrails ? (
                  <Text style={styles.modalItem}>
                    Guardrails: Trust {activeProof.guardrails.trust_score ?? '—'} · TVL ${
                      activeProof.guardrails.tvl ?? '—'
                    }
                  </Text>
                ) : null}
                <Text style={styles.modalExplanation}>{activeProof.explanation}</Text>
              </View>
            ) : null}
            <TouchableOpacity style={styles.secondaryButton} onPress={() => setProofOpen(false)}>
              <Text style={styles.secondaryButtonText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: UI.colors.background },
  content: { padding: 20, paddingBottom: 60 },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  title: { fontSize: 26, fontWeight: '700', color: UI.colors.text },
  subtitle: { fontSize: 14, color: UI.colors.textSecondary, marginTop: 4 },
  section: {
    backgroundColor: UI.colors.surface,
    borderRadius: 16,
    padding: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: UI.colors.border,
  },
  sectionTitle: { fontSize: 18, fontWeight: '700', color: UI.colors.text, marginBottom: 12 },
  label: { fontSize: 14, fontWeight: '600', color: UI.colors.text, marginTop: 10 },
  subtext: { fontSize: 12, color: UI.colors.textSecondary, marginTop: 6 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: 8 },
  chip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: UI.colors.border,
    backgroundColor: UI.colors.background,
  },
  chipActive: { backgroundColor: UI.colors.primary, borderColor: UI.colors.primary },
  chipText: { fontSize: 12, color: UI.colors.text },
  chipTextActive: { color: '#fff' },
  stepperRow: { flexDirection: 'row', alignItems: 'center', gap: 12, marginTop: 8 },
  stepperButton: {
    width: 36,
    height: 36,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: UI.colors.border,
    backgroundColor: UI.colors.background,
  },
  stepperValue: { fontSize: 16, fontWeight: '700', color: UI.colors.text },
  primaryButton: {
    marginTop: 16,
    backgroundColor: UI.colors.primary,
    paddingVertical: 12,
    borderRadius: 12,
    alignItems: 'center',
  },
  primaryButtonText: { color: '#fff', fontWeight: '600' },
  secondaryButton: {
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: UI.colors.border,
    backgroundColor: UI.colors.background,
  },
  secondaryButtonText: { color: UI.colors.text, fontWeight: '600' },
  repairCard: {
    borderWidth: 1,
    borderColor: UI.colors.border,
    borderRadius: 14,
    padding: 14,
    marginTop: 12,
    backgroundColor: UI.colors.background,
  },
  repairTitle: { fontSize: 14, fontWeight: '700', color: UI.colors.error },
  repairSubtitle: { fontSize: 13, fontWeight: '600', color: UI.colors.text, marginTop: 6 },
  repairDesc: { fontSize: 12, color: UI.colors.textSecondary, marginTop: 4 },
  repairActions: { flexDirection: 'row', gap: 10, marginTop: 12, flexWrap: 'wrap' },
  emptyState: { alignItems: 'center', paddingVertical: 20 },
  emptyTitle: { fontSize: 16, fontWeight: '700', color: UI.colors.text },
  emptyText: { fontSize: 12, color: UI.colors.textSecondary, marginTop: 4 },
  loadingContainer: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { marginTop: 10, color: UI.colors.textSecondary },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    padding: 20,
  },
  modalCard: {
    backgroundColor: UI.colors.surface,
    borderRadius: 16,
    padding: 20,
  },
  modalTitle: { fontSize: 18, fontWeight: '700', marginBottom: 12, color: UI.colors.text },
  modalItem: { fontSize: 13, color: UI.colors.text, marginBottom: 6 },
  modalExplanation: { fontSize: 12, color: UI.colors.textSecondary, marginTop: 8 },
});
