/**
 * Vault Portfolio Screen
 *
 * Shows all user's ERC-4626 vault positions and DeFi positions in one view.
 * Includes strategy rotation suggestions, auto-compound status,
 * and the ERC4626VaultCard for new deposits.
 *
 * Part of Phase 5: Yield Forge
 */
import React, { useState, useCallback, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  Pressable,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useNavigation } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';
import { useQuery, gql } from '@apollo/client';
import ERC4626VaultCard from '../../../components/blockchain/ERC4626VaultCard';
import { YieldAggregatorService, type UserPosition } from '../../blockchain/services/YieldAggregatorService';

// ---------- GraphQL ----------

const DEFI_ACCOUNT_QUERY = gql`
  query DefiAccountForVaults($walletAddress: String!) {
    defiAccount(walletAddress: $walletAddress) {
      totalValueUsd
      totalEarningsUsd
      healthFactor
      positions {
        id
        poolName
        poolSymbol
        protocol
        chain
        stakedAmount
        stakedValueUsd
        currentApy
        rewardsEarned
        healthFactor
        healthStatus
        healthReason
        isActive
      }
    }
  }
`;

// ---------- Helpers ----------

function formatUsd(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(2)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(2)}K`;
  return `$${value.toFixed(2)}`;
}

// ---------- Components ----------

interface RotationSuggestion {
  positionId: string;
  currentProtocol: string;
  currentApy: number;
  suggestedProtocol: string;
  suggestedApy: number;
  improvement: number;
  asset: string;
}

function RotationCard({ suggestion }: { suggestion: RotationSuggestion }) {
  return (
    <View style={styles.rotationCard}>
      <View style={styles.rotationHeader}>
        <Ionicons name="swap-horizontal" size={18} color="#F59E0B" />
        <Text style={styles.rotationTitle}>Strategy Rotation Opportunity</Text>
      </View>
      <Text style={styles.rotationBody}>
        Your {suggestion.asset} on {suggestion.currentProtocol} is earning{' '}
        <Text style={{ fontWeight: '700' }}>{suggestion.currentApy.toFixed(1)}%</Text>.
        {'\n'}Move to {suggestion.suggestedProtocol} for{' '}
        <Text style={{ fontWeight: '700', color: '#10B981' }}>
          {suggestion.suggestedApy.toFixed(1)}%
        </Text>{' '}
        (+{suggestion.improvement.toFixed(1)}% improvement).
      </Text>
      <Pressable
        style={({ pressed }) => [styles.rotationBtn, pressed && { opacity: 0.8 }]}
        onPress={() =>
          Alert.alert(
            'Rotate Strategy',
            `This will withdraw from ${suggestion.currentProtocol} and deposit into ${suggestion.suggestedProtocol}.\n\nCoW Swap will handle any token conversions for MEV-protected, gas-efficient execution.\n\nComing soon!`,
          )
        }
      >
        <Text style={styles.rotationBtnText}>Review Rotation</Text>
      </Pressable>
    </View>
  );
}

function PositionRow({ position }: { position: any }) {
  const apyColor = position.currentApy >= 5 ? '#10B981' : position.currentApy >= 2 ? '#F59E0B' : '#6B7280';
  const healthStatus = position.healthStatus || 'green';
  const healthColor = healthStatus === 'green' ? '#10B981' : healthStatus === 'amber' ? '#F59E0B' : '#EF4444';

  return (
    <View style={styles.positionRow}>
      <View style={styles.positionLeft}>
        <View style={styles.positionSymbolRow}>
          <View style={[styles.healthDot, { backgroundColor: healthColor }]} />
          <Text style={styles.positionSymbol}>{position.poolSymbol}</Text>
        </View>
        <Text style={styles.positionProtocol}>
          {position.protocol} · {position.chain}
          {position.healthReason ? ` · ${position.healthReason}` : ''}
        </Text>
      </View>
      <View style={styles.positionRight}>
        <Text style={styles.positionValue}>
          {formatUsd(parseFloat(position.stakedValueUsd || '0'))}
        </Text>
        <Text style={[styles.positionApy, { color: apyColor }]}>
          {position.currentApy?.toFixed(1) || '0.0'}% APY
        </Text>
      </View>
    </View>
  );
}

// ---------- Main Screen ----------

export default function VaultPortfolioScreen() {
  const navigation = useNavigation<any>();
  const [refreshing, setRefreshing] = useState(false);
  const [rotations, setRotations] = useState<RotationSuggestion[]>([]);
  const [checkingRotations, setCheckingRotations] = useState(false);

  // TODO: Get from wallet context
  const walletAddress = '';

  const { data, loading, refetch } = useQuery(DEFI_ACCOUNT_QUERY, {
    variables: { walletAddress: walletAddress || 'not_connected' },
    fetchPolicy: 'cache-and-network',
    skip: !walletAddress,
  });

  const account = data?.defiAccount;
  const positions = account?.positions?.filter((p: any) => p.isActive) || [];
  const totalValue = account?.totalValueUsd || 0;
  const totalEarnings = account?.totalEarningsUsd || 0;

  // Check for rotation opportunities
  const checkRotations = useCallback(async () => {
    if (positions.length === 0) return;

    setCheckingRotations(true);
    const aggregator = YieldAggregatorService.getInstance();
    const suggestions: RotationSuggestion[] = [];

    for (const pos of positions) {
      const userPos: UserPosition = {
        id: pos.id,
        protocol: pos.protocol,
        asset: pos.poolSymbol,
        amount: parseFloat(pos.stakedAmount),
        apy: pos.currentApy || 0,
        earned: parseFloat(pos.rewardsEarned || '0'),
        chain: pos.chain,
        chainId: 1,
      };

      const result = await aggregator.checkRotationOpportunity(userPos);
      if (result.shouldRotate && result.suggestion) {
        suggestions.push({
          positionId: pos.id,
          currentProtocol: pos.protocol,
          currentApy: pos.currentApy || 0,
          suggestedProtocol: result.suggestion.protocol,
          suggestedApy: result.suggestion.apy,
          improvement: result.apyImprovement || 0,
          asset: pos.poolSymbol,
        });
      }
    }

    setRotations(suggestions);
    setCheckingRotations(false);
  }, [positions]);

  useEffect(() => {
    if (positions.length > 0) {
      checkRotations();
    }
  }, [positions.length]);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await refetch();
    await checkRotations();
    setRefreshing(false);
  }, [refetch, checkRotations]);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#667eea" />
      }
    >
      {/* Header */}
      <LinearGradient
        colors={['#4338CA', '#6366F1', '#818CF8']}
        style={styles.hero}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        <Pressable
          style={styles.backButton}
          onPress={() => navigation.goBack()}
        >
          <Ionicons name="arrow-back" size={24} color="#E0E7FF" />
        </Pressable>

        <View style={styles.heroContent}>
          <View style={styles.heroTitleRow}>
            <Ionicons name="layers" size={28} color="#C7D2FE" />
            <Text style={styles.heroTitle}>Vault Portfolio</Text>
          </View>
          <Text style={styles.heroSubtitle}>
            Auto-compounding vaults and yield positions
          </Text>

          {/* Portfolio summary */}
          <View style={styles.summaryRow}>
            <View style={styles.summaryItem}>
              <Text style={styles.summaryValue}>
                {totalValue > 0 ? formatUsd(totalValue) : '--'}
              </Text>
              <Text style={styles.summaryLabel}>Total Deposited</Text>
            </View>
            <View style={styles.summaryDivider} />
            <View style={styles.summaryItem}>
              <Text style={[styles.summaryValue, { color: '#34D399' }]}>
                {totalEarnings > 0 ? `+${formatUsd(totalEarnings)}` : '--'}
              </Text>
              <Text style={styles.summaryLabel}>Total Earned</Text>
            </View>
          </View>
        </View>
      </LinearGradient>

      {/* Strategy Rotation Suggestions */}
      {rotations.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Rotation Opportunities</Text>
          {rotations.map((r) => (
            <RotationCard key={r.positionId} suggestion={r} />
          ))}
        </View>
      )}

      {checkingRotations && (
        <View style={styles.checkingRow}>
          <ActivityIndicator size="small" color="#667eea" />
          <Text style={styles.checkingText}>Checking for better yields...</Text>
        </View>
      )}

      {/* Active Positions */}
      {positions.length > 0 && (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Active Positions</Text>
          <View style={styles.positionsCard}>
            {positions.map((pos: any) => (
              <PositionRow key={pos.id} position={pos} />
            ))}
          </View>
        </View>
      )}

      {/* ERC-4626 Vaults */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Deposit into Vaults</Text>
        <ERC4626VaultCard
          walletAddress={walletAddress}
          onDepositSuccess={(vaultId, amount) => {
            refetch();
          }}
          onWithdrawSuccess={(vaultId, amount) => {
            refetch();
          }}
        />
      </View>

      {/* No Wallet Connected State */}
      {!walletAddress && (
        <View style={styles.emptyState}>
          <Ionicons name="wallet-outline" size={48} color="#9CA3AF" />
          <Text style={styles.emptyTitle}>Connect Your Wallet</Text>
          <Text style={styles.emptySubtitle}>
            Connect your wallet to see your vault positions and deposit into auto-compounding vaults.
          </Text>
          <Pressable
            style={({ pressed }) => [styles.connectBtn, pressed && { opacity: 0.8 }]}
            onPress={() => navigation.navigate('DeFiFortress')}
          >
            <Text style={styles.connectBtnText}>Go to DeFi Fortress</Text>
          </Pressable>
        </View>
      )}

      {/* Info Footer */}
      <View style={styles.infoFooter}>
        <Ionicons name="information-circle" size={16} color="#6B7280" />
        <Text style={styles.infoFooterText}>
          Auto-compounding vaults reinvest rewards automatically. Share prices
          increase over time as yield accrues — no manual harvesting needed.
          Strategy rotation uses CoW Swap for MEV-protected token swaps.
        </Text>
      </View>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

// ---------- Styles ----------

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  content: { paddingBottom: 32 },

  // Hero
  hero: {
    paddingTop: 56,
    paddingBottom: 28,
    paddingHorizontal: 20,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
  },
  backButton: {
    position: 'absolute',
    top: 52,
    left: 16,
    zIndex: 10,
    padding: 4,
  },
  heroContent: { alignItems: 'center', marginTop: 8 },
  heroTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginBottom: 6,
  },
  heroTitle: {
    fontSize: 26,
    fontWeight: '800',
    color: '#E0E7FF',
    letterSpacing: -0.5,
  },
  heroSubtitle: {
    fontSize: 14,
    color: '#C7D2FE',
    textAlign: 'center',
    marginBottom: 20,
  },
  summaryRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.12)',
    borderRadius: 16,
    paddingVertical: 16,
    paddingHorizontal: 24,
    gap: 20,
  },
  summaryItem: { alignItems: 'center', flex: 1 },
  summaryDivider: {
    width: 1,
    height: 32,
    backgroundColor: 'rgba(255,255,255,0.2)',
  },
  summaryValue: {
    fontSize: 24,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: -0.5,
  },
  summaryLabel: {
    fontSize: 12,
    color: '#C7D2FE',
    marginTop: 4,
  },

  // Sections
  section: {
    marginTop: 20,
    paddingHorizontal: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 12,
  },

  // Rotation Card
  rotationCard: {
    backgroundColor: '#FFFBEB',
    borderRadius: 14,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#FDE68A',
  },
  rotationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  rotationTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#92400E',
  },
  rotationBody: {
    fontSize: 14,
    color: '#78350F',
    lineHeight: 20,
    marginBottom: 12,
  },
  rotationBtn: {
    backgroundColor: '#F59E0B',
    borderRadius: 10,
    paddingVertical: 10,
    alignItems: 'center',
  },
  rotationBtnText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },

  // Checking row
  checkingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
  },
  checkingText: {
    fontSize: 13,
    color: '#6B7280',
  },

  // Positions
  positionsCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  positionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  positionLeft: {},
  positionSymbolRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  healthDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  positionSymbol: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  positionProtocol: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  positionRight: { alignItems: 'flex-end' },
  positionValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  positionApy: {
    fontSize: 13,
    fontWeight: '600',
    marginTop: 2,
  },

  // Empty state
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
    paddingHorizontal: 32,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#374151',
    marginTop: 12,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    marginTop: 8,
    lineHeight: 20,
  },
  connectBtn: {
    marginTop: 16,
    backgroundColor: '#667eea',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 10,
  },
  connectBtnText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 14,
  },

  // Footer
  infoFooter: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    marginHorizontal: 16,
    marginTop: 20,
    backgroundColor: '#F3F4F6',
    borderRadius: 12,
    padding: 14,
  },
  infoFooterText: {
    fontSize: 12,
    color: '#6B7280',
    lineHeight: 18,
    flex: 1,
  },
});
