import React, { useState, useEffect, useMemo, useCallback } from 'react';
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
  Alert,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { gql, useQuery, useMutation, useLazyQuery } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';
import { LinearGradient } from 'expo-linear-gradient';
import { ethers } from 'ethers';
import UI from '../../../shared/constants';
import logger from '../../../utils/logger';
import { useWallet } from '../../../wallet/WalletProvider';
import { useRoute } from '@react-navigation/native';

const AUTO_SPEND_NOTICE_KEY = 'defi_autopilot_auto_spend_notice_seen';

const AUTOPILOT_QUERY = gql`
  query AutopilotCommand {
    autopilotStatus {
      enabled
      relayerConfigured
      relayerPausedChainIds
      circuitBreaker {
        state
        reason
        triggeredAt
        triggeredBy
        autoResumeAt
      }
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
        spendPermissionEnabled
        spendPermissionExpiresAt
      }
    }
    pendingRepairs {
      id
      fromVault
      toVault
      estimatedApyDelta
      gasEstimate
      options {
        variant
        toVault
        toPoolId
        estimatedApyDelta
        proof {
          calmarImprovement
          explanation
          ifThen
          plainSummary
          beforeAfter
          policyAlignment
        }
      }
      proof {
        calmarImprovement
        tvlStabilityCheck
        policyAlignment
        explanation
        ifThen
        plainSummary
        beforeAfter
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
      executionPayload
    }
  }
`;

const GET_SPEND_PERMISSION_TYPED_DATA = gql`
  query GetSpendPermissionTypedData(
    $chainId: Int!
    $maxAmountWei: String!
    $tokenAddress: String!
    $validUntilSeconds: Int!
    $nonce: String!
  ) {
    spendPermissionTypedData(
      chainId: $chainId
      maxAmountWei: $maxAmountWei
      tokenAddress: $tokenAddress
      validUntilSeconds: $validUntilSeconds
      nonce: $nonce
    )
  }
`;

const GET_REPAIR_AUTH_TYPED_DATA = gql`
  query GetRepairAuthorizationTypedData(
    $chainId: Int!
    $fromVault: String!
    $toVault: String!
    $amountWei: String!
    $deadline: Int!
    $nonce: Int!
  ) {
    repairAuthorizationTypedData(
      chainId: $chainId
      fromVault: $fromVault
      toVault: $toVault
      amountWei: $amountWei
      deadline: $deadline
      nonce: $nonce
    )
  }
`;

const GET_FORWARDER_NONCE = gql`
  query GetRepairForwarderNonce($chainId: Int!, $userAddress: String!) {
    repairForwarderNonce(chainId: $chainId, userAddress: $userAddress)
  }
`;

const SUBMIT_REPAIR_VIA_RELAYER = gql`
  mutation SubmitRepairViaRelayer(
    $userAddress: String!
    $chainId: Int!
    $fromVault: String!
    $toVault: String!
    $amountWei: String!
    $deadline: Int!
    $nonce: Int!
    $signature: String!
    $repairId: String
  ) {
    submitRepairViaRelayer(
      userAddress: $userAddress
      chainId: $chainId
      fromVault: $fromVault
      toVault: $toVault
      amountWei: $amountWei
      deadline: $deadline
      nonce: $nonce
      signature: $signature
      repairId: $repairId
    ) {
      success
      txHash
      message
    }
  }
`;

const SUBMIT_SPEND_PERMISSION = gql`
  mutation SubmitSpendPermission(
    $wallet_address: String!
    $chain_id: Int!
    $max_amount_wei: String!
    $token_address: String!
    $valid_until_seconds: Int!
    $nonce: String!
    $signature: String!
    $raw_typed_data: JSONString
  ) {
    submitSpendPermission(
      wallet_address: $wallet_address
      chain_id: $chain_id
      max_amount_wei: $max_amount_wei
      token_address: $token_address
      valid_until_seconds: $valid_until_seconds
      nonce: $nonce
      signature: $signature
      raw_typed_data: $raw_typed_data
    ) {
      ok
      message
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

const REVOKE_SPEND_PERMISSION = gql`
  mutation RevokeAutopilotSpendPermission {
    revokeAutopilotSpendPermission {
      ok
      message
      policy {
        spendPermissionEnabled
        spendPermissionExpiresAt
      }
    }
  }
`;

const REPORT_REPAIR_EXECUTED_ON_CHAIN = gql`
  mutation ReportRepairExecutedOnChain($repairId: String!, $txHash: String!) {
    reportRepairExecutedOnChain(repairId: $repairId, txHash: $txHash) {
      ok
      message
    }
  }
`;

// ERC-4626 vault calls for repair on-chain (withdraw from source, deposit to target)
const ERC4626_ABI = [
  'function withdraw(uint256 assets, address receiver, address owner) returns (uint256)',
  'function deposit(uint256 assets, address receiver) returns (uint256)',
];

/** Build and send the two repair txs (withdraw then deposit) via wallet. */
async function submitRepairOnChain(
  payload: {
    chainId: number;
    fromVaultAddress: string;
    toVaultAddress: string;
    amountHuman: string;
    decimals?: number;
  },
  userAddress: string,
  sendTransaction: (tx: { to: string; data: string; value?: string }) => Promise<string>,
  decimalsDefault: number = 18,
): Promise<{ withdrawHash?: string; depositHash?: string; error?: string }> {
  const iface = new ethers.utils.Interface(ERC4626_ABI);
  const decimals = payload.decimals ?? decimalsDefault;
  const amountWei = ethers.utils.parseUnits(payload.amountHuman, decimals);
  try {
    const withdrawData = iface.encodeFunctionData('withdraw', [
      amountWei,
      userAddress,
      userAddress,
    ]);
    const withdrawHash = await sendTransaction({
      to: payload.fromVaultAddress,
      data: withdrawData,
    });
    const depositData = iface.encodeFunctionData('deposit', [amountWei, userAddress]);
    const depositHash = await sendTransaction({
      to: payload.toVaultAddress,
      data: depositData,
    });
    return { withdrawHash, depositHash };
  } catch (e: any) {
    return { error: e?.message || 'On-chain repair failed' };
  }
}

const GOALS = [
  { id: 'FORTRESS', label: 'Fortress', icon: 'shield', desc: 'Safety first' },
  { id: 'BALANCED', label: 'Balanced', icon: 'activity', desc: 'Risk & reward' },
  { id: 'SPECULATIVE', label: 'Yield Max', icon: 'trending-up', desc: 'Max returns' },
];

const LEVELS = [
  { id: 'NOTIFY_ONLY', label: 'Notify', icon: 'bell', desc: 'You decide' },
  { id: 'APPROVE_REPAIRS', label: 'Approve', icon: 'check-square', desc: 'Confirm moves' },
  { id: 'AUTO_BOUNDED', label: 'Auto', icon: 'cpu', desc: 'Hands-free' },
];

/** Convert ISO/timestamp to relative time string */
function relativeTime(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diffMs = now - then;
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHrs = Math.floor(diffMin / 60);
  if (diffHrs < 24) return `${diffHrs}h ago`;
  const diffDays = Math.floor(diffHrs / 24);
  return `${diffDays}d ago`;
}

// USDC (or main stable) per chain for spend permission
const DEFAULT_TOKEN_BY_CHAIN: Record<number, string> = {
  1: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
  137: '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
  42161: '0xaf88d065e77c8cC2239327C5Bb45045926D470c77',
  11155111: '0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238', // Sepolia USDC
};

export default function DeFiAutopilotScreen() {
  const route = useRoute<any>();
  const { data, loading, refetch } = useQuery(AUTOPILOT_QUERY, {
    fetchPolicy: 'network-only',
  });
  const wallet = useWallet();
  const { address, chainId, signTypedData, sendTransaction, isConnected } = wallet;

  const [updatePolicy] = useMutation(UPDATE_POLICY);
  const [toggleAutopilot] = useMutation(TOGGLE_AUTOPILOT);
  const [executeRepair, { loading: executingRepair }] = useMutation(EXECUTE_REPAIR);
  const [revertAutopilotMove, { loading: revertingMove }] = useMutation(REVERT_MOVE);
  const [submitSpendPermission, { loading: grantingPermission }] = useMutation(SUBMIT_SPEND_PERMISSION);
  const [getTypedData] = useLazyQuery(GET_SPEND_PERMISSION_TYPED_DATA);
  const [getRepairAuthTypedData] = useLazyQuery(GET_REPAIR_AUTH_TYPED_DATA);
  const [getForwarderNonce] = useLazyQuery(GET_FORWARDER_NONCE);
  const [submitRepairViaRelayer, { loading: submittingViaRelayer }] = useMutation(SUBMIT_REPAIR_VIA_RELAYER);
  const [revokeSpendPermission, { loading: revokingPermission }] = useMutation(REVOKE_SPEND_PERMISSION);
  const [reportRepairExecutedOnChain] = useMutation(REPORT_REPAIR_EXECUTED_ON_CHAIN);

  const [submittingOnChain, setSubmittingOnChain] = useState(false);
  const [permissionRequestModalOpen, setPermissionRequestModalOpen] = useState(false);

  const status = data?.autopilotStatus;
  const policy = status?.policy;
  const lastMove = status?.lastMove;
  const pendingRepairs = data?.pendingRepairs || [];
  const relayerConfigured = !!status?.relayerConfigured;
  const relayerPausedChainIds: number[] = status?.relayerPausedChainIds ?? [];

  const [enabled, setEnabled] = useState(false);
  const [riskLevel, setRiskLevel] = useState('FORTRESS');
  const [drawdown, setDrawdown] = useState(5);
  const [targetApy, setTargetApy] = useState(8);
  const [autonomyLevel, setAutonomyLevel] = useState('NOTIFY_ONLY');
  const [proofOpen, setProofOpen] = useState(false);
  const [activeProof, setActiveProof] = useState<any>(null);
  const [autoSpendNoticeVisible, setAutoSpendNoticeVisible] = useState(false);

  useEffect(() => {
    if (status) setEnabled(!!status.enabled);

    if (policy) {
      setRiskLevel(policy.riskLevel || 'FORTRESS');
      setDrawdown(Math.round((policy.maxDrawdown || 0.05) * 100));
      setTargetApy(Math.round((policy.targetApy || 0.08) * 100));
      setAutonomyLevel(policy.level || 'NOTIFY_ONLY');
    }
  }, [status, policy]);

  // One-time AUTO_SPEND notice: show when user has AUTO_SPEND + spend permission and hasn't seen it
  useEffect(() => {
    if (!policy?.level || policy.level !== 'AUTO_SPEND' || !policy.spendPermissionEnabled) return;
    let cancelled = false;
    (async () => {
      try {
        const seen = await AsyncStorage.getItem(AUTO_SPEND_NOTICE_KEY);
        if (!cancelled && !seen) setAutoSpendNoticeVisible(true);
      } catch {
        if (!cancelled) setAutoSpendNoticeVisible(false);
      }
    })();
    return () => { cancelled = true; };
  }, [policy?.level, policy?.spendPermissionEnabled]);

  const dismissAutoSpendNotice = useCallback(async () => {
    setAutoSpendNoticeVisible(false);
    try {
      await AsyncStorage.setItem(AUTO_SPEND_NOTICE_KEY, '1');
    } catch {}
  }, []);

  // Deep link from push: open proof for repairId when opened via "Tap to see the proof"
  const deepLinkRepairId = route.params?.repairId;
  useEffect(() => {
    if (!deepLinkRepairId || loading || !data) return;
    const repairs = data?.pendingRepairs || [];
    const match = repairs.find((r: any) => r.id === deepLinkRepairId);
    if (match?.proof) {
      setActiveProof(match.proof);
      setProofOpen(true);
    } else if (status?.lastMove?.id === deepLinkRepairId) {
      setActiveProof({ explanation: 'Move completed. See Last Move below for details.', ...status.lastMove });
      setProofOpen(true);
    }
  }, [deepLinkRepairId, loading, data, status?.lastMove]);

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

  const handleExecuteRepair = useCallback(async (repairId: string) => {
    try {
      const result = await executeRepair({ variables: { repairId } });
      const receipt = result.data?.executeRepair?.receipt;
      const executionPayload = result.data?.executeRepair?.executionPayload as Record<string, unknown> | null | undefined;
      await refetch();
      if (receipt && !receipt.success) {
        Alert.alert('Repair failed', receipt.message || 'Unknown error');
        return;
      }
      if (executionPayload && isConnected && address) {
        const chainIdNum = (executionPayload.chainId as number) || chainId;
        if (chainIdNum !== chainId) {
          Alert.alert(
            'Wrong network',
            `Repair is on chain ${chainIdNum}. Switch your wallet to that network and run Execute again, or submit the move manually.`,
          );
          return;
        }
        setSubmittingOnChain(true);
        try {
          const outcome = await submitRepairOnChain(
            {
              chainId: chainIdNum,
              fromVaultAddress: (executionPayload.fromVaultAddress as string) || '',
              toVaultAddress: (executionPayload.toVaultAddress as string) || '',
              amountHuman: (executionPayload.amountHuman as string) || '0',
              decimals: executionPayload.decimals as number | undefined,
            },
            address,
            (tx) => sendTransaction({ ...tx, from: address }),
            18,
          );
          if (outcome.error) {
            Alert.alert('On-chain repair failed', outcome.error);
          } else if (outcome.withdrawHash || outcome.depositHash) {
            const txHash = outcome.depositHash || outcome.withdrawHash || '';
            try {
              await reportRepairExecutedOnChain({
                variables: { repairId, txHash },
              });
            } catch (e) {
              logger.warn('Report repair executed on chain failed', e);
            }
            Alert.alert(
              'Repair submitted',
              `Withdraw: ${outcome.withdrawHash || '—'}\nDeposit: ${outcome.depositHash || '—'}`,
            );
          }
        } finally {
          setSubmittingOnChain(false);
        }
      }
    } catch (error: any) {
      logger.error('Execute repair error:', error);
      Alert.alert('Error', error?.message || 'Execute repair failed');
    }
  }, [executeRepair, refetch, isConnected, address, chainId, sendTransaction]);

  const handleGrantSpendPermission = useCallback(async () => {
    if (!isConnected || !address || chainId == null) {
      Alert.alert('Wallet required', 'Connect your wallet to grant spend permission.');
      return;
    }
    const tokenAddress = DEFAULT_TOKEN_BY_CHAIN[chainId] || DEFAULT_TOKEN_BY_CHAIN[1];
    const maxAmountWei = '500000000'; // 500 USDC (6 decimals)
    const validUntilSeconds = Math.floor(Date.now() / 1000) + 30 * 24 * 3600;
    const nonce = Date.now().toString();
    try {
      const { data: typedDataRes } = await getTypedData({
        variables: {
          chainId,
          maxAmountWei,
          tokenAddress,
          validUntilSeconds,
          nonce,
        },
      });
      const typedData = typedDataRes?.spendPermissionTypedData as Record<string, unknown> | null | undefined;
      if (!typedData) {
        Alert.alert('Error', 'Could not get spend permission data.');
        return;
      }
      const signature = await signTypedData(typedData);
      const { data: submitRes } = await submitSpendPermission({
        variables: {
          wallet_address: address,
          chain_id: chainId,
          max_amount_wei: maxAmountWei,
          token_address: tokenAddress,
          valid_until_seconds: validUntilSeconds,
          nonce,
          signature,
          raw_typed_data: typedData,
        },
      });
      const ok = submitRes?.submitSpendPermission?.ok;
      const message = submitRes?.submitSpendPermission?.message;
      if (ok) {
        Alert.alert('Spend permission granted', message || 'You can now auto-approve repairs within the limit.');
        refetch();
      } else {
        Alert.alert('Failed', message || 'Could not store spend permission.');
      }
    } catch (e: any) {
      logger.error('Grant spend permission error:', e);
      Alert.alert('Error', e?.message || 'Grant spend permission failed');
    }
  }, [isConnected, address, chainId, getTypedData, signTypedData, submitSpendPermission, refetch]);

  const handleSubmitViaRelayer = useCallback(async (repairId: string) => {
    if (!isConnected || !address || chainId == null) {
      Alert.alert('Wallet required', 'Connect your wallet first.');
      return;
    }
    try {
      const execResult = await executeRepair({ variables: { repairId } });
      const executionPayload = execResult.data?.executeRepair?.executionPayload as Record<string, unknown> | null | undefined;
      const withinSpendPermission = !!executionPayload?.withinSpendPermission;
      if (!executionPayload || !withinSpendPermission || !relayerConfigured) {
        Alert.alert(
          'Relayer not available',
          withinSpendPermission ? 'Relayer is not configured on the server.' : 'This repair is outside your spend permission; sign in wallet instead.',
        );
        return;
      }
      const chainIdNum = (executionPayload.chainId as number) || chainId;
      const fromVault = (executionPayload.fromVaultAddress as string) || '';
      const toVault = (executionPayload.toVaultAddress as string) || '';
      const amountHuman = (executionPayload.amountHuman as string) || '0';
      const decimals = (executionPayload.decimals as number) ?? 18;
      const amountWei = ethers.utils.parseUnits(amountHuman, decimals).toString();
      const deadline = Math.floor(Date.now() / 1000) + 900; // 15 min
      const { data: nonceData } = await getForwarderNonce({
        variables: { chainId: chainIdNum, userAddress: address },
      });
      const nonce = nonceData?.repairForwarderNonce ?? 0;
      const { data: typedDataRes } = await getRepairAuthTypedData({
        variables: {
          chainId: chainIdNum,
          fromVault,
          toVault,
          amountWei,
          deadline,
          nonce,
        },
      });
      const typedData = typedDataRes?.repairAuthorizationTypedData as Record<string, unknown> | null | undefined;
      if (!typedData) {
        Alert.alert('Error', 'Could not get repair authorization data.');
        return;
      }
      const signature = await signTypedData(typedData);
      const { data: submitRes } = await submitRepairViaRelayer({
        variables: {
          userAddress: address,
          chainId: chainIdNum,
          fromVault,
          toVault,
          amountWei,
          deadline,
          nonce,
          signature,
          repairId,
        },
      });
      const ok = submitRes?.submitRepairViaRelayer?.success;
      const txHash = submitRes?.submitRepairViaRelayer?.txHash;
      const message = submitRes?.submitRepairViaRelayer?.message;
      if (ok && txHash) {
        Alert.alert('Repair submitted', `Tx: ${txHash}`);
        refetch();
      } else {
        Alert.alert('Relayer failed', message || 'Could not submit via relayer.');
      }
    } catch (e: any) {
      logger.error('Submit via relayer error:', e);
      Alert.alert('Error', e?.message || 'Submit via relayer failed.');
    }
  }, [isConnected, address, chainId, relayerConfigured, executeRepair, getForwarderNonce, getRepairAuthTypedData, signTypedData, submitRepairViaRelayer, refetch]);

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
      <LinearGradient
        colors={['#0F172A', '#1E293B', '#1E3A5F']}
        style={styles.loadingContainer}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        <View style={styles.loadingCard}>
          <View style={styles.loadingIconWrap}>
            <Icon name="cpu" size={32} color="#6366F1" />
          </View>
          <ActivityIndicator size="large" color="#6366F1" style={{ marginTop: 16 }} />
          <Text style={styles.loadingText}>Loading Auto-Pilot…</Text>
          <Text style={styles.loadingSubtext}>Syncing policy + repair queue</Text>
        </View>
      </LinearGradient>
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
        {/* CRISIS BANNER: DeFi paused when circuit breaker is OPEN */}
        {status?.circuitBreaker?.state === 'OPEN' ? (
          <View style={styles.crisisBanner}>
            <Icon name="alert-triangle" size={20} color="#FEF3C7" />
            <View style={styles.crisisBannerText}>
              <Text style={styles.crisisBannerTitle}>DeFi paused</Text>
              <Text style={styles.crisisBannerReason}>
                {status.circuitBreaker.reason || 'System maintenance'}
              </Text>
              {status.circuitBreaker.autoResumeAt ? (
                <Text style={styles.crisisBannerHint}>
                  May resume automatically. Check back later.
                </Text>
              ) : (
                <Text style={styles.crisisBannerHint}>
                  No new repairs until an admin resumes.
                </Text>
              )}
            </View>
          </View>
        ) : null}

        {/* HERO HEADER */}
        <LinearGradient
          colors={['#0F172A', '#1E293B', '#1E3A5F']}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.hero}
        >
          <View style={styles.heroTopRow}>
            <View style={styles.heroTitleBlock}>
              <View style={styles.heroTitleRow}>
                <View style={styles.heroIconWrap}>
                  <Icon name="cpu" size={20} color="#818CF8" />
                </View>
                <Text style={styles.heroTitle}>Auto-Pilot</Text>
              </View>
              <View
                style={[
                  styles.statusPill,
                  enabled
                    ? styles.statusPillActive
                    : styles.statusPillPaused,
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
                  false: 'rgba(100,116,139,0.45)',
                  true: 'rgba(99,102,241,0.5)',
                }}
                thumbColor={Platform.OS === 'android' ? '#FFFFFF' : undefined}
              />
            </View>
          </View>

          <Text style={styles.heroSubtitle}>Protecting your wealth in real-time.</Text>

          {/* QUICK STATS */}
          <View style={styles.statRow}>
            <View style={styles.statCard}>
              <Icon name="target" size={14} color="#818CF8" style={{ marginBottom: 4 }} />
              <Text style={styles.statLabel}>Target</Text>
              <Text style={styles.statValue}>{formattedTarget}</Text>
            </View>
            <View style={styles.statCard}>
              <Icon name="shield" size={14} color="#F59E0B" style={{ marginBottom: 4 }} />
              <Text style={styles.statLabel}>Drawdown</Text>
              <Text style={styles.statValue}>{formattedDrawdown}</Text>
            </View>
            <View style={styles.statCard}>
              <Icon name="settings" size={14} color="#10B981" style={{ marginBottom: 4 }} />
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
                    active && styles.segmentActive,
                  ]}
                  onPress={() => setRiskLevel(goal.id)}
                  activeOpacity={0.85}
                >
                  <Icon
                    name={goal.icon}
                    size={16}
                    color={active ? '#FFFFFF' : '#64748B'}
                    style={{ marginBottom: 2 }}
                  />
                  <Text style={[styles.segmentText, active && styles.segmentTextActive]}>
                    {goal.label}
                  </Text>
                  <Text style={[styles.segmentDesc, active && styles.segmentDescActive]}>
                    {goal.desc}
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
              <Icon name="minus" size={16} color="#6366F1" />
            </TouchableOpacity>

            <View style={styles.stepCenter}>
              <View style={styles.stepValueRing}>
                <Text style={styles.stepValue}>{formattedDrawdown}</Text>
              </View>
              <Text style={styles.stepHint}>max peak-to-trough</Text>
            </View>

            <TouchableOpacity
              style={styles.stepBtn}
              onPress={() => setDrawdown(Math.min(15, drawdown + 1))}
              activeOpacity={0.8}
            >
              <Icon name="plus" size={16} color="#6366F1" />
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
              <Icon name="minus" size={16} color="#6366F1" />
            </TouchableOpacity>

            <View style={styles.stepCenter}>
              <View style={styles.stepValueRing}>
                <Text style={styles.stepValue} numberOfLines={1}>{targetApy}%</Text>
                <Text style={styles.stepValueSub}>APY</Text>
              </View>
              <Text style={styles.stepHint}>desired annual yield</Text>
            </View>

            <TouchableOpacity
              style={styles.stepBtn}
              onPress={() => setTargetApy(Math.min(20, targetApy + 1))}
              activeOpacity={0.8}
            >
              <Icon name="plus" size={16} color="#6366F1" />
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
                    active && styles.segmentActive,
                  ]}
                  onPress={() => setAutonomyLevel(level.id)}
                  activeOpacity={0.85}
                >
                  <Icon
                    name={level.icon}
                    size={16}
                    color={active ? '#FFFFFF' : '#64748B'}
                    style={{ marginBottom: 2 }}
                  />
                  <Text style={[styles.segmentText, active && styles.segmentTextActive]}>
                    {level.label}
                  </Text>
                  <Text style={[styles.segmentDesc, active && styles.segmentDescActive]}>
                    {level.desc}
                  </Text>
                </TouchableOpacity>
              );
            })}
          </View>

          <TouchableOpacity style={styles.primaryBtn} onPress={handleSavePolicy} activeOpacity={0.9}>
            <Icon name="check" size={18} color="#FFFFFF" />
            <Text style={styles.primaryBtnText}>Save Intent</Text>
          </TouchableOpacity>

          {isConnected && (
            <>
              {policy?.spendPermissionEnabled ? (
                <TouchableOpacity
                  style={[styles.secondaryBtn, { marginTop: 12 }]}
                  onPress={async () => {
                    try {
                      await revokeSpendPermission();
                      await refetch();
                      Alert.alert('Revoked', 'Spend permission has been revoked. One-tap repairs will require wallet approval.');
                    } catch (e: any) {
                      Alert.alert('Error', e?.message || 'Could not revoke.');
                    }
                  }}
                  disabled={revokingPermission}
                  activeOpacity={0.85}
                >
                  <Icon name="unlock" size={16} color="#0F172A" />
                  <Text style={styles.secondaryBtnText}>
                    {revokingPermission ? 'Revoking…' : 'Revoke spend permission'}
                  </Text>
                </TouchableOpacity>
              ) : (
                <TouchableOpacity
                  style={[styles.ghostBtn, { marginTop: 12 }]}
                  onPress={() => setPermissionRequestModalOpen(true)}
                  disabled={grantingPermission}
                  activeOpacity={0.85}
                >
                  <Icon name="lock" size={16} color={UI.colors.primary || '#6366F1'} />
                  <Text style={styles.ghostBtnText}>
                    {grantingPermission ? 'Signing in wallet…' : 'Grant spend permission (EIP-712)'}
                  </Text>
                </TouchableOpacity>
              )}
            </>
          )}

          {/* Permission Request: explain delegation + revoke before signing */}
          <Modal
            visible={permissionRequestModalOpen}
            animationType="slide"
            transparent
            onRequestClose={() => setPermissionRequestModalOpen(false)}
          >
            <Pressable
              style={styles.modalOverlay}
              onPress={() => setPermissionRequestModalOpen(false)}
            >
              <Pressable style={styles.permissionModalCard} onPress={(e) => e.stopPropagation()}>
                <LinearGradient
                  colors={['#0F172A', '#1E293B', '#1E3A5F']}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 1 }}
                  style={styles.permissionModalHeader}
                >
                  <View style={styles.permissionIconWrap}>
                    <Icon name="shield" size={28} color="#818CF8" />
                  </View>
                  <Text style={styles.permissionModalTitle}>Permission Request</Text>
                  <Text style={styles.permissionModalSubtitle}>
                    You are about to delegate repair execution to the Auto-Pilot relayer.
                  </Text>
                </LinearGradient>
                <View style={styles.permissionModalBody}>
                  <Text style={styles.permissionModalLabel}>What you're delegating</Text>
                  <Text style={styles.permissionModalText}>
                    The RepairForwarder (and our relayer) can move your funds between vaults on your behalf, only when a repair fits your policy and stays within the limits below.
                  </Text>
                  <Text style={styles.permissionModalLabel}>Limits</Text>
                  <View style={styles.permissionBullet}>
                    <Icon name="check-circle" size={14} color="#10B981" />
                    <Text style={styles.permissionBulletText}>Max 500 USDC per repair</Text>
                  </View>
                  <View style={styles.permissionBullet}>
                    <Icon name="check-circle" size={14} color="#10B981" />
                    <Text style={styles.permissionBulletText}>Permission valid for 30 days</Text>
                  </View>
                  <View style={styles.permissionBullet}>
                    <Icon name="check-circle" size={14} color="#10B981" />
                    <Text style={styles.permissionBulletText}>Only moves approved by your intent (target APY, drawdown, risk level)</Text>
                  </View>
                  <Text style={[styles.permissionModalLabel, { marginTop: 16 }]}>You stay in control</Text>
                  <View style={styles.permissionBullet}>
                    <Icon name="lock" size={14} color="#6366F1" />
                    <Text style={styles.permissionBulletText}>
                      Revoke anytime from this screen or your wallet. One-time signature per repair when using one-tap.
                    </Text>
                  </View>
                </View>
                <View style={styles.permissionModalActions}>
                  <TouchableOpacity
                    style={[styles.ghostBtn, { marginBottom: 8 }]}
                    onPress={() => setPermissionRequestModalOpen(false)}
                    activeOpacity={0.85}
                  >
                    <Text style={styles.ghostBtnText}>Cancel</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.primaryBtn}
                    onPress={async () => {
                      setPermissionRequestModalOpen(false);
                      await handleGrantSpendPermission();
                    }}
                    disabled={grantingPermission}
                    activeOpacity={0.9}
                  >
                    <Icon name="check" size={18} color="#FFFFFF" />
                    <Text style={styles.primaryBtnText}>
                      {grantingPermission ? 'Signing…' : 'I understand, continue'}
                    </Text>
                  </TouchableOpacity>
                </View>
              </Pressable>
            </Pressable>
          </Modal>
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
                <Icon name="check-circle" size={28} color="#10B981" />
              </View>
              <Text style={styles.emptyTitle}>All Clear</Text>
              <Text style={styles.emptyText}>Your positions are within policy. No repairs needed.</Text>
            </View>
          ) : (
            pendingRepairs.map((repair: any) => (
              <View key={repair.id} style={styles.alertCard}>
                <View style={styles.alertAccentStrip} />
                <View style={styles.alertContent}>
                  <View style={styles.alertHeader}>
                    <View style={styles.alertLeft}>
                      <View style={styles.alertBadge}>
                        <View style={styles.alertPulseDot} />
                        <Icon name="alert-triangle" size={14} color="#DC2626" />
                        <Text style={styles.alertBadgeText}>Action Required</Text>
                      </View>
                      <Text style={styles.alertRoute}>
                        {repair.fromVault}{' '}
                        <Icon name="arrow-right" size={14} color="#94A3B8" />{' '}
                        {repair.toVault}
                      </Text>
                    </View>
                    {repair.estimatedApyDelta != null && (
                      <View style={styles.alertApyChip}>
                        <Icon name="trending-up" size={12} color="#10B981" />
                        <Text style={styles.alertApyText}>
                          +{Number(repair.estimatedApyDelta).toFixed(2)}%
                        </Text>
                      </View>
                    )}
                  </View>

                  {!!repair.proof?.explanation && (
                    <Text style={styles.alertDesc} numberOfLines={3}>
                      {repair.proof.explanation}
                    </Text>
                  )}

                  {repair.options?.length > 0 && (
                    <Text style={styles.alertOptions}>
                      Alternatives: {repair.options.map((o: any) => o.variant?.replace('_', ' ') || o.variant).join(' · ')}
                    </Text>
                  )}

                  {/* Why this move — full width */}
                  <TouchableOpacity
                    style={styles.whyMoveBtn}
                    onPress={() => openProof(repair.proof)}
                    activeOpacity={0.85}
                  >
                    <Icon name="info" size={16} color="#6366F1" />
                    <Text style={styles.ghostBtnText}>Why this move</Text>
                  </TouchableOpacity>

                  {/* Action buttons — side by side */}
                  <View style={styles.alertActionRow}>
                    {relayerConfigured && (
                      <TouchableOpacity
                        style={[
                          styles.relayerBtn,
                          (submittingViaRelayer || (chainId != null && relayerPausedChainIds.includes(chainId))) && styles.btnDisabled,
                        ]}
                        onPress={() => handleSubmitViaRelayer(repair.id)}
                        disabled={
                          submittingViaRelayer ||
                          executingRepair ||
                          submittingOnChain ||
                          (chainId != null && relayerPausedChainIds.includes(chainId))
                        }
                        activeOpacity={0.85}
                      >
                        <Icon name="send" size={14} color="#6366F1" />
                        <Text style={styles.relayerBtnText}>
                          {submittingViaRelayer
                            ? 'Submitting…'
                            : chainId != null && relayerPausedChainIds.includes(chainId)
                              ? 'Paused'
                              : 'One-tap'}
                        </Text>
                      </TouchableOpacity>
                    )}
                    <TouchableOpacity
                      style={[styles.executeBtn, (executingRepair || submittingOnChain) && styles.btnDisabled]}
                      onPress={() => handleExecuteRepair(repair.id)}
                      disabled={executingRepair || submittingOnChain}
                      activeOpacity={0.9}
                    >
                      <Icon name={executingRepair || submittingOnChain ? 'loader' : 'zap'} size={16} color="#FFFFFF" />
                      <Text style={styles.executeBtnText}>
                        {submittingOnChain ? 'Wallet…' : executingRepair ? 'Running…' : 'Execute Repair'}
                      </Text>
                    </TouchableOpacity>
                  </View>
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
                <Icon name="clock" size={18} color="#6366F1" />
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.cardTitle}>Last Move</Text>
                <Text style={styles.cardSubtitle}>Undo is available only within the revert window.</Text>
              </View>
            </View>

            <View style={styles.lastMoveRow}>
              <View style={styles.lastMoveTimeline}>
                <View style={styles.timelineDot} />
                <View style={styles.timelineLine} />
              </View>
              <View style={styles.lastMoveInfo}>
                <View style={styles.lastMoveRouteRow}>
                  <Icon name="check-circle" size={14} color="#10B981" />
                  <Text style={styles.lastMoveRoute}>
                    {lastMove.fromVault}{' '}
                    <Icon name="arrow-right" size={12} color="#94A3B8" />{' '}
                    {lastMove.toVault}
                  </Text>
                </View>
                <Text style={styles.lastMoveTime}>
                  {lastMove.executedAt ? relativeTime(lastMove.executedAt) : 'Recently executed'}
                </Text>
              </View>
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
              <View style={styles.sheetTitleLeft}>
                <Icon name="file-text" size={18} color="#6366F1" />
                <Text style={styles.sheetTitle}>Proof of Repair</Text>
              </View>
              <TouchableOpacity onPress={() => setProofOpen(false)} style={styles.sheetClose} activeOpacity={0.8}>
                <Icon name="x" size={18} color="#0F172A" />
              </TouchableOpacity>
            </View>

            {activeProof ? (
              <View style={styles.sheetBody}>
                <View style={styles.kvRow}>
                  <View style={styles.kvLeft}>
                    <Icon name="bar-chart-2" size={14} color="#6366F1" />
                    <Text style={styles.kLabel}>Calmar improvement</Text>
                  </View>
                  <Text style={styles.kValue}>{activeProof.calmarImprovement?.toFixed(2) || '0.00'}</Text>
                </View>

                <View style={styles.kvDivider} />

                <View style={styles.kvRow}>
                  <View style={styles.kvLeft}>
                    <Icon name={activeProof.tvlStabilityCheck ? 'check-circle' : 'x-circle'} size={14} color={activeProof.tvlStabilityCheck ? '#10B981' : '#EF4444'} />
                    <Text style={styles.kLabel}>TVL stability</Text>
                  </View>
                  <Text style={[styles.kValue, { color: activeProof.tvlStabilityCheck ? '#10B981' : '#EF4444' }]}>
                    {activeProof.tvlStabilityCheck ? 'Stable' : 'Unstable'}
                  </Text>
                </View>

                <View style={styles.kvDivider} />

                <View style={styles.kvRow}>
                  <View style={styles.kvLeft}>
                    <Icon name={activeProof.policyAlignment ? 'check-circle' : 'x-circle'} size={14} color={activeProof.policyAlignment ? '#10B981' : '#EF4444'} />
                    <Text style={styles.kLabel}>Policy match</Text>
                  </View>
                  <Text style={[styles.kValue, { color: activeProof.policyAlignment ? '#10B981' : '#EF4444' }]}>
                    {activeProof.policyAlignment ? 'Within limits' : 'Outside limits'}
                  </Text>
                </View>

                <View style={styles.kvDivider} />

                <View style={styles.kvRow}>
                  <View style={styles.kvLeft}>
                    <Icon name={activeProof.integrityCheck?.isErc4626Compliant ? 'check-circle' : 'help-circle'} size={14} color={activeProof.integrityCheck?.isErc4626Compliant ? '#10B981' : '#94A3B8'} />
                    <Text style={styles.kLabel}>Integrity</Text>
                  </View>
                  <Text style={styles.kValue}>
                    {activeProof.integrityCheck?.isErc4626Compliant ? 'ERC-4626' : 'Unknown'}
                  </Text>
                </View>

                {activeProof.policyVersion ? (
                  <>
                    <View style={styles.kvDivider} />
                    <View style={styles.kvRow}>
                      <View style={styles.kvLeft}>
                        <Icon name="hash" size={14} color="#64748B" />
                        <Text style={styles.kLabel}>Policy version</Text>
                      </View>
                      <Text style={styles.kValue}>{activeProof.policyVersion}</Text>
                    </View>
                  </>
                ) : null}

                {activeProof.guardrails ? (
                  <>
                    <View style={styles.kvDivider} />
                    <View style={styles.kvRow}>
                      <View style={styles.kvLeft}>
                        <Icon name="shield" size={14} color="#64748B" />
                        <Text style={styles.kLabel}>Guardrails</Text>
                      </View>
                      <Text style={styles.kValue}>
                        Trust {activeProof.guardrails.trust_score ?? '—'} · TVL ${activeProof.guardrails.tvl ?? '—'}
                      </Text>
                    </View>
                  </>
                ) : null}

                {activeProof.beforeAfter?.current && activeProof.beforeAfter?.target ? (
                  <>
                    <View style={styles.kvDivider} />
                    <View style={styles.explainBox}>
                      <View style={[styles.explainAccent, { backgroundColor: '#6366F1' }]} />
                      <View style={styles.explainContent}>
                        <Text style={styles.explainLabel}>Before → After</Text>
                        <View style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: 6 }}>
                          <View>
                            <Text style={[styles.explainText, { fontWeight: '600', marginBottom: 4 }]}>Current</Text>
                            <Text style={styles.explainText}>Calmar {activeProof.beforeAfter.current.calmar}</Text>
                            <Text style={styles.explainText}>Max DD {activeProof.beforeAfter.current.max_drawdown}</Text>
                            <Text style={styles.explainText}>TVL stability {activeProof.beforeAfter.current.tvl_stability}</Text>
                            <Text style={styles.explainText}>APY {activeProof.beforeAfter.current.apy}</Text>
                          </View>
                          <View style={{ alignItems: 'flex-end' }}>
                            <Text style={[styles.explainText, { fontWeight: '600', marginBottom: 4 }]}>Target</Text>
                            <Text style={styles.explainText}>Calmar {activeProof.beforeAfter.target.calmar}</Text>
                            <Text style={styles.explainText}>Max DD {activeProof.beforeAfter.target.max_drawdown}</Text>
                            <Text style={styles.explainText}>TVL stability {activeProof.beforeAfter.target.tvl_stability}</Text>
                            <Text style={styles.explainText}>APY {activeProof.beforeAfter.target.apy}</Text>
                          </View>
                        </View>
                      </View>
                    </View>
                  </>
                ) : null}

                {(!!activeProof.plainSummary || !!activeProof.ifThen || !!activeProof.explanation) && (
                  <View style={styles.explainBox}>
                    <View style={styles.explainAccent} />
                    <View style={styles.explainContent}>
                      <Text style={styles.explainLabel}>Why this repair</Text>
                      <Text style={styles.explainText}>
                        {activeProof.plainSummary || activeProof.ifThen || activeProof.explanation}
                      </Text>
                      {!!activeProof.ifThen && activeProof.plainSummary && activeProof.ifThen !== activeProof.plainSummary && (
                        <Text style={[styles.explainText, { marginTop: 8 }]}>{activeProof.ifThen}</Text>
                      )}
                      {!!activeProof.explanation && (activeProof.explanation !== (activeProof.plainSummary || activeProof.ifThen)) && (
                        <Text style={[styles.explainText, { marginTop: 8, opacity: 0.9 }]}>{activeProof.explanation}</Text>
                      )}
                    </View>
                  </View>
                )}

                {/* Verified badge */}
                <View style={styles.verifiedBadge}>
                  <Icon name="shield" size={12} color="#10B981" />
                  <Text style={styles.verifiedText}>Verified by Fortress Engine</Text>
                </View>
              </View>
            ) : null}

            <TouchableOpacity style={styles.secondaryBtn} onPress={() => setProofOpen(false)} activeOpacity={0.9}>
              <Icon name="chevron-down" size={18} color="#0F172A" />
              <Text style={styles.secondaryBtnText}>Close</Text>
            </TouchableOpacity>
          </Pressable>
        </Pressable>
      </Modal>

      {/* AUTO_SPEND first-time notice */}
      <Modal visible={autoSpendNoticeVisible} transparent animationType="fade">
        <Pressable style={styles.sheetOverlay} onPress={dismissAutoSpendNotice}>
          <Pressable style={styles.autoSpendNoticeCard} onPress={() => {}}>
            <Icon name="zap" size={28} color="#6366F1" style={{ marginBottom: 12 }} />
            <Text style={styles.autoSpendNoticeTitle}>Auto-Pilot will execute repairs for you</Text>
            <Text style={styles.autoSpendNoticeBody}>
              With Auto-Spend on and your spend permission granted, Auto-Pilot can execute repairs within your limits without asking each time. You’ll still get alerts for each move.
            </Text>
            <TouchableOpacity style={styles.primaryBtn} onPress={dismissAutoSpendNotice} activeOpacity={0.9}>
              <Text style={styles.primaryBtnText}>Got it</Text>
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
    backgroundColor: '#F8FAFC',
  },
  container: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  content: {
    paddingHorizontal: 16,
    paddingTop: 0,
    paddingBottom: 70,
  },

  crisisBanner: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 12,
    backgroundColor: '#92400E',
    padding: 14,
    borderRadius: 12,
    marginBottom: 16,
  },
  crisisBannerText: { flex: 1 },
  crisisBannerTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FEF3C7',
    marginBottom: 4,
  },
  crisisBannerReason: {
    fontSize: 13,
    color: '#FDE68A',
    marginBottom: 4,
  },
  crisisBannerHint: {
    fontSize: 12,
    color: '#FCD34D',
    opacity: 0.9,
  },

  autoSpendNoticeCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 24,
    marginHorizontal: 24,
    maxWidth: 400,
    alignSelf: 'center',
  },
  autoSpendNoticeTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 8,
    textAlign: 'center',
  },
  autoSpendNoticeBody: {
    fontSize: 14,
    color: '#475569',
    lineHeight: 22,
    marginBottom: 20,
    textAlign: 'center',
  },

  /* ============ HERO ============ */
  hero: {
    borderRadius: 24,
    padding: 20,
    overflow: 'hidden',
    marginBottom: 20,
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 12 },
    shadowOpacity: 0.25,
    shadowRadius: 24,
    elevation: 8,
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
  heroTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  heroIconWrap: {
    width: 36,
    height: 36,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(129,140,248,0.15)',
    borderWidth: 1,
    borderColor: 'rgba(129,140,248,0.25)',
  },
  heroTitle: {
    fontSize: 32,
    fontWeight: '900',
    letterSpacing: -0.5,
    color: '#F1F5F9',
  },
  heroSubtitle: {
    marginTop: 8,
    fontSize: 14,
    color: '#94A3B8',
    lineHeight: 20,
  },
  heroToggle: {
    alignItems: 'flex-end',
    gap: 6,
  },
  toggleLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#94A3B8',
  },

  /* STATUS PILL */
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
  statusPillActive: {
    backgroundColor: 'rgba(16,185,129,0.20)',
    borderColor: 'rgba(16,185,129,0.40)',
    shadowColor: '#10B981',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.35,
    shadowRadius: 8,
    elevation: 3,
  },
  statusPillPaused: {
    backgroundColor: 'rgba(239,68,68,0.20)',
    borderColor: 'rgba(239,68,68,0.40)',
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

  /* QUICK STATS (frosted glass) */
  statRow: {
    marginTop: 16,
    flexDirection: 'row',
    gap: 10,
  },
  statCard: {
    flex: 1,
    borderRadius: 16,
    padding: 12,
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.12)',
  },
  statLabel: {
    fontSize: 10,
    fontWeight: '700',
    color: '#94A3B8',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 4,
  },
  statValue: {
    fontSize: 15,
    fontWeight: '900',
    color: '#F1F5F9',
    letterSpacing: -0.2,
  },

  /* ============ CARD ============ */
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.18)',
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.06,
    shadowRadius: 16,
    elevation: 3,
  },
  cardTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 16,
  },
  iconBadge: {
    width: 40,
    height: 40,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(99,102,241,0.10)',
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
    marginTop: 3,
    fontSize: 13,
    color: '#64748B',
    lineHeight: 18,
  },

  label: {
    fontSize: 12,
    fontWeight: '700',
    color: '#64748B',
    marginTop: 16,
    marginBottom: 10,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },

  /* ============ SEGMENTS ============ */
  segmentRow: {
    flexDirection: 'row',
    gap: 8,
  },
  segment: {
    flex: 1,
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 14,
    borderRadius: 16,
    backgroundColor: '#F1F5F9',
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.30)',
  },
  segmentActive: {
    backgroundColor: '#6366F1',
    borderColor: '#6366F1',
    shadowColor: '#6366F1',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
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
  segmentDesc: {
    marginTop: 2,
    fontSize: 10,
    fontWeight: '600',
    color: '#94A3B8',
  },
  segmentDescActive: {
    color: 'rgba(255,255,255,0.75)',
  },

  /* ============ STEPPER ============ */
  stepper: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    borderRadius: 20,
    padding: 12,
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.22)',
    backgroundColor: '#F8FAFC',
  },
  stepBtn: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    borderWidth: 1.5,
    borderColor: 'rgba(99,102,241,0.30)',
    shadowColor: '#6366F1',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  stepCenter: {
    alignItems: 'center',
    justifyContent: 'center',
    flex: 1,
    paddingHorizontal: 10,
  },
  stepValueRing: {
    width: 72,
    height: 72,
    borderRadius: 36,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 3,
    borderColor: 'rgba(99,102,241,0.20)',
    backgroundColor: '#FFFFFF',
    overflow: 'hidden',
  },
  stepValue: {
    fontSize: 20,
    fontWeight: '900',
    color: '#0F172A',
    letterSpacing: -0.3,
    textAlign: 'center',
  },
  stepValueSub: {
    fontSize: 14,
    fontWeight: '800',
    color: '#0F172A',
    letterSpacing: -0.2,
    marginTop: -2,
    textAlign: 'center',
  },
  stepHint: {
    marginTop: 6,
    fontSize: 11,
    fontWeight: '600',
    color: '#94A3B8',
  },
  helperText: {
    marginTop: 10,
    fontSize: 13,
    color: '#64748B',
    lineHeight: 18,
  },
  helperEmph: {
    color: '#6366F1',
    fontWeight: '800',
  },

  /* ============ BUTTONS ============ */
  primaryBtn: {
    marginTop: 16,
    backgroundColor: '#6366F1',
    paddingVertical: 15,
    paddingHorizontal: 20,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 10,
    shadowColor: '#6366F1',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.30,
    shadowRadius: 16,
    elevation: 6,
  },
  primaryBtnText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '800',
    letterSpacing: 0.1,
  },
  secondaryBtn: {
    marginTop: 14,
    paddingVertical: 13,
    paddingHorizontal: 16,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.30)',
    backgroundColor: '#F8FAFC',
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 10,
  },
  secondaryBtnText: {
    color: '#0F172A',
    fontSize: 14,
    fontWeight: '700',
  },
  ghostBtn: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: 'rgba(99,102,241,0.25)',
    backgroundColor: 'rgba(99,102,241,0.06)',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  ghostBtnText: {
    fontSize: 13,
    fontWeight: '800',
    color: '#6366F1',
  },
  btnDisabled: {
    opacity: 0.5,
  },

  /* ============ EMPTY STATE ============ */
  empty: {
    alignItems: 'center',
    paddingVertical: 32,
  },
  emptyIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(16,185,129,0.12)',
    borderWidth: 1,
    borderColor: 'rgba(16,185,129,0.25)',
    marginBottom: 12,
    shadowColor: '#10B981',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.2,
    shadowRadius: 12,
    elevation: 3,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '900',
    color: '#0F172A',
  },
  emptyText: {
    marginTop: 6,
    fontSize: 14,
    color: '#64748B',
    textAlign: 'center',
    lineHeight: 20,
    paddingHorizontal: 20,
  },

  /* ============ ALERT / REPAIR CARD ============ */
  alertCard: {
    marginTop: 14,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(239,68,68,0.18)',
    backgroundColor: '#FFFFFF',
    overflow: 'hidden',
    flexDirection: 'row',
    shadowColor: '#EF4444',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
  },
  alertAccentStrip: {
    width: 4,
    backgroundColor: '#EF4444',
    borderTopLeftRadius: 20,
    borderBottomLeftRadius: 20,
  },
  alertContent: {
    flex: 1,
    padding: 16,
  },
  alertHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 10,
  },
  alertLeft: {
    flex: 1,
    gap: 8,
  },
  alertBadge: {
    alignSelf: 'flex-start',
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 999,
    backgroundColor: 'rgba(239,68,68,0.10)',
    borderWidth: 1,
    borderColor: 'rgba(239,68,68,0.20)',
  },
  alertPulseDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#EF4444',
  },
  alertBadgeText: {
    fontSize: 11,
    fontWeight: '800',
    color: '#DC2626',
    letterSpacing: 0.3,
  },
  alertRoute: {
    fontSize: 14,
    fontWeight: '800',
    color: '#0F172A',
    letterSpacing: -0.1,
  },
  alertApyChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 12,
    backgroundColor: 'rgba(16,185,129,0.10)',
    borderWidth: 1,
    borderColor: 'rgba(16,185,129,0.20)',
  },
  alertApyText: {
    fontSize: 13,
    fontWeight: '900',
    color: '#10B981',
  },
  alertDesc: {
    marginTop: 10,
    fontSize: 13,
    color: '#64748B',
    lineHeight: 19,
  },
  alertOptions: {
    marginTop: 6,
    fontSize: 12,
    color: '#6366F1',
    fontWeight: '600',
  },
  whyMoveBtn: {
    marginTop: 12,
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: 'rgba(99,102,241,0.20)',
    backgroundColor: 'rgba(99,102,241,0.05)',
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    gap: 8,
  },
  alertActionRow: {
    marginTop: 10,
    flexDirection: 'row',
    gap: 10,
    alignItems: 'center',
  },
  relayerBtn: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: 'rgba(99,102,241,0.25)',
    backgroundColor: 'rgba(99,102,241,0.06)',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
  },
  relayerBtnText: {
    fontSize: 13,
    fontWeight: '800',
    color: '#6366F1',
  },
  executeBtn: {
    flex: 1,
    backgroundColor: '#6366F1',
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'row',
    gap: 6,
    shadowColor: '#6366F1',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 4,
  },
  executeBtnText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '800',
  },

  /* ============ LAST MOVE ============ */
  lastMoveRow: {
    flexDirection: 'row',
    padding: 14,
    borderRadius: 18,
    backgroundColor: '#F8FAFC',
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.18)',
    gap: 12,
  },
  lastMoveTimeline: {
    alignItems: 'center',
    width: 16,
    paddingTop: 4,
  },
  timelineDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#10B981',
    borderWidth: 2,
    borderColor: 'rgba(16,185,129,0.30)',
  },
  timelineLine: {
    flex: 1,
    width: 2,
    backgroundColor: 'rgba(16,185,129,0.20)',
    marginTop: 4,
    borderRadius: 1,
  },
  lastMoveInfo: {
    flex: 1,
    gap: 6,
  },
  lastMoveRouteRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  lastMoveRoute: {
    fontSize: 14,
    fontWeight: '800',
    color: '#0F172A',
    flex: 1,
  },
  lastMoveTime: {
    fontSize: 12,
    fontWeight: '600',
    color: '#94A3B8',
  },

  /* ============ LOADING ============ */
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 22,
  },
  loadingIconWrap: {
    width: 64,
    height: 64,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(99,102,241,0.12)',
    borderWidth: 1,
    borderColor: 'rgba(99,102,241,0.25)',
  },
  loadingCard: {
    width: '100%',
    maxWidth: 380,
    borderRadius: 24,
    padding: 28,
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.10)',
  },
  loadingText: {
    marginTop: 14,
    fontSize: 18,
    fontWeight: '900',
    color: '#F1F5F9',
  },
  loadingSubtext: {
    marginTop: 6,
    fontSize: 13,
    fontWeight: '600',
    color: '#94A3B8',
  },

  /* ============ PERMISSION MODAL ============ */
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(15,23,42,0.55)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  permissionModalCard: {
    width: '100%',
    maxWidth: 400,
    backgroundColor: '#FFFFFF',
    borderRadius: 24,
    overflow: 'hidden',
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: 16 },
    shadowOpacity: 0.15,
    shadowRadius: 24,
    elevation: 8,
  },
  permissionModalHeader: {
    alignItems: 'center',
    paddingVertical: 24,
    paddingHorizontal: 20,
  },
  permissionIconWrap: {
    width: 56,
    height: 56,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(129,140,248,0.15)',
    borderWidth: 1,
    borderColor: 'rgba(129,140,248,0.30)',
  },
  permissionModalTitle: {
    marginTop: 12,
    fontSize: 22,
    fontWeight: '900',
    color: '#F1F5F9',
    letterSpacing: -0.3,
  },
  permissionModalSubtitle: {
    marginTop: 8,
    fontSize: 14,
    color: '#94A3B8',
    textAlign: 'center',
    lineHeight: 20,
  },
  permissionModalBody: {
    paddingHorizontal: 20,
    paddingBottom: 16,
  },
  permissionModalLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#64748B',
    marginTop: 12,
    marginBottom: 8,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  permissionModalText: {
    fontSize: 14,
    color: '#334155',
    lineHeight: 20,
    marginBottom: 4,
  },
  permissionBullet: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    paddingVertical: 6,
  },
  permissionBulletText: {
    flex: 1,
    fontSize: 14,
    color: '#334155',
    lineHeight: 20,
  },
  permissionModalActions: {
    paddingHorizontal: 20,
    paddingBottom: 20,
    gap: 0,
  },

  /* ============ PROOF SHEET ============ */
  sheetOverlay: {
    flex: 1,
    backgroundColor: 'rgba(15,23,42,0.55)',
    justifyContent: 'flex-end',
  },
  sheet: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 28,
    borderTopRightRadius: 28,
    padding: 20,
    shadowColor: '#0F172A',
    shadowOffset: { width: 0, height: -8 },
    shadowOpacity: 0.1,
    shadowRadius: 16,
    elevation: 6,
  },
  sheetHandle: {
    alignSelf: 'center',
    width: 40,
    height: 4,
    borderRadius: 999,
    backgroundColor: 'rgba(148,163,184,0.40)',
    marginBottom: 14,
  },
  sheetTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 14,
  },
  sheetTitleLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
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
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F1F5F9',
    borderWidth: 1,
    borderColor: 'rgba(148,163,184,0.20)',
  },
  sheetBody: {
    paddingTop: 4,
    paddingBottom: 8,
    gap: 0,
  },
  kvRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 4,
  },
  kvLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  kvDivider: {
    height: 1,
    backgroundColor: 'rgba(148,163,184,0.15)',
    marginHorizontal: 4,
  },
  kLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: '#64748B',
  },
  kValue: {
    fontSize: 13,
    fontWeight: '800',
    color: '#0F172A',
  },
  explainBox: {
    marginTop: 12,
    borderRadius: 16,
    overflow: 'hidden',
    flexDirection: 'row',
    backgroundColor: 'rgba(99,102,241,0.06)',
    borderWidth: 1,
    borderColor: 'rgba(99,102,241,0.15)',
  },
  explainAccent: {
    width: 4,
    backgroundColor: '#6366F1',
  },
  explainContent: {
    flex: 1,
    padding: 14,
  },
  explainLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#6366F1',
    letterSpacing: 0.3,
    textTransform: 'uppercase',
    marginBottom: 6,
  },
  explainText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#334155',
    lineHeight: 19,
  },
  verifiedBadge: {
    marginTop: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 8,
    borderRadius: 12,
    backgroundColor: 'rgba(16,185,129,0.08)',
    borderWidth: 1,
    borderColor: 'rgba(16,185,129,0.18)',
  },
  verifiedText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#10B981',
    letterSpacing: 0.3,
  },
});
