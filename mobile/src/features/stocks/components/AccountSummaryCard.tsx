import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { Dimensions } from 'react-native';
import { AccountSummarySkeleton } from './SkeletonLoader';

const { width } = Dimensions.get('window');

const C = {
  card: '#FFFFFF',
  line: '#E9EAF0',
  text: '#111827',
  sub: '#6B7280',
  primary: '#007AFF',
  green: '#22C55E',
  red: '#EF4444',
  amber: '#F59E0B',
  successSoft: '#EAFBF1',
  dangerSoft: '#FEECEC',
};

interface AccountSummaryCardProps {
  account: {
    portfolioValue?: number;
    equity?: number;
    buyingPower?: number;
    cash?: number;
    dayTradingBuyingPower?: number;
    isDayTradingEnabled?: boolean;
    tradingBlocked?: boolean;
    accountStatus?: string;
  } | null;
  alpacaAccount?: {
    id?: string;
    status?: string;
    approvedAt?: string | null;
  } | null;
  loading?: boolean;
}

const formatMoney = (v?: number, digits = 2) =>
  `$${(Number(v) || 0).toLocaleString(undefined, {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}`;

const Chip = ({
  label,
  tone = 'neutral',
}: {
  label: string;
  tone?: 'neutral' | 'success' | 'danger' | 'warning' | 'info';
}) => {
  const toneMap: any = {
    neutral: { bg: '#F3F4F6', color: C.sub },
    success: { bg: C.successSoft, color: C.green },
    danger: { bg: C.dangerSoft, color: C.red },
    warning: { bg: '#FFF7ED', color: C.amber },
    info: { bg: '#E8F1FF', color: C.primary },
  };
  const t = toneMap[tone];
  return (
    <View style={[styles.chip, { backgroundColor: t.bg }]}>
      <Text style={[styles.chipText, { color: t.color }]}>{label}</Text>
    </View>
  );
};

export const AccountSummaryCard: React.FC<AccountSummaryCardProps> = React.memo(
  ({ account, alpacaAccount, loading = false }) => {
    if (loading) {
      return <AccountSummarySkeleton />;
    }

    if (!account) {
      return (
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={styles.cardTitle}>Account Summary</Text>
          </View>
          <Text style={[styles.sub, { textAlign: 'center' }]}>
            Unable to load account data.
          </Text>
        </View>
      );
    }

    return (
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle}>Account Summary</Text>
          {account.accountStatus ? (
            <Chip
              label={account.accountStatus.toUpperCase()}
              tone={account.accountStatus?.toLowerCase() === 'active' ? 'success' : 'warning'}
            />
          ) : null}
        </View>

        <View style={styles.grid}>
          <View style={[styles.gridCell, styles.gridCellTopLeft]}>
            <Text style={styles.label}>Portfolio Value</Text>
            <Text style={styles.value}>{formatMoney(account.portfolioValue)}</Text>
          </View>
          <View style={[styles.gridCell, styles.gridCellTopRight]}>
            <Text style={styles.label}>Equity</Text>
            <Text style={styles.value}>{formatMoney(account.equity)}</Text>
          </View>
          <View style={[styles.gridCell, styles.gridCellMiddleLeft]}>
            <Text style={styles.label}>Buying Power</Text>
            <Text style={styles.value}>{formatMoney(account.buyingPower)}</Text>
          </View>
          <View style={[styles.gridCell, styles.gridCellMiddleRight]}>
            <Text style={styles.label}>Cash</Text>
            <Text style={styles.value}>{formatMoney(account.cash)}</Text>
          </View>
          <View style={[styles.gridCell, styles.gridCellBottomLeft]}>
            <Text style={styles.label}>DT Buying Power</Text>
            <Text style={styles.value}>{formatMoney(account.dayTradingBuyingPower)}</Text>
          </View>
          <View style={[styles.gridCell, styles.gridCellBottomRight]}>
            <Text style={styles.label}>Day Trading</Text>
            <Text
              style={[
                styles.value,
                { color: account.isDayTradingEnabled ? C.green : C.red },
              ]}
            >
              {account.isDayTradingEnabled ? 'Enabled' : 'Disabled'}
            </Text>
          </View>
        </View>

        {account.tradingBlocked && (
          <View style={styles.alertSoft}>
            <Icon name="alert-triangle" size={16} color={C.amber} />
            <Text style={[styles.sub, { marginLeft: 8 }]}>Trading is currently blocked</Text>
          </View>
        )}

        {/* Alpaca Account Status */}
        {alpacaAccount && (
          <View style={styles.alpacaStatusCard}>
            <View style={styles.alpacaStatusHeader}>
              <Icon
                name="shield"
                size={16}
                color={alpacaAccount.approvedAt ? C.green : C.amber}
              />
              <Text style={styles.alpacaStatusTitle}>Alpaca Account</Text>
              <Chip
                label={alpacaAccount.status?.toUpperCase() || 'UNKNOWN'}
                tone={alpacaAccount.approvedAt ? 'success' : 'warning'}
              />
            </View>

            {!alpacaAccount.approvedAt && (
              <View style={styles.kycPrompt}>
                <Text style={styles.kycPromptText}>
                  Complete KYC verification to start trading with real money
                </Text>
                <TouchableOpacity
                  style={styles.kycButton}
                  onPress={() => {
                    Alert.alert(
                      'KYC Verification',
                      'This will open the KYC verification process. You\'ll need to provide identity documents and personal information.',
                      [
                        { text: 'Cancel', style: 'cancel' },
                        {
                          text: 'Start KYC',
                          onPress: () => {
                            Alert.alert('KYC Process', 'KYC verification process would start here.');
                          },
                        },
                      ]
                    );
                  }}
                >
                  <Text style={styles.kycButtonText}>Start KYC</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        )}
      </View>
    );
  },
  (prevProps, nextProps) => {
    // Custom comparison for better memoization
    return (
      prevProps.loading === nextProps.loading &&
      prevProps.account?.id === nextProps.account?.id &&
      prevProps.account?.portfolioValue === nextProps.account?.portfolioValue &&
      prevProps.alpacaAccount?.id === nextProps.alpacaAccount?.id &&
      prevProps.alpacaAccount?.approvedAt === nextProps.alpacaAccount?.approvedAt
    );
  }
);

AccountSummaryCard.displayName = 'AccountSummaryCard';

const styles = StyleSheet.create({
  card: {
    backgroundColor: C.card,
    borderRadius: 16,
    padding: 16,
    marginTop: 12,
    shadowColor: 'rgba(16,24,40,0.08)',
    shadowOpacity: 1,
    shadowRadius: 10,
    shadowOffset: { width: 0, height: 2 },
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  cardTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: C.text,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: C.line,
    marginTop: 8,
  },
  gridCell: {
    width: (width - 16 * 2 - 1) / 2,
    paddingVertical: 12,
    paddingHorizontal: 12,
  },
  gridCellTopLeft: {
    borderRightWidth: StyleSheet.hairlineWidth,
    borderRightColor: C.line,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: C.line,
  },
  gridCellTopRight: {
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: C.line,
  },
  gridCellMiddleLeft: {
    borderRightWidth: StyleSheet.hairlineWidth,
    borderRightColor: C.line,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: C.line,
  },
  gridCellMiddleRight: {
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: C.line,
  },
  gridCellBottomLeft: {
    borderRightWidth: StyleSheet.hairlineWidth,
    borderRightColor: C.line,
  },
  gridCellBottomRight: {
    // No borders for bottom right
  },
  label: {
    fontSize: 12,
    color: C.sub,
  },
  value: {
    fontSize: 16,
    fontWeight: '700',
    color: C.text,
  },
  sub: {
    fontSize: 13,
    color: C.sub,
  },
  chip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
    alignSelf: 'flex-start',
  },
  chipText: {
    fontSize: 11,
    fontWeight: '700',
  },
  centerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
  },
  alertSoft: {
    marginTop: 12,
    padding: 12,
    borderRadius: 12,
    backgroundColor: '#FFF7E6',
    flexDirection: 'row',
    alignItems: 'center',
  },
  alpacaStatusCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: 12,
    padding: 16,
    marginTop: 12,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  alpacaStatusHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  alpacaStatusTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: C.text,
    marginLeft: 8,
    flex: 1,
  },
  kycPrompt: {
    marginTop: 8,
    padding: 12,
    backgroundColor: '#FEF3C7',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#FDE68A',
  },
  kycPromptText: {
    fontSize: 13,
    color: '#92400E',
    marginBottom: 8,
    lineHeight: 18,
  },
  kycButton: {
    backgroundColor: '#F59E0B',
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  kycButtonText: {
    color: '#FFFFFF',
    fontSize: 13,
    fontWeight: '600',
  },
});

