import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  SafeAreaView,
  Switch,
  ActivityIndicator,
} from 'react-native';
import { useQuery, useMutation } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

// GraphQL Queries and Mutations
const GET_USER_PROFILE = gql`
  query GetUserProfile {
    me {
      id
      name
      email
      phone
      dateOfBirth
      address {
        street
        city
        state
        zipCode
        country
      }
      preferences {
        theme
        notifications
        privacy
        language
      }
      security {
        twoFactorEnabled
        biometricEnabled
        lastPasswordChange
      }
    }
  }
`;

const UPDATE_PROFILE = gql`
  mutation UpdateProfile($input: ProfileUpdateInput!) {
    updateProfile(input: $input) {
      success
      message
      user {
        id
        name
        email
        phone
        dateOfBirth
        address {
          street
          city
          state
          zipCode
          country
        }
      }
    }
  }
`;

const UPDATE_PREFERENCES = gql`
  mutation UpdatePreferences($preferences: PreferencesInput!) {
    updatePreferences(preferences: $preferences) {
      success
      message
      preferences {
        theme
        notifications
        privacy
        language
      }
    }
  }
`;

const UPDATE_SECURITY = gql`
  mutation UpdateSecurity($security: SecurityInput!) {
    updateSecurity(security: $security) {
      success
      message
      security {
        twoFactorEnabled
        biometricEnabled
        lastPasswordChange
      }
    }
  }
`;

const CHANGE_PASSWORD = gql`
  mutation ChangePassword($currentPassword: String!, $newPassword: String!) {
    changePassword(currentPassword: $currentPassword, newPassword: $newPassword) {
      success
      message
    }
  }
`;

const AccountManagementScreen = ({ navigateTo }) => {
  const [activeSection, setActiveSection] = useState('profile');
  const [isEditing, setIsEditing] = useState(false);
  
  // Form states
  const [profileData, setProfileData] = useState({
    name: '',
    email: '',
    phone: '',
    dateOfBirth: '',
    address: {
      street: '',
      city: '',
      state: '',
      zipCode: '',
      country: 'US',
    },
  });

  const [preferences, setPreferences] = useState({
    theme: 'light',
    notifications: true,
    privacy: 'public',
    language: 'en',
  });

  const [security, setSecurity] = useState({
    twoFactorEnabled: false,
    biometricEnabled: false,
  });

  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  // GraphQL queries
  const { data: userData, loading: userLoading, refetch: refetchUser } = useQuery(
    GET_USER_PROFILE,
    {
      errorPolicy: 'all',
      onCompleted: (data) => {
        if (data?.me) {
          setProfileData({
            name: data.me.name || '',
            email: data.me.email || '',
            phone: data.me.phone || '',
            dateOfBirth: data.me.dateOfBirth || '',
            address: data.me.address || {
              street: '',
              city: '',
              state: '',
              zipCode: '',
              country: 'US',
            },
          });
          setPreferences(data.me.preferences || preferences);
          setSecurity(data.me.security || security);
        }
      },
      onError: (error) => {
        console.error('User profile query error:', error);
      }
    }
  );

  // GraphQL mutations
  const [updateProfile, { loading: profileLoading }] = useMutation(UPDATE_PROFILE, {
    onCompleted: (data) => {
      if (data.updateProfile.success) {
        Alert.alert('Success', 'Profile updated successfully');
        setIsEditing(false);
        refetchUser();
      } else {
        Alert.alert('Error', data.updateProfile.message);
      }
    },
    onError: (error) => {
      Alert.alert('Error', `Failed to update profile: ${error.message}`);
    }
  });

  const [updatePreferences, { loading: preferencesLoading }] = useMutation(UPDATE_PREFERENCES, {
    onCompleted: (data) => {
      if (data.updatePreferences.success) {
        Alert.alert('Success', 'Preferences updated successfully');
        refetchUser();
      } else {
        Alert.alert('Error', data.updatePreferences.message);
      }
    },
    onError: (error) => {
      Alert.alert('Error', `Failed to update preferences: ${error.message}`);
    }
  });

  const [updateSecurity, { loading: securityLoading }] = useMutation(UPDATE_SECURITY, {
    onCompleted: (data) => {
      if (data.updateSecurity.success) {
        Alert.alert('Success', 'Security settings updated successfully');
        refetchUser();
      } else {
        Alert.alert('Error', data.updateSecurity.message);
      }
    },
    onError: (error) => {
      Alert.alert('Error', `Failed to update security settings: ${error.message}`);
    }
  });

  const [changePassword, { loading: passwordLoading }] = useMutation(CHANGE_PASSWORD, {
    onCompleted: (data) => {
      if (data.changePassword.success) {
        Alert.alert('Success', 'Password changed successfully');
        setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
      } else {
        Alert.alert('Error', data.changePassword.message);
      }
    },
    onError: (error) => {
      Alert.alert('Error', `Failed to change password: ${error.message}`);
    }
  });

  const handleProfileUpdate = () => {
    if (!profileData.name || !profileData.email) {
      Alert.alert('Error', 'Name and email are required');
      return;
    }
    
    updateProfile({
      variables: {
        input: profileData
      }
    });
  };

  const handlePreferencesUpdate = () => {
    updatePreferences({
      variables: {
        preferences: preferences
      }
    });
  };

  const handleSecurityUpdate = () => {
    updateSecurity({
      variables: {
        security: security
      }
    });
  };

  const handlePasswordChange = () => {
    if (!passwordData.currentPassword || !passwordData.newPassword) {
      Alert.alert('Error', 'Current password and new password are required');
      return;
    }
    
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      Alert.alert('Error', 'New password and confirmation do not match');
      return;
    }
    
    if (passwordData.newPassword.length < 8) {
      Alert.alert('Error', 'New password must be at least 8 characters long');
      return;
    }
    
    changePassword({
      variables: {
        currentPassword: passwordData.currentPassword,
        newPassword: passwordData.newPassword
      }
    });
  };

  const renderProfileSection = () => (
    <View style={styles.section}>
      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Personal Information</Text>
        <TouchableOpacity
          onPress={() => setIsEditing(!isEditing)}
          style={styles.editButton}
        >
          <Icon name={isEditing ? 'x' : 'edit-3'} size={16} color="#007AFF" />
          <Text style={styles.editButtonText}>
            {isEditing ? 'Cancel' : 'Edit'}
          </Text>
        </TouchableOpacity>
      </View>

      <View style={styles.form}>
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Full Name</Text>
          <TextInput
            style={[styles.input, !isEditing && styles.inputDisabled]}
            value={profileData.name}
            onChangeText={(text) => setProfileData({...profileData, name: text})}
            editable={isEditing}
            placeholder="Enter your full name"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Email Address</Text>
          <TextInput
            style={[styles.input, !isEditing && styles.inputDisabled]}
            value={profileData.email}
            onChangeText={(text) => setProfileData({...profileData, email: text})}
            editable={isEditing}
            placeholder="Enter your email"
            keyboardType="email-address"
            autoCapitalize="none"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Phone Number</Text>
          <TextInput
            style={[styles.input, !isEditing && styles.inputDisabled]}
            value={profileData.phone}
            onChangeText={(text) => setProfileData({...profileData, phone: text})}
            editable={isEditing}
            placeholder="Enter your phone number"
            keyboardType="phone-pad"
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Date of Birth</Text>
          <TextInput
            style={[styles.input, !isEditing && styles.inputDisabled]}
            value={profileData.dateOfBirth}
            onChangeText={(text) => setProfileData({...profileData, dateOfBirth: text})}
            editable={isEditing}
            placeholder="MM/DD/YYYY"
          />
        </View>

        <Text style={styles.subsectionTitle}>Address</Text>
        
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Street Address</Text>
          <TextInput
            style={[styles.input, !isEditing && styles.inputDisabled]}
            value={profileData.address.street}
            onChangeText={(text) => setProfileData({
              ...profileData, 
              address: {...profileData.address, street: text}
            })}
            editable={isEditing}
            placeholder="Enter street address"
          />
        </View>

        <View style={styles.row}>
          <View style={[styles.inputGroup, { flex: 1, marginRight: 8 }]}>
            <Text style={styles.label}>City</Text>
            <TextInput
              style={[styles.input, !isEditing && styles.inputDisabled]}
              value={profileData.address.city}
              onChangeText={(text) => setProfileData({
                ...profileData, 
                address: {...profileData.address, city: text}
              })}
              editable={isEditing}
              placeholder="City"
            />
          </View>
          <View style={[styles.inputGroup, { flex: 1, marginLeft: 8 }]}>
            <Text style={styles.label}>State</Text>
            <TextInput
              style={[styles.input, !isEditing && styles.inputDisabled]}
              value={profileData.address.state}
              onChangeText={(text) => setProfileData({
                ...profileData, 
                address: {...profileData.address, state: text}
              })}
              editable={isEditing}
              placeholder="State"
            />
          </View>
        </View>

        <View style={styles.row}>
          <View style={[styles.inputGroup, { flex: 1, marginRight: 8 }]}>
            <Text style={styles.label}>ZIP Code</Text>
            <TextInput
              style={[styles.input, !isEditing && styles.inputDisabled]}
              value={profileData.address.zipCode}
              onChangeText={(text) => setProfileData({
                ...profileData, 
                address: {...profileData.address, zipCode: text}
              })}
              editable={isEditing}
              placeholder="ZIP"
              keyboardType="numeric"
            />
          </View>
          <View style={[styles.inputGroup, { flex: 1, marginLeft: 8 }]}>
            <Text style={styles.label}>Country</Text>
            <TextInput
              style={[styles.input, !isEditing && styles.inputDisabled]}
              value={profileData.address.country}
              onChangeText={(text) => setProfileData({
                ...profileData, 
                address: {...profileData.address, country: text}
              })}
              editable={isEditing}
              placeholder="Country"
            />
          </View>
        </View>

        {isEditing && (
          <TouchableOpacity
            style={styles.saveButton}
            onPress={handleProfileUpdate}
            disabled={profileLoading}
          >
            {profileLoading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.saveButtonText}>Save Changes</Text>
            )}
          </TouchableOpacity>
        )}
      </View>
    </View>
  );

  const renderPreferencesSection = () => (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>Preferences</Text>
      
      <View style={styles.preferenceItem}>
        <View style={styles.preferenceInfo}>
          <Text style={styles.preferenceTitle}>Theme</Text>
          <Text style={styles.preferenceDescription}>Choose your preferred theme</Text>
        </View>
        <View style={styles.preferenceControl}>
          <TouchableOpacity
            style={[styles.themeButton, preferences.theme === 'light' && styles.themeButtonActive]}
            onPress={() => setPreferences({...preferences, theme: 'light'})}
          >
            <Text style={[styles.themeButtonText, preferences.theme === 'light' && styles.themeButtonTextActive]}>
              Light
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.themeButton, preferences.theme === 'dark' && styles.themeButtonActive]}
            onPress={() => setPreferences({...preferences, theme: 'dark'})}
          >
            <Text style={[styles.themeButtonText, preferences.theme === 'dark' && styles.themeButtonTextActive]}>
              Dark
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      <View style={styles.preferenceItem}>
        <View style={styles.preferenceInfo}>
          <Text style={styles.preferenceTitle}>Notifications</Text>
          <Text style={styles.preferenceDescription}>Receive push notifications</Text>
        </View>
        <Switch
          value={preferences.notifications}
          onValueChange={(value) => setPreferences({...preferences, notifications: value})}
          trackColor={{ false: '#E5E5EA', true: '#007AFF' }}
          thumbColor="#fff"
        />
      </View>

      <View style={styles.preferenceItem}>
        <View style={styles.preferenceInfo}>
          <Text style={styles.preferenceTitle}>Privacy</Text>
          <Text style={styles.preferenceDescription}>Control your profile visibility</Text>
        </View>
        <View style={styles.preferenceControl}>
          <TouchableOpacity
            style={[styles.privacyButton, preferences.privacy === 'public' && styles.privacyButtonActive]}
            onPress={() => setPreferences({...preferences, privacy: 'public'})}
          >
            <Text style={[styles.privacyButtonText, preferences.privacy === 'public' && styles.privacyButtonTextActive]}>
              Public
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.privacyButton, preferences.privacy === 'private' && styles.privacyButtonActive]}
            onPress={() => setPreferences({...preferences, privacy: 'private'})}
          >
            <Text style={[styles.privacyButtonText, preferences.privacy === 'private' && styles.privacyButtonTextActive]}>
              Private
            </Text>
          </TouchableOpacity>
        </View>
      </View>

      <TouchableOpacity
        style={styles.saveButton}
        onPress={handlePreferencesUpdate}
        disabled={preferencesLoading}
      >
        {preferencesLoading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.saveButtonText}>Save Preferences</Text>
        )}
      </TouchableOpacity>
    </View>
  );

  const renderSecuritySection = () => (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>Security</Text>
      
      <View style={styles.preferenceItem}>
        <View style={styles.preferenceInfo}>
          <Text style={styles.preferenceTitle}>Two-Factor Authentication</Text>
          <Text style={styles.preferenceDescription}>Add an extra layer of security</Text>
        </View>
        <Switch
          value={security.twoFactorEnabled}
          onValueChange={(value) => setSecurity({...security, twoFactorEnabled: value})}
          trackColor={{ false: '#E5E5EA', true: '#007AFF' }}
          thumbColor="#fff"
        />
      </View>

      <View style={styles.preferenceItem}>
        <View style={styles.preferenceInfo}>
          <Text style={styles.preferenceTitle}>Biometric Authentication</Text>
          <Text style={styles.preferenceDescription}>Use fingerprint or face ID</Text>
        </View>
        <Switch
          value={security.biometricEnabled}
          onValueChange={(value) => setSecurity({...security, biometricEnabled: value})}
          trackColor={{ false: '#E5E5EA', true: '#007AFF' }}
          thumbColor="#fff"
        />
      </View>

      <View style={styles.passwordSection}>
        <Text style={styles.subsectionTitle}>Change Password</Text>
        
        <View style={styles.inputGroup}>
          <Text style={styles.label}>Current Password</Text>
          <TextInput
            style={styles.input}
            value={passwordData.currentPassword}
            onChangeText={(text) => setPasswordData({...passwordData, currentPassword: text})}
            placeholder="Enter current password"
            secureTextEntry
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>New Password</Text>
          <TextInput
            style={styles.input}
            value={passwordData.newPassword}
            onChangeText={(text) => setPasswordData({...passwordData, newPassword: text})}
            placeholder="Enter new password"
            secureTextEntry
          />
        </View>

        <View style={styles.inputGroup}>
          <Text style={styles.label}>Confirm New Password</Text>
          <TextInput
            style={styles.input}
            value={passwordData.confirmPassword}
            onChangeText={(text) => setPasswordData({...passwordData, confirmPassword: text})}
            placeholder="Confirm new password"
            secureTextEntry
          />
        </View>

        <TouchableOpacity
          style={styles.saveButton}
          onPress={handlePasswordChange}
          disabled={passwordLoading}
        >
          {passwordLoading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.saveButtonText}>Change Password</Text>
          )}
        </TouchableOpacity>
      </View>

      <TouchableOpacity
        style={styles.saveButton}
        onPress={handleSecurityUpdate}
        disabled={securityLoading}
      >
        {securityLoading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.saveButtonText}>Save Security Settings</Text>
        )}
      </TouchableOpacity>
    </View>
  );

  const sections = [
    { key: 'profile', title: 'Profile', icon: 'user' },
    { key: 'preferences', title: 'Preferences', icon: 'settings' },
    { key: 'security', title: 'Security', icon: 'shield' },
  ];

  if (userLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading account settings...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigateTo('profile')}>
          <Icon name="arrow-left" size={24} color="#000" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Account Management</Text>
        <View style={{ width: 24 }} />
      </View>

      {/* Section Navigation */}
      <View style={styles.sectionNavigation}>
        {sections.map((section) => (
          <TouchableOpacity
            key={section.key}
            style={[
              styles.sectionTab,
              activeSection === section.key && styles.activeSectionTab
            ]}
            onPress={() => setActiveSection(section.key)}
          >
            <Icon 
              name={section.icon} 
              size={16} 
              color={activeSection === section.key ? '#007AFF' : '#8E8E93'} 
            />
            <Text style={[
              styles.sectionTabText,
              activeSection === section.key && styles.activeSectionTabText
            ]}>
              {section.title}
            </Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Content */}
      <ScrollView style={styles.content}>
        {activeSection === 'profile' && renderProfileSection()}
        {activeSection === 'preferences' && renderPreferencesSection()}
        {activeSection === 'security' && renderSecuritySection()}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F2F2F7',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
  },
  sectionNavigation: {
    flexDirection: 'row',
    backgroundColor: '#fff',
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  sectionTab: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 16,
    borderBottomWidth: 2,
    borderBottomColor: 'transparent',
  },
  activeSectionTab: {
    borderBottomColor: '#007AFF',
  },
  sectionTabText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#8E8E93',
    marginLeft: 6,
  },
  activeSectionTabText: {
    color: '#007AFF',
    fontWeight: '600',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  section: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000',
  },
  subsectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginTop: 20,
    marginBottom: 16,
  },
  editButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#F0F8FF',
    borderRadius: 8,
  },
  editButtonText: {
    fontSize: 14,
    color: '#007AFF',
    fontWeight: '600',
    marginLeft: 4,
  },
  form: {
    flex: 1,
  },
  inputGroup: {
    marginBottom: 16,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: '#000',
    marginBottom: 6,
  },
  input: {
    backgroundColor: '#F2F2F7',
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    color: '#000',
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  inputDisabled: {
    backgroundColor: '#F8F9FA',
    color: '#8E8E93',
  },
  row: {
    flexDirection: 'row',
  },
  preferenceItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#F2F2F7',
  },
  preferenceInfo: {
    flex: 1,
  },
  preferenceTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000',
    marginBottom: 4,
  },
  preferenceDescription: {
    fontSize: 14,
    color: '#8E8E93',
  },
  preferenceControl: {
    flexDirection: 'row',
  },
  themeButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    marginLeft: 8,
    backgroundColor: '#F2F2F7',
  },
  themeButtonActive: {
    backgroundColor: '#007AFF',
  },
  themeButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#8E8E93',
  },
  themeButtonTextActive: {
    color: '#fff',
  },
  privacyButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    marginLeft: 8,
    backgroundColor: '#F2F2F7',
  },
  privacyButtonActive: {
    backgroundColor: '#007AFF',
  },
  privacyButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#8E8E93',
  },
  privacyButtonTextActive: {
    color: '#fff',
  },
  passwordSection: {
    marginTop: 20,
    paddingTop: 20,
    borderTopWidth: 1,
    borderTopColor: '#F2F2F7',
  },
  saveButton: {
    backgroundColor: '#007AFF',
    borderRadius: 8,
    paddingVertical: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 20,
  },
  saveButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#8E8E93',
  },
});

export default AccountManagementScreen;
