/**
 * NFTDetailScreen — The Web3 Tutor in your wallet.
 *
 * Tabs:
 *   Overview  — image, name, floor/last sale, traits
 *   Learn     — story, rarity explainer, 1-sentence lesson, tap-to-expand glossary
 *   Utility   — perks list + official links
 *   Risk      — risk level badge + plain-English explanation
 *
 * Navigated to from NFTGallery via onNFTSelect callback.
 * "Ask about this NFT" deep-links into the existing TutorAskExplainScreen
 * with the NFT pre-loaded as context.
 */
import React, { useState } from 'react';
import {
  View,
  Text,
  Image,
  ScrollView,
  Pressable,
  StyleSheet,
  Linking,
  Dimensions,
  ActivityIndicator,
  Share,
  Clipboard,
  ToastAndroid,
  Platform,
  Alert,
} from 'react-native';
import Feather from '@expo/vector-icons/Feather';
import { useNavigation, useRoute } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';

const { width } = Dimensions.get('window');

// ---------------------------------------------------------------------------
// Types (mirrors GraphQL NFTType + enrichment)
// ---------------------------------------------------------------------------

interface GlossaryTerm {
  term: string;
  definition: string;
}

interface EducationContent {
  story?: string;
  raritySummary?: string;
  lesson?: string;
  glossary?: GlossaryTerm[];
  confidence?: number;
  source?: string;
}

interface UtilityLink {
  label: string;
  url: string;
}

interface UtilityData {
  perks?: string[];
  officialLinks?: UtilityLink[];
}

interface RiskData {
  level?: string; // LOW | MED | HIGH
  reasons?: string[];
  recommendedAction?: string;
}

export interface NFTDetailParams {
  id: string;
  tokenId: string;
  contractAddress: string;
  name: string;
  description?: string;
  imageUrl?: string;
  collectionName: string;
  chain: string;
  attributes?: Array<{ traitType: string; value: string }>;
  floorPrice?: number;
  lastSalePrice?: number;
  educationContent?: EducationContent;
  utilityData?: UtilityData;
  risk?: RiskData;
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

const TABS = ['Overview', 'Learn', 'Utility', 'Risk'] as const;
type Tab = typeof TABS[number];

function RiskBadge({ level }: { level?: string }) {
  const config = {
    LOW: { bg: '#D1FAE5', color: '#065F46', icon: 'shield' as const, label: 'Low Risk' },
    MED: { bg: '#FEF3C7', color: '#92400E', icon: 'alert-triangle' as const, label: 'Review' },
    HIGH: { bg: '#FEE2E2', color: '#991B1B', icon: 'alert-circle' as const, label: 'High Risk' },
  };
  const c = config[(level as keyof typeof config) || 'MED'] || config.MED;
  return (
    <View style={[styles.riskBadge, { backgroundColor: c.bg }]}>
      <Feather name={c.icon} size={13} color={c.color} />
      <Text style={[styles.riskBadgeText, { color: c.color }]}>{c.label}</Text>
    </View>
  );
}

function GlossaryCard({ term, definition, forceExpanded }: GlossaryTerm & { forceExpanded?: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const isOpen = forceExpanded || expanded;
  return (
    <Pressable
      style={styles.glossaryCard}
      onPress={() => setExpanded(e => !e)}
    >
      <View style={styles.glossaryHeader}>
        <Text style={styles.glossaryTerm}>{term}</Text>
        <Feather name={isOpen ? 'chevron-up' : 'chevron-down'} size={16} color="#6B7280" />
      </View>
      {isOpen && (
        <Text style={styles.glossaryDefinition}>{definition}</Text>
      )}
    </Pressable>
  );
}

function OverviewTab({ nft }: { nft: NFTDetailParams }) {
  const chainColors: Record<string, string> = {
    ethereum: '#627EEA',
    polygon: '#8247E5',
    arbitrum: '#28A0F0',
    optimism: '#FF0420',
    base: '#0052FF',
  };
  const chainColor = chainColors[nft.chain] || '#6B7280';

  return (
    <ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false}>
      {/* Image */}
      <View style={styles.imageContainer}>
        {nft.imageUrl ? (
          <Image source={{ uri: nft.imageUrl }} style={styles.nftImage} resizeMode="cover" />
        ) : (
          <View style={[styles.nftImage, styles.imagePlaceholder]}>
            <Feather name="image" size={48} color="#9CA3AF" />
          </View>
        )}
      </View>

      {/* Name + collection */}
      <View style={styles.overviewMeta}>
        <Text style={styles.nftName}>{nft.name}</Text>
        <View style={styles.collectionRow}>
          <View style={[styles.chainDot, { backgroundColor: chainColor }]} />
          <Text style={styles.collectionName}>{nft.collectionName}</Text>
          <Text style={styles.chainLabel}> · {nft.chain.charAt(0).toUpperCase() + nft.chain.slice(1)}</Text>
        </View>
        {nft.description ? (
          <Text style={styles.description}>{nft.description}</Text>
        ) : null}
      </View>

      {/* Price row */}
      {(nft.floorPrice || nft.lastSalePrice) ? (
        <View style={styles.priceRow}>
          {nft.floorPrice ? (
            <View style={styles.priceCard}>
              <Text style={styles.priceLabel}>Floor Price</Text>
              <Text style={styles.priceValue}>{nft.floorPrice.toFixed(4)} ETH</Text>
            </View>
          ) : null}
          {nft.lastSalePrice ? (
            <View style={styles.priceCard}>
              <Text style={styles.priceLabel}>Last Sale</Text>
              <Text style={styles.priceValue}>{nft.lastSalePrice.toFixed(4)} ETH</Text>
            </View>
          ) : null}
        </View>
      ) : null}

      {/* Traits */}
      {nft.attributes && nft.attributes.length > 0 ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Traits</Text>
          <View style={styles.traitsGrid}>
            {nft.attributes.map((attr, i) => (
              <View key={i} style={styles.traitChip}>
                <Text style={styles.traitType}>{attr.traitType}</Text>
                <Text style={styles.traitValue}>{attr.value}</Text>
              </View>
            ))}
          </View>
        </View>
      ) : null}

      {/* Contract info */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Contract</Text>
        <View style={styles.contractCard}>
          <View style={styles.contractAddressRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.contractLabel}>Address</Text>
              <Text style={styles.contractAddress} numberOfLines={1}>
                {nft.contractAddress}
              </Text>
            </View>
            <Pressable
              style={({ pressed }) => [styles.copyBtn, pressed && { opacity: 0.65 }]}
              onPress={() => {
                Clipboard.setString(nft.contractAddress);
                if (Platform.OS === 'android') {
                  ToastAndroid.show('Address copied', ToastAndroid.SHORT);
                } else {
                  Alert.alert('Copied', 'Contract address copied to clipboard.');
                }
              }}
            >
              <Feather name="copy" size={14} color="#7C3AED" />
            </Pressable>
          </View>
          <Text style={styles.contractLabel}>Token ID</Text>
          <Text style={styles.contractValue}>#{nft.tokenId}</Text>
        </View>
      </View>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

function LearnTab({
  nft,
  onAskTutor,
  onShareLesson,
}: {
  nft: NFTDetailParams;
  onAskTutor: () => void;
  onShareLesson: () => void;
}) {
  const ed = nft.educationContent;
  const hasRichContent = ed?.confidence && ed.confidence > 0.8;
  const [beginnerMode, setBeginnerMode] = useState(false);

  return (
    <ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false}>
      {/* Beginner Mode toggle */}
      <View style={styles.beginnerRow}>
        <View style={styles.beginnerLabelRow}>
          <Feather name="book-open" size={14} color="#7C3AED" />
          <Text style={styles.beginnerLabel}>Beginner Mode</Text>
        </View>
        <Pressable
          style={[styles.toggleTrack, beginnerMode && styles.toggleTrackOn]}
          onPress={() => setBeginnerMode(b => !b)}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
        >
          <View style={[styles.toggleThumb, beginnerMode && styles.toggleThumbOn]} />
        </Pressable>
      </View>

      {/* Lesson pill */}
      {ed?.lesson ? (
        <View style={styles.lessonPill}>
          <Feather name="zap" size={16} color="#7C3AED" />
          <Text style={styles.lessonText}>{ed.lesson}</Text>
        </View>
      ) : null}

      {/* Story */}
      {ed?.story ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>The Story</Text>
          <Text style={styles.bodyText}>{ed.story}</Text>
        </View>
      ) : null}

      {/* Rarity */}
      {ed?.raritySummary ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Rarity Explained</Text>
          <Text style={styles.bodyText}>{ed.raritySummary}</Text>
        </View>
      ) : null}

      {/* Glossary — auto-expanded in Beginner Mode */}
      {ed?.glossary && ed.glossary.length > 0 ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            {beginnerMode ? 'Key Terms  (all expanded)' : 'Key Terms  Tap to expand'}
          </Text>
          {ed.glossary.map((g, i) => (
            <GlossaryCard key={i} term={g.term} definition={g.definition} forceExpanded={beginnerMode} />
          ))}
        </View>
      ) : null}

      {/* Content confidence note */}
      {!hasRichContent ? (
        <View style={styles.genericNote}>
          <Feather name="info" size={14} color="#6366F1" />
          <Text style={styles.genericNoteText}>
            Connect a wallet to unlock collection-specific education for your own NFTs.
          </Text>
        </View>
      ) : null}

      {/* Action row: Ask + Share */}
      <View style={styles.learnActions}>
        <Pressable
          style={({ pressed }) => [styles.askTutorBtn, styles.learnActionBtn, pressed && { opacity: 0.85 }]}
          onPress={onAskTutor}
        >
          <Feather name="message-circle" size={18} color="#FFFFFF" />
          <Text style={styles.askTutorText}>Ask about this NFT</Text>
        </Pressable>

        <Pressable
          style={({ pressed }) => [styles.shareLessonBtn, pressed && { opacity: 0.85 }]}
          onPress={onShareLesson}
        >
          <Feather name="share-2" size={17} color="#7C3AED" />
          <Text style={styles.shareLessonText}>Share Lesson</Text>
        </Pressable>
      </View>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

function UtilityTab({ nft }: { nft: NFTDetailParams }) {
  const perks = nft.utilityData?.perks || [];
  const links = nft.utilityData?.officialLinks || [];
  const hasUtility = perks.length > 0 || links.length > 0;

  return (
    <ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false}>
      {!hasUtility ? (
        <View style={styles.emptyTab}>
          <Feather name="gift" size={40} color="#D1D5DB" />
          <Text style={styles.emptyTabTitle}>No utility data yet</Text>
          <Text style={styles.emptyTabDesc}>
            Connect your wallet to check for perks, events, and token-gated access tied to this NFT.
          </Text>
        </View>
      ) : (
        <>
          {perks.length > 0 ? (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>What This Unlocks</Text>
              {perks.map((perk, i) => (
                <View key={i} style={styles.perkRow}>
                  <View style={styles.perkDot} />
                  <Text style={styles.perkText}>{perk}</Text>
                </View>
              ))}
            </View>
          ) : null}

          {links.length > 0 ? (
            <View style={styles.section}>
              <Text style={styles.sectionTitle}>Official Links</Text>
              {links.map((link, i) => (
                <Pressable
                  key={i}
                  style={({ pressed }) => [styles.linkCard, pressed && { opacity: 0.8 }]}
                  onPress={() => Linking.openURL(link.url)}
                >
                  <Text style={styles.linkLabel}>{link.label}</Text>
                  <Feather name="external-link" size={15} color="#3B82F6" />
                </Pressable>
              ))}
            </View>
          ) : null}
        </>
      )}
      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

function RiskTab({ nft }: { nft: NFTDetailParams }) {
  const risk = nft.risk;
  const levelConfig = {
    LOW: { bg: '#D1FAE5', border: '#6EE7B7', color: '#065F46', icon: 'shield' as const, headline: 'This NFT looks safe' },
    MED: { bg: '#FEF3C7', border: '#FCD34D', color: '#92400E', icon: 'alert-triangle' as const, headline: 'Worth a closer look' },
    HIGH: { bg: '#FEE2E2', border: '#FCA5A5', color: '#991B1B', icon: 'alert-circle' as const, headline: 'Proceed with caution' },
  };
  const level = (risk?.level as keyof typeof levelConfig) || 'MED';
  const c = levelConfig[level] || levelConfig.MED;

  return (
    <ScrollView style={styles.tabContent} showsVerticalScrollIndicator={false}>
      <View style={[styles.riskBanner, { backgroundColor: c.bg, borderColor: c.border }]}>
        <Feather name={c.icon} size={28} color={c.color} />
        <Text style={[styles.riskHeadline, { color: c.color }]}>{c.headline}</Text>
      </View>

      {risk?.reasons && risk.reasons.length > 0 ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Why</Text>
          {risk.reasons.map((reason, i) => (
            <View key={i} style={styles.reasonRow}>
              <Feather name="check" size={14} color="#6B7280" />
              <Text style={styles.reasonText}>{reason}</Text>
            </View>
          ))}
        </View>
      ) : null}

      {risk?.recommendedAction ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recommendation</Text>
          <View style={styles.recommendationCard}>
            <Text style={styles.recommendationText}>{risk.recommendedAction}</Text>
          </View>
        </View>
      ) : null}

      {/* Always show this safety tip */}
      <View style={styles.safetyTip}>
        <Feather name="info" size={14} color="#6366F1" />
        <Text style={styles.safetyTipText}>
          Never approve transactions or share your seed phrase based on NFT ownership claims. Always verify official links before connecting your wallet.
        </Text>
      </View>

      {/* Etherscan verification link */}
      <Pressable
        style={({ pressed }) => [styles.etherscanBtn, pressed && { opacity: 0.8 }]}
        onPress={() => {
          const base = nft.chain === 'polygon'
            ? 'https://polygonscan.com/address/'
            : 'https://etherscan.io/address/';
          Linking.openURL(`${base}${nft.contractAddress}`);
        }}
      >
        <Feather name="external-link" size={14} color="#3B82F6" />
        <Text style={styles.etherscanBtnText}>
          Verify on {nft.chain === 'polygon' ? 'PolygonScan' : 'Etherscan'}
        </Text>
      </Pressable>

      <View style={{ height: 40 }} />
    </ScrollView>
  );
}

// ---------------------------------------------------------------------------
// Main Screen
// ---------------------------------------------------------------------------

export default function NFTDetailScreen() {
  const navigation = useNavigation<any>();
  const route = useRoute<any>();
  const nft: NFTDetailParams = route.params?.nft;

  const [activeTab, setActiveTab] = useState<Tab>('Overview');

  if (!nft) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#7C3AED" />
      </View>
    );
  }

  const handleAskTutor = () => {
    navigation.navigate('tutor-ask-explain', {
      initialQuestion: `Explain ${nft.name} from the ${nft.collectionName} collection. What makes it special and what blockchain concepts does it illustrate?`,
    });
  };

  const handleShare = async () => {
    try {
      await Share.share({
        message: `Check out ${nft.name} — ${nft.collectionName} on ${nft.chain}. Floor: ${nft.floorPrice ? nft.floorPrice.toFixed(3) + ' ETH' : 'N/A'}`,
      });
    } catch (_) {}
  };

  const handleShareLesson = async () => {
    const ed = nft.educationContent;
    const lesson = ed?.lesson ?? `${nft.name} is part of the ${nft.collectionName} collection on ${nft.chain}.`;
    const story = ed?.story ? `\n\n${ed.story.slice(0, 200)}…` : '';
    try {
      await Share.share({
        message: `💡 Web3 Lesson from ${nft.name}\n\n${lesson}${story}\n\nLearn more in the RichesReach NFT Gallery.`,
      });
    } catch (_) {}
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <LinearGradient colors={['#1E1B4B', '#312E81']} style={styles.header}>
        <View style={styles.headerRow}>
          <Pressable
            style={({ pressed }) => [styles.backBtn, pressed && { opacity: 0.7 }]}
            onPress={() => navigation.goBack()}
          >
            <Feather name="arrow-left" size={22} color="#FFFFFF" />
          </Pressable>
          <View style={styles.headerCenter}>
            <Text style={styles.headerTitle} numberOfLines={1}>{nft.name}</Text>
            <Text style={styles.headerSubtitle} numberOfLines={1}>{nft.collectionName}</Text>
          </View>
          <View style={styles.headerRight}>
            <RiskBadge level={nft.risk?.level} />
            <Pressable
              style={({ pressed }) => [styles.shareBtn, pressed && { opacity: 0.7 }]}
              onPress={handleShare}
            >
              <Feather name="share-2" size={18} color="#C4B5FD" />
            </Pressable>
          </View>
        </View>

        {/* Tab bar */}
        <View style={styles.tabBar}>
          {TABS.map(tab => (
            <Pressable
              key={tab}
              style={[styles.tabItem, activeTab === tab && styles.tabItemActive]}
              onPress={() => setActiveTab(tab)}
            >
              <Text style={[styles.tabLabel, activeTab === tab && styles.tabLabelActive]}>
                {tab}
              </Text>
              {tab === 'Learn' && (
                <View style={styles.learnBadge}>
                  <Text style={styles.learnBadgeText}>✨</Text>
                </View>
              )}
            </Pressable>
          ))}
        </View>
      </LinearGradient>

      {/* Tab content */}
      {activeTab === 'Overview' && <OverviewTab nft={nft} />}
      {activeTab === 'Learn' && <LearnTab nft={nft} onAskTutor={handleAskTutor} onShareLesson={handleShareLesson} />}
      {activeTab === 'Utility' && <UtilityTab nft={nft} />}
      {activeTab === 'Risk' && <RiskTab nft={nft} />}
    </View>
  );
}

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#F9FAFB' },
  loadingContainer: { flex: 1, alignItems: 'center', justifyContent: 'center' },

  // Header
  header: {
    paddingTop: 56,
    paddingBottom: 0,
    paddingHorizontal: 16,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 10,
  },
  backBtn: { padding: 4 },
  headerCenter: { flex: 1 },
  headerTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  headerSubtitle: {
    fontSize: 12,
    color: '#A5B4FC',
    marginTop: 1,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  shareBtn: { padding: 4 },

  // Risk badge
  riskBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  riskBadgeText: {
    fontSize: 11,
    fontWeight: '700',
  },

  // Tab bar
  tabBar: {
    flexDirection: 'row',
    borderBottomWidth: 0,
  },
  tabItem: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    gap: 4,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  tabItemActive: {
    borderBottomColor: '#A5B4FC',
  },
  tabLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#A5B4FC',
  },
  tabLabelActive: {
    color: '#FFFFFF',
  },
  learnBadge: {
    marginLeft: 2,
  },
  learnBadgeText: {
    fontSize: 11,
  },

  // Tab content
  tabContent: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 16,
  },

  // Overview
  imageContainer: {
    alignItems: 'center',
    marginBottom: 16,
  },
  nftImage: {
    width: width - 32,
    height: width - 32,
    borderRadius: 16,
    backgroundColor: '#E5E7EB',
  },
  imagePlaceholder: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  overviewMeta: {
    marginBottom: 16,
  },
  nftName: {
    fontSize: 22,
    fontWeight: '800',
    color: '#111827',
    marginBottom: 6,
  },
  collectionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  chainDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  collectionName: {
    fontSize: 14,
    color: '#374151',
    fontWeight: '600',
  },
  chainLabel: {
    fontSize: 14,
    color: '#9CA3AF',
  },
  description: {
    fontSize: 14,
    color: '#6B7280',
    lineHeight: 20,
  },
  priceRow: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 20,
  },
  priceCard: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
  },
  priceLabel: {
    fontSize: 11,
    color: '#9CA3AF',
    fontWeight: '500',
    marginBottom: 4,
  },
  priceValue: {
    fontSize: 18,
    fontWeight: '800',
    color: '#111827',
  },
  traitsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  traitChip: {
    backgroundColor: '#EDE9FE',
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  traitType: {
    fontSize: 10,
    color: '#7C3AED',
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 2,
  },
  traitValue: {
    fontSize: 13,
    color: '#4C1D95',
    fontWeight: '700',
  },
  contractCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    gap: 4,
  },
  contractAddressRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  copyBtn: {
    padding: 8,
    backgroundColor: '#EDE9FE',
    borderRadius: 8,
  },
  contractLabel: {
    fontSize: 11,
    color: '#9CA3AF',
    fontWeight: '500',
    marginTop: 8,
  },
  contractAddress: {
    fontSize: 12,
    color: '#374151',
    fontFamily: 'monospace',
  },
  contractValue: {
    fontSize: 14,
    color: '#111827',
    fontWeight: '600',
  },

  // Learn tab
  lessonPill: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    backgroundColor: '#EDE9FE',
    borderRadius: 14,
    padding: 14,
    marginBottom: 16,
  },
  lessonText: {
    flex: 1,
    fontSize: 14,
    color: '#4C1D95',
    fontWeight: '600',
    lineHeight: 20,
  },
  bodyText: {
    fontSize: 15,
    color: '#374151',
    lineHeight: 24,
  },
  glossaryCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    padding: 14,
    marginBottom: 8,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 2,
  },
  glossaryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  glossaryTerm: {
    fontSize: 14,
    fontWeight: '700',
    color: '#111827',
  },
  glossaryDefinition: {
    fontSize: 13,
    color: '#6B7280',
    lineHeight: 19,
    marginTop: 8,
  },
  genericNote: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    backgroundColor: '#EEF2FF',
    borderRadius: 10,
    padding: 12,
    marginBottom: 16,
  },
  genericNoteText: {
    flex: 1,
    fontSize: 12,
    color: '#4338CA',
    lineHeight: 17,
  },
  // Beginner Mode toggle
  beginnerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#F5F3FF',
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 10,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: '#DDD6FE',
  },
  beginnerLabelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  beginnerLabel: {
    fontSize: 13,
    fontWeight: '700',
    color: '#4C1D95',
  },
  toggleTrack: {
    width: 44,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#D1D5DB',
    padding: 2,
    justifyContent: 'center',
  },
  toggleTrackOn: {
    backgroundColor: '#7C3AED',
  },
  toggleThumb: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: '#FFFFFF',
    alignSelf: 'flex-start',
  },
  toggleThumbOn: {
    alignSelf: 'flex-end',
  },

  // Learn tab action row
  learnActions: {
    gap: 10,
    marginTop: 8,
  },
  learnActionBtn: {
    // extends askTutorBtn
  },
  askTutorBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#7C3AED',
    borderRadius: 14,
    paddingVertical: 15,
  },
  askTutorText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  shareLessonBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: '#EDE9FE',
    borderRadius: 14,
    paddingVertical: 13,
    borderWidth: 1,
    borderColor: '#C4B5FD',
  },
  shareLessonText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#7C3AED',
  },

  // Utility tab
  perkRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    marginBottom: 10,
  },
  perkDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#7C3AED',
    marginTop: 5,
  },
  perkText: {
    flex: 1,
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
  },
  linkCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    padding: 14,
    marginBottom: 8,
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 2,
  },
  linkLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#3B82F6',
  },

  // Risk tab
  riskBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    borderRadius: 14,
    borderWidth: 1,
    padding: 16,
    marginBottom: 20,
  },
  riskHeadline: {
    fontSize: 17,
    fontWeight: '800',
  },
  reasonRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    marginBottom: 8,
  },
  reasonText: {
    flex: 1,
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
  },
  recommendationCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: 10,
    padding: 14,
    borderLeftWidth: 3,
    borderLeftColor: '#7C3AED',
  },
  recommendationText: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 21,
  },
  safetyTip: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    backgroundColor: '#EEF2FF',
    borderRadius: 10,
    padding: 12,
    marginTop: 8,
  },
  safetyTipText: {
    flex: 1,
    fontSize: 12,
    color: '#4338CA',
    lineHeight: 17,
  },
  etherscanBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
    backgroundColor: '#EFF6FF',
    borderRadius: 10,
    padding: 12,
    marginTop: 10,
    borderWidth: 1,
    borderColor: '#BFDBFE',
  },
  etherscanBtnText: {
    fontSize: 13,
    fontWeight: '600',
    color: '#3B82F6',
  },

  // Empty states
  emptyTab: {
    alignItems: 'center',
    paddingVertical: 48,
    paddingHorizontal: 24,
  },
  emptyTabTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#374151',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyTabDesc: {
    fontSize: 14,
    color: '#9CA3AF',
    textAlign: 'center',
    lineHeight: 20,
  },

  // Shared
  section: {
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#9CA3AF',
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 10,
  },
});
