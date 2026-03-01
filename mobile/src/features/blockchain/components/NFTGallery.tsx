import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Image,
  ActivityIndicator,
  Dimensions,
} from 'react-native';
import Icon from 'react-native-vector-icons/Feather';
import { useNavigation } from '@react-navigation/native';
import { useQuery, gql } from '@apollo/client';

const { width } = Dimensions.get('window');

const GET_USER_NFTS = gql`
  query GetUserNFTs($address: String!, $chain: String) {
    userNFTs(address: $address, chain: $chain) {
      id
      tokenId
      contractAddress
      name
      description
      imageUrl
      collectionName
      chain
      attributes {
        traitType
        value
      }
      floorPrice
      lastSalePrice
      educationContent {
        story
        raritySummary
        lesson
        glossary {
          term
          definition
        }
        confidence
        source
      }
      utilityData {
        perks
        officialLinks {
          label
          url
        }
      }
      risk {
        level
        reasons
        recommendedAction
      }
    }
  }
`;

interface GlossaryTerm {
  term: string;
  definition: string;
}

interface NFT {
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
  educationContent?: {
    story?: string;
    raritySummary?: string;
    lesson?: string;
    glossary?: GlossaryTerm[];
    confidence?: number;
    source?: string;
  };
  utilityData?: {
    perks?: string[];
    officialLinks?: Array<{ label: string; url: string }>;
  };
  risk?: {
    level?: string;
    reasons?: string[];
    recommendedAction?: string;
  };
}

interface NFTGalleryProps {
  walletAddress?: string;
  chain?: string;
  onNFTSelect?: (nft: NFT) => void;
}

const C = {
  bg: '#0A0A0A',
  card: '#1A1A1A',
  text: '#FFFFFF',
  sub: '#888888',
  primary: '#00D4FF',
  success: '#00FF88',
  border: '#2A2A2A',
};

const DEMO_NFTS: NFT[] = [
  {
    id: 'demo-1', tokenId: '4201',
    contractAddress: '0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D',
    name: 'Bored Ape #4201', collectionName: 'Bored Ape Yacht Club',
    chain: 'ethereum', floorPrice: 14.29, lastSalePrice: 16.5,
    imageUrl: 'https://ipfs.io/ipfs/QmRRPWG96cmgTn2qSzjwr2qvfNEuhunv6FNeMFGa9bx6mQ',
    description: 'A unique ape from the Bored Ape Yacht Club collection.',
    risk: {
      level: 'LOW',
      reasons: ['Contract verified on Etherscan', 'Top-5 collection by volume', 'Active development team'],
      recommendedAction: 'No action needed — this is a well-established collection.',
    },
    educationContent: {
      lesson: 'Your Bored Ape is an ERC-721 token: a unique entry in Ethereum\'s permanent ledger that no company — not even Yuga Labs — can delete, freeze, or reassign without your private key. That immutability is what "true ownership" means on-chain.',
      story: 'Bored Ape Yacht Club launched in April 2021 with 10,000 hand-drawn apes and became the defining "profile picture" (PFP) collection of the NFT era. Ownership grants access to the Yacht Club — real events, exclusive merch, and governance rights over the ApeCoin DAO. It proved NFTs could be more than art: they became membership keys to a community.',
      raritySummary: 'BAYC traits like gold fur, laser eyes, or solid gold backgrounds appear in less than 1% of the collection. Rarity is determined by combining all trait frequencies — rarer combinations command significant premiums on secondary markets.',
      glossary: [
        { term: 'ERC-721', definition: 'The Ethereum standard for non-fungible tokens — each token is unique, unlike ERC-20 coins which are interchangeable.' },
        { term: 'Floor price', definition: "The lowest asking price in a collection. It's the cost to enter the club, not the value of your specific ape." },
        { term: 'ApeCoin (APE)', definition: 'A governance token given to BAYC/MAYC holders. Owning APE lets you vote on how the ApeCoin DAO spends its treasury.' },
      ],
      confidence: 0.95,
      source: 'cached_collection',
    },
    utilityData: {
      perks: [
        'Access to the Bored Ape Yacht Club private Discord',
        'ApeCoin (APE) governance rights via the ApeCoin DAO',
        'Exclusive IRL events — ApeFest and invite-only gatherings',
        'Commercial IP rights to use your ape\'s image',
        'Eligibility for future Yuga Labs airdrops and land in Otherside metaverse',
      ],
      officialLinks: [
        { label: 'Yuga Labs', url: 'https://yuga.com' },
        { label: 'ApeCoin DAO', url: 'https://apecoin.com' },
        { label: 'Otherside', url: 'https://otherside.xyz' },
      ],
    },
  },
  {
    id: 'demo-2', tokenId: '7804',
    contractAddress: '0xb47e3cd837dDF8e4c57F05d70Ab865de6e193BBB',
    name: 'CryptoPunk #7804', collectionName: 'CryptoPunks',
    chain: 'ethereum', floorPrice: 44.95, lastSalePrice: 48.0,
    imageUrl: 'https://www.larvalabs.com/public/images/cryptopunks/punk7804.png',
    description: 'One of the original 10,000 CryptoPunks.',
    risk: {
      level: 'LOW',
      reasons: ['Contract verified', '8+ years of on-chain history', 'Acquired by Yuga Labs'],
      recommendedAction: 'No action needed — this is a well-established collection.',
    },
    educationContent: {
      lesson: 'CryptoPunks predate ERC-721 and use a custom on-chain marketplace contract from 2017 that\'s still operating today. This is blockchain permanence in action: code deployed years ago continues to run without any company maintaining it.',
      story: 'CryptoPunks were created by Larva Labs in June 2017 — before the ERC-721 standard even existed. The 10,000 pixel-art characters were given away free and inspired the entire NFT movement. Acquired by Yuga Labs in 2022, Punks are widely considered the "original blue-chip" NFT and cultural artifacts of early crypto history.',
      raritySummary: 'Only 88 Zombies, 24 Apes, and 9 Aliens exist among the 10,000 Punks — making them the rarest types. Attribute count also matters: a Punk with 0 or 7 attributes is rarer than average. Aliens with minimal attributes have sold for thousands of ETH.',
      glossary: [
        { term: 'On-chain metadata', definition: "The NFT's image and traits stored directly on the blockchain — unlike most NFTs where images sit on external servers that could go offline." },
        { term: 'Blue-chip NFT', definition: 'A collection with a long track record, high liquidity, and broad recognition — analogous to blue-chip stocks.' },
        { term: 'Provenance', definition: 'The verifiable history of ownership for an NFT, recorded permanently on-chain from its first mint to today.' },
      ],
      confidence: 0.95,
      source: 'cached_collection',
    },
    utilityData: {
      perks: [
        'CryptoPunks holder commercial IP rights (granted by Yuga Labs, 2022)',
        'Cultural status as one of the earliest NFT artifacts',
        'On-chain marketplace — buy, sell, and bid directly via the contract',
      ],
      officialLinks: [
        { label: 'CryptoPunks', url: 'https://cryptopunks.app' },
        { label: 'Larva Labs', url: 'https://larvalabs.com' },
      ],
    },
  },
  {
    id: 'demo-3', tokenId: '1337',
    contractAddress: '0x60E4d786628Fea6478F785A6d7e704777c86a7c6',
    name: 'Mutant Ape #1337', collectionName: 'Mutant Ape Yacht Club',
    chain: 'ethereum', floorPrice: 3.12, lastSalePrice: 3.5,
    imageUrl: 'https://ipfs.io/ipfs/QmPbxeGcXhYQQNgsC6a36dDyYUcHgMLnGKnF8pVFmGsvqi',
    description: 'A mutant ape from the MAYC collection.',
    risk: {
      level: 'LOW',
      reasons: ['Contract verified', 'Yuga Labs ecosystem', 'High trading volume'],
      recommendedAction: 'No action needed — this is a well-established collection.',
    },
    educationContent: {
      lesson: 'Airdrops — like the mutant serum sent to BAYC holders — are one of the most powerful Web3 loyalty tools. Projects reward early or existing holders with new tokens or NFTs, creating value for the community without a traditional sale.',
      story: 'Mutant Ape Yacht Club launched in August 2021 as a companion to BAYC. Existing BAYC holders received "mutant serum" to transform their apes; another 20,000 were sold publicly. MAYC gave the broader community a path into the Yuga ecosystem at a lower price point while maintaining many of the same membership benefits.',
      raritySummary: 'M3 Mega Mutant serums — which created the rarest MAYC — were only held by a handful of BAYC owners. Serums were tiered (M1, M2, M3), so a Mutant Ape\'s origin serum directly impacts its rarity tier and market value.',
      glossary: [
        { term: 'Airdrop', definition: 'Free tokens or NFTs sent directly to wallet addresses, usually as a reward for holding another asset or being an early adopter.' },
        { term: 'Companion collection', definition: 'A secondary NFT collection tied to an existing one, expanding the ecosystem while offering a lower entry price.' },
      ],
      confidence: 0.95,
      source: 'cached_collection',
    },
    utilityData: {
      perks: [
        'Access to MAYC holder Discord channels',
        'Eligibility for Yuga Labs ecosystem events',
        'Commercial IP rights to your Mutant Ape\'s image',
        'Otherside metaverse access',
      ],
      officialLinks: [
        { label: 'Yuga Labs', url: 'https://yuga.com' },
      ],
    },
  },
  {
    id: 'demo-4', tokenId: '9921',
    contractAddress: '0x49cF6f5d44E70224e2E23fDcdd2C053F30aDA28B',
    name: 'CloneX #9921', collectionName: 'CloneX',
    chain: 'ethereum', floorPrice: 1.85, lastSalePrice: 2.1,
    imageUrl: 'https://clonex-assets.rtfkt.com/images/9921.png',
    description: 'A next-gen avatar from RTFKT x Nike.',
    risk: {
      level: 'LOW',
      reasons: ['Nike-backed (RTFKT acquired 2021)', 'Contract verified', 'Active product roadmap'],
      recommendedAction: 'No action needed — this is a well-established collection.',
    },
    educationContent: {
      lesson: 'CloneX demonstrates how traditional brands are entering Web3: Nike acquired RTFKT to own the IP and the on-chain relationship with customers. NFT ownership can unlock physical products — bridging digital tokens with real-world goods.',
      story: 'CloneX launched in December 2021 as a collaboration between RTFKT Studio and Nike — making it one of the first major NFT collections from a global sportswear brand. The 20,000 avatars are designed as next-generation digital identities, with physical Nike sneaker claims and metaverse utility built in from launch.',
      raritySummary: 'CloneX has 8 DNA types: Human, Robot, Undead, Alien, Angel, Demon, and two rare variants. Non-Human DNA types are significantly rarer and command premiums. File type (3D vs 2D) and specific drip traits further differentiate value.',
      glossary: [
        { term: 'Physical redemption', definition: 'When an NFT holder can claim a real-world item (shoes, merch, tickets) by "burning" or proving ownership of their token.' },
        { term: 'Digital identity', definition: "Using an NFT as your avatar or profile picture across platforms — asserting ownership of your online persona." },
      ],
      confidence: 0.95,
      source: 'cached_collection',
    },
    utilityData: {
      perks: [
        'Nike x RTFKT physical sneaker claim eligibility',
        'Access to RTFKT creator drops and forging events',
        'CloneX metaverse avatar across supported platforms',
        'Early access to future RTFKT collections',
      ],
      officialLinks: [
        { label: 'RTFKT', url: 'https://rtfkt.com' },
        { label: 'Nike NFT', url: 'https://www.nike.com/nft' },
      ],
    },
  },
  {
    id: 'demo-5', tokenId: '3820',
    contractAddress: '0x8a90CAb2b38dba80c64b7734e58Ee1dB38B8992e',
    name: 'Doodle #3820', collectionName: 'Doodles',
    chain: 'ethereum', floorPrice: 1.2, lastSalePrice: 1.4,
    imageUrl: 'https://ipfs.io/ipfs/QmPMc4tcBsMqLRuCQtPmPe84bpSjrC3Ky7t3JWuHXYB4aS/3820.png',
    description: 'A hand-drawn doodle from the Doodles collection.',
    risk: {
      level: 'LOW',
      reasons: ['Contract verified', 'Pharrell Williams partnership', 'Active community treasury'],
      recommendedAction: 'No action needed — this is a well-established collection.',
    },
    educationContent: {
      lesson: 'Doodles pioneered the "community treasury" model: a percentage of secondary sale royalties flows into a shared pool that NFT holders vote on how to spend. This is decentralized governance in action — your NFT is also a voting share.',
      story: 'Doodles launched in October 2021 with 10,000 hand-drawn characters by illustrator Burnt Toast. Beyond art, Doodles established a community treasury funded by royalties, governed by holders. Pharrell Williams joined as Chief Brand Officer in 2022, and the project expanded into music, animation, and physical consumer products.',
      raritySummary: 'Rare traits include Rainbow backgrounds (under 1%), Alien heads, and Gold outfits. Doodles uses a Points system where rarer traits score higher — the total score determines a Doodle\'s rarity rank within the collection.',
      glossary: [
        { term: 'Royalties', definition: 'A percentage (usually 5–10%) paid to the original creator every time their NFT is resold on secondary markets.' },
        { term: 'Community treasury', definition: 'A shared pool of funds, often from royalties, that NFT holders govern collectively via on-chain or off-chain voting.' },
        { term: 'PFP (Profile Picture)', definition: 'An NFT used as a social media avatar. PFP collections often double as membership passes to communities.' },
      ],
      confidence: 0.95,
      source: 'cached_collection',
    },
    utilityData: {
      perks: [
        'Doodles community treasury governance rights',
        'Access to exclusive Doodles events and activations',
        'Early access to Doodles2 and extended universe drops',
        'Physical and digital consumer products from the Doodles brand',
      ],
      officialLinks: [
        { label: 'Doodles', url: 'https://doodles.app' },
      ],
    },
  },
  {
    id: 'demo-6', tokenId: '512',
    contractAddress: '0x1A92f7381B9F03921564a437210bB9396471050C',
    name: 'Cool Cat #512', collectionName: 'Cool Cats',
    chain: 'polygon', floorPrice: 0.18, lastSalePrice: 0.22,
    imageUrl: 'https://ipfs.io/ipfs/QmTNBQDbggLZdKF1fRgWnXsnRikd52zL5ciNu769g9y9K7/512.png',
    description: 'A cool cat just chilling.',
    risk: {
      level: 'LOW',
      reasons: ['Contract verified on Etherscan', 'Active since July 2021', 'Established community'],
      recommendedAction: 'No action needed — this is a well-established collection.',
    },
    educationContent: {
      lesson: 'Cool Cats is an example of how NFT projects build "lore" — a narrative universe that gives holders emotional attachment beyond the art. Storytelling increases long-term retention and can expand a collection\'s IP value over time.',
      story: 'Cool Cats launched in July 2021 with 9,999 randomly generated cats. An early standout of the PFP era, Cool Cats built a strong community through frequent holder benefits and a clear brand identity. The collection expanded with Cool Pets — companion NFTs — and has focused on storytelling and animation to build a long-term IP.',
      raritySummary: 'Cool Cats are scored on a tier system: Cool (3–4 pts), Extra Cool (5 pts), Super Cool (6 pts), and Beyond Cool (7+ pts). Higher point totals indicate rarer trait combinations. Wild backgrounds and unique outfits significantly boost a Cat\'s rarity score.',
      glossary: [
        { term: 'NFT lore', definition: "The backstory, world-building, and narrative that a project builds around its collection to deepen community engagement." },
        { term: 'Companion NFT', definition: 'A secondary collection designed to pair with a primary one — like Cool Pets for Cool Cats — extending the ecosystem.' },
      ],
      confidence: 0.95,
      source: 'cached_collection',
    },
    utilityData: {
      perks: [
        'Cool Cats holder Discord access',
        'Eligibility for Cool Pets companion NFT benefits',
        'Exclusive holder merchandise and event access',
        'Voting rights on community initiatives',
      ],
      officialLinks: [
        { label: 'Cool Cats', url: 'https://coolcatsnft.com' },
      ],
    },
  },
];

type FilterChip = 'All' | 'Historical' | 'High Utility' | 'High Risk' | 'Beginner-Friendly';

const FILTER_CHIPS: FilterChip[] = ['All', 'Historical', 'High Utility', 'High Risk', 'Beginner-Friendly'];

// Maps filter chips to matching logic
const HISTORICAL_CONTRACTS = new Set([
  '0xb47e3cd837dDF8e4c57F05d70Ab865de6e193BBB', // CryptoPunks
  '0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D', // BAYC
]);

function matchesFilter(nft: NFT, filter: FilterChip): boolean {
  if (filter === 'All') return true;
  if (filter === 'Historical') return HISTORICAL_CONTRACTS.has(nft.contractAddress);
  if (filter === 'High Utility') return (nft.utilityData?.perks?.length ?? 0) > 0;
  if (filter === 'High Risk') return nft.risk?.level === 'HIGH' || nft.risk?.level === 'MED';
  if (filter === 'Beginner-Friendly') return nft.risk?.level === 'LOW';
  return true;
}

export default function NFTGallery({ walletAddress, chain, onNFTSelect }: NFTGalleryProps) {
  const navigation = useNavigation<any>();
  const [selectedChain, setSelectedChain] = useState(chain || 'ethereum');
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<FilterChip>('All');

  const { data, loading, error, refetch } = useQuery<{ userNFTs: NFT[] }>(GET_USER_NFTS, {
    variables: { address: walletAddress || '', chain: selectedChain },
    skip: !walletAddress,
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  // Use real data when wallet connected, demo data otherwise
  const nfts = walletAddress
    ? (data?.userNFTs || [])
    : DEMO_NFTS.filter(nft => nft.chain === selectedChain);
  const collections = Array.from(new Set(nfts.map(nft => nft.collectionName)));

  const handleNFTPress = (nft: NFT) => {
    if (onNFTSelect) {
      onNFTSelect(nft);
    }
    // Always navigate to NFTDetail — passes full nft object as params
    navigation.navigate('nft-detail', { nft });
  };

  const handleJourneyPress = () => {
    navigation.navigate('nft-journey', {
      nfts: nfts.map(n => ({
        contractAddress: n.contractAddress,
        collectionName: n.collectionName,
        chain: n.chain,
      })),
    });
  };

  const filteredNFTs = nfts
    .filter(nft => !selectedCollection || nft.collectionName === selectedCollection)
    .filter(nft => matchesFilter(nft, activeFilter));

  if (loading) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color={C.primary} />
      </View>
    );
  }

  if (error) {
    return (
      <View style={styles.container}>
        <View style={[styles.card, { borderLeftColor: '#FF4444' }]}>
          <Icon name="alert-circle" size={20} color="#FF4444" />
          <Text style={[styles.errorText, { color: '#FF4444' }]}>
            Failed to load NFTs: {error.message}
          </Text>
          <TouchableOpacity onPress={() => refetch()} style={styles.retryButton}>
            <Text style={styles.retryText}>Retry</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  const riskConfig = {
    LOW: { color: '#065F46', bg: '#D1FAE5', icon: 'shield' as const },
    MED: { color: '#92400E', bg: '#FEF3C7', icon: 'alert-triangle' as const },
    HIGH: { color: '#991B1B', bg: '#FEE2E2', icon: 'alert-circle' as const },
  };

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={true}
        nestedScrollEnabled={true}
      >
      {/* Journey CTA */}
      <TouchableOpacity style={styles.journeyBanner} onPress={handleJourneyPress} activeOpacity={0.85}>
        <View style={styles.journeyLeft}>
          <Icon name="map" size={18} color="#7C3AED" />
          <View>
            <Text style={styles.journeyTitle}>Your NFT Journey</Text>
            <Text style={styles.journeySubtitle}>Lessons built from your collection</Text>
          </View>
        </View>
        <Icon name="chevron-right" size={16} color="#7C3AED" />
      </TouchableOpacity>

      {/* Filter Chips */}
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.filterRow}
        contentContainerStyle={{ gap: 8, paddingRight: 8 }}
      >
        {FILTER_CHIPS.map(chip => {
          const active = activeFilter === chip;
          const chipColors: Record<FilterChip, { bg: string; text: string; activeBg: string; activeText: string }> = {
            'All':                { bg: C.card, text: C.sub, activeBg: C.primary, activeText: C.text },
            'Historical':         { bg: C.card, text: C.sub, activeBg: '#7C3AED', activeText: '#FFFFFF' },
            'High Utility':       { bg: C.card, text: C.sub, activeBg: '#059669', activeText: '#FFFFFF' },
            'High Risk':          { bg: C.card, text: C.sub, activeBg: '#DC2626', activeText: '#FFFFFF' },
            'Beginner-Friendly':  { bg: C.card, text: C.sub, activeBg: '#2563EB', activeText: '#FFFFFF' },
          };
          const cc = chipColors[chip];
          return (
            <TouchableOpacity
              key={chip}
              style={[
                styles.filterChip,
                { backgroundColor: active ? cc.activeBg : cc.bg },
              ]}
              onPress={() => setActiveFilter(chip)}
              activeOpacity={0.75}
            >
              <Text style={[styles.filterChipText, { color: active ? cc.activeText : cc.text }]}>
                {chip === 'Historical' ? '🏛 ' : chip === 'High Utility' ? '🎁 ' : chip === 'High Risk' ? '⚠️ ' : chip === 'Beginner-Friendly' ? '🟢 ' : ''}
                {chip}
              </Text>
            </TouchableOpacity>
          );
        })}
      </ScrollView>

      {/* Chain Selector */}
      <View style={styles.chainSelector}>
        {['ethereum', 'polygon', 'arbitrum', 'optimism', 'base'].map(chainName => (
          <TouchableOpacity
            key={chainName}
            style={[
              styles.chainButton,
              { backgroundColor: selectedChain === chainName ? C.primary : C.card },
            ]}
            onPress={() => setSelectedChain(chainName)}
          >
            <Text
              style={[
                styles.chainText,
                { color: selectedChain === chainName ? C.text : C.sub },
              ]}
            >
              {chainName.charAt(0).toUpperCase() + chainName.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Collection Filter */}
      {collections.length > 0 && (
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.collectionFilter}>
          <TouchableOpacity
            style={[
              styles.collectionChip,
              { backgroundColor: !selectedCollection ? C.primary : C.card },
            ]}
            onPress={() => setSelectedCollection(null)}
          >
            <Text
              style={[
                styles.collectionChipText,
                { color: !selectedCollection ? C.text : C.sub },
              ]}
            >
              All
            </Text>
          </TouchableOpacity>
          {collections.map(collection => (
            <TouchableOpacity
              key={collection}
              style={[
                styles.collectionChip,
                { backgroundColor: selectedCollection === collection ? C.primary : C.card },
              ]}
              onPress={() => setSelectedCollection(collection)}
            >
              <Text
                style={[
                  styles.collectionChipText,
                  { color: selectedCollection === collection ? C.text : C.sub },
                ]}
              >
                {collection}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      )}

      {/* NFT Grid */}
      {filteredNFTs.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Icon name="image" size={64} color={C.sub} />
          <Text style={[styles.emptyText, { color: C.sub }]}>
            {walletAddress ? 'No NFTs found on this chain' : 'No demo NFTs on this chain'}
          </Text>
        </View>
      ) : (
        <View style={styles.grid}>
          {filteredNFTs.map(nft => {
            const riskLevel = (nft.risk?.level as keyof typeof riskConfig) || 'MED';
            const rc = riskConfig[riskLevel] || riskConfig.MED;
            return (
              <TouchableOpacity
                key={nft.id}
                style={styles.nftCard}
                onPress={() => handleNFTPress(nft)}
              >
                {/* Risk badge overlay */}
                <View style={[styles.riskOverlay, { backgroundColor: rc.bg }]}>
                  <Icon name={rc.icon} size={10} color={rc.color} />
                </View>
                {/* Learn pill overlay */}
                <View style={styles.learnOverlay}>
                  <Text style={styles.learnOverlayText}>✨ Learn</Text>
                </View>

                {nft.imageUrl ? (
                  <Image source={{ uri: nft.imageUrl }} style={styles.nftImage} />
                ) : (
                  <View style={[styles.nftImage, styles.placeholderImage]}>
                    <Icon name="image" size={32} color={C.sub} />
                  </View>
                )}
                <View style={styles.nftInfo}>
                  <Text style={[styles.nftName, { color: C.text }]} numberOfLines={1}>
                    {nft.name || `#${nft.tokenId}`}
                  </Text>
                  <Text style={[styles.collectionName, { color: C.sub }]} numberOfLines={1}>
                    {nft.collectionName}
                  </Text>
                  {nft.floorPrice && (
                    <Text style={[styles.price, { color: C.primary }]}>
                      Floor: {nft.floorPrice.toFixed(4)} ETH
                    </Text>
                  )}
                </View>
              </TouchableOpacity>
            );
          })}
        </View>
      )}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: C.bg,
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 16,
  },
  // Filter chips row
  filterRow: {
    marginBottom: 14,
  },
  filterChip: {
    paddingHorizontal: 13,
    paddingVertical: 7,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: C.border,
  },
  filterChipText: {
    fontSize: 12,
    fontWeight: '600',
  },

  chainSelector: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
  },
  chainButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: C.border,
  },
  chainText: {
    fontSize: 12,
    fontWeight: '600',
  },
  collectionFilter: {
    marginBottom: 16,
  },
  collectionChip: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
    borderWidth: 1,
    borderColor: C.border,
  },
  collectionChipText: {
    fontSize: 12,
    fontWeight: '500',
  },
  // Journey banner
  journeyBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#F5F3FF',
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: '#DDD6FE',
  },
  journeyLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  journeyTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#4C1D95',
  },
  journeySubtitle: {
    fontSize: 11,
    color: '#7C3AED',
    marginTop: 1,
  },

  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  nftCard: {
    width: (width - 48) / 2,
    backgroundColor: C.card,
    borderRadius: 12,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: C.border,
  },
  // Risk badge — top-left corner overlay
  riskOverlay: {
    position: 'absolute',
    top: 8,
    left: 8,
    zIndex: 10,
    width: 22,
    height: 22,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center',
  },
  // Learn pill — top-right corner overlay
  learnOverlay: {
    position: 'absolute',
    top: 8,
    right: 8,
    zIndex: 10,
    backgroundColor: 'rgba(124,58,237,0.85)',
    borderRadius: 8,
    paddingHorizontal: 6,
    paddingVertical: 3,
  },
  learnOverlayText: {
    fontSize: 9,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  nftImage: {
    width: '100%',
    height: (width - 48) / 2,
    backgroundColor: C.border,
  },
  placeholderImage: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  nftInfo: {
    padding: 12,
  },
  nftName: {
    fontSize: 14,
    fontWeight: '600',
    marginBottom: 4,
  },
  collectionName: {
    fontSize: 12,
    marginBottom: 4,
  },
  price: {
    fontSize: 11,
    fontWeight: '600',
  },
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 40,
  },
  emptyText: {
    fontSize: 14,
    marginTop: 16,
    textAlign: 'center',
  },
  card: {
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderLeftWidth: 4,
    alignItems: 'center',
    gap: 8,
  },
  errorText: {
    fontSize: 14,
    textAlign: 'center',
  },
  retryButton: {
    marginTop: 8,
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: C.primary,
    borderRadius: 6,
  },
  retryText: {
    color: C.text,
    fontSize: 13,
    fontWeight: '600',
  },
});

