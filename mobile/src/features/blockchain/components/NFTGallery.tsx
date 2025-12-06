import React, { useState, useEffect } from 'react';
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
    }
  }
`;

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

export default function NFTGallery({ walletAddress, chain, onNFTSelect }: NFTGalleryProps) {
  const [selectedChain, setSelectedChain] = useState(chain || 'ethereum');
  const [selectedCollection, setSelectedCollection] = useState<string | null>(null);

  const { data, loading, error, refetch } = useQuery<{ userNFTs: NFT[] }>(GET_USER_NFTS, {
    variables: { address: walletAddress || '', chain: selectedChain },
    skip: !walletAddress,
    fetchPolicy: 'cache-and-network',
    errorPolicy: 'all',
  });

  const nfts = data?.userNFTs || [];
  const collections = Array.from(new Set(nfts.map(nft => nft.collectionName)));

  const filteredNFTs = selectedCollection
    ? nfts.filter(nft => nft.collectionName === selectedCollection)
    : nfts;

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

  return (
    <View style={styles.container}>
      <ScrollView 
        style={styles.scrollView}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={true}
        nestedScrollEnabled={true}
      >
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
            {walletAddress ? 'No NFTs found' : 'Connect wallet to view NFTs'}
          </Text>
        </View>
      ) : (
        <View style={styles.grid}>
          {filteredNFTs.map(nft => (
            <TouchableOpacity
              key={nft.id}
              style={styles.nftCard}
              onPress={() => onNFTSelect?.(nft)}
            >
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
          ))}
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

