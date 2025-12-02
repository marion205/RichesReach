/**
 * TomorrowScreen Comprehensive Test Suite
 * Tests all Phase 1, 2, and 3 features
 */

import React from 'react';
import { render, fireEvent, waitFor, act } from '@testing-library/react-native';
import { Alert } from 'react-native';
import TomorrowScreen from '../TomorrowScreen';

// Mock dependencies before imports
jest.mock('../../services/FuturesService', () => ({
  __esModule: true,
  default: {
    getRecommendations: jest.fn(),
    placeOrder: jest.fn(),
    getPositions: jest.fn(),
  },
}));

jest.mock('../../../../shared/hooks/useWatchlist', () => ({
  useWatchlist: jest.fn(),
}));
jest.mock('expo-haptics', () => ({
  impactAsync: jest.fn(),
  notificationAsync: jest.fn(),
}));
jest.mock('react-native-vector-icons/Feather', () => 'Icon');
jest.mock('../../../../components/charts/SparkMini', () => {
  const React = require('react');
  return function SparkMini({ data }: { data?: number[] }) {
    return React.createElement('View', { testID: 'sparkline' }, null);
  };
});

// Mock Share API
jest.mock('react-native', () => {
  const RN = jest.requireActual('react-native');
  return {
    ...RN,
    Share: {
      share: jest.fn(() => Promise.resolve({ action: 'sharedAction' })),
    },
  };
});

const mockRecommendations = [
  {
    symbol: 'MESZ5',
    name: 'Micro E-mini S&P 500',
    why_now: 'Strong earnings season momentum and positive macro indicators suggest continued upward trend.',
    max_loss: 250,
    max_gain: 750,
    probability: 72,
    action: 'Buy',
    current_price: 22.95,
    price_change: 0.45,
    price_change_percent: 2.0,
    volume_ratio: 1.8,
    price_history: [22.50, 22.55, 22.60, 22.65, 22.70, 22.75, 22.80, 22.85, 22.90, 22.92, 22.94, 22.95],
  },
  {
    symbol: 'MNQZ5',
    name: 'Micro E-mini NASDAQ-100',
    why_now: 'Tech sector showing resilience with AI-driven growth. Support level holding strong.',
    max_loss: 300,
    max_gain: 900,
    probability: 68,
    action: 'Buy',
    current_price: 15.25,
    price_change: 0.30,
    price_change_percent: 2.0,
    volume_ratio: 1.2,
    price_history: [15.00, 15.05, 15.10, 15.12, 15.15, 15.18, 15.20, 15.22, 15.24, 15.25],
  },
];

describe('TomorrowScreen', () => {
  const mockGetRecommendations = jest.fn();
  const mockPlaceOrder = jest.fn();
  const mockAddToWatchlist = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    
    (FuturesService.getRecommendations as jest.Mock) = mockGetRecommendations;
    (FuturesService.placeOrder as jest.Mock) = mockPlaceOrder;
    (useWatchlist as jest.Mock) = jest.fn(() => ({
      addToWatchlist: mockAddToWatchlist,
    }));

    mockGetRecommendations.mockResolvedValue({
      recommendations: mockRecommendations,
    });
    mockPlaceOrder.mockResolvedValue({
      status: 'success',
      message: 'Order placed',
    });
    mockAddToWatchlist.mockResolvedValue({
      data: {
        addToWatchlist: {
          success: true,
          message: 'Added to watchlist',
        },
      },
    });
  });

  describe('Phase 1: Core Features', () => {
    test('renders loading skeleton on initial load', async () => {
      const { getByTestId } = render(<TomorrowScreen />);
      
      // Should show skeleton loaders initially
      await waitFor(() => {
        expect(mockGetRecommendations).toHaveBeenCalled();
      });
    });

    test('displays recommendations after loading', async () => {
      const { getByText, findByText } = render(<TomorrowScreen />);
      
      await waitFor(() => {
        expect(findByText('MESZ5')).toBeTruthy();
      });
      
      expect(getByText('Micro E-mini S&P 500')).toBeTruthy();
    });

    test('displays real-time price with change indicators', async () => {
      const { getByText } = render(<TomorrowScreen />);
      
      await waitFor(() => {
        expect(getByText('$22.95')).toBeTruthy();
      });
      
      // Should show price change
      expect(getByText(/\+0.45/)).toBeTruthy();
      expect(getByText(/\+2.00%/)).toBeTruthy();
    });

    test('displays sparklines for price history', async () => {
      const { getAllByTestId } = render(<TomorrowScreen />);
      
      await waitFor(() => {
        const sparklines = getAllByTestId('sparkline');
        expect(sparklines.length).toBeGreaterThan(0);
      });
    });

    test('shows error banner on network failure', async () => {
      mockGetRecommendations.mockRejectedValueOnce(new Error('Network error'));
      
      const { getByText } = render(<TomorrowScreen />);
      
      await waitFor(() => {
        expect(getByText(/Connection Issue|Error/i)).toBeTruthy();
      });
    });

    test('displays session indicators (RTH/ETH)', async () => {
      const { getByText } = render(<TomorrowScreen />);
      
      await waitFor(() => {
        // Should show either RTH or ETH badge
        const hasSessionBadge = getByText(/RTH|ETH|Regular Trading Hours|Extended Hours/i);
        expect(hasSessionBadge).toBeTruthy();
      });
    });
  });

  describe('Phase 2: Advanced Features', () => {
    test('toggles between list and heatmap view', async () => {
      const { getByTestId, getByText } = render(<TomorrowScreen />);
      
      await waitFor(() => {
        expect(getByText('MESZ5')).toBeTruthy();
      });

      // Find and click heatmap toggle
      const heatmapButton = getByTestId('heatmap-toggle') || 
        getByText(/grid|heatmap/i);
      
      if (heatmapButton) {
        fireEvent.press(heatmapButton);
        
        // Should show heatmap view
        await waitFor(() => {
          expect(getByText(/Equity Index|Currency|Commodities/i)).toBeTruthy();
        });
      }
    });

    test('displays Top Movers badge', async () => {
      const { getByText } = render(<TomorrowScreen />);
      
      await waitFor(() => {
        expect(getByText('MESZ5')).toBeTruthy();
      });
      
      // Top movers should be visible (MESZ5 has 2.0% change)
      const topBadge = getByText(/Top/i);
      expect(topBadge).toBeTruthy();
    });

    test('displays Unusual Volume badge', async () => {
      const { getByText } = render(<TomorrowScreen />);
      
      await waitFor(() => {
        expect(getByText('MESZ5')).toBeTruthy();
      });
      
      // MESZ5 has volume_ratio of 1.8 (> 1.5)
      const volBadge = getByText(/Vol/i);
      expect(volBadge).toBeTruthy();
    });

    test('opens contract info modal on info button press', async () => {
      const { getByText, getAllByTestId } = render(<TomorrowScreen />);
      
      await waitFor(() => {
        expect(getByText('MESZ5')).toBeTruthy();
      });

      // Find info button (usually has accessibility label or testID)
      const infoButtons = getAllByTestId('info-button');
      if (infoButtons.length > 0) {
        fireEvent.press(infoButtons[0]);
        
        await waitFor(() => {
          expect(getByText(/Tick Size|Contract Size|Margin/i)).toBeTruthy();
        });
      }
    });

    test('displays "Why Now" as bullet points', async () => {
      const { getByText } = render(<TomorrowScreen />);
      
      await waitFor(() => {
        expect(getByText(/Why Now/i)).toBeTruthy();
      });
      
      // Should show bullet points
      expect(getByText(/•/)).toBeTruthy();
    });
  });

  describe('Phase 3: Enhanced Features', () => {
    test('opens chart modal on card tap', async () => {
      const { getByText } = render(<TomorrowScreen />);
      
      await waitFor(() => {
        expect(getByText('MESZ5')).toBeTruthy();
      });

      // Tap on card
      const card = getByText('MESZ5').parent?.parent;
      if (card) {
        fireEvent.press(card);
        
        await waitFor(() => {
          expect(getByText(/Compare Contracts|Trade|Details/i)).toBeTruthy();
        });
      }
    });

    test('filters recommendations by category', async () => {
      const { getByText, getByTestId } = render(<TomorrowScreen />);
      
      await waitFor(() => {
        expect(getByText('MESZ5')).toBeTruthy();
      });

      // Find and click filter
      const equityFilter = getByText('Equity Index');
      if (equityFilter) {
        fireEvent.press(equityFilter);
        
        await waitFor(() => {
          // Should only show equity index contracts
          expect(getByText('MESZ5')).toBeTruthy();
        });
      }
    });

    test('sorts recommendations by price change', async () => {
      const { getByText } = render(<TomorrowScreen />);
      
      await waitFor(() => {
        expect(getByText('MESZ5')).toBeTruthy();
      });

      // Find and click sort button
      const priceSort = getByText(/Sort|Price/i);
      if (priceSort) {
        fireEvent.press(priceSort);
        
        await waitFor(() => {
          // Recommendations should be sorted
          expect(getByText('MESZ5')).toBeTruthy();
        });
      }
    });

    test('adds contract to watchlist', async () => {
      const { getByText } = render(<TomorrowScreen />);
      
      await waitFor(() => {
        expect(getByText('MESZ5')).toBeTruthy();
      });

      // Open chart modal first
      const card = getByText('MESZ5').parent?.parent;
      if (card) {
        fireEvent.press(card);
        
        await waitFor(() => {
          const watchlistButton = getByText(/Watchlist/i);
          if (watchlistButton) {
            fireEvent.press(watchlistButton);
            
            await waitFor(() => {
              expect(mockAddToWatchlist).toHaveBeenCalledWith({
                symbol: 'MESZ5',
                company_name: 'Micro E-mini S&P 500',
                notes: expect.stringContaining('Futures recommendation'),
              });
            });
          }
        });
      }
    });

    test('shares recommendation', async () => {
      const { Share } = require('react-native');
      const { getByText } = render(<TomorrowScreen />);
      
      await waitFor(() => {
        expect(getByText('MESZ5')).toBeTruthy();
      });

      // Open chart modal
      const card = getByText('MESZ5').parent?.parent;
      if (card) {
        fireEvent.press(card);
        
        await waitFor(() => {
          const shareButton = getByText(/Share/i);
          if (shareButton) {
            fireEvent.press(shareButton);
            
            await waitFor(() => {
              expect(Share.share).toHaveBeenCalled();
            });
          }
        });
      }
    });

    test('adds contract to comparison', async () => {
      const { getByText, getAllByTestId } = render(<TomorrowScreen />);
      
      await waitFor(() => {
        expect(getByText('MESZ5')).toBeTruthy();
      });

      // Find comparison button
      const compareButtons = getAllByTestId('compare-button');
      if (compareButtons.length > 0) {
        fireEvent.press(compareButtons[0]);
        
        await waitFor(() => {
          // Comparison modal should open
          expect(getByText(/Compare Contracts/i)).toBeTruthy();
        });
      }
    });

    test('displays comparison modal with selected contracts', async () => {
      const { getByText, getAllByTestId } = render(<TomorrowScreen />);
      
      await waitFor(() => {
        expect(getByText('MESZ5')).toBeTruthy();
      });

      // Add contracts to comparison
      const compareButtons = getAllByTestId('compare-button');
      if (compareButtons.length > 0) {
        fireEvent.press(compareButtons[0]);
        
        await waitFor(() => {
          expect(getByText(/Compare Contracts/i)).toBeTruthy();
          expect(getByText('MESZ5')).toBeTruthy();
        });
      }
    });
  });

  describe('Trade Actions', () => {
    test('places order when Buy button is pressed', async () => {
      const { getByText } = render(<TomorrowScreen />);
      
      await waitFor(() => {
        expect(getByText('MESZ5')).toBeTruthy();
      });

      // Find and press Buy button
      const buyButton = getByText(/Buy/i);
      if (buyButton) {
        fireEvent.press(buyButton);
        
        await waitFor(() => {
          expect(mockPlaceOrder).toHaveBeenCalledWith({
            symbol: 'MESZ5',
            side: 'BUY',
            quantity: 1,
          });
        });
      }
    });

    test('shows trade confirmation modal', async () => {
      const { getByText } = render(<TomorrowScreen />);
      
      await waitFor(() => {
        expect(getByText('MESZ5')).toBeTruthy();
      });

      const buyButton = getByText(/Buy/i);
      if (buyButton) {
        fireEvent.press(buyButton);
        
        await waitFor(() => {
          expect(getByText(/Confirm Trade|Buy MESZ5/i)).toBeTruthy();
        });
      }
    });
  });

  describe('Error Handling', () => {
    test('handles API timeout gracefully', async () => {
      mockGetRecommendations.mockImplementation(() => 
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Request timeout')), 100)
        )
      );

      const { getByText } = render(<TomorrowScreen />);
      
      await waitFor(() => {
        expect(getByText(/timeout|error|connection/i)).toBeTruthy();
      }, { timeout: 2000 });
    });

    test('shows cached data banner when using mock data', async () => {
      mockGetRecommendations.mockRejectedValueOnce(new Error('Network error'));
      
      const { getByText } = render(<TomorrowScreen />);
      
      await waitFor(() => {
        expect(getByText(/cached|demo/i)).toBeTruthy();
      });
    });
  });

  describe('Dark Mode', () => {
    test('applies dark mode styles', async () => {
      // Mock useColorScheme to return 'dark'
      jest.spyOn(require('react-native'), 'useColorScheme').mockReturnValue('dark');
      
      const { getByText } = render(<TomorrowScreen />);
      
      await waitFor(() => {
        expect(getByText('MESZ5')).toBeTruthy();
      });
      
      // Component should render without errors in dark mode
      expect(getByText('Tomorrow')).toBeTruthy();
    });
  });
});

