/**
 * Family Management Modal
 * Create family groups, invite members, manage permissions
 */

import React, { useState, useEffect } from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  TextInput,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import Icon from 'react-native-vector-icons/Feather';
import { familySharingService, FamilyGroup, FamilyMember } from '../services/FamilySharingService';

interface FamilyManagementModalProps {
  visible: boolean;
  onClose: () => void;
  onFamilyCreated?: (group: FamilyGroup) => void;
}

export const FamilyManagementModal: React.FC<FamilyManagementModalProps> = ({
  visible,
  onClose,
  onFamilyCreated,
}) => {
  const [familyGroup, setFamilyGroup] = useState<FamilyGroup | null>(null);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState<'member' | 'teen'>('member');
  const [loading, setLoading] = useState(false);
  const [inviteCode, setInviteCode] = useState('');

  useEffect(() => {
    if (visible) {
      loadFamilyGroup();
    }
  }, [visible]);

  const loadFamilyGroup = async () => {
    try {
      setLoading(true);
      const group = await familySharingService.getFamilyGroup();
      setFamilyGroup(group);
      // If group was loaded and we have a callback, notify
      if (group && onFamilyCreated) {
        onFamilyCreated(group);
      }
    } catch (error: any) {
      console.error('[FamilyManagement] Failed to load group:', error);
      // Don't show alert for network timeouts or 404s (no group exists yet)
      // Only show alert for unexpected errors
      if (error?.message && 
          !error.message.includes('timed out') && 
          !error.message.includes('404') &&
          !error.message.includes('No family group found')) {
        Alert.alert(
          'Connection Error',
          `Unable to connect to server: ${error.message}\n\nPlease check:\n- Backend server is running\n- Network connection is active`,
          [{ text: 'OK' }]
        );
      }
    } finally {
      setLoading(false);
    }
  };

  const createFamilyGroup = async () => {
    try {
      setLoading(true);
      const group = await familySharingService.createFamilyGroup('My Family');
      setFamilyGroup(group);
      if (onFamilyCreated) {
        onFamilyCreated(group);
      }
      Alert.alert('Success', 'Family group created! Invite members to share your orb.');
    } catch (error: any) {
      console.error('[FamilyManagement] Create family group error:', error);
      const errorMessage = (error?.message || 'Unknown error occurred').toLowerCase();
      
      // If user already has a family group, load it instead of showing error
      // Check for various forms of this error message
      if (errorMessage.includes('already has a family group') || 
          errorMessage.includes('user already has') ||
          errorMessage.includes('already has') && errorMessage.includes('family')) {
        console.log('[FamilyManagement] User already has a family group, loading it...');
        // Try to load the existing group
        try {
          const existingGroup = await familySharingService.getFamilyGroup();
          if (existingGroup) {
            setFamilyGroup(existingGroup);
            if (onFamilyCreated) {
              onFamilyCreated(existingGroup);
            }
            Alert.alert(
              'Family Group Found',
              'You already have a family group. It has been loaded.',
              [{ text: 'OK' }]
            );
            return;
          }
        } catch (loadError) {
          console.error('[FamilyManagement] Failed to load existing group:', loadError);
          // Fall through to show error
        }
      }
      
      // Show error for other cases
      Alert.alert(
        'Error', 
        `Failed to create family group: ${errorMessage}\n\nPlease check:\n- Backend server is running\n- You are logged in\n- Network connection is active`,
        [{ text: 'OK' }]
      );
    } finally {
      setLoading(false);
    }
  };

  const sendInvite = async () => {
    if (!inviteEmail.trim()) {
      Alert.alert('Error', 'Please enter an email address');
      return;
    }

    try {
      setLoading(true);
      const result = await familySharingService.inviteMember(inviteEmail, inviteRole);
      setInviteCode(result.inviteCode);
      setInviteEmail('');
      Alert.alert(
        'Invite Sent!',
        `Invite code: ${result.inviteCode}\n\nShare this code with ${inviteEmail}`,
        [{ text: 'OK' }]
      );
      await loadFamilyGroup();
    } catch (error) {
      Alert.alert('Error', 'Failed to send invite. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const updatePermissions = async (memberId: string, permissions: Partial<FamilyMember['permissions']>) => {
    try {
      setLoading(true);
      await familySharingService.updateMemberPermissions(memberId, permissions);
      await loadFamilyGroup();
      Alert.alert('Success', 'Permissions updated');
    } catch (error) {
      Alert.alert('Error', 'Failed to update permissions');
    } finally {
      setLoading(false);
    }
  };

  const removeMember = async (memberId: string) => {
    Alert.alert(
      'Remove Member',
      'Are you sure you want to remove this member?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Remove',
          style: 'destructive',
          onPress: async () => {
            try {
              setLoading(true);
              await familySharingService.removeMember(memberId);
              await loadFamilyGroup();
            } catch (error) {
              Alert.alert('Error', 'Failed to remove member');
            } finally {
              setLoading(false);
            }
          },
        },
      ]
    );
  };

  return (
    <Modal
      visible={visible}
      animationType="slide"
      presentationStyle="pageSheet"
      onRequestClose={onClose}
    >
      <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerContent}>
            <Icon name="users" size={24} color="#007AFF" />
            <Text style={styles.title}>Family Sharing</Text>
          </View>
          <TouchableOpacity onPress={onClose} style={styles.closeButton}>
            <Icon name="x" size={24} color="#8E8E93" />
          </TouchableOpacity>
        </View>

        <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
          {loading && !familyGroup && (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#007AFF" />
            </View>
          )}

          {!familyGroup ? (
            // Create Family Group
            <View style={styles.createSection}>
              <View style={styles.iconContainer}>
                <Icon name="users" size={48} color="#007AFF" />
              </View>
              <Text style={styles.sectionTitle}>Create Family Group</Text>
              <Text style={styles.sectionSubtitle}>
                Share your Constellation Orb with family members. See real-time updates and collaborate on financial goals.
              </Text>
              <TouchableOpacity
                style={styles.createButton}
                onPress={createFamilyGroup}
                disabled={loading}
              >
                <Icon name="plus" size={20} color="#FFFFFF" />
                <Text style={styles.createButtonText}>Create Family Group</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <>
              {/* Family Info */}
              <View style={styles.familyInfo}>
                <Text style={styles.familyName}>{familyGroup.name}</Text>
                <Text style={styles.familySubtext}>
                  {familyGroup.members.length} member{familyGroup.members.length !== 1 ? 's' : ''}
                </Text>
              </View>

              {/* Members List */}
              <View style={styles.membersSection}>
                <Text style={styles.sectionTitle}>Family Members</Text>
                {familyGroup.members.map((member) => (
                  <View key={member.id} style={styles.memberCard}>
                    <View style={styles.memberHeader}>
                      <View style={styles.memberAvatar}>
                        <Text style={styles.memberInitial}>
                          {member.name.charAt(0).toUpperCase()}
                        </Text>
                      </View>
                      <View style={styles.memberInfo}>
                        <Text style={styles.memberName}>{member.name}</Text>
                        <Text style={styles.memberEmail}>{member.email}</Text>
                        <View style={styles.roleBadge}>
                          <Text style={styles.roleText}>{member.role}</Text>
                        </View>
                      </View>
                      {member.role !== 'owner' && (
                        <TouchableOpacity
                          style={styles.removeButton}
                          onPress={() => removeMember(member.id)}
                        >
                          <Icon name="x" size={16} color="#FF3B30" />
                        </TouchableOpacity>
                      )}
                    </View>

                    {/* Permissions (for owner) */}
                    {familyGroup.ownerId === familyGroup.members.find(m => m.role === 'owner')?.userId && (
                      <View style={styles.permissionsSection}>
                        <Text style={styles.permissionsTitle}>Permissions</Text>
                        <View style={styles.permissionRow}>
                          <Text style={styles.permissionLabel}>View Orb</Text>
                          <TouchableOpacity
                            style={[
                              styles.toggle,
                              member.permissions.canViewOrb && styles.toggleActive,
                            ]}
                            onPress={() =>
                              updatePermissions(member.id, {
                                canViewOrb: !member.permissions.canViewOrb,
                              })
                            }
                          >
                            <View
                              style={[
                                styles.toggleThumb,
                                member.permissions.canViewOrb && styles.toggleThumbActive,
                              ]}
                            />
                          </TouchableOpacity>
                        </View>
                        {member.role === 'teen' && (
                          <View style={styles.permissionRow}>
                            <Text style={styles.permissionLabel}>Spending Limit</Text>
                            <TextInput
                              style={styles.spendingInput}
                              placeholder="$0"
                              keyboardType="numeric"
                              value={member.permissions.spendingLimit?.toString() || ''}
                              onChangeText={(text) =>
                                updatePermissions(member.id, {
                                  spendingLimit: parseFloat(text) || 0,
                                })
                              }
                            />
                          </View>
                        )}
                      </View>
                    )}
                  </View>
                ))}
              </View>

              {/* Invite Section */}
              <View style={styles.inviteSection}>
                <Text style={styles.sectionTitle}>Invite Family Member</Text>
                <TextInput
                  style={styles.emailInput}
                  placeholder="Enter email address"
                  value={inviteEmail}
                  onChangeText={setInviteEmail}
                  keyboardType="email-address"
                  autoCapitalize="none"
                />
                <View style={styles.roleSelector}>
                  <TouchableOpacity
                    style={[
                      styles.roleOption,
                      inviteRole === 'member' && styles.roleOptionActive,
                    ]}
                    onPress={() => setInviteRole('member')}
                  >
                    <Text
                      style={[
                        styles.roleOptionText,
                        inviteRole === 'member' && styles.roleOptionTextActive,
                      ]}
                    >
                      Member
                    </Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[
                      styles.roleOption,
                      inviteRole === 'teen' && styles.roleOptionActive,
                    ]}
                    onPress={() => setInviteRole('teen')}
                  >
                    <Text
                      style={[
                        styles.roleOptionText,
                        inviteRole === 'teen' && styles.roleOptionTextActive,
                      ]}
                    >
                      Teen Account
                    </Text>
                  </TouchableOpacity>
                </View>
                <TouchableOpacity
                  style={styles.inviteButton}
                  onPress={sendInvite}
                  disabled={loading || !inviteEmail.trim()}
                >
                  <Icon name="send" size={20} color="#FFFFFF" />
                  <Text style={styles.inviteButtonText}>Send Invite</Text>
                </TouchableOpacity>
              </View>

              {/* Settings */}
              <View style={styles.settingsSection}>
                <Text style={styles.sectionTitle}>Family Settings</Text>
                <View style={styles.settingRow}>
                  <Text style={styles.settingLabel}>Sync Frequency</Text>
                  <Text style={styles.settingValue}>
                    {familyGroup.settings.syncFrequency}
                  </Text>
                </View>
                <View style={styles.settingRow}>
                  <Text style={styles.settingLabel}>Allow Teen Accounts</Text>
                  <Text style={styles.settingValue}>
                    {familyGroup.settings.allowTeenAccounts ? 'Yes' : 'No'}
                  </Text>
                </View>
              </View>
            </>
          )}
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F8F9FA',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  headerContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  closeButton: {
    padding: 4,
  },
  content: {
    flex: 1,
    padding: 20,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 40,
  },
  createSection: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 32,
    alignItems: 'center',
    marginTop: 40,
  },
  iconContainer: {
    width: 96,
    height: 96,
    borderRadius: 48,
    backgroundColor: '#007AFF20',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 8,
  },
  sectionSubtitle: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 24,
  },
  createButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    paddingHorizontal: 24,
    paddingVertical: 16,
    borderRadius: 12,
    gap: 8,
  },
  createButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  familyInfo: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
    alignItems: 'center',
  },
  familyName: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  familySubtext: {
    fontSize: 14,
    color: '#8E8E93',
  },
  membersSection: {
    marginBottom: 24,
  },
  memberCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
  },
  memberHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  memberAvatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
  },
  memberInitial: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  memberInfo: {
    flex: 1,
  },
  memberName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 4,
  },
  memberEmail: {
    fontSize: 13,
    color: '#8E8E93',
    marginBottom: 8,
  },
  roleBadge: {
    alignSelf: 'flex-start',
    backgroundColor: '#007AFF20',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  roleText: {
    fontSize: 11,
    fontWeight: '700',
    color: '#007AFF',
    textTransform: 'uppercase',
  },
  removeButton: {
    padding: 8,
  },
  permissionsSection: {
    marginTop: 16,
    paddingTop: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  permissionsTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1C1C1E',
    marginBottom: 12,
  },
  permissionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  permissionLabel: {
    fontSize: 14,
    color: '#1C1C1E',
  },
  toggle: {
    width: 44,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#E5E5EA',
    justifyContent: 'center',
    padding: 2,
  },
  toggleActive: {
    backgroundColor: '#34C759',
  },
  toggleThumb: {
    width: 20,
    height: 20,
    borderRadius: 10,
    backgroundColor: '#FFFFFF',
  },
  toggleThumbActive: {
    alignSelf: 'flex-end',
  },
  spendingInput: {
    borderWidth: 1,
    borderColor: '#E5E5EA',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
    fontSize: 14,
    width: 100,
    textAlign: 'right',
  },
  inviteSection: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
  },
  emailInput: {
    borderWidth: 1,
    borderColor: '#E5E5EA',
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    marginBottom: 16,
  },
  roleSelector: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 16,
  },
  roleOption: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    alignItems: 'center',
  },
  roleOptionActive: {
    backgroundColor: '#007AFF20',
    borderColor: '#007AFF',
  },
  roleOptionText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#8E8E93',
  },
  roleOptionTextActive: {
    color: '#007AFF',
  },
  inviteButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    paddingVertical: 16,
    borderRadius: 12,
    gap: 8,
  },
  inviteButtonText: {
    fontSize: 16,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  settingsSection: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
  },
  settingRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  settingLabel: {
    fontSize: 14,
    color: '#1C1C1E',
  },
  settingValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#007AFF',
  },
});

export default FamilyManagementModal;

