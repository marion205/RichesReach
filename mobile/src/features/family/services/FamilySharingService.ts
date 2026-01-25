/**
 * Family Sharing Service
 * Manages multi-user orb sharing, invites, and parental controls
 */

import { API_HTTP } from '../../../config/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import logger from '../../../utils/logger';

export interface FamilyMember {
  id: string;
  userId: string;
  name: string;
  email: string;
  role: 'owner' | 'member' | 'teen';
  avatar?: string;
  permissions: {
    canViewOrb: boolean;
    canEditGoals: boolean;
    canViewDetails: boolean;
    canInvite: boolean;
    spendingLimit?: number;
  };
  joinedAt: string;
  lastActive?: string;
}

export interface FamilyGroup {
  id: string;
  name: string;
  ownerId: string;
  members: FamilyMember[];
  sharedOrb: {
    enabled: boolean;
    netWorth: number;
    lastSynced: string;
  };
  settings: {
    allowTeenAccounts: boolean;
    requireApproval: boolean;
    syncFrequency: 'realtime' | 'hourly' | 'daily';
  };
  createdAt: string;
}

export interface OrbSyncEvent {
  type: 'gesture' | 'update' | 'view';
  userId: string;
  userName: string;
  timestamp: string;
  data?: any;
}

class FamilySharingService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = `${API_HTTP}/api/family`;
  }

  private async getAuthHeaders(): Promise<Record<string, string>> {
    const token = await AsyncStorage.getItem('token') || await AsyncStorage.getItem('authToken');
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  /**
   * Get current user's family group
   */
  async getFamilyGroup(): Promise<FamilyGroup | null> {
    try {
      const headers = await this.getAuthHeaders();
      
      // Add timeout to prevent hanging requests
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
      
      try {
        const response = await fetch(`${this.baseUrl}/group`, {
          method: 'GET',
          headers,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          if (response.status === 404) {
            // User not in a family group - this is normal, not an error
            return null;
          }
          // For 500 errors, log but don't throw - allow app to continue
          if (response.status === 500) {
            const errorText = await response.text().catch(() => 'Unknown error');
            logger.warn('[FamilySharing] Server error fetching family group (500):', errorText);
            // Return null to allow app to continue - user just doesn't have a family group
            return null;
          }
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
      } catch (fetchError: any) {
        clearTimeout(timeoutId);
        if (fetchError.name === 'AbortError') {
          logger.warn('[FamilySharing] Request timed out, returning null');
          return null; // Return null instead of throwing for timeout
        }
        // For other fetch errors, log but return null to allow app to continue
        logger.warn('[FamilySharing] Fetch error (non-critical):', fetchError.message || fetchError);
        return null;
      }
    } catch (error: any) {
      // Log but don't throw - return null to allow app to continue
      logger.warn('[FamilySharing] Error fetching family group (non-critical):', error.message || error);
      return null;
    }
  }

  /**
   * Create a new family group
   */
  async createFamilyGroup(name: string): Promise<FamilyGroup> {
    try {
      const headers = await this.getAuthHeaders();
      
      // Add timeout to prevent hanging requests
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout
      
      try {
        const response = await fetch(`${this.baseUrl}/group`, {
          method: 'POST',
          headers,
          body: JSON.stringify({ name }),
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorText = await response.text();
          let errorMessage = `HTTP error! status: ${response.status}`;
          try {
            const errorJson = JSON.parse(errorText);
            errorMessage = errorJson.detail || errorJson.message || errorMessage;
          } catch {
            errorMessage = errorText || errorMessage;
          }
          throw new Error(errorMessage);
        }

        return await response.json();
      } catch (fetchError: any) {
        clearTimeout(timeoutId);
        if (fetchError.name === 'AbortError') {
          throw new Error('Request timed out. Please check:\n- Backend server is running\n- Network connection is active\n- API endpoint is accessible');
        }
        throw fetchError;
      }
    } catch (error) {
      logger.error('[FamilySharing] Failed to create family group:', error);
      throw error;
    }
  }

  /**
   * Invite a family member
   */
  async inviteMember(email: string, role: 'member' | 'teen' = 'member'): Promise<{ success: boolean; inviteCode: string }> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${this.baseUrl}/invite`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ email, role }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      logger.error('[FamilySharing] Failed to invite member:', error);
      throw error;
    }
  }

  /**
   * Accept an invite
   */
  async acceptInvite(inviteCode: string): Promise<FamilyGroup> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${this.baseUrl}/invite/accept`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ inviteCode }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      logger.error('[FamilySharing] Failed to accept invite:', error);
      throw error;
    }
  }

  /**
   * Update member permissions (for parental controls)
   */
  async updateMemberPermissions(
    memberId: string,
    permissions: Partial<FamilyMember['permissions']>
  ): Promise<FamilyMember> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${this.baseUrl}/members/${memberId}/permissions`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify({ permissions }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      logger.error('[FamilySharing] Failed to update permissions:', error);
      throw error;
    }
  }

  /**
   * Sync orb state across family members
   */
  async syncOrbState(state: {
    netWorth: number;
    gesture?: string;
    viewMode?: string;
  }): Promise<void> {
    try {
      const headers = await this.getAuthHeaders();
      await fetch(`${this.baseUrl}/orb/sync`, {
        method: 'POST',
        headers,
        body: JSON.stringify(state),
      });
    } catch (error) {
      logger.warn('[FamilySharing] Failed to sync orb state:', error);
      // Don't throw - sync failures shouldn't break the app
    }
  }

  /**
   * Get real-time orb sync events (for WebSocket)
   */
  async getOrbSyncEvents(since?: string): Promise<OrbSyncEvent[]> {
    try {
      const headers = await this.getAuthHeaders();
      const url = `${this.baseUrl}/orb/events${since ? `?since=${since}` : ''}`;
      const response = await fetch(url, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      logger.error('[FamilySharing] Failed to fetch sync events:', error);
      return [];
    }
  }

  /**
   * Remove a family member
   */
  async removeMember(memberId: string): Promise<void> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${this.baseUrl}/members/${memberId}`, {
        method: 'DELETE',
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      logger.error('[FamilySharing] Failed to remove member:', error);
      throw error;
    }
  }

  /**
   * Leave family group
   */
  async leaveFamilyGroup(): Promise<void> {
    try {
      const headers = await this.getAuthHeaders();
      const response = await fetch(`${this.baseUrl}/group/leave`, {
        method: 'POST',
        headers,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      logger.error('[FamilySharing] Failed to leave family group:', error);
      throw error;
    }
  }
}

// Export singleton instance
export const familySharingService = new FamilySharingService();
export default familySharingService;

