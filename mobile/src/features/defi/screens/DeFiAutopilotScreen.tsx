import React, { useState, useEffect, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Switch,
  Modal,
  Pressable,
  Platform,
} from 'react-native';
import { gql, useQuery, useMutation } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import { LinearGradient } from 'expo-linear-gradient';
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
  { id: 'FORTRESS', label: 'Fortress' },
  { id: 'BALANCED', label: 'Balanced' },
  { id: 'SPECULATIVE', label: 'Yield Max' },
];

const LEVELS = [
  { id: 'NOTIFY_ONLY', label: 'Notify' },
  { id: 'APPROVE_REPAIRS', label: 'Approve' },
  { id: 'AUTO_BOUNDED', label: 'Auto' },
];

export default function DeFiAutopilotScreen() {
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
  const pendingRepairs = data?.pendingRepairs || [];

  const [enabled, setEnabled] = useState(false);
  const [riskLevel, setRiskLevel] = useState('FORTRESS');
  const [drawdown, setDrawdown] = useState(5);
  const [targetApy, setTargetApy] = useState(8);
  const [autonomyLevel, setAutonomyLevel] = useState('NOTIFY_ONLY');
  const [proofOpen, setProofOpen] = useState(false);
  const [activeProof, setActiveProof] = useState<any>(null);

  useEffect(() => {
    if (status) setEnabled(!!status.enabled);

    if (policy) {
      setRiskLevel(policy.riskLevel || 'FORTRESS');
      setDrawdown(Math.round((policy.maxDrawdown || 0.05) * 100));
      setTargetApy(Math.round((policy.targetApy || 0.08) * 100));
      setAutonomyLevel(policy.level || 'NOTIFY_ONLY');
    }
  }, [status, policy]);

  const formattedDrawdown = useMemo(() => `${drawdown}%`, [drawdown]);
  const formattedTarget = useMemo(() => `${targetApy}% APY`, [targetApy]);

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
        <View style={styles.loadingCard}>
          <ActivityIndicator size="large" color={UI.colors.primary} />
          <Text style={styles.loadingText}>Loading Auto-Pilot…</Text>
          <Text style={styles.loadingSubtext}>Syncing policy + repair queue</Text>
        </View>
      </View>
    );
  }

  const statusTone = enabled ? 'ACTIVE' : 'PAUSED';
  const statusBg = enabled ? 'rgba(16, 185, 129, 0.14)' : 'rgba(239, 68, 68, 0.14)';
  const statusFg = enabled ? '#10B981' : '#EF4444';

  return (
    <View style={styles.screen}>
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false}
      >
        {/* HERO HEADER */}
        <LinearGradient
          colors={[
            UI.colors.primary ? `${UI.colors.primary}22` : 'rgba(99,102,241,0.14)',
            'rgba(255,255,255,0)',
          ]}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.hero}
        >
          <View style={styles.heroTopRow}>
            <View style={styles.heroTitleBlock}>
              <Text style={styles.heroTitle}>Auto-Pilot</Text>
              <View
                style={[
                  styles.statusPill,
                  { backgroundColor: statusBg, borderColor: `${statusFg}33` },
                ]}
              >
                <View style={[styles.statusDot, { backgroundColor: statusFg }]} />
                <Text style={[styles.statusText, { color: statusFg }]}>{statusTone}</Text>
              </View>
            </View>

            <View style={styles.heroToggle}>
              <Text style={styles.toggleLabel}>{enabled ? 'On' : 'Off'}</Text>
              <Switch
                value={enabled}
                onValueChange={handleToggle}
                trackColor={{
                  false: 'rgba(148,163,184,0.45)',
                  true: `${UI.colors.primary || '#6366F1'}66`,
                }}
                thumbColor={Platform.OS === 'android' ? '#FFFFFF' : undefined}
              />
            </View>
          </View>

          <Text style={styles.heroSubtitle}>Protecting your wealth in real-time.</Text>

          {/* QUICK STATS */}
          <View style={styles.statRow}>
            <View style={styles.statCard}>
              <Text style={styles.statLabel}>Target</Text>
              <Text style={styles.statValue}>{formattedTarget}</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statLabel}>Drawdown</Text>
              <Text style={styles.statValue}>{formattedDrawdown}</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statLabel}>Mode</Text>
              <Text style={styles.statValue}>
                {LEVELS.find((l) => l.id === autonomyLevel)?.label ?? 'Notify'}
              </Text>
            </View>
          </View>
        </LinearGradient>

        {/* INTENT */}
        <View style={styles.card}>
          <View style={styles.cardTitleRow}>
            <View style={styles.iconBadge}>
              <Icon name="sliders" size={18} color={UI.colors.primary || '#6366F1'} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.cardTitle}>The Intent</Text>
              <Text style={styles.cardSubtitle}>Set rules once. Auto-Pilot enforces them.</Text>
            </View>
          </View>

          <Text style={styles.label}>Goal</Text>
          <View style={styles.segmentRow}>
            {GOALS.map((goal) => {
              const active = riskLevel === goal.id;
              return (
                <TouchableOpacity
                  key={goal.id}
                  style={[
                    styles.segment,
                    active && {
                      backgroundColor: UI.colors.primary || '#6366F1',
                      borderColor: UI.colors.primary || '#6366F1',
                    },
                  ]}
                  onPress={() => setRiskLevel(goal.id)}
                  activeOpacity={0.85}
                >
                  <Text style={[styles.segmentText, active && styles.segmentTextActive]}>
                    {goal.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>

          <Text style={styles.label}>Maximum Tolerance</Text>
          <View style={styles.stepper}>
            <TouchableOpacity
              style={styles.stepBtn}
              onPress={() => setDrawdown(Math.max(2, drawdown - 1))}
              activeOpacity={0.8}
            >
              <Icon name="minus" size={18} color={UI.colors.text || '#0F172A'} />
            </TouchableOpacity>

            <View style={styles.stepCenter}>
              <Text style={styles.stepValue}>{formattedDrawdown}</Text>
              <Text style={styles.stepHint}>max peak-to-trough</Text>
            </View>

            <TouchableOpacity
              style={styles.stepBtn}
              onPress={() => setDrawdown(Math.min(15, drawdown + 1))}
              activeOpacity={0.8}
            >
              <Icon name="plus" size={18} color={UI.colors.text || '#0F172A'} />
            </TouchableOpacity>
          </View>
          <Text style={styles.helperText}>
            If a pool drops more than <Text style={styles.helperEmph}>{formattedDrawdown}</Text>{' '}
            from peak, we trigger an immediate repair.
          </Text>

          <Text style={styles.label}>Target Yield</Text>
          <View style={styles.stepper}>
            <TouchableOpacity
              style={styles.stepBtn}
              onPress={() => setTargetApy(Math.max(2, targetApy - 1))}
              activeOpacity={0.8}
            >
              <Icon name="minus" size={18} color={UI.colors.text || '#0F172A'} />
            </TouchableOpacity>

            <View style={styles.stepCenter}>
              <Text style={styles.stepValue}>{formattedTarget}</Text>
              <Text style={styles.stepHint}>desired annual yield</Text>
            </View>

            <TouchableOpacity
              style={styles.stepBtn}
              onPress={() => setTargetApy(Math.min(20, targetApy + 1))}
              activeOpacity={0.8}
            >
              <Icon name="plus" size={18} color={UI.colors.text || '#0F172A'} />
            </TouchableOpacity>
          </View>

          <Text style={styles.label}>Autonomy</Text>
          <View style={styles.segmentRow}>
            {LEVELS.map((level) => {
              const active = autonomyLevel === level.id;
              return (
                <TouchableOpacity
                  key={level.id}
                  style={[
                    styles.segment,
                    active && {
                      backgroundColor: UI.colors.primary || '#6366F1',
                      borderColor: UI.colors.primary || '#6366F1',
                    },
                  ]}
                  onPress={() => setAutonomyLevel(level.id)}
                  activeOpacity={0.85}
                >
                  <Text style={[styles.segmentText, active && styles.segmentTextActive]}>
                    {level.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>

          <TouchableOpacity style={styles.primaryBtn} onPress={handleSavePolicy} activeOpacity={0.9}>
            <Icon name="check" size={18} color="#FFFFFF" />
            <Text style={styles.primaryBtnText}>Save Intent</Text>
          </TouchableOpacity>
        </View>

        {/* REPAIR QUEUE */}
        <View style={styles.card}>
          <View style={styles.cardTitleRow}>
            <View style={styles.iconBadge}>
              <Icon name="shield" size={18} color={UI.colors.primary || '#6366F1'} />
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.cardTitle}>Active Repair Queue</Text>
              <Text style={styles.cardSubtitle}>
                Only shows actions that improve safety + policy alignment.
              </Text>
            </View>
          </View>

          {pendingRepairs.length === 0 ? (
            <View style={styles.empty}>
              <View style={styles.emptyIcon}>
                <Icon name="check-circle" size={20} color="#10B981" />
              </View>
              <Text style={styles.emptyTitle}>All clear</Text>
              <Text style={styles.emptyText}>Your positions are within policy.</Text>
            </View>
          ) : (
            pendingRepairs.map((repair: any) => (
              <View key={repair.id} style={styles.alertCard}>
                <View style={styles.alertHeader}>
                  <View style={styles.alertLeft}>
                    <View style={styles.alertBadge}>
                      <Icon name="alert-triangle" size={16} color="#DC2626" />
                      <Text style={styles.alertBadgeText}>Action Required</Text>
                    </View>
                    <Text style={styles.alertRoute}>
                      {repair.fromVault} <Text style={{ color: '#94A3B8' }}>→</Text> {repair.toVault}
                    </Text>
                  </View>
                  <View style={styles.alertMeta}>
                    <Text style={styles.alertMetaText}>
                      ΔAPY{' '}
                      {repair.estimatedApyDelta != null
                        ? `${Number(repair.estimatedApyDelta).toFixed(2)}%`
                        : '—'}
                    </Text>
                  </View>
                </View>

                {!!repair.proof?.explanation && (
                  <Text style={styles.alertDesc} numberOfLines={3}>
                    {repair.proof.explanation}
                  </Text>
                )}

                <View style={styles.alertActions}>
                  <TouchableOpacity
                    style={styles.ghostBtn}
                    onPress={() => openProof(repair.proof)}
                    activeOpacity={0.85}
                  >
                    <Icon name="info" size={16} color={UI.colors.primary || '#6366F1'} />
                    <Text style={styles.ghostBtnText}>Why this move</Text>
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={[styles.primaryBtn, executingRepair && styles.btnDisabled]}
                    onPress={() => handleExecuteRepair(repair.id)}
                    disabled={executingRepair}
                    activeOpacity={0.9}
                  >
                    <Icon name={executingRepair ? 'loader' : 'zap'} size={18} color="#FFFFFF" />
                    <Text style={styles.primaryBtnText}>
                      {executingRepair ? 'Executing…' : 'Execute 1-Tap Repair'}
                    </Text>
                  </TouchableOpacity>
                </View>
              </View>
            ))
          )}
        </View>

        {/* LAST MOVE */}
        {lastMove ? (
          <View style={styles.card}>
            <View style={styles.cardTitleRow}>
              <View style={styles.iconBadge}>
                <Icon name="clock" size={18} color={UI.colors.primary || '#6366F1'} />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.cardTitle}>Last Move</Text>
                <Text style={styles.cardSubtitle}>Undo is available only within the revert window.</Text>
              </View>
            </View>

            <View style={styles.lastMoveRow}>
              <Text style={styles.lastMoveRoute}>
                {lastMove.fromVault} <Text style={{ color: '#94A3B8' }}>→</Text> {lastMove.toVault}
              </Text>
              <Text style={styles.lastMoveTime}>Executed at {lastMove.executedAt}</Text>
            </View>

            <TouchableOpacity
              style={[
                styles.secondaryBtn,
                (!lastMove.canRevert || revertingMove) && styles.btnDisabled,
              ]}
              onPress={handleRevertMove}
              disabled={!lastMove.canRevert || revertingMove}
              activeOpacity={0.9}
            >
              <Icon name="corner-up-left" size={18} color="#0F172A" />
              <Text style={styles.secondaryBtnText}>
                {lastMove.canRevert ? (revertingMove ? 'Reverting…' : 'Revert This Move') : 'Revert Unavailable'}
              </Text>
            </TouchableOpacity>
          </View>
        ) : null}

        <View style={{ height: 28 }} />
      </ScrollView>

      {/* PROOF DRAWER (BOTTOM SHEET) */}
      <Modal visible={proofOpen} transparent animationType="fade" onRequestClose={() => setProofOpen(false)}>
        <Pressable style={styles.sheetOverlay} onPress={() => setProofOpen(false)}>
          <Pressable style={styles.sheet} onPress={() => {}}>
            <View style={styles.sheetHandle} />

            <View style={styles.sheetTitleRow}>
              <Text style={styles.sheetTitle}>Proof</Text>
              <TouchableOpacity onPress={() => setProofOpen(false)} style={styles.sheetClose} activeOpacity={0.8}>
                <Icon name="x" size={18} color="#0F172A" />
              </TouchableOpacity>
            </View>

            {activeProof ? (
              <View style={styles.sheetBody}>
                <View style={styles.kvRow}>
                  <Text style={styles.kLabel}>Calmar improvement</Text>
                  <Text style={styles.kValue}>{activeProof.calmarImprovement?.toFixed(2) || '0.00'}</Text>
                </View>

                <View style={styles.kvRow}>
                  <Text style={styles.kLabel}>TVL stability</Text>
                  <Text style={styles.kValue}>{activeProof.tvlStabilityCheck ? 'Stable ✅' : 'Unstable'}</Text>
                </View>

                <View style={styles.kvRow}>
                  <Text style={styles.kLabel}>Policy match</Text>
                  <Text style={styles.kValue}>{activeProof.policyAlignment ? 'Within limits ✅' : 'Outside limits'}</Text>
                </View>

                <View style={styles.kvRow}>
                  <Text style={styles.kLabel}>Integrity</Text>
                  <Text style={styles.kValue}>
                    {activeProof.integrityCheck?.isErc4626Compliant ? 'ERC-4626 ✅' : 'Unknown'}
                  </Text>
                </View>

                {activeProof.policyVersion ? (
                  <View style={styles.kvRow}>
                    <Text style={styles.kLabel}>Policy version</Text>
                    <Text style={styles.kValue}>{activeProof.policyVersion}</Text>
                  </View>
                ) : null}

                {activeProof.guardrails ? (
                  <View style={styles.kvRow}>
                    <Text style={styles.kLabel}>Guardrails</Text>
                    <Text style={styles.kValue}>
                      Trust {activeProof.guardrails.trust_score ?? '—'} · TVL ${activeProof.guardrails.tvl ?? '—'}
                    </Text>
                  </View>
                ) : null}

                {!!activeProof.explanation && (
                  <View style={styles.explainBox}>
                    <Text style={styles.explainText}>{activeProof.explanation}</Text>
                  </View>
                )}
              </View>
            ) : null}

            <TouchableOpacity style={styles.secondaryBtn} onPress={() => setProofOpen(false)} activeOpacity={0.9}>
              <Icon name="chevron-down" size={18} color="#0F172A" />
              <Text style={styles.secondaryBtnText}>Close</Text>
            </TouchableOpacity>
          </Pressable>
        </Pressable>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: UI.colors.background || '#F7F9FC',
  },
  container: {
    flex: 1,
    backgroundColor: UI.colors.background || '#F7F9FC',
  },
  content: {
    padding: 18,
    paddingBottom: 70,
  },

  /* HERO */
  hero: {
    borderRadius: 24,
    padding: 18,
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.28)',
    backgroundColor: UI.colors.surface || '#FFFFFF',
    overflow: 'hidden',
    marginBottom: 18,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.06,
    shadowRadius: 18,
    elevation: 3,
  },
  heroTopRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: 12,
  },
  heroTitleBlock: {
    flex: 1,
    gap: 10,
  },
  heroTitle: {
    fontSize: 30,
    fontWeight: '800',
    letterSpacing: -0.4,
    color: UI.colors.text || '#0F172A',
  },
  heroSubtitle: {
    marginTop: 10,
    fontSize: 14,
    color: UI.colors.textSecondary || '#64748B',
    lineHeight: 20,
  },
  heroToggle: {
    alignItems: 'flex-end',
    gap: 6,
  },
  toggleLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#64748B',
  },

  /* STATUS */
  statusPill: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 999,
    borderWidth: 1,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 999,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 0.6,
  },

  /* STATS */
  statRow: {
    marginTop: 14,
    flexDirection: 'row',
    gap: 10,
  },
  statCard: {
    flex: 1,
    borderRadius: 16,
    padding: 12,
    backgroundColor: 'rgba(241,245,249,0.65)',
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.22)',
  },
  statLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#64748B',
    marginBottom: 6,
  },
  statValue: {
    fontSize: 14,
    fontWeight: '800',
    color: '#0F172A',
    letterSpacing: -0.2,
  },

  /* CARD */
  card: {
    backgroundColor: UI.colors.surface || '#FFFFFF',
    borderRadius: 24,
    padding: 18,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.28)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.06,
    shadowRadius: 18,
    elevation: 3,
  },
  cardTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 14,
  },
  iconBadge: {
    width: 38,
    height: 38,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(99,102,241,0.12)',
    borderWidth: 1,
    borderColor: 'rgba(99,102,241,0.18)',
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#0F172A',
    letterSpacing: -0.2,
  },
  cardSubtitle: {
    marginTop: 4,
    fontSize: 13,
    color: '#64748B',
    lineHeight: 18,
  },

  label: {
    fontSize: 13,
    fontWeight: '800',
    color: '#0F172A',
    marginTop: 14,
    marginBottom: 8,
    letterSpacing: 0.2,
  },

  /* SEGMENTS */
  segmentRow: {
    flexDirection: 'row',
    gap: 10,
    flexWrap: 'wrap',
  },
  segment: {
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 999,
    backgroundColor: '#F1F5F9',
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.35)',
  },
  segmentText: {
    fontSize: 13,
    fontWeight: '800',
    color: '#334155',
    letterSpacing: 0.1,
  },
  segmentTextActive: {
    color: '#FFFFFF',
  },

  /* STEPPER */
  stepper: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderRadius: 18,
    padding: 10,
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.28)',
    backgroundColor: '#F8FAFC',
  },
  stepBtn: {
    width: 48,
    height: 48,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#EEF2F7',
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.24)',
  },
  stepCenter: {
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
    paddingHorizontal: 10,
  },
  stepValue: {
    fontSize: 18,
    fontWeight: '900',
    color: '#0F172A',
    letterSpacing: -0.2,
  },
  stepHint: {
    marginTop: 4,
    fontSize: 11,
    fontWeight: '700',
    color: '#64748B',
  },
  helperText: {
    marginTop: 10,
    fontSize: 13,
    color: '#64748B',
    lineHeight: 18,
  },
  helperEmph: {
    color: '#0F172A',
    fontWeight: '800',
  },

  /* BUTTONS */
  primaryBtn: {
    marginTop: 16,
    backgroundColor: UI.colors.primary || '#6366F1',
    paddingVertical: 14,
    paddingHorizontal: 14,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 10,
    shadowColor: UI.colors.primary || '#6366F1',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.22,
    shadowRadius: 16,
    elevation: 6,
  },
  primaryBtnText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '900',
    letterSpacing: 0.2,
  },
  secondaryBtn: {
    marginTop: 14,
    paddingVertical: 13,
    paddingHorizontal: 14,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.38)',
    backgroundColor: '#F8FAFC',
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 10,
  },
  secondaryBtnText: {
    color: '#0F172A',
    fontSize: 14,
    fontWeight: '800',
  },
  ghostBtn: {
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: 'rgba(99,102,241,0.30)',
    backgroundColor: 'rgba(99,102,241,0.08)',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  ghostBtnText: {
    fontSize: 13,
    fontWeight: '900',
    color: UI.colors.primary || '#6366F1',
  },
  btnDisabled: {
    opacity: 0.6,
  },

  /* EMPTY */
  empty: {
    alignItems: 'center',
    paddingVertical: 26,
  },
  emptyIcon: {
    width: 44,
    height: 44,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(16,185,129,0.12)',
    borderWidth: 1,
    borderColor: 'rgba(16,185,129,0.20)',
    marginBottom: 10,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: '900',
    color: '#0F172A',
  },
  emptyText: {
    marginTop: 6,
    fontSize: 13,
    color: '#64748B',
    textAlign: 'center',
    lineHeight: 18,
  },

  /* ALERT CARD */
  alertCard: {
    marginTop: 12,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(239,68,68,0.22)',
    backgroundColor: '#FFFFFF',
    padding: 14,
    overflow: 'hidden',
  },
  alertHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 10,
  },
  alertLeft: {
    flex: 1,
    gap: 10,
  },
  alertBadge: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    backgroundColor: 'rgba(239,68,68,0.10)',
    borderWidth: 1,
    borderColor: 'rgba(239,68,68,0.18)',
  },
  alertBadgeText: {
    fontSize: 12,
    fontWeight: '900',
    color: '#DC2626',
    letterSpacing: 0.2,
  },
  alertRoute: {
    fontSize: 14,
    fontWeight: '900',
    color: '#0F172A',
    letterSpacing: -0.1,
  },
  alertMeta: {
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderRadius: 14,
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.22)',
  },
  alertMetaText: {
    fontSize: 12,
    fontWeight: '900',
    color: '#0F172A',
  },
  alertDesc: {
    marginTop: 10,
    fontSize: 13,
    color: '#64748B',
    lineHeight: 18,
  },
  alertActions: {
    marginTop: 14,
    flexDirection: 'row',
    gap: 10,
    flexWrap: 'wrap',
    alignItems: 'center',
  },

  /* LAST MOVE */
  lastMoveRow: {
    marginTop: 6,
    padding: 14,
    borderRadius: 18,
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.22)',
  },
  lastMoveRoute: {
    fontSize: 14,
    fontWeight: '900',
    color: '#0F172A',
  },
  lastMoveTime: {
    marginTop: 6,
    fontSize: 12,
    fontWeight: '700',
    color: '#64748B',
  },

  /* LOADING */
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: UI.colors.background || '#F7F9FC',
    padding: 22,
  },
  loadingCard: {
    width: '100%',
    maxWidth: 380,
    borderRadius: 24,
    padding: 22,
    alignItems: 'center',
    backgroundColor: UI.colors.surface || '#FFFFFF',
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.28)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 10 },
    shadowOpacity: 0.08,
    shadowRadius: 18,
    elevation: 4,
  },
  loadingText: {
    marginTop: 14,
    fontSize: 16,
    fontWeight: '900',
    color: '#0F172A',
  },
  loadingSubtext: {
    marginTop: 6,
    fontSize: 13,
    fontWeight: '700',
    color: '#64748B',
  },

  /* SHEET */
  sheetOverlay: {
    flex: 1,
    backgroundColor: 'rgba(15,23,42,0.45)',
    justifyContent: 'flex-end',
  },
  sheet: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 18,
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.28)',
  },
  sheetHandle: {
    alignSelf: 'center',
    width: 48,
    height: 5,
    borderRadius: 999,
    backgroundColor: 'rgba(148,163,184,0.45)',
    marginBottom: 12,
  },
  sheetTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  sheetTitle: {
    fontSize: 18,
    fontWeight: '900',
    color: '#0F172A',
    letterSpacing: -0.2,
  },
  sheetClose: {
    width: 36,
    height: 36,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F1F5F9',
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.25)',
  },
  sheetBody: {
    paddingTop: 6,
    paddingBottom: 2,
    gap: 10,
  },
  kvRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 10,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderRadius: 16,
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.22)',
  },
  kLabel: {
    fontSize: 12,
    fontWeight: '900',
    color: '#64748B',
    letterSpacing: 0.2,
  },
  kValue: {
    fontSize: 12,
    fontWeight: '900',
    color: '#0F172A',
  },
  explainBox: {
    marginTop: 6,
    borderRadius: 16,
    padding: 12,
    backgroundColor: 'rgba(99,102,241,0.08)',
    borderWidth: 1,
    borderColor: 'rgba(99,102,241,0.22)',
  },
  explainText: {
    fontSize: 13,
    fontWeight: '700',
    color: '#334155',
    lineHeight: 18,
  },
});
