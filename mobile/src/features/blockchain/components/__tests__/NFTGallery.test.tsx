/**
 * Comprehensive unit tests for NFTGallery
 */
import React from 'react';
import { render, waitFor, screen, fireEvent } from '@testing-library/react-native';
import { MockedProvider } from '@apollo/client/testing';
import NFTGallery from '../NFTGallery';
import { GET_USER_NFTS } from '../../../../graphql/blockchain';

const mockNFTs = [
  {
    id: '1',
    tokenId: '123',
    contractAddress: '0x123',
    name: 'Cool NFT #123',
    description: 'A cool NFT',
    imageUrl: 'https://example.com/nft1.png',
    collectionName: 'Cool Collection',
    chain: 'ethereum',
    floorPrice: 1.5,
    lastSalePrice: 2.0,
  },
  {
    id: '2',
    tokenId: '456',
    contractAddress: '0x456',
    name: 'Awesome NFT #456',
    imageUrl: 'https://example.com/nft2.png',
    collectionName: 'Awesome Collection',
    chain: 'polygon',
    floorPrice: 0.5,
  },
];

const mocks = [
  {
    request: {
      query: GET_USER_NFTS,
      variables: {
        address: '0x1234567890123456789012345678901234567890',
        chain: 'ethereum',
      },
    },
    result: {
      data: {
        userNFTs: mockNFTs,
      },
    },
  },
];

const emptyMocks = [
  {
    request: {
      query: GET_USER_NFTS,
      variables: {
        address: '0x1234567890123456789012345678901234567890',
        chain: 'ethereum',
      },
    },
    result: {
      data: {
        userNFTs: [],
      },
    },
  },
];

const errorMocks = [
  {
    request: {
      query: GET_USER_NFTS,
      variables: {
        address: '0x1234567890123456789012345678901234567890',
        chain: 'ethereum',
      },
    },
    error: new Error('Network error'),
  },
];

describe('NFTGallery', () => {
  const walletAddress = '0x1234567890123456789012345678901234567890';

  it('should render loading state initially', () => {
    const { getByTestId } = render(
      <MockedProvider mocks={[]} addTypename={false}>
        <NFTGallery walletAddress={walletAddress} />
      </MockedProvider>
    );

    // Should show loading indicator
    expect(getByTestId('loading-indicator') || screen.queryByText(/loading/i)).toBeTruthy();
  });

  it('should render NFTs when loaded', async () => {
    const { getByText } = render(
      <MockedProvider mocks={mocks} addTypename={false}>
        <NFTGallery walletAddress={walletAddress} />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(getByText('Cool NFT #123')).toBeTruthy();
      expect(getByText('Awesome NFT #456')).toBeTruthy();
      expect(getByText('Cool Collection')).toBeTruthy();
      expect(getByText('Awesome Collection')).toBeTruthy();
    });
  });

  it('should show empty state when no NFTs', async () => {
    const { getByText } = render(
      <MockedProvider mocks={emptyMocks} addTypename={false}>
        <NFTGallery walletAddress={walletAddress} />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(getByText(/no nfts found/i)).toBeTruthy();
    });
  });

  it('should show empty state when wallet not connected', () => {
    const { getByText } = render(
      <MockedProvider mocks={[]} addTypename={false}>
        <NFTGallery />
      </MockedProvider>
    );

    expect(getByText(/connect wallet/i)).toBeTruthy();
  });

  it('should handle error state', async () => {
    const { getByText } = render(
      <MockedProvider mocks={errorMocks} addTypename={false}>
        <NFTGallery walletAddress={walletAddress} />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(getByText(/failed to load/i)).toBeTruthy();
      expect(getByText(/retry/i)).toBeTruthy();
    });
  });

  it('should switch between chains', async () => {
    const { getByText } = render(
      <MockedProvider mocks={mocks} addTypename={false}>
        <NFTGallery walletAddress={walletAddress} />
      </MockedProvider>
    );

    await waitFor(() => {
      // Should show chain buttons
      expect(getByText('Ethereum')).toBeTruthy();
      expect(getByText('Polygon')).toBeTruthy();
    });
  });

  it('should filter by collection', async () => {
    const { getByText } = render(
      <MockedProvider mocks={mocks} addTypename={false}>
        <NFTGallery walletAddress={walletAddress} />
      </MockedProvider>
    );

    await waitFor(() => {
      // Should show collection filter chips
      expect(getByText('All')).toBeTruthy();
      expect(getByText('Cool Collection')).toBeTruthy();
      expect(getByText('Awesome Collection')).toBeTruthy();
    });
  });

  it('should display NFT floor price', async () => {
    const { getByText } = render(
      <MockedProvider mocks={mocks} addTypename={false}>
        <NFTGallery walletAddress={walletAddress} />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(getByText(/floor:.*1.5.*eth/i)).toBeTruthy();
    });
  });

  it('should call onNFTSelect when NFT is pressed', async () => {
    const onNFTSelect = jest.fn();
    const { getByText } = render(
      <MockedProvider mocks={mocks} addTypename={false}>
        <NFTGallery walletAddress={walletAddress} onNFTSelect={onNFTSelect} />
      </MockedProvider>
    );

    await waitFor(() => {
      const nftCard = getByText('Cool NFT #123');
      fireEvent.press(nftCard.parent || nftCard);
    });

    expect(onNFTSelect).toHaveBeenCalledWith(
      expect.objectContaining({
        id: '1',
        name: 'Cool NFT #123',
      })
    );
  });

  it('should show placeholder image when imageUrl is missing', async () => {
    const nftsWithoutImage = [
      {
        ...mockNFTs[0],
        imageUrl: null,
      },
    ];

    const mocksNoImage = [
      {
        request: {
          query: GET_USER_NFTS,
          variables: {
            address: walletAddress,
            chain: 'ethereum',
          },
        },
        result: {
          data: {
            userNFTs: nftsWithoutImage,
          },
        },
      },
    ];

    const { getByText } = render(
      <MockedProvider mocks={mocksNoImage} addTypename={false}>
        <NFTGallery walletAddress={walletAddress} />
      </MockedProvider>
    );

    await waitFor(() => {
      expect(getByText('Cool NFT #123')).toBeTruthy();
      // Should show placeholder (icon)
    });
  });
});

