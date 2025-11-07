/**
 * Unit tests for FamilySharingService
 */

import { familySharingService, FamilyGroup, FamilyMember } from '../FamilySharingService';

// Mock fetch
global.fetch = jest.fn();

describe('FamilySharingService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock AsyncStorage
    require('@react-native-async-storage/async-storage').default.getItem = jest.fn(
      (key: string) => Promise.resolve(key === 'token' ? 'test-token' : null)
    );
  });

  describe('getFamilyGroup', () => {
    it('should fetch family group successfully', async () => {
      const mockGroup: FamilyGroup = {
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
        ],
        sharedOrb: {
          enabled: true,
          netWorth: 100000,
          lastSynced: '2025-01-01T00:00:00Z',
        },
        settings: {
          allowTeenAccounts: true,
          requireApproval: false,
          syncFrequency: 'realtime',
        },
        createdAt: '2025-01-01T00:00:00Z',
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockGroup,
      });

      const result = await familySharingService.getFamilyGroup();

      expect(result).toEqual(mockGroup);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/family/group'),
        expect.objectContaining({
          method: 'GET',
          headers: expect.objectContaining({
            'Authorization': 'Bearer test-token',
          }),
        })
      );
    });

    it('should return null if no family group exists', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

      const result = await familySharingService.getFamilyGroup();

      expect(result).toBeNull();
    });

    it('should handle errors gracefully', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      const result = await familySharingService.getFamilyGroup();

      expect(result).toBeNull();
    });
  });

  describe('createFamilyGroup', () => {
    it('should create family group successfully', async () => {
      const mockGroup: FamilyGroup = {
        id: 'family_123',
        name: 'My Family',
        ownerId: 'user_123',
        members: [],
        sharedOrb: {
          enabled: true,
          netWorth: 0,
          lastSynced: '2025-01-01T00:00:00Z',
        },
        settings: {
          allowTeenAccounts: true,
          requireApproval: false,
          syncFrequency: 'realtime',
        },
        createdAt: '2025-01-01T00:00:00Z',
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockGroup,
      });

      const result = await familySharingService.createFamilyGroup('My Family');

      expect(result).toEqual(mockGroup);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/family/group'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ name: 'My Family' }),
        })
      );
    });

    it('should throw error on failure', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

      await expect(
        familySharingService.createFamilyGroup('My Family')
      ).rejects.toThrow();
    });
  });

  describe('inviteMember', () => {
    it('should send invite successfully', async () => {
      const mockResponse = {
        success: true,
        inviteCode: 'ABC123XYZ',
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const result = await familySharingService.inviteMember('member@example.com', 'member');

      expect(result).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/family/invite'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            email: 'member@example.com',
            role: 'member',
          }),
        })
      );
    });

    it('should default to member role', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, inviteCode: 'CODE' }),
      });

      await familySharingService.inviteMember('member@example.com');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          body: JSON.stringify({
            email: 'member@example.com',
            role: 'member',
          }),
        })
      );
    });
  });

  describe('acceptInvite', () => {
    it('should accept invite successfully', async () => {
      const mockGroup: FamilyGroup = {
        id: 'family_123',
        name: 'My Family',
        ownerId: 'user_123',
        members: [],
        sharedOrb: { enabled: true, netWorth: 0, lastSynced: '' },
        settings: { allowTeenAccounts: true, requireApproval: false, syncFrequency: 'realtime' },
        createdAt: '2025-01-01T00:00:00Z',
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockGroup,
      });

      const result = await familySharingService.acceptInvite('ABC123XYZ');

      expect(result).toEqual(mockGroup);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/family/invite/accept'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ inviteCode: 'ABC123XYZ' }),
        })
      );
    });
  });

  describe('updateMemberPermissions', () => {
    it('should update permissions successfully', async () => {
      const mockMember: FamilyMember = {
        id: 'member_1',
        userId: 'user_456',
        name: 'Jane',
        email: 'jane@example.com',
        role: 'teen',
        permissions: {
          canViewOrb: true,
          canEditGoals: false,
          canViewDetails: true,
          canInvite: false,
          spendingLimit: 100,
        },
        joinedAt: '2025-01-01T00:00:00Z',
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockMember,
      });

      const result = await familySharingService.updateMemberPermissions('member_1', {
        spendingLimit: 100,
      });

      expect(result).toEqual(mockMember);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/family/members/member_1/permissions'),
        expect.objectContaining({
          method: 'PATCH',
          body: JSON.stringify({
            permissions: { spendingLimit: 100 },
          }),
        })
      );
    });
  });

  describe('syncOrbState', () => {
    it('should sync orb state without throwing', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
      });

      await expect(
        familySharingService.syncOrbState({
          netWorth: 100000,
          gesture: 'tap',
        })
      ).resolves.not.toThrow();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/family/orb/sync'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            netWorth: 100000,
            gesture: 'tap',
          }),
        })
      );
    });

    it('should handle sync failures gracefully', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      await expect(
        familySharingService.syncOrbState({ netWorth: 100000 })
      ).resolves.not.toThrow();
    });
  });

  describe('getOrbSyncEvents', () => {
    it('should fetch sync events successfully', async () => {
      const mockEvents = [
        {
          type: 'gesture',
          userId: 'user_123',
          userName: 'John',
          timestamp: '2025-01-01T00:00:00Z',
          data: { gesture: 'tap' },
        },
      ];

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => mockEvents,
      });

      const result = await familySharingService.getOrbSyncEvents();

      expect(result).toEqual(mockEvents);
    });

    it('should include since parameter if provided', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      });

      await familySharingService.getOrbSyncEvents('2025-01-01T00:00:00Z');

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('?since=2025-01-01T00:00:00Z'),
        expect.any(Object)
      );
    });

    it('should return empty array on error', async () => {
      (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('Network error'));

      const result = await familySharingService.getOrbSyncEvents();

      expect(result).toEqual([]);
    });
  });

  describe('removeMember', () => {
    it('should remove member successfully', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
      });

      await expect(
        familySharingService.removeMember('member_1')
      ).resolves.not.toThrow();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/family/members/member_1'),
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });
  });

  describe('leaveFamilyGroup', () => {
    it('should leave family group successfully', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
      });

      await expect(
        familySharingService.leaveFamilyGroup()
      ).resolves.not.toThrow();

      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/family/group/leave'),
        expect.objectContaining({
          method: 'POST',
        })
      );
    });
  });
});

