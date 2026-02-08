/**
 * DeFi Positions Screen
 *
 * Shows the user's active DeFi positions with:
 * - Health factor gauge (visual risk indicator)
 * - Position cards with staked amounts, rewards, APY
 * - Transaction history
 * - Manage actions (harvest, withdraw, add more)
 *
 * Part of Phase 2: Wallet Stronghold
 */
import React, { useState, useCallback } from 'react';
import {
  View,
  Text,
  ScrollView,
  Pressable,
  StyleSheet,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import Feather from '@expo/vector-icons/Feather';
import { useNavigation } from '@react-navigation/native';
import { useQuery, gql } from '@apollo/client';
import { LinearGradient } from 'expo-linear-gradient';
import { useWallet } from '../../../wallet/WalletProvider';
import logger from '../../../utils/logger';

// ---------- GraphQL Queries ----------

const DEFI_ACCOUNT_QUERY = gql`
  query DefiAccount {
    defiAccount {
      healthFactor
      availableBorrowUsd
      collateralUsd
      debtUsd
      ltvWeighted
      liqThresholdWeighted
      supplies
      borrows
      pricesUsd
    }
  }
`;

const USER_POSITIONS_QUERY = gql`
  query TopYields($limit: Int) {
    topYields(limit: $limit) {
      id
      protocol
      chain
      symbol
      apy
      tvl
      risk
    }
  }
`;

// ---------- Health Factor Gauge ----------

function HealthFactorGauge({ healthFactor }: { healthFactor: number }) {
  const getStatus = (hf: number) => {
    if (hf === 0) return { label: 'No Position', color: '#9CA3AF', bgColor: '#F3F4F6', icon: 'minus' as const };
    if (hf >= 2.0) return { label: 'Very Safe', color: '#10B981', bgColor: '#D1FAE5', icon: 'shield' as const };
    if (hf >= 1.5) return { label: 'Safe', color: '#34D399', bgColor: '#ECFDF5', icon: 'check-circle' as const };
    if (hf >= 1.2) return { label: 'Moderate', color: '#F59E0B', bgColor: '#FEF3C7', icon: 'alert-triangle' as const };
    if (hf >= 1.05) return { label: 'At Risk', color: '#EF4444', bgColor: '#FEE2E2', icon: 'alert-circle' as const };
    return { label: 'DANGER', color: '#DC2626', bgColor: '#FEE2E2', icon: 'x-circle' as const };
  };

  const status = getStatus(healthFactor);

  // Gauge fill percentage (HF 0-3 maps to 0-100%)
  const fillPct = healthFactor === 0 ? 0 : Math.min(100, (healthFactor / 3) * 100);

  return (
    <View style={[styles.gaugeContainer, { backgroundColor: status.bgColor }]}>
      <View style={styles.gaugeHeader}>
        <View style={styles.gaugeIconRow}>
          <Feather name={status.icon} size={20} color={status.color} />
          <Text style={[styles.gaugeLabel, { color: status.color }]}>{status.label}</Text>
        </View>
        <Text style={[styles.gaugeValue, { color: status.color }]}>
          {healthFactor === 0 ? '--' : healthFactor.toFixed(2)}
        </Text>
      </View>

      {/* Visual bar */}
      <View style={styles.gaugeBarBg}>
        <View
          style={[
            styles.gaugeBarFill,
            {
              width: `${fillPct}%`,
              backgroundColor: status.color,
            },
          ]}
        />
        {/* Danger zone marker at 1.0 */}
        <View style={styles.gaugeDangerMarker} />
      </View>

      <View style={styles.gaugeFooter}>
        <Text style={styles.gaugeFooterText}>Liquidation</Text>
        <Text style={styles.gaugeFooterText}>Health Factor</Text>
        <Text style={styles.gaugeFooterText}>Very Safe</Text>
      </View>
    </View>
  );
}

// ---------- Account Summary Card ----------

function AccountSummary({
  collateral,
  debt,
  availableBorrow,
}: {
  collateral: number;
  debt: number;
  availableBorrow: number;
}) {
  return (
    <View style={styles.summaryCard}>
      <View style={styles.summaryRow}>
        <View style={styles.summaryItem}>
          <Text style={styles.summaryLabel}>Total Collateral</Text>
          <Text style={styles.summaryValue}>${collateral.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</Text>
        </View>
        <View style={styles.summaryDivider} />
        <View style={styles.summaryItem}>
          <Text style={styles.summaryLabel}>Total Debt</Text>
          <Text style={[styles.summaryValue, debt > 0 && { color: '#EF4444' }]}>
            ${debt.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </Text>
        </View>
      </View>
      <View style={styles.borrowRow}>
        <Text style={styles.borrowLabel}>Available to Borrow</Text>
        <Text style={styles.borrowValue}>
          ${availableBorrow.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </Text>
      </View>
    </View>
  );
}

// ---------- Position Card ----------

interface SupplyPosition {
  symbol: string;
  amount: string;
  valueUsd: number;
}

function PositionCard({
  position,
  onHarvest,
  onWithdraw,
  onAddMore,
}: {
  position: SupplyPosition;
  onHarvest: () => void;
  onWithdraw: () => void;
  onAddMore: () => void;
}) {
  return (
    <View style={styles.positionCard}>
      <View style={styles.positionHeader}>
        <View style={styles.positionLeft}>
          <View style={styles.positionIconBg}>
            <Feather name="layers" size={18} color="#10B981" />
          </View>
          <View>
            <Text style={styles.positionSymbol}>{position.symbol}</Text>
            <Text style={styles.positionAmount}>
              {parseFloat(position.amount).toLocaleString('en-US', { maximumFractionDigits: 6 })} tokens
            </Text>
          </View>
        </View>
        <View style={styles.positionRight}>
          <Text style={styles.positionValueUsd}>
            ${position.valueUsd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </Text>
          <View style={styles.activeBadge}>
            <View style={styles.activeDot} />
            <Text style={styles.activeBadgeText}>Active</Text>
          </View>
        </View>
      </View>

      {/* Actions */}
      <View style={styles.positionActions}>
        <Pressable
          style={({ pressed }) => [styles.posActionBtn, styles.posActionHarvest, pressed && { opacity: 0.8 }]}
          onPress={onHarvest}
        >
          <Feather name="gift" size={14} color="#10B981" />
          <Text style={[styles.posActionText, { color: '#10B981' }]}>Harvest</Text>
        </Pressable>
        <Pressable
          style={({ pressed }) => [styles.posActionBtn, styles.posActionAdd, pressed && { opacity: 0.8 }]}
          onPress={onAddMore}
        >
          <Feather name="plus" size={14} color="#3B82F6" />
          <Text style={[styles.posActionText, { color: '#3B82F6' }]}>Add More</Text>
        </Pressable>
        <Pressable
          style={({ pressed }) => [styles.posActionBtn, styles.posActionWithdraw, pressed && { opacity: 0.8 }]}
          onPress={onWithdraw}
        >
          <Feather name="arrow-down-circle" size={14} color="#F59E0B" />
          <Text style={[styles.posActionText, { color: '#F59E0B' }]}>Withdraw</Text>
        </Pressable>
      </View>
    </View>
  );
}

// ---------- Empty State ----------

function EmptyPositions({ onDeposit }: { onDeposit: () => void }) {
  return (
    <View style={styles.emptyState}>
      <View style={styles.emptyIconBg}>
        <Feather name="shield" size={40} color="#10B981" />
      </View>
      <Text style={styles.emptyTitle}>No Active Positions</Text>
      <Text style={styles.emptyDesc}>
        Start earning yield by depositing into a DeFi protocol. Your Fortress awaits.
      </Text>
      <Pressable
        style={({ pressed }) => [styles.emptyBtn, pressed && { opacity: 0.85 }]}
        onPress={onDeposit}
      >
        <Feather name="plus-circle" size={18} color="#FFFFFF" />
        <Text style={styles.emptyBtnText}>Make Your First Deposit</Text>
      </Pressable>
    </View>
  );
}

// ---------- Not Connected State ----------

function WalletNotConnected({ onConnect }: { onConnect: () => void }) {
  return (
    <View style={styles.emptyState}>
      <View style={[styles.emptyIconBg, { backgroundColor: '#DBEAFE' }]}>
        <Feather name="link" size={40} color="#3B82F6" />
      </View>
      <Text style={styles.emptyTitle}>Connect Your Wallet</Text>
      <Text style={styles.emptyDesc}>
        Connect a wallet to view and manage your DeFi positions.
      </Text>
      <Pressable
        style={({ pressed }) => [styles.emptyBtn, { backgroundColor: '#3B82F6' }, pressed && { opacity: 0.85 }]}
        onPress={onConnect}
      >
        <Feather name="link-2" size={18} color="#FFFFFF" />
        <Text style={styles.emptyBtnText}>Connect Wallet</Text>
      </Pressable>
    </View>
  );
}

// ---------- Main Screen ----------

export default function DeFiPositionsScreen() {
  const navigation = useNavigation<any>();
  const { isConnected, address, connect } = useWallet();
  const [refreshing, setRefreshing] = useState(false);

  const {
    data: accountData,
    loading,
    refetch,
  } = useQuery(DEFI_ACCOUNT_QUERY, {
    skip: !isConnected,
    fetchPolicy: 'cache-and-network',
  });

  const account = accountData?.defiAccount;
  const healthFactor = account?.healthFactor || 0;
  const collateral = account?.collateralUsd || 0;
  const debt = account?.debtUsd || 0;
  const availableBorrow = account?.availableBorrowUsd || 0;
  const supplies: SupplyPosition[] = account?.supplies || [];

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await refetch();
    } catch (e) {
      logger.warn('Position refresh error:', e);
    }
    setRefreshing(false);
  }, [refetch]);

  const handleConnect = useCallback(async () => {
    try {
      await connect();
    } catch (e) {
      logger.error('Wallet connect error from positions:', e);
    }
  }, [connect]);

  return (
    <View style={styles.container}>
      {/* Header */}
      <LinearGradient
        colors={['#064E3B', '#065F46']}
        style={styles.header}
      >
        <View style={styles.headerRow}>
          <Pressable
            style={({ pressed }) => [styles.backBtn, pressed && { opacity: 0.7 }]}
            onPress={() => navigation.goBack()}
          >
            <Feather name="arrow-left" size={22} color="#FFFFFF" />
          </Pressable>
          <Text style={styles.headerTitle}>My Positions</Text>
          <View style={{ width: 36 }} />
        </View>
        {isConnected && address && (
          <View style={styles.walletBadge}>
            <View style={styles.walletDot} />
            <Text style={styles.walletText}>
              {address.slice(0, 6)}...{address.slice(-4)}
            </Text>
          </View>
        )}
      </LinearGradient>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#10B981" />
        }
      >
        {/* Not connected state */}
        {!isConnected ? (
          <WalletNotConnected onConnect={handleConnect} />
        ) : loading && !account ? (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#10B981" />
            <Text style={styles.loadingText}>Loading positions...</Text>
          </View>
        ) : (
          <>
            {/* Health Factor Gauge */}
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Health Factor</Text>
              <HealthFactorGauge healthFactor={healthFactor} />
            </View>

            {/* Account Summary */}
            {(collateral > 0 || debt > 0) && (
              <View style={styles.section}>
                <Text style={styles.sectionTitle}>Account Summary</Text>
                <AccountSummary
                  collateral={collateral}
                  debt={debt}
                  availableBorrow={availableBorrow}
                />
              </View>
            )}

            {/* Active Positions */}
            <View style={styles.section}>
              <View style={styles.sectionHeaderRow}>
                <Text style={styles.sectionTitle}>Active Positions</Text>
                <Text style={styles.positionCount}>
                  {supplies.length} {supplies.length === 1 ? 'position' : 'positions'}
                </Text>
              </View>

              {supplies.length === 0 ? (
                <EmptyPositions
                  onDeposit={() => navigation.navigate('DeFiFortress')}
                />
              ) : (
                supplies.map((pos, idx) => (
                  <PositionCard
                    key={`${pos.symbol}-${idx}`}
                    position={pos}
                    onHarvest={() => {
                      logger.log('Harvest pressed for:', pos.symbol);
                      // Phase 2: Harvest will be wired to HybridTransactionService
                    }}
                    onWithdraw={() => {
                      logger.log('Withdraw pressed for:', pos.symbol);
                      // Phase 2: Withdraw flow
                    }}
                    onAddMore={() => {
                      navigation.navigate('DeFiFortress');
                    }}
                  />
                ))
              )}
            </View>

            {/* Quick Actions */}
            <View style={styles.section}>
              <View style={styles.quickActionsRow}>
                <Pressable
                  style={({ pressed }) => [styles.quickActionCard, pressed && { opacity: 0.85 }]}
                  onPress={() => navigation.navigate('DeFiFortress')}
                >
                  <Feather name="plus-circle" size={22} color="#10B981" />
                  <Text style={styles.quickActionLabel}>New Deposit</Text>
                </Pressable>
                <Pressable
                  style={({ pressed }) => [styles.quickActionCard, pressed && { opacity: 0.85 }]}
                  onPress={() => navigation.navigate('DeFiFortress')}
                >
                  <Feather name="bar-chart-2" size={22} color="#3B82F6" />
                  <Text style={styles.quickActionLabel}>Yield Optimizer</Text>
                </Pressable>
                <Pressable
                  style={({ pressed }) => [styles.quickActionCard, pressed && { opacity: 0.85 }]}
                  onPress={() => {
                    navigation.navigate('Learn');
                  }}
                >
                  <Feather name="book-open" size={22} color="#F59E0B" />
                  <Text style={styles.quickActionLabel}>DeFi Guide</Text>
                </Pressable>
              </View>
            </View>

            {/* Testnet Banner */}
            <View style={styles.testnetBanner}>
              <Feather name="info" size={16} color="#6366F1" />
              <Text style={styles.testnetText}>
                Sepolia Testnet — No real funds at risk. Perfect for practice.
              </Text>
            </View>
          </>
        )}

        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}

// ---------- Styles ----------

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },

  // Header
  header: {
    paddingTop: 56,
    paddingBottom: 16,
    paddingHorizontal: 20,
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  backBtn: { padding: 6 },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  walletBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'center',
    marginTop: 10,
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: 'rgba(255,255,255,0.15)',
    borderRadius: 20,
    gap: 6,
  },
  walletDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#34D399',
  },
  walletText: {
    fontSize: 13,
    color: '#A7F3D0',
    fontFamily: 'monospace',
  },

  // Scroll
  scrollView: { flex: 1 },
  scrollContent: { paddingTop: 20 },

  // Sections
  section: { paddingHorizontal: 16, marginBottom: 20 },
  sectionTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 10,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  positionCount: {
    fontSize: 13,
    color: '#6B7280',
    fontWeight: '500',
  },

  // Health Factor Gauge
  gaugeContainer: {
    padding: 16,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(0,0,0,0.05)',
  },
  gaugeHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  gaugeIconRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  gaugeLabel: {
    fontSize: 15,
    fontWeight: '700',
  },
  gaugeValue: {
    fontSize: 28,
    fontWeight: '900',
    letterSpacing: -0.5,
  },
  gaugeBarBg: {
    height: 10,
    borderRadius: 5,
    backgroundColor: 'rgba(0,0,0,0.08)',
    overflow: 'hidden',
    position: 'relative',
  },
  gaugeBarFill: {
    height: '100%',
    borderRadius: 5,
  },
  gaugeDangerMarker: {
    position: 'absolute',
    left: '33.3%',
    top: -2,
    width: 2,
    height: 14,
    backgroundColor: '#EF4444',
    borderRadius: 1,
  },
  gaugeFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 6,
  },
  gaugeFooterText: {
    fontSize: 10,
    color: '#9CA3AF',
    fontWeight: '500',
  },

  // Account Summary
  summaryCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
  },
  summaryRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  summaryItem: {
    flex: 1,
    alignItems: 'center',
  },
  summaryLabel: {
    fontSize: 12,
    color: '#6B7280',
    marginBottom: 4,
    fontWeight: '500',
  },
  summaryValue: {
    fontSize: 22,
    fontWeight: '800',
    color: '#111827',
  },
  summaryDivider: {
    width: 1,
    height: 40,
    backgroundColor: '#E5E7EB',
  },
  borrowRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 14,
    paddingTop: 14,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
  },
  borrowLabel: {
    fontSize: 13,
    color: '#6B7280',
    fontWeight: '500',
  },
  borrowValue: {
    fontSize: 16,
    fontWeight: '700',
    color: '#10B981',
  },

  // Position Card
  positionCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
  },
  positionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  positionLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  positionIconBg: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: '#ECFDF5',
    alignItems: 'center',
    justifyContent: 'center',
  },
  positionSymbol: {
    fontSize: 16,
    fontWeight: '700',
    color: '#111827',
  },
  positionAmount: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  positionRight: {
    alignItems: 'flex-end',
  },
  positionValueUsd: {
    fontSize: 18,
    fontWeight: '800',
    color: '#111827',
  },
  activeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 4,
  },
  activeDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#10B981',
  },
  activeBadgeText: {
    fontSize: 11,
    color: '#10B981',
    fontWeight: '600',
  },

  // Position Actions
  positionActions: {
    flexDirection: 'row',
    gap: 8,
  },
  posActionBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 4,
    paddingVertical: 10,
    borderRadius: 10,
  },
  posActionHarvest: {
    backgroundColor: '#ECFDF5',
  },
  posActionAdd: {
    backgroundColor: '#EFF6FF',
  },
  posActionWithdraw: {
    backgroundColor: '#FFFBEB',
  },
  posActionText: {
    fontSize: 12,
    fontWeight: '600',
  },

  // Quick Actions
  quickActionsRow: {
    flexDirection: 'row',
    gap: 10,
  },
  quickActionCard: {
    flex: 1,
    alignItems: 'center',
    gap: 8,
    padding: 16,
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
  },
  quickActionLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: '#374151',
    textAlign: 'center',
  },

  // Empty State
  emptyState: {
    alignItems: 'center',
    paddingVertical: 48,
    paddingHorizontal: 32,
  },
  emptyIconBg: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#D1FAE5',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
  },
  emptyDesc: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 24,
  },
  emptyBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 24,
    paddingVertical: 14,
    backgroundColor: '#10B981',
    borderRadius: 14,
  },
  emptyBtnText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFFFFF',
  },

  // Loading
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 60,
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
    color: '#6B7280',
  },

  // Testnet Banner
  testnetBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginHorizontal: 16,
    paddingHorizontal: 14,
    paddingVertical: 10,
    backgroundColor: '#EEF2FF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#C7D2FE',
  },
  testnetText: {
    flex: 1,
    fontSize: 12,
    color: '#6366F1',
    lineHeight: 16,
  },
});
