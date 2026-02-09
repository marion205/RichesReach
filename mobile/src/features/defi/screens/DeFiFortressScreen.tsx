/**
 * DeFi Fortress Screen — Phase 6: Fortress Complete
 *
 * The branded "aha moment" for RichesReach DeFi.
 * Shows Ghost Whisper AI, portfolio analytics, achievements,
 * live yield data, and education entry points.
 * Designed to feel approachable and empowering for BIPOC investors.
 */
import React, { useState, useCallback, useEffect, useRef } from 'react';
import {
  View,
  Text,
  ScrollView,
  Pressable,
  StyleSheet,
  RefreshControl,
  Animated,
  ActivityIndicator,
} from 'react-native';
import Feather from '@expo/vector-icons/Feather';
import { useNavigation } from '@react-navigation/native';
import { useQuery, gql } from '@apollo/client';
import { LinearGradient } from 'expo-linear-gradient';
import logger from '../../../utils/logger';

// ---------- GraphQL Queries ----------

const TOP_YIELDS_QUERY = gql`
  query TopYields($chain: String, $limit: Int) {
    topYields(chain: $chain, limit: $limit) {
      id
      protocol
      chain
      symbol
      poolAddress
      apy
      tvl
      risk
    }
  }
`;

const AI_YIELD_OPTIMIZER_QUERY = gql`
  query AIYieldOptimizer($userRiskTolerance: Float!, $chain: String, $limit: Int) {
    aiYieldOptimizer(userRiskTolerance: $userRiskTolerance, chain: $chain, limit: $limit) {
      expectedApy
      totalRisk
      explanation
      optimizationStatus
      allocations {
        id
        protocol
        apy
        tvl
        risk
        symbol
        chain
        weight
      }
    }
  }
`;

const GHOST_WHISPER_QUERY = gql`
  query GhostWhisper {
    ghostWhisper {
      message
      action
      confidence
      reasoning
      suggestedPool
    }
  }
`;

const ACHIEVEMENTS_QUERY = gql`
  query DefiAchievements {
    defiAchievements {
      id
      title
      description
      icon
      color
      category
      earned
      earnedAt
      progress
    }
  }
`;

const PORTFOLIO_ANALYTICS_QUERY = gql`
  query PortfolioAnalytics {
    portfolioAnalytics {
      totalDepositedUsd
      totalRewardsUsd
      totalPositions
      activeChains
      activeProtocols
      realizedApy
      sharpeRatio
      maxDrawdownEstimate
      portfolioDiversityScore
    }
  }
`;

// ---------- Helpers ----------

function formatTVL(tvl: number): string {
  if (tvl >= 1_000_000_000) return `$${(tvl / 1_000_000_000).toFixed(1)}B`;
  if (tvl >= 1_000_000) return `$${(tvl / 1_000_000).toFixed(1)}M`;
  if (tvl >= 1_000) return `$${(tvl / 1_000).toFixed(0)}K`;
  return `$${tvl.toFixed(0)}`;
}

function formatUSD(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(1)}K`;
  return `$${value.toFixed(2)}`;
}

function riskLabel(risk: number): { text: string; color: string } {
  if (risk <= 0.25) return { text: 'Low Risk', color: '#10B981' };
  if (risk <= 0.5) return { text: 'Medium', color: '#F59E0B' };
  return { text: 'Higher Risk', color: '#EF4444' };
}

function chainIcon(chain: string): string {
  const map: Record<string, string> = {
    ethereum: 'circle',
    polygon: 'hexagon',
    arbitrum: 'triangle',
    base: 'square',
    optimism: 'octagon',
  };
  return map[chain] || 'globe';
}

function ghostWhisperActionIcon(action: string): string {
  const map: Record<string, string> = {
    deposit: 'plus-circle',
    rotate: 'refresh-cw',
    harvest: 'zap',
    diversify: 'git-branch',
    hold: 'shield',
  };
  return map[action] || 'message-circle';
}

// ---------- Animated Yield Counter ----------

function AnimatedAPY({ value }: { value: number }) {
  const animValue = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(animValue, {
      toValue: value,
      duration: 1200,
      useNativeDriver: false,
    }).start();
  }, [value]);

  return (
    <View style={styles.apyContainer}>
      <Text style={styles.apyValue}>{value.toFixed(1)}%</Text>
      <Text style={styles.apyLabel}>Expected APY</Text>
    </View>
  );
}

// ---------- Ghost Whisper Card ----------

interface GhostWhisperData {
  message: string;
  action: string;
  confidence: number;
  reasoning: string;
  suggestedPool?: any;
}

function GhostWhisperCard({ whisper, onPress }: { whisper: GhostWhisperData; onPress: () => void }) {
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.05, duration: 1500, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 1500, useNativeDriver: true }),
      ])
    ).start();
  }, []);

  const confidenceLabel = whisper.confidence >= 0.8 ? 'High' : whisper.confidence >= 0.5 ? 'Medium' : 'Low';
  const confidenceColor = whisper.confidence >= 0.8 ? '#10B981' : whisper.confidence >= 0.5 ? '#F59E0B' : '#6B7280';

  return (
    <Pressable onPress={onPress}>
      <Animated.View style={[styles.ghostWhisperCard, { transform: [{ scale: pulseAnim }] }]}>
        <LinearGradient
          colors={['#1E1B4B', '#312E81', '#3730A3']}
          style={styles.ghostWhisperGradient}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        >
          <View style={styles.ghostWhisperHeader}>
            <View style={styles.ghostWhisperTitleRow}>
              <Feather name="message-circle" size={18} color="#A5B4FC" />
              <Text style={styles.ghostWhisperTitle}>Ghost Whisper</Text>
            </View>
            <View style={[styles.confidenceBadge, { backgroundColor: confidenceColor + '30' }]}>
              <Text style={[styles.confidenceText, { color: confidenceColor }]}>{confidenceLabel}</Text>
            </View>
          </View>
          <Text style={styles.ghostWhisperMessage}>{whisper.message}</Text>
          <View style={styles.ghostWhisperAction}>
            <Feather name={ghostWhisperActionIcon(whisper.action) as any} size={16} color="#C4B5FD" />
            <Text style={styles.ghostWhisperActionText}>{whisper.reasoning}</Text>
          </View>
        </LinearGradient>
      </Animated.View>
    </Pressable>
  );
}

// ---------- Achievement Badge ----------

interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string;
  color: string;
  category: string;
  earned: boolean;
  progress: number;
}

function AchievementBadge({ achievement }: { achievement: Achievement }) {
  return (
    <View style={[styles.achievementBadge, !achievement.earned && styles.achievementLocked]}>
      <View
        style={[
          styles.achievementIconContainer,
          { backgroundColor: achievement.earned ? achievement.color + '20' : '#F3F4F6' },
        ]}
      >
        <Feather
          name={achievement.icon as any}
          size={20}
          color={achievement.earned ? achievement.color : '#9CA3AF'}
        />
      </View>
      <Text
        style={[styles.achievementTitle, !achievement.earned && { color: '#9CA3AF' }]}
        numberOfLines={1}
      >
        {achievement.title}
      </Text>
      {!achievement.earned && achievement.progress > 0 && (
        <View style={styles.progressBarContainer}>
          <View style={[styles.progressBar, { width: `${Math.min(achievement.progress * 100, 100)}%`, backgroundColor: achievement.color }]} />
        </View>
      )}
      {achievement.earned && (
        <Feather name="check-circle" size={12} color={achievement.color} style={{ marginTop: 2 }} />
      )}
    </View>
  );
}

// ---------- Analytics Mini Card ----------

function AnalyticsStat({ label, value, icon, color }: { label: string; value: string; icon: string; color: string }) {
  return (
    <View style={styles.analyticsStat}>
      <Feather name={icon as any} size={16} color={color} />
      <Text style={styles.analyticsValue}>{value}</Text>
      <Text style={styles.analyticsLabel}>{label}</Text>
    </View>
  );
}

// ---------- Yield Card ----------

interface YieldItem {
  id: string;
  protocol: string;
  chain: string;
  symbol: string;
  apy: number;
  tvl: number;
  risk: number;
}

function YieldCard({ item, onPress }: { item: YieldItem; onPress: () => void }) {
  const riskInfo = riskLabel(item.risk);

  return (
    <Pressable
      style={({ pressed }) => [styles.yieldCard, pressed && { opacity: 0.85 }]}
      onPress={onPress}
    >
      <View style={styles.yieldCardHeader}>
        <View style={styles.yieldCardLeft}>
          <Text style={styles.yieldSymbol}>{item.symbol}</Text>
          <Text style={styles.yieldProtocol}>{item.protocol}</Text>
        </View>
        <View style={styles.yieldCardRight}>
          <Text style={styles.yieldApy}>{item.apy.toFixed(1)}%</Text>
          <Text style={styles.yieldApyLabel}>APY</Text>
        </View>
      </View>
      <View style={styles.yieldCardFooter}>
        <View style={styles.yieldMeta}>
          <Feather name="lock" size={12} color="#6B7280" />
          <Text style={styles.yieldMetaText}>{formatTVL(item.tvl)} TVL</Text>
        </View>
        <View style={[styles.riskBadge, { backgroundColor: riskInfo.color + '20' }]}>
          <Text style={[styles.riskBadgeText, { color: riskInfo.color }]}>{riskInfo.text}</Text>
        </View>
        <View style={styles.yieldMeta}>
          <Feather name={chainIcon(item.chain) as any} size={12} color="#6B7280" />
          <Text style={styles.yieldMetaText}>{item.chain}</Text>
        </View>
      </View>
    </Pressable>
  );
}

// ---------- Main Screen ----------

export default function DeFiFortressScreen() {
  const navigation = useNavigation<any>();
  const [selectedChain, setSelectedChain] = useState<string>('all');
  const [refreshing, setRefreshing] = useState(false);
  const [showAllAchievements, setShowAllAchievements] = useState(false);

  // Yield data
  const { data: yieldsData, loading: yieldsLoading, refetch: refetchYields } = useQuery(
    TOP_YIELDS_QUERY,
    {
      variables: { chain: selectedChain === 'all' ? null : selectedChain, limit: 10 },
      fetchPolicy: 'cache-and-network',
    }
  );

  // AI Optimizer
  const { data: optimizerData } = useQuery(AI_YIELD_OPTIMIZER_QUERY, {
    variables: { userRiskTolerance: 0.5, chain: selectedChain === 'all' ? 'ethereum' : selectedChain, limit: 5 },
    fetchPolicy: 'cache-and-network',
  });

  // Ghost Whisper
  const { data: whisperData, refetch: refetchWhisper } = useQuery(GHOST_WHISPER_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  // Achievements
  const { data: achievementsData, refetch: refetchAchievements } = useQuery(ACHIEVEMENTS_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  // Portfolio Analytics
  const { data: analyticsData, refetch: refetchAnalytics } = useQuery(PORTFOLIO_ANALYTICS_QUERY, {
    fetchPolicy: 'cache-and-network',
  });

  const yields: YieldItem[] = yieldsData?.topYields || [];
  const optimizer = optimizerData?.aiYieldOptimizer;
  const expectedApy = optimizer?.expectedApy || 0;
  const ghostWhisper: GhostWhisperData | null = whisperData?.ghostWhisper || null;
  const achievements: Achievement[] = achievementsData?.defiAchievements || [];
  const analytics = analyticsData?.portfolioAnalytics;

  const earnedCount = achievements.filter((a) => a.earned).length;
  const displayedAchievements = showAllAchievements ? achievements : achievements.slice(0, 5);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      await Promise.all([
        refetchYields(),
        refetchWhisper(),
        refetchAchievements(),
        refetchAnalytics(),
      ]);
    } catch (e) {
      logger.warn('DeFi refresh error:', e);
    }
    setRefreshing(false);
  }, [refetchYields, refetchWhisper, refetchAchievements, refetchAnalytics]);

  const chains = ['all', 'ethereum', 'polygon', 'arbitrum', 'base'];

  const handleGhostWhisperPress = useCallback(() => {
    if (!ghostWhisper) return;
    switch (ghostWhisper.action) {
      case 'deposit':
        navigation.navigate('Crypto');
        break;
      case 'rotate':
        navigation.navigate('VaultPortfolio');
        break;
      case 'harvest':
        navigation.navigate('DeFiPositions');
        break;
      case 'diversify':
        navigation.navigate('VaultPortfolio');
        break;
      default:
        navigation.navigate('DeFiPositions');
    }
  }, [ghostWhisper, navigation]);

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#10B981" />}
    >
      {/* ---- Hero Section ---- */}
      <LinearGradient
        colors={['#064E3B', '#065F46', '#047857']}
        style={styles.hero}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        <View style={styles.heroContent}>
          <View style={styles.heroTitleRow}>
            <Feather name="shield" size={28} color="#34D399" />
            <Text style={styles.heroTitle}>DeFi Fortress</Text>
          </View>
          <Text style={styles.heroSubtitle}>
            Earn yield on your crypto. AI-guided. Community-backed.
          </Text>

          {expectedApy > 0 ? (
            <AnimatedAPY value={expectedApy} />
          ) : (
            <View style={styles.apyContainer}>
              <Text style={styles.apyValue}>--</Text>
              <Text style={styles.apyLabel}>Connect to see your yield</Text>
            </View>
          )}

          {optimizer?.explanation ? (
            <Text style={styles.heroExplanation}>{optimizer.explanation}</Text>
          ) : null}
        </View>
      </LinearGradient>

      {/* ---- Ghost Whisper AI ---- */}
      {ghostWhisper && (
        <View style={{ marginTop: -16, marginHorizontal: 16, marginBottom: 12 }}>
          <GhostWhisperCard whisper={ghostWhisper} onPress={handleGhostWhisperPress} />
        </View>
      )}

      {/* ---- Quick Actions ---- */}
      <View style={styles.quickActions}>
        <Pressable
          style={({ pressed }) => [styles.actionBtn, pressed && { opacity: 0.8 }]}
          onPress={() => navigation.navigate('Crypto')}
        >
          <Feather name="plus-circle" size={20} color="#10B981" />
          <Text style={styles.actionText}>Deposit</Text>
        </Pressable>
        <Pressable
          style={({ pressed }) => [styles.actionBtn, pressed && { opacity: 0.8 }]}
          onPress={() => navigation.navigate('DeFiPositions')}
        >
          <Feather name="layers" size={20} color="#3B82F6" />
          <Text style={styles.actionText}>Positions</Text>
        </Pressable>
        <Pressable
          style={({ pressed }) => [styles.actionBtn, pressed && { opacity: 0.8 }]}
          onPress={() => navigation.navigate('VaultPortfolio')}
        >
          <Feather name="box" size={20} color="#8B5CF6" />
          <Text style={styles.actionText}>Vaults</Text>
        </Pressable>
        <Pressable
          style={({ pressed }) => [styles.actionBtn, pressed && { opacity: 0.8 }]}
          onPress={() => navigation.navigate('Learn')}
        >
          <Feather name="book-open" size={20} color="#F59E0B" />
          <Text style={styles.actionText}>Learn</Text>
        </Pressable>
      </View>

      {/* ---- Portfolio Analytics Dashboard ---- */}
      {analytics && analytics.totalPositions > 0 && (
        <View style={styles.analyticsCard}>
          <View style={styles.analyticsHeader}>
            <Feather name="bar-chart-2" size={18} color="#111827" />
            <Text style={styles.analyticsCardTitle}>Portfolio Analytics</Text>
          </View>
          <View style={styles.analyticsGrid}>
            <AnalyticsStat
              label="Deposited"
              value={formatUSD(analytics.totalDepositedUsd)}
              icon="download"
              color="#3B82F6"
            />
            <AnalyticsStat
              label="Earned"
              value={formatUSD(analytics.totalRewardsUsd)}
              icon="trending-up"
              color="#10B981"
            />
            <AnalyticsStat
              label="Sharpe"
              value={analytics.sharpeRatio?.toFixed(2) || '--'}
              icon="activity"
              color="#8B5CF6"
            />
            <AnalyticsStat
              label="Diversity"
              value={`${Math.round(analytics.portfolioDiversityScore || 0)}/100`}
              icon="pie-chart"
              color="#F59E0B"
            />
          </View>
          <View style={styles.analyticsSubRow}>
            <Text style={styles.analyticsSubText}>
              {analytics.totalPositions} position{analytics.totalPositions !== 1 ? 's' : ''} across{' '}
              {analytics.activeChains?.length || 0} chain{(analytics.activeChains?.length || 0) !== 1 ? 's' : ''}
            </Text>
            {analytics.realizedApy > 0 && (
              <Text style={[styles.analyticsSubText, { color: '#10B981', fontWeight: '700' }]}>
                {analytics.realizedApy.toFixed(1)}% APY
              </Text>
            )}
          </View>
        </View>
      )}

      {/* ---- Achievements ---- */}
      {achievements.length > 0 && (
        <View style={styles.achievementsSection}>
          <View style={styles.achievementsHeader}>
            <View>
              <Text style={styles.sectionTitle}>Achievements</Text>
              <Text style={styles.sectionSubtitle}>
                {earnedCount}/{achievements.length} earned
              </Text>
            </View>
            {achievements.length > 5 && (
              <Pressable onPress={() => setShowAllAchievements(!showAllAchievements)}>
                <Text style={styles.seeAllText}>
                  {showAllAchievements ? 'Show Less' : 'See All'}
                </Text>
              </Pressable>
            )}
          </View>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.achievementsScroll}
          >
            {displayedAchievements.map((achievement) => (
              <AchievementBadge key={achievement.id} achievement={achievement} />
            ))}
          </ScrollView>
        </View>
      )}

      {/* ---- DeFi Fortress 101 Card ---- */}
      <Pressable
        style={({ pressed }) => [styles.educationCard, pressed && { opacity: 0.9 }]}
        onPress={() =>
          navigation.navigate('Learn', {
            screen: 'LearnMain',
            params: { initialPathId: 'defiBasics' },
          })
        }
      >
        <View style={styles.educationLeft}>
          <Feather name="shield" size={24} color="#10B981" />
        </View>
        <View style={styles.educationRight}>
          <Text style={styles.educationTitle}>DeFi Fortress 101</Text>
          <Text style={styles.educationDesc}>
            New to DeFi? Learn yield farming, wallets, and how to protect your position.
          </Text>
        </View>
        <Feather name="chevron-right" size={20} color="#9CA3AF" />
      </Pressable>

      {/* ---- DeFi Mastery Card (Advanced) ---- */}
      <Pressable
        style={({ pressed }) => [
          styles.educationCard,
          { borderColor: '#C4B5FD', backgroundColor: '#EDE9FE' },
          pressed && { opacity: 0.9 },
        ]}
        onPress={() =>
          navigation.navigate('Learn', {
            screen: 'LearnMain',
            params: { initialPathId: 'defiAdvanced' },
          })
        }
      >
        <View style={[styles.educationLeft, { backgroundColor: '#DDD6FE' }]}>
          <Feather name="zap" size={24} color="#7C3AED" />
        </View>
        <View style={styles.educationRight}>
          <Text style={[styles.educationTitle, { color: '#5B21B6' }]}>DeFi Mastery</Text>
          <Text style={[styles.educationDesc, { color: '#6D28D9' }]}>
            Advanced: IL deep dives, leverage strategies, vaults, and DAO governance.
          </Text>
        </View>
        <Feather name="chevron-right" size={20} color="#9CA3AF" />
      </Pressable>

      {/* ---- Auto-Pilot Command Card ---- */}
      <Pressable
        style={({ pressed }) => [
          styles.educationCard,
          { borderColor: '#93C5FD', backgroundColor: '#EFF6FF' },
          pressed && { opacity: 0.9 },
        ]}
        onPress={() => navigation.navigate('DeFiAutopilot')}
      >
        <View style={[styles.educationLeft, { backgroundColor: '#DBEAFE' }]}>
          <Feather name="cpu" size={24} color="#2563EB" />
        </View>
        <View style={styles.educationRight}>
          <Text style={[styles.educationTitle, { color: '#1D4ED8' }]}>Auto-Pilot Command</Text>
          <Text style={[styles.educationDesc, { color: '#1E40AF' }]}>
            Set your intent and let the fortress repair risk automatically.
          </Text>
        </View>
        <Feather name="chevron-right" size={20} color="#9CA3AF" />
      </Pressable>

      {/* ---- IL Calculator Card ---- */}
      <Pressable
        style={({ pressed }) => [
          styles.educationCard,
          { borderColor: '#DDD6FE', backgroundColor: '#F5F3FF' },
          pressed && { opacity: 0.9 },
        ]}
        onPress={() => navigation.navigate('ILCalculator')}
      >
        <View style={[styles.educationLeft, { backgroundColor: '#EDE9FE' }]}>
          <Feather name="percent" size={24} color="#7C3AED" />
        </View>
        <View style={styles.educationRight}>
          <Text style={[styles.educationTitle, { color: '#5B21B6' }]}>IL Calculator</Text>
          <Text style={[styles.educationDesc, { color: '#6D28D9' }]}>
            Calculate impermanent loss before entering a liquidity pool.
          </Text>
        </View>
        <Feather name="chevron-right" size={20} color="#9CA3AF" />
      </Pressable>

      {/* ---- Chain Selector ---- */}
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Top Yields</Text>
        <Text style={styles.sectionSubtitle}>Live data from DeFi protocols</Text>
      </View>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chainSelector}>
        {chains.map((chain) => (
          <Pressable
            key={chain}
            style={[
              styles.chainPill,
              selectedChain === chain && styles.chainPillActive,
            ]}
            onPress={() => setSelectedChain(chain)}
          >
            <Text
              style={[
                styles.chainPillText,
                selectedChain === chain && styles.chainPillTextActive,
              ]}
            >
              {chain === 'all' ? 'All Chains' : chain.charAt(0).toUpperCase() + chain.slice(1)}
            </Text>
          </Pressable>
        ))}
      </ScrollView>

      {/* ---- Yield Cards ---- */}
      {yieldsLoading && yields.length === 0 ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#10B981" />
          <Text style={styles.loadingText}>Loading live yields...</Text>
        </View>
      ) : yields.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Feather name="inbox" size={40} color="#9CA3AF" />
          <Text style={styles.emptyText}>No yields found for this chain</Text>
          <Text style={styles.emptySubtext}>Try selecting a different chain above</Text>
        </View>
      ) : (
        yields.map((item) => (
          <YieldCard
            key={item.id}
            item={item}
            onPress={() => {
              navigation.navigate('PoolAnalytics', {
                poolId: item.id,
                poolSymbol: `${item.protocol} ${item.symbol}`,
              });
            }}
          />
        ))
      )}

      {/* ---- Bottom Spacer ---- */}
      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

// ---------- Styles ----------

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  content: { paddingBottom: 32 },

  // Hero
  hero: { paddingTop: 60, paddingBottom: 32, paddingHorizontal: 20, borderBottomLeftRadius: 24, borderBottomRightRadius: 24 },
  heroContent: { alignItems: 'center' },
  heroTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 8 },
  heroTitle: { fontSize: 28, fontWeight: '800', color: '#ECFDF5', letterSpacing: -0.5 },
  heroSubtitle: { fontSize: 15, color: '#A7F3D0', textAlign: 'center', marginBottom: 20 },
  heroExplanation: { fontSize: 12, color: '#A7F3D0', textAlign: 'center', marginTop: 12, paddingHorizontal: 20, opacity: 0.8 },

  // APY Counter
  apyContainer: { alignItems: 'center', marginVertical: 8 },
  apyValue: { fontSize: 48, fontWeight: '900', color: '#34D399', letterSpacing: -1 },
  apyLabel: { fontSize: 14, color: '#A7F3D0', marginTop: 2 },

  // Ghost Whisper
  ghostWhisperCard: { borderRadius: 16, overflow: 'hidden', elevation: 4, shadowColor: '#312E81', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.2, shadowRadius: 8 },
  ghostWhisperGradient: { padding: 16, borderRadius: 16 },
  ghostWhisperHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  ghostWhisperTitleRow: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  ghostWhisperTitle: { fontSize: 14, fontWeight: '700', color: '#C7D2FE', letterSpacing: 0.5 },
  ghostWhisperMessage: { fontSize: 16, fontWeight: '600', color: '#E0E7FF', lineHeight: 22, marginBottom: 10 },
  ghostWhisperAction: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  ghostWhisperActionText: { fontSize: 13, color: '#A5B4FC', flex: 1 },
  confidenceBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8 },
  confidenceText: { fontSize: 11, fontWeight: '700' },

  // Quick Actions
  quickActions: { flexDirection: 'row', justifyContent: 'space-around', paddingVertical: 16, paddingHorizontal: 12 },
  actionBtn: { alignItems: 'center', gap: 6, padding: 12, borderRadius: 12, backgroundColor: '#FFFFFF', minWidth: 80, elevation: 1, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 2 },
  actionText: { fontSize: 12, fontWeight: '600', color: '#374151' },

  // Portfolio Analytics
  analyticsCard: { marginHorizontal: 16, marginBottom: 16, padding: 16, backgroundColor: '#FFFFFF', borderRadius: 16, elevation: 1, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 3 },
  analyticsHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  analyticsCardTitle: { fontSize: 16, fontWeight: '700', color: '#111827' },
  analyticsGrid: { flexDirection: 'row', justifyContent: 'space-between' },
  analyticsStat: { alignItems: 'center', flex: 1, gap: 4 },
  analyticsValue: { fontSize: 16, fontWeight: '800', color: '#111827' },
  analyticsLabel: { fontSize: 11, color: '#6B7280', fontWeight: '500' },
  analyticsSubRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 12, paddingTop: 12, borderTopWidth: 1, borderTopColor: '#F3F4F6' },
  analyticsSubText: { fontSize: 12, color: '#6B7280' },

  // Achievements
  achievementsSection: { marginBottom: 16 },
  achievementsHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 20, marginBottom: 12 },
  achievementsScroll: { paddingHorizontal: 16, gap: 12 },
  achievementBadge: { width: 90, alignItems: 'center', padding: 12, backgroundColor: '#FFFFFF', borderRadius: 12, elevation: 1, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 2 },
  achievementLocked: { opacity: 0.6 },
  achievementIconContainer: { width: 44, height: 44, borderRadius: 22, alignItems: 'center', justifyContent: 'center', marginBottom: 6 },
  achievementTitle: { fontSize: 11, fontWeight: '600', color: '#374151', textAlign: 'center' },
  progressBarContainer: { width: '100%', height: 3, backgroundColor: '#F3F4F6', borderRadius: 2, marginTop: 4, overflow: 'hidden' },
  progressBar: { height: '100%', borderRadius: 2 },
  seeAllText: { fontSize: 13, fontWeight: '600', color: '#3B82F6' },

  // Education Card
  educationCard: { flexDirection: 'row', alignItems: 'center', marginHorizontal: 16, marginBottom: 12, padding: 16, backgroundColor: '#ECFDF5', borderRadius: 16, gap: 12, borderWidth: 1, borderColor: '#A7F3D0' },
  educationLeft: { width: 44, height: 44, borderRadius: 12, backgroundColor: '#D1FAE5', alignItems: 'center', justifyContent: 'center' },
  educationRight: { flex: 1 },
  educationTitle: { fontSize: 16, fontWeight: '700', color: '#064E3B', marginBottom: 4 },
  educationDesc: { fontSize: 13, color: '#065F46', lineHeight: 18 },

  // Section
  sectionHeader: { paddingHorizontal: 20, marginBottom: 8 },
  sectionTitle: { fontSize: 20, fontWeight: '700', color: '#111827' },
  sectionSubtitle: { fontSize: 13, color: '#6B7280', marginTop: 2 },

  // Chain Selector
  chainSelector: { paddingLeft: 16, marginBottom: 16 },
  chainPill: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20, backgroundColor: '#F3F4F6', marginRight: 8 },
  chainPillActive: { backgroundColor: '#064E3B' },
  chainPillText: { fontSize: 13, fontWeight: '600', color: '#6B7280' },
  chainPillTextActive: { color: '#FFFFFF' },

  // Yield Card
  yieldCard: { marginHorizontal: 16, marginBottom: 12, padding: 16, backgroundColor: '#FFFFFF', borderRadius: 16, elevation: 1, shadowColor: '#000', shadowOffset: { width: 0, height: 1 }, shadowOpacity: 0.05, shadowRadius: 3 },
  yieldCardHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  yieldCardLeft: {},
  yieldCardRight: { alignItems: 'flex-end' },
  yieldSymbol: { fontSize: 18, fontWeight: '700', color: '#111827' },
  yieldProtocol: { fontSize: 13, color: '#6B7280', marginTop: 2 },
  yieldApy: { fontSize: 24, fontWeight: '800', color: '#10B981' },
  yieldApyLabel: { fontSize: 11, color: '#6B7280', fontWeight: '600' },
  yieldCardFooter: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  yieldMeta: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  yieldMetaText: { fontSize: 12, color: '#6B7280' },
  riskBadge: { paddingHorizontal: 8, paddingVertical: 3, borderRadius: 8 },
  riskBadgeText: { fontSize: 11, fontWeight: '600' },

  // States
  loadingContainer: { alignItems: 'center', paddingVertical: 40, gap: 12 },
  loadingText: { fontSize: 14, color: '#6B7280' },
  emptyContainer: { alignItems: 'center', paddingVertical: 40, gap: 8 },
  emptyText: { fontSize: 16, fontWeight: '600', color: '#6B7280' },
  emptySubtext: { fontSize: 13, color: '#9CA3AF' },
});
