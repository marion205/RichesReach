/**
 * DeFi Tribe Card
 *
 * A specialized Wealth Circle subgroup focused on DeFi strategies.
 * Shows strategy shares from community members ("I'm earning X% on Y")
 * and links to DeFi Fortress tools.
 *
 * Part of Phase 3: Community Vanguard
 */
import React from 'react';
import { View, Text, Pressable, StyleSheet } from 'react-native';
import Feather from '@expo/vector-icons/Feather';

// ---------- Types ----------

export interface StrategyShare {
  id: string;
  author: string;
  protocol: string;
  symbol: string;
  apy: number;
  chain: string;
  message: string;
  likes: number;
  timestamp: string;
}

export interface DeFiTribe {
  id: string;
  name: string;
  description: string;
  memberCount: number;
  strategyShares: StrategyShare[];
  icon: string;
  color: string;
}

// ---------- Strategy Share Row ----------

function StrategyShareRow({ share }: { share: StrategyShare }) {
  return (
    <View style={styles.shareRow}>
      <View style={styles.shareIconBg}>
        <Feather name="trending-up" size={14} color="#10B981" />
      </View>
      <View style={styles.shareContent}>
        <Text style={styles.shareMessage} numberOfLines={2}>
          {share.message}
        </Text>
        <View style={styles.shareMeta}>
          <Text style={styles.shareAuthor}>{share.author}</Text>
          <Text style={styles.shareDot}>·</Text>
          <Text style={styles.shareApyBadge}>{share.apy.toFixed(1)}% APY</Text>
          <Text style={styles.shareDot}>·</Text>
          <View style={styles.shareLikes}>
            <Feather name="heart" size={10} color="#EF4444" />
            <Text style={styles.shareLikesText}>{share.likes}</Text>
          </View>
        </View>
      </View>
    </View>
  );
}

// ---------- DeFi Tribe Card ----------

interface DeFiTribeCardProps {
  tribe: DeFiTribe;
  onPress: () => void;
  onShareStrategy?: () => void;
}

export default function DeFiTribeCard({ tribe, onPress, onShareStrategy }: DeFiTribeCardProps) {
  return (
    <Pressable
      style={({ pressed }) => [styles.card, pressed && { opacity: 0.92 }]}
      onPress={onPress}
    >
      {/* Header */}
      <View style={styles.cardHeader}>
        <View style={[styles.tribeIconBg, { backgroundColor: tribe.color + '20' }]}>
          <Feather name={tribe.icon as any} size={22} color={tribe.color} />
        </View>
        <View style={styles.tribeInfo}>
          <Text style={styles.tribeName}>{tribe.name}</Text>
          <Text style={styles.tribeDesc} numberOfLines={1}>{tribe.description}</Text>
        </View>
        <View style={styles.memberBadge}>
          <Feather name="users" size={12} color="#6B7280" />
          <Text style={styles.memberCount}>{tribe.memberCount}</Text>
        </View>
      </View>

      {/* Strategy Shares */}
      {tribe.strategyShares.length > 0 && (
        <View style={styles.sharesSection}>
          <Text style={styles.sharesTitle}>Latest Strategies</Text>
          {tribe.strategyShares.slice(0, 2).map((share) => (
            <StrategyShareRow key={share.id} share={share} />
          ))}
        </View>
      )}

      {/* Footer Actions */}
      <View style={styles.cardFooter}>
        <Pressable
          style={({ pressed }) => [styles.footerBtn, styles.joinBtn, pressed && { opacity: 0.8 }]}
          onPress={onPress}
        >
          <Feather name="log-in" size={14} color="#10B981" />
          <Text style={[styles.footerBtnText, { color: '#10B981' }]}>View Tribe</Text>
        </Pressable>
        {onShareStrategy && (
          <Pressable
            style={({ pressed }) => [styles.footerBtn, styles.shareBtn, pressed && { opacity: 0.8 }]}
            onPress={onShareStrategy}
          >
            <Feather name="share-2" size={14} color="#7C3AED" />
            <Text style={[styles.footerBtnText, { color: '#7C3AED' }]}>Share Strategy</Text>
          </Pressable>
        )}
      </View>
    </Pressable>
  );
}

// ---------- Default Tribes Data ----------

export const DEFAULT_DEFI_TRIBES: DeFiTribe[] = [
  {
    id: 'yield-hunters',
    name: 'Yield Hunters',
    description: 'Finding the best yield opportunities across DeFi',
    memberCount: 342,
    icon: 'target',
    color: '#10B981',
    strategyShares: [
      {
        id: 's1',
        author: 'YieldKing',
        protocol: 'Aave V3',
        symbol: 'USDC',
        apy: 8.5,
        chain: 'ethereum',
        message: "Earning 8.5% on Aave V3 USDC — stable and audited. My Fortress is growing!",
        likes: 24,
        timestamp: '2h ago',
      },
      {
        id: 's2',
        author: 'DeFiNewbie',
        protocol: 'Compound V3',
        symbol: 'ETH',
        apy: 3.2,
        chain: 'ethereum',
        message: "Just started earning on my ETH! 3.2% APY on Compound. Small start, big dreams.",
        likes: 41,
        timestamp: '5h ago',
      },
    ],
  },
  {
    id: 'risk-managers',
    name: 'Risk Managers',
    description: 'Protecting positions and managing health factors',
    memberCount: 187,
    icon: 'shield',
    color: '#3B82F6',
    strategyShares: [
      {
        id: 's3',
        author: 'SafeHandles',
        protocol: 'Aave V3',
        symbol: 'WBTC',
        apy: 1.8,
        chain: 'polygon',
        message: "Keeping health factor above 2.0 on my WBTC position. Sleep well knowing it's safe.",
        likes: 18,
        timestamp: '1d ago',
      },
    ],
  },
  {
    id: 'defi-beginners',
    name: 'DeFi First Steps',
    description: 'New to DeFi? Start here with the community',
    memberCount: 523,
    icon: 'compass',
    color: '#F59E0B',
    strategyShares: [
      {
        id: 's4',
        author: 'BuildingWealth',
        protocol: 'Lido',
        symbol: 'stETH',
        apy: 4.1,
        chain: 'ethereum',
        message: "Just staked my first ETH with Lido! 4.1% APY and I can still use stETH in DeFi.",
        likes: 55,
        timestamp: '3h ago',
      },
    ],
  },
];

// ---------- Styles ----------

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 16,
    marginBottom: 14,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 3,
  },

  // Header
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  tribeIconBg: {
    width: 44,
    height: 44,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  tribeInfo: { flex: 1 },
  tribeName: { fontSize: 16, fontWeight: '700', color: '#111827' },
  tribeDesc: { fontSize: 12, color: '#6B7280', marginTop: 2 },
  memberBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: '#F3F4F6',
    borderRadius: 8,
  },
  memberCount: { fontSize: 12, fontWeight: '600', color: '#6B7280' },

  // Shares
  sharesSection: { marginBottom: 12 },
  sharesTitle: { fontSize: 12, fontWeight: '600', color: '#9CA3AF', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 },
  shareRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
  },
  shareIconBg: {
    width: 28,
    height: 28,
    borderRadius: 8,
    backgroundColor: '#ECFDF5',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 2,
  },
  shareContent: { flex: 1 },
  shareMessage: { fontSize: 13, color: '#374151', lineHeight: 18 },
  shareMeta: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 4 },
  shareAuthor: { fontSize: 11, color: '#9CA3AF', fontWeight: '500' },
  shareDot: { fontSize: 11, color: '#D1D5DB' },
  shareApyBadge: { fontSize: 11, fontWeight: '700', color: '#10B981' },
  shareLikes: { flexDirection: 'row', alignItems: 'center', gap: 2 },
  shareLikesText: { fontSize: 11, color: '#9CA3AF' },

  // Footer
  cardFooter: { flexDirection: 'row', gap: 8 },
  footerBtn: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 10,
    borderRadius: 10,
  },
  joinBtn: { backgroundColor: '#ECFDF5' },
  shareBtn: { backgroundColor: '#F5F3FF' },
  footerBtnText: { fontSize: 13, fontWeight: '600' },
});
