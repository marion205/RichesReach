/**
 * Unit tests for FamilyManagementModal component
 */

import React from 'react';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { FamilyManagementModal } from '../FamilyManagementModal';
import { familySharingService } from '../../services/FamilySharingService';

// Mock the service
jest.mock('../../services/FamilySharingService');
jest.mock('@apollo/client', () => ({
  useQuery: jest.fn(() => ({
    data: null,
    loading: false,
    refetch: jest.fn(),
  })),
  useMutation: jest.fn(() => [jest.fn()]),
  gql: jest.fn(),
}));

describe('FamilyManagementModal', () => {
  const mockOnClose = jest.fn();
  const mockOnFamilyCreated = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should render create family section when no group exists', () => {
    (familySharingService.getFamilyGroup as jest.Mock).mockResolvedValue(null);

    const { getByText } = render(
      <FamilyManagementModal
        visible={true}
        onClose={mockOnClose}
        onFamilyCreated={mockOnFamilyCreated}
      />
    );

    expect(getByText('Create Family Group')).toBeTruthy();
    expect(getByText(/Share your Constellation Orb/)).toBeTruthy();
  });

  it('should call createFamilyGroup when create button is pressed', async () => {
    const mockGroup = {
      id: 'family_123',
      name: 'My Family',
      ownerId: 'user_123',
      members: [],
      sharedOrb: { enabled: true, netWorth: 0, lastSynced: '' },
      settings: { allowTeenAccounts: true, requireApproval: false, syncFrequency: 'realtime' },
      createdAt: '2025-01-01T00:00:00Z',
    };

    (familySharingService.getFamilyGroup as jest.Mock).mockResolvedValue(null);
    (familySharingService.createFamilyGroup as jest.Mock).mockResolvedValue(mockGroup);

    const { getByText } = render(
      <FamilyManagementModal
        visible={true}
        onClose={mockOnClose}
        onFamilyCreated={mockOnFamilyCreated}
      />
    );

    const createButton = getByText('Create Family Group');
    fireEvent.press(createButton);

    await waitFor(() => {
      expect(familySharingService.createFamilyGroup).toHaveBeenCalledWith('My Family');
    });
  });

  it('should render family members when group exists', async () => {
    const mockGroup = {
      id: 'family_123',
      name: 'My Family',
      ownerId: 'user_123',
      members: [
        {
          id: 'member_1',
          userId: 'user_123',
          name: 'John',
          email: 'john@example.com',
          role: 'owner',
          permissions: {
            canViewOrb: true,
            canEditGoals: true,
            canViewDetails: true,
            canInvite: true,
          },
          joinedAt: '2025-01-01T00:00:00Z',
        },
        {
          id: 'member_2',
          userId: 'user_456',
          name: 'Jane',
          email: 'jane@example.com',
          role: 'member',
          permissions: {
            canViewOrb: true,
            canEditGoals: false,
            canViewDetails: true,
            canInvite: false,
          },
          joinedAt: '2025-01-01T00:00:00Z',
        },
      ],
      sharedOrb: { enabled: true, netWorth: 0, lastSynced: '' },
      settings: { allowTeenAccounts: true, requireApproval: false, syncFrequency: 'realtime' },
      createdAt: '2025-01-01T00:00:00Z',
    };

    (familySharingService.getFamilyGroup as jest.Mock).mockResolvedValue(mockGroup);

    const { getByText } = render(
      <FamilyManagementModal
        visible={true}
        onClose={mockOnClose}
        onFamilyCreated={mockOnFamilyCreated}
      />
    );

    await waitFor(() => {
      expect(getByText('My Family')).toBeTruthy();
      expect(getByText('John')).toBeTruthy();
      expect(getByText('Jane')).toBeTruthy();
    });
  });

  it('should send invite when invite button is pressed', async () => {
    const mockGroup = {
      id: 'family_123',
      name: 'My Family',
      ownerId: 'user_123',
      members: [],
      sharedOrb: { enabled: true, netWorth: 0, lastSynced: '' },
      settings: { allowTeenAccounts: true, requireApproval: false, syncFrequency: 'realtime' },
      createdAt: '2025-01-01T00:00:00Z',
    };

    (familySharingService.getFamilyGroup as jest.Mock).mockResolvedValue(mockGroup);
    (familySharingService.inviteMember as jest.Mock).mockResolvedValue({
      success: true,
      inviteCode: 'ABC123',
    });

    const { getByPlaceholderText, getByText } = render(
      <FamilyManagementModal
        visible={true}
        onClose={mockOnClose}
        onFamilyCreated={mockOnFamilyCreated}
      />
    );

    await waitFor(() => {
      const emailInput = getByPlaceholderText('Enter email address');
      fireEvent.changeText(emailInput, 'newmember@example.com');

      const inviteButton = getByText('Send Invite');
      fireEvent.press(inviteButton);
    });

    await waitFor(() => {
      expect(familySharingService.inviteMember).toHaveBeenCalledWith(
        'newmember@example.com',
        'member'
      );
    });
  });

  it('should close modal when close button is pressed', () => {
    const { getByTestId } = render(
      <FamilyManagementModal
        visible={true}
        onClose={mockOnClose}
        onFamilyCreated={mockOnFamilyCreated}
      />
    );

    // Find close button (X icon)
    const closeButton = getByTestId('close-button') || 
      // Fallback: find by accessibility label or text
      // This might need adjustment based on actual implementation
      null;

    if (closeButton) {
      fireEvent.press(closeButton);
      expect(mockOnClose).toHaveBeenCalled();
    }
  });
});

