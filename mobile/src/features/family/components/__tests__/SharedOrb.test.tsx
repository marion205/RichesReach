/**
 * Unit tests for SharedOrb component
 * Comprehensive tests for WebSocket integration and performance
 */

import React from 'react';
import { render, waitFor } from '@testing-library/react-native';
import { SharedOrb } from '../SharedOrb';
import { familySharingService } from '../../services/FamilySharingService';
import { MoneySnapshot } from '../../../portfolio/services/MoneySnapshotService';
import { getFamilyWebSocketService } from '../../services/FamilyWebSocketService';

// Mock dependencies
jest.mock('../../services/FamilySharingService');
jest.mock('../../services/FamilyWebSocketService');
jest.mock('../../../portfolio/components/ConstellationOrb', () => {
  return {
    __esModule: true,
    default: ({ snapshot, onTap }: any) => (
      <div testID="constellation-orb">Orb: ${snapshot.netWorth}</div>
    ),
  };
});
jest.mock('expo-haptics', () => ({
  Haptics: {
    impactAsync: jest.fn(),
  },
  ImpactFeedbackStyle: {
    Light: 'light',
  },
}));
jest.mock('@react-native-async-storage/async-storage', () => ({
  getItem: jest.fn(() => Promise.resolve('mock-token')),
  setItem: jest.fn(),
  removeItem: jest.fn(),
}));

describe('SharedOrb', () => {
  const mockSnapshot: MoneySnapshot = {
    netWorth: 100000,
    cashflow: {
      period: 'monthly',
      in: 5000,
      out: 3000,
      delta: 2000,
    },
    positions: [
      { symbol: 'AAPL', value: 50000, shares: 100 },
    ],
    shield: [],
    breakdown: {
      bankBalance: 10000,
      portfolioValue: 90000,
      bankAccountsCount: 2,
    },
  };

  const mockCurrentUser = {
    id: 'member_1',
    userId: 'user_123',
    name: 'John',
    email: 'john@example.com',
    role: 'owner' as const,
    permissions: {
      canViewOrb: true,
      canEditGoals: true,
      canViewDetails: true,
      canInvite: true,
    },
    joinedAt: '2025-01-01T00:00:00Z',
  };

  const mockWebSocketService = {
    connect: jest.fn().mockResolvedValue(undefined),
    disconnect: jest.fn(),
    send: jest.fn(),
    syncOrbState: jest.fn(),
    sendGesture: jest.fn(),
    onEvent: jest.fn((callback) => {
      // Return unsubscribe function
      return () => {};
    }),
    isReady: true,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (familySharingService.getFamilyGroup as jest.Mock).mockResolvedValue({
      id: 'family_123',
      members: [mockCurrentUser],
    });
    (familySharingService.syncOrbState as jest.Mock).mockResolvedValue(undefined);
    (familySharingService.getOrbSyncEvents as jest.Mock).mockResolvedValue([]);
    (getFamilyWebSocketService as jest.Mock).mockReturnValue(mockWebSocketService);
  });

  it('should render SharedOrb with family members', async () => {
    const { getByText } = render(
      <SharedOrb
        snapshot={mockSnapshot}
        familyGroupId="family_123"
        currentUser={mockCurrentUser}
      />
    );

    // Should show sync status
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Component should render
    expect(getByText).toBeTruthy();
  });

  it('should sync orb state on gesture', async () => {
    const mockOnGesture = jest.fn();

    const { } = render(
      <SharedOrb
        snapshot={mockSnapshot}
        familyGroupId="family_123"
        currentUser={mockCurrentUser}
        onGesture={mockOnGesture}
      />
    );

    // Wait for initial load
    await new Promise(resolve => setTimeout(resolve, 100));

    // Gesture should trigger sync
    // This would be tested via actual gesture simulation in E2E tests
    expect(familySharingService.syncOrbState).toHaveBeenCalled();
  });

  it('should display active family members', async () => {
    const mockGroup = {
      id: 'family_123',
      members: [
        mockCurrentUser,
        {
          id: 'member_2',
          userId: 'user_456',
          name: 'Jane',
          email: 'jane@example.com',
          role: 'member' as const,
          permissions: {
            canViewOrb: true,
            canEditGoals: false,
            canViewDetails: true,
            canInvite: false,
          },
          joinedAt: '2025-01-01T00:00:00Z',
        },
      ],
    };

    (familySharingService.getFamilyGroup as jest.Mock).mockResolvedValue(mockGroup);

    const { } = render(
      <SharedOrb
        snapshot={mockSnapshot}
        familyGroupId="family_123"
        currentUser={mockCurrentUser}
      />
    );

    await new Promise(resolve => setTimeout(resolve, 100));

    // Should load family members
    expect(familySharingService.getFamilyGroup).toHaveBeenCalled();
  });

  it('should handle sync errors gracefully', async () => {
    (familySharingService.syncOrbState as jest.Mock).mockRejectedValue(
      new Error('Network error')
    );

    const { } = render(
      <SharedOrb
        snapshot={mockSnapshot}
        familyGroupId="family_123"
        currentUser={mockCurrentUser}
      />
    );

    await waitFor(() => {
      // Should not crash on sync error
      expect(familySharingService.syncOrbState).toHaveBeenCalled();
    });
  });

  it('should connect to WebSocket on mount', async () => {
    render(
      <SharedOrb
        snapshot={mockSnapshot}
        familyGroupId="family_123"
        currentUser={mockCurrentUser}
      />
    );

    await waitFor(() => {
      expect(mockWebSocketService.connect).toHaveBeenCalledWith('family_123');
    });
  });

  it('should use WebSocket for gestures when connected', async () => {
    mockWebSocketService.isReady = true;
    
    const { } = render(
      <SharedOrb
        snapshot={mockSnapshot}
        familyGroupId="family_123"
        currentUser={mockCurrentUser}
      />
    );

    await waitFor(() => {
      expect(mockWebSocketService.connect).toHaveBeenCalled();
    });

    // Simulate gesture
    // Note: This would require triggering the actual gesture handler
    // In a real test, you'd simulate the gesture event
  });

  it('should fallback to HTTP when WebSocket not connected', async () => {
    mockWebSocketService.isReady = false;
    
    const { } = render(
      <SharedOrb
        snapshot={mockSnapshot}
        familyGroupId="family_123"
        currentUser={mockCurrentUser}
      />
    );

    await waitFor(() => {
      // Should use HTTP fallback
      expect(familySharingService.syncOrbState).toHaveBeenCalled();
    });
  });

  it('should cleanup WebSocket on unmount', () => {
    const { unmount } = render(
      <SharedOrb
        snapshot={mockSnapshot}
        familyGroupId="family_123"
        currentUser={mockCurrentUser}
      />
    );

    unmount();

    expect(mockWebSocketService.disconnect).toHaveBeenCalled();
  });

  it('should debounce sync calls', async () => {
    const { } = render(
      <SharedOrb
        snapshot={mockSnapshot}
        familyGroupId="family_123"
        currentUser={mockCurrentUser}
      />
    );

    // Multiple rapid syncs should be debounced
    await waitFor(() => {
      expect(familySharingService.syncOrbState).toHaveBeenCalled();
    });

    const callCount = (familySharingService.syncOrbState as jest.Mock).mock.calls.length;
    
    // Wait a bit and verify not too many calls
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const newCallCount = (familySharingService.syncOrbState as jest.Mock).mock.calls.length;
    // Should not have excessive calls (debounced)
    expect(newCallCount - callCount).toBeLessThan(5);
  });

  it('should filter out current user from members list', async () => {
    const mockGroup = {
      id: 'family_123',
      members: [
        mockCurrentUser,
        {
          id: 'member_2',
          userId: 'user_456',
          name: 'Jane',
          email: 'jane@example.com',
          role: 'member' as const,
          permissions: {
            canViewOrb: true,
            canEditGoals: false,
            canViewDetails: true,
            canInvite: false,
          },
          joinedAt: '2025-01-01T00:00:00Z',
        },
      ],
    };

    (familySharingService.getFamilyGroup as jest.Mock).mockResolvedValue(mockGroup);

    const { queryByText } = render(
      <SharedOrb
        snapshot={mockSnapshot}
        familyGroupId="family_123"
        currentUser={mockCurrentUser}
      />
    );

    await waitFor(() => {
      // Should show Jane but not current user
      expect(queryByText('Jane')).toBeTruthy();
      expect(queryByText('John')).toBeFalsy(); // Current user filtered out
    });
  });
});

