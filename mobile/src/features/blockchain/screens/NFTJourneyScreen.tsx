/**
 * NFTJourneyScreen — Personalized Web3 learning path derived from wallet holdings.
 *
 * Heuristic engine:
 *   - Ethereum bluechips (BAYC, Punks, MAYC) → "NFT History & Ethereum 101"
 *   - Polygon/cheap mints → "Layer-2s & Low Fees"
 *   - Utility collections (CloneX, Doodles) → "What Your NFT Unlocks"
 *   - Multi-chain → "Cross-Chain & Bridges"
 *   - No NFTs (demo mode) → all paths shown as starter suggestions
 *
 * Module cards reuse the same style as LearningPathsScreen for visual consistency.
 * Tapping a module navigates to TutorModuleScreen with the topic pre-filled.
 */
import React, { useMemo, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  Pressable,
  StyleSheet,
  Dimensions,
} from 'react-native';
import Feather from '@expo/vector-icons/Feather';
import { useNavigation, useRoute } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';

const { width } = Dimensions.get('window');

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface OwnedNFT {
  contractAddress: string;
  collectionName: string;
  chain: string;
}

interface JourneyModule {
  id: string;
  title: string;
  description: string;
  duration: string;
  icon: string;
  color: string;
  tutorTopic: string; // passed to TutorModuleScreen
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  tags: string[];
}

// ---------------------------------------------------------------------------
// All available Web3 learning modules
// ---------------------------------------------------------------------------

const WEB3_MODULES: JourneyModule[] = [
  {
    id: 'nft-history',
    title: 'NFT History & Ethereum 101',
    description: 'From CryptoPunks (2017) to the PFP era — how NFTs went from a niche experiment to a cultural phenomenon, and what Ethereum makes possible.',
    duration: '8 min',
    icon: 'clock',
    color: '#627EEA',
    tutorTopic: 'NFT history on Ethereum from CryptoPunks to BAYC',
    difficulty: 'Beginner',
    tags: ['ethereum', 'history', 'pfp'],
  },
  {
    id: 'true-ownership',
    title: 'True Ownership on the Blockchain',
    description: 'What it actually means to "own" an NFT — private keys, ERC-721, and why no company can take it away.',
    duration: '5 min',
    icon: 'key',
    color: '#7C3AED',
    tutorTopic: 'True ownership of NFTs: private keys, ERC-721, and blockchain immutability',
    difficulty: 'Beginner',
    tags: ['ownership', 'erc-721', 'ethereum'],
  },
  {
    id: 'rarity-explained',
    title: 'Rarity & Trait Scoring',
    description: 'How rarity is calculated across a collection, why it affects price, and how to read trait percentages.',
    duration: '6 min',
    icon: 'star',
    color: '#F59E0B',
    tutorTopic: 'NFT rarity: trait frequency, rarity scores, and how they affect value',
    difficulty: 'Beginner',
    tags: ['rarity', 'traits', 'valuation'],
  },
  {
    id: 'l2-fees',
    title: 'Layer-2s & Low Gas Fees',
    description: 'Why Polygon, Arbitrum, and Base exist — and how rollups make NFTs accessible without $50 gas fees.',
    duration: '7 min',
    icon: 'layers',
    color: '#8247E5',
    tutorTopic: 'Layer-2 networks: Polygon, Arbitrum, Base, and how rollups reduce gas fees',
    difficulty: 'Beginner',
    tags: ['layer2', 'polygon', 'gas', 'fees'],
  },
  {
    id: 'utility-unlocks',
    title: 'What Your NFT Actually Unlocks',
    description: 'Token gating, Discord access, physical redemptions, DAO voting — the real-world utility hiding behind your NFT.',
    duration: '6 min',
    icon: 'unlock',
    color: '#10B981',
    tutorTopic: 'NFT utility: token gating, physical redemptions, DAO governance, and Discord access',
    difficulty: 'Beginner',
    tags: ['utility', 'token-gating', 'dao', 'perks'],
  },
  {
    id: 'royalties-governance',
    title: 'Royalties, DAOs & Community Governance',
    description: 'How secondary sale royalties work, what a community treasury is, and how holders vote on project decisions.',
    duration: '7 min',
    icon: 'users',
    color: '#EC4899',
    tutorTopic: 'NFT royalties, community treasuries, and DAO governance for holders',
    difficulty: 'Intermediate',
    tags: ['royalties', 'dao', 'governance', 'community'],
  },
  {
    id: 'risk-safety',
    title: 'NFT Safety & Scam Prevention',
    description: 'The most common NFT scams — fake mints, phishing Discord links, drainer contracts — and exactly how to avoid them.',
    duration: '8 min',
    icon: 'shield',
    color: '#EF4444',
    tutorTopic: 'NFT scam prevention: fake mints, phishing, drainer contracts, and wallet safety',
    difficulty: 'Beginner',
    tags: ['safety', 'scams', 'security'],
  },
  {
    id: 'cross-chain',
    title: 'Cross-Chain NFTs & Bridges',
    description: 'Why NFTs live on specific chains, what bridging is, and the risks of moving assets between networks.',
    duration: '6 min',
    icon: 'shuffle',
    color: '#06B6D4',
    tutorTopic: 'Cross-chain NFTs: bridges, chain interoperability, and bridging risks',
    difficulty: 'Intermediate',
    tags: ['cross-chain', 'bridge', 'multi-chain'],
  },
  {
    id: 'brands-web3',
    title: 'Why Brands Are Entering Web3',
    description: 'Nike x RTFKT, Starbucks Odyssey, Adidas Originals — how traditional companies are using NFTs to build direct customer relationships.',
    duration: '5 min',
    icon: 'briefcase',
    color: '#F97316',
    tutorTopic: 'Why major brands like Nike and Starbucks are entering Web3 with NFTs',
    difficulty: 'Beginner',
    tags: ['brands', 'nike', 'rtfkt', 'enterprise'],
  },
  {
    id: 'nft-valuation',
    title: 'How to Value an NFT',
    description: 'Floor price, rarity rank, last sale, collection volume, and why "price" is different from "value" in NFTs.',
    duration: '9 min',
    icon: 'trending-up',
    color: '#0EA5E9',
    tutorTopic: 'NFT valuation: floor price, rarity, volume, liquidity, and intrinsic value',
    difficulty: 'Intermediate',
    tags: ['valuation', 'floor-price', 'trading'],
  },
];

// ---------------------------------------------------------------------------
// Heuristic engine — map wallet → recommended modules
// ---------------------------------------------------------------------------

const ETHEREUM_BLUECHIP_CONTRACTS = new Set([
  '0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d', // BAYC
  '0xb47e3cd837ddf8e4c57f05d70ab865de6e193bbb', // CryptoPunks
  '0x60e4d786628fea6478f785a6d7e704777c86a7c6', // MAYC
]);
const UTILITY_CONTRACTS = new Set([
  '0x49cf6f5d44e70224e2e23fdcdd2c053f30ada28b', // CloneX
  '0x8a90cab2b38dba80c64b7734e58ee1db38b8992e', // Doodles
  '0x1a92f7381b9f03921564a437210bb9396471050c', // Cool Cats
]);

function buildJourney(nfts: OwnedNFT[]): { recommended: JourneyModule[]; all: JourneyModule[] } {
  if (!nfts || nfts.length === 0) {
    // No wallet — show beginner path
    const beginner = WEB3_MODULES.filter(m => m.difficulty === 'Beginner');
    return { recommended: beginner.slice(0, 4), all: WEB3_MODULES };
  }

  const contracts = nfts.map(n => n.contractAddress.toLowerCase());
  const chains = new Set(nfts.map(n => n.chain));
  const hasEthBluechip = contracts.some(c => ETHEREUM_BLUECHIP_CONTRACTS.has(c));
  const hasUtility = contracts.some(c => UTILITY_CONTRACTS.has(c));
  const hasPolygon = chains.has('polygon');
  const isMultiChain = chains.size > 1;

  const recommended: JourneyModule[] = [];
  const addIfNotPresent = (id: string) => {
    const m = WEB3_MODULES.find(m => m.id === id);
    if (m && !recommended.find(r => r.id === id)) recommended.push(m);
  };

  // Everyone starts with true ownership + safety
  addIfNotPresent('true-ownership');
  addIfNotPresent('risk-safety');

  if (hasEthBluechip) {
    addIfNotPresent('nft-history');
    addIfNotPresent('rarity-explained');
    addIfNotPresent('royalties-governance');
  }
  if (hasUtility) {
    addIfNotPresent('utility-unlocks');
    addIfNotPresent('brands-web3');
  }
  if (hasPolygon) {
    addIfNotPresent('l2-fees');
  }
  if (isMultiChain) {
    addIfNotPresent('cross-chain');
  }
  // Fill up to 5 with remaining beginner modules
  for (const m of WEB3_MODULES) {
    if (recommended.length >= 5) break;
    if (!recommended.find(r => r.id === m.id)) recommended.push(m);
  }

  return { recommended: recommended.slice(0, 5), all: WEB3_MODULES };
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function ModuleCard({
  module,
  index,
  onPress,
}: {
  module: JourneyModule;
  index: number;
  onPress: () => void;
}) {
  const difficultyColor = {
    Beginner: '#10B981',
    Intermediate: '#F59E0B',
    Advanced: '#EF4444',
  }[module.difficulty];

  return (
    <Pressable
      style={({ pressed }) => [styles.moduleCard, pressed && { opacity: 0.9 }]}
      onPress={onPress}
    >
      <View style={styles.moduleLeft}>
        <View style={[styles.moduleIconBg, { backgroundColor: module.color + '20' }]}>
          <Feather name={module.icon as any} size={20} color={module.color} />
        </View>
        <View style={styles.moduleIndexBadge}>
          <Text style={styles.moduleIndexText}>{index + 1}</Text>
        </View>
      </View>
      <View style={styles.moduleContent}>
        <Text style={styles.moduleTitle}>{module.title}</Text>
        <Text style={styles.moduleDesc} numberOfLines={2}>{module.description}</Text>
        <View style={styles.moduleMeta}>
          <View style={[styles.difficultyBadge, { backgroundColor: difficultyColor + '20' }]}>
            <Text style={[styles.difficultyText, { color: difficultyColor }]}>{module.difficulty}</Text>
          </View>
          <View style={styles.durationRow}>
            <Feather name="clock" size={11} color="#9CA3AF" />
            <Text style={styles.durationText}>{module.duration}</Text>
          </View>
        </View>
      </View>
      <Feather name="chevron-right" size={18} color="#D1D5DB" />
    </Pressable>
  );
}

// ---------------------------------------------------------------------------
// Main Screen
// ---------------------------------------------------------------------------

export default function NFTJourneyScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const ownedNfts: OwnedNFT[] = route.params?.nfts || [];

  const [showAll, setShowAll] = useState(false);

  const { recommended, all } = useMemo(() => buildJourney(ownedNfts), [ownedNfts]);
  const displayModules = showAll ? all : recommended;

  const isDemo = ownedNfts.length === 0;
  const chains = [...new Set(ownedNfts.map(n => n.chain))];

  const navigateToModule = (module: JourneyModule) => {
    navigation.navigate('tutor-module', { topic: module.tutorTopic });
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <LinearGradient colors={['#1E1B4B', '#4C1D95']} style={styles.header}>
        <View style={styles.headerRow}>
          <Pressable
            style={({ pressed }) => [styles.backBtn, pressed && { opacity: 0.7 }]}
            onPress={() => navigation.goBack()}
          >
            <Feather name="arrow-left" size={22} color="#FFFFFF" />
          </Pressable>
          <Text style={styles.headerTitle}>Your NFT Journey</Text>
          <View style={{ width: 30 }} />
        </View>

        {/* Stats row */}
        <View style={styles.statsRow}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{isDemo ? '6' : ownedNfts.length}</Text>
            <Text style={styles.statLabel}>{isDemo ? 'Demo NFTs' : 'NFTs Owned'}</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{isDemo ? '5' : chains.length}</Text>
            <Text style={styles.statLabel}>{isDemo ? 'Chains' : `Chain${chains.length !== 1 ? 's' : ''}`}</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{recommended.length}</Text>
            <Text style={styles.statLabel}>Lessons for You</Text>
          </View>
        </View>
      </LinearGradient>

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Intro */}
        {isDemo ? (
          <View style={styles.demoBanner}>
            <View style={styles.demoBannerTop}>
              <Feather name="info" size={15} color="#6366F1" />
              <Text style={styles.demoBannerText}>
                Connect your wallet to get a journey built from your actual collection.
              </Text>
            </View>
            <Pressable
              style={({ pressed }) => [styles.browseNFTsBtn, pressed && { opacity: 0.75 }]}
              onPress={() => navigation.goBack()}
            >
              <Feather name="grid" size={13} color="#6366F1" />
              <Text style={styles.browseNFTsBtnText}>Browse NFTs ↗</Text>
            </Pressable>
          </View>
        ) : (
          <View style={styles.personalizedBanner}>
            <Feather name="zap" size={15} color="#7C3AED" />
            <Text style={styles.personalizedBannerText}>
              These lessons were chosen based on what you actually own.
            </Text>
          </View>
        )}

        {/* Recommended modules */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            {showAll ? 'All Web3 Lessons' : 'Recommended for You'}
          </Text>
          {displayModules.map((module, i) => (
            <ModuleCard
              key={module.id}
              module={module}
              index={i}
              onPress={() => navigateToModule(module)}
            />
          ))}
        </View>

        {/* Toggle all */}
        <Pressable
          style={({ pressed }) => [styles.toggleBtn, pressed && { opacity: 0.8 }]}
          onPress={() => setShowAll(v => !v)}
        >
          <Text style={styles.toggleBtnText}>
            {showAll ? 'Show recommended only' : `Browse all ${all.length} lessons`}
          </Text>
          <Feather name={showAll ? 'chevron-up' : 'chevron-down'} size={16} color="#7C3AED" />
        </Pressable>

        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },

  // Header
  header: {
    paddingTop: 56,
    paddingBottom: 20,
    paddingHorizontal: 16,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  backBtn: { padding: 4 },
  headerTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  statsRow: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255,255,255,0.12)',
    borderRadius: 14,
    paddingVertical: 14,
    paddingHorizontal: 16,
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 22,
    fontWeight: '900',
    color: '#FFFFFF',
  },
  statLabel: {
    fontSize: 11,
    color: '#C4B5FD',
    marginTop: 2,
    fontWeight: '500',
  },
  statDivider: {
    width: 1,
    backgroundColor: 'rgba(255,255,255,0.2)',
    marginVertical: 4,
  },

  // Content
  scrollView: { flex: 1 },
  scrollContent: { padding: 16 },

  demoBanner: {
    flexDirection: 'column',
    backgroundColor: '#EEF2FF',
    borderRadius: 10,
    padding: 12,
    marginBottom: 20,
    gap: 10,
  },
  demoBannerTop: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
  },
  demoBannerText: {
    flex: 1,
    fontSize: 13,
    color: '#4338CA',
    lineHeight: 18,
  },
  browseNFTsBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    alignSelf: 'flex-start',
    backgroundColor: '#E0E7FF',
    borderRadius: 8,
    paddingVertical: 6,
    paddingHorizontal: 10,
  },
  browseNFTsBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#4338CA',
  },
  personalizedBanner: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    backgroundColor: '#EDE9FE',
    borderRadius: 10,
    padding: 12,
    marginBottom: 20,
  },
  personalizedBannerText: {
    flex: 1,
    fontSize: 13,
    color: '#5B21B6',
    lineHeight: 18,
  },

  section: { marginBottom: 12 },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#9CA3AF',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 12,
  },

  // Module card
  moduleCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
    gap: 12,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 3,
  },
  moduleLeft: {
    position: 'relative',
  },
  moduleIconBg: {
    width: 44,
    height: 44,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  moduleIndexBadge: {
    position: 'absolute',
    bottom: -4,
    right: -4,
    width: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: '#7C3AED',
    alignItems: 'center',
    justifyContent: 'center',
  },
  moduleIndexText: {
    fontSize: 10,
    fontWeight: '800',
    color: '#FFFFFF',
  },
  moduleContent: { flex: 1 },
  moduleTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 3,
  },
  moduleDesc: {
    fontSize: 12,
    color: '#6B7280',
    lineHeight: 17,
    marginBottom: 8,
  },
  moduleMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  difficultyBadge: {
    paddingHorizontal: 7,
    paddingVertical: 3,
    borderRadius: 6,
  },
  difficultyText: {
    fontSize: 10,
    fontWeight: '700',
  },
  durationRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 3,
  },
  durationText: {
    fontSize: 11,
    color: '#9CA3AF',
  },

  toggleBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#DDD6FE',
    backgroundColor: '#F5F3FF',
  },
  toggleBtnText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#7C3AED',
  },
});
