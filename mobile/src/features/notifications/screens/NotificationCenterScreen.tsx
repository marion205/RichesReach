import React, { useState, useEffect } from 'react';
import { 
  View, 
  Text, 
  TouchableOpacity, 
  StyleSheet, 
  ScrollView, 
  ActivityIndicator, 
  Alert,
  Switch
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

export default function NotificationCenterScreen() {
  const [loading, setLoading] = useState(false);
  const [preferences, setPreferences] = useState({
    dailyDigestEnabled: true,
    dailyDigestTime: '08:00',
    regimeAlertsEnabled: true,
    regimeAlertUrgency: 'medium',
    missionRemindersEnabled: true,
    missionReminderTime: '19:00',
    streakAlertsEnabled: true,
    achievementNotificationsEnabled: true,
    recoveryRitualEnabled: true,
    quietHoursEnabled: false,
    quietHoursStart: '22:00',
    quietHoursEnd: '07:00'
  });

  const [recentNotifications, setRecentNotifications] = useState([
    {
      id: '1',
      type: 'regime_alert',
      title: '📊 Market Regime Alert',
      body: 'Market shifted from sideways consolidation to early bull market. Confidence: 85%.',
      timestamp: '2024-01-15T10:30:00Z',
      read: false,
      priority: 'medium'
    },
    {
      id: '2',
      type: 'daily_digest',
      title: '🎙️ Your Daily Market Briefing',
      body: 'Your personalized 60-second market digest is ready! Tap to listen.',
      timestamp: '2024-01-15T08:00:00Z',
      read: true,
      priority: 'normal'
    },
    {
      id: '3',
      type: 'mission_reminder',
      title: '🎯 Day 5 Mission Ready',
      body: 'Your daily momentum mission is waiting! Take 5 minutes to complete it.',
      timestamp: '2024-01-14T19:00:00Z',
      read: true,
      priority: 'normal'
    },
    {
      id: '4',
      type: 'achievement',
      title: '🏆 Week Warrior',
      body: 'Congratulations! You\'ve maintained a 7-day streak.',
      timestamp: '2024-01-14T15:45:00Z',
      read: true,
      priority: 'normal'
    }
  ]);

  const updatePreference = (key: string, value: any) => {
    setPreferences(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const markAsRead = (notificationId: string) => {
    setRecentNotifications(prev => 
      prev.map(notif => 
        notif.id === notificationId 
          ? { ...notif, read: true }
          : notif
      )
    );
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'regime_alert': return 'trending-up';
      case 'daily_digest': return 'mic';
      case 'mission_reminder': return 'flag';
      case 'achievement': return 'trophy';
      case 'recovery_ritual': return 'refresh';
      default: return 'notifications';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return '#ef4444';
      case 'high': return '#f59e0b';
      case 'medium': return '#3b82f6';
      case 'normal': return '#6b7280';
      default: return '#6b7280';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) {
      return `${diffDays}d ago`;
    } else if (diffHours > 0) {
      return `${diffHours}h ago`;
    } else {
      const diffMinutes = Math.floor(diffMs / (1000 * 60));
      return `${diffMinutes}m ago`;
    }
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.title}>🔔 Notification Center</Text>
      <Text style={styles.subtitle}>
        Manage your notifications and stay informed about market changes
      </Text>

      {/* Recent Notifications */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Recent Notifications</Text>
        {recentNotifications.map((notification) => (
          <TouchableOpacity
            key={notification.id}
            style={[
              styles.notificationCard,
              !notification.read && styles.unreadNotification
            ]}
            onPress={() => markAsRead(notification.id)}
          >
            <View style={styles.notificationHeader}>
              <View style={styles.notificationIconContainer}>
                <Ionicons 
                  name={getNotificationIcon(notification.type)} 
                  size={20} 
                  color={getPriorityColor(notification.priority)} 
                />
              </View>
              <View style={styles.notificationContent}>
                <Text style={[
                  styles.notificationTitle,
                  !notification.read && styles.unreadTitle
                ]}>
                  {notification.title}
                </Text>
                <Text style={styles.notificationBody}>
                  {notification.body}
                </Text>
                <Text style={styles.notificationTime}>
                  {formatTimestamp(notification.timestamp)}
                </Text>
              </View>
              {!notification.read && (
                <View style={styles.unreadDot} />
              )}
            </View>
          </TouchableOpacity>
        ))}
      </View>

      {/* Notification Preferences */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Notification Preferences</Text>
        
        {/* Daily Digest */}
        <View style={styles.preferenceCard}>
          <View style={styles.preferenceHeader}>
            <Ionicons name="mic" size={20} color="#3b82f6" />
            <Text style={styles.preferenceTitle}>Daily Voice Digest</Text>
            <Switch
              value={preferences.dailyDigestEnabled}
              onValueChange={(value) => updatePreference('dailyDigestEnabled', value)}
              trackColor={{ false: '#e5e7eb', true: '#3b82f6' }}
              thumbColor={preferences.dailyDigestEnabled ? '#ffffff' : '#f3f4f6'}
            />
          </View>
          {preferences.dailyDigestEnabled && (
            <View style={styles.preferenceDetail}>
              <Text style={styles.preferenceLabel}>Time: {preferences.dailyDigestTime}</Text>
            </View>
          )}
        </View>

        {/* Regime Alerts */}
        <View style={styles.preferenceCard}>
          <View style={styles.preferenceHeader}>
            <Ionicons name="trending-up" size={20} color="#f59e0b" />
            <Text style={styles.preferenceTitle}>Regime Alerts</Text>
            <Switch
              value={preferences.regimeAlertsEnabled}
              onValueChange={(value) => updatePreference('regimeAlertsEnabled', value)}
              trackColor={{ false: '#e5e7eb', true: '#f59e0b' }}
              thumbColor={preferences.regimeAlertsEnabled ? '#ffffff' : '#f3f4f6'}
            />
          </View>
          {preferences.regimeAlertsEnabled && (
            <View style={styles.preferenceDetail}>
              <Text style={styles.preferenceLabel}>Urgency: {preferences.regimeAlertUrgency}</Text>
            </View>
          )}
        </View>

        {/* Mission Reminders */}
        <View style={styles.preferenceCard}>
          <View style={styles.preferenceHeader}>
            <Ionicons name="flag" size={20} color="#10b981" />
            <Text style={styles.preferenceTitle}>Mission Reminders</Text>
            <Switch
              value={preferences.missionRemindersEnabled}
              onValueChange={(value) => updatePreference('missionRemindersEnabled', value)}
              trackColor={{ false: '#e5e7eb', true: '#10b981' }}
              thumbColor={preferences.missionRemindersEnabled ? '#ffffff' : '#f3f4f6'}
            />
          </View>
          {preferences.missionRemindersEnabled && (
            <View style={styles.preferenceDetail}>
              <Text style={styles.preferenceLabel}>Time: {preferences.missionReminderTime}</Text>
            </View>
          )}
        </View>

        {/* Streak Alerts */}
        <View style={styles.preferenceCard}>
          <View style={styles.preferenceHeader}>
            <Ionicons name="flame" size={20} color="#ef4444" />
            <Text style={styles.preferenceTitle}>Streak Alerts</Text>
            <Switch
              value={preferences.streakAlertsEnabled}
              onValueChange={(value) => updatePreference('streakAlertsEnabled', value)}
              trackColor={{ false: '#e5e7eb', true: '#ef4444' }}
              thumbColor={preferences.streakAlertsEnabled ? '#ffffff' : '#f3f4f6'}
            />
          </View>
        </View>

        {/* Achievement Notifications */}
        <View style={styles.preferenceCard}>
          <View style={styles.preferenceHeader}>
            <Ionicons name="trophy" size={20} color="#8b5cf6" />
            <Text style={styles.preferenceTitle}>Achievement Notifications</Text>
            <Switch
              value={preferences.achievementNotificationsEnabled}
              onValueChange={(value) => updatePreference('achievementNotificationsEnabled', value)}
              trackColor={{ false: '#e5e7eb', true: '#8b5cf6' }}
              thumbColor={preferences.achievementNotificationsEnabled ? '#ffffff' : '#f3f4f6'}
            />
          </View>
        </View>

        {/* Recovery Ritual */}
        <View style={styles.preferenceCard}>
          <View style={styles.preferenceHeader}>
            <Ionicons name="refresh" size={20} color="#06b6d4" />
            <Text style={styles.preferenceTitle}>Recovery Ritual</Text>
            <Switch
              value={preferences.recoveryRitualEnabled}
              onValueChange={(value) => updatePreference('recoveryRitualEnabled', value)}
              trackColor={{ false: '#e5e7eb', true: '#06b6d4' }}
              thumbColor={preferences.recoveryRitualEnabled ? '#ffffff' : '#f3f4f6'}
            />
          </View>
        </View>

        {/* Quiet Hours */}
        <View style={styles.preferenceCard}>
          <View style={styles.preferenceHeader}>
            <Ionicons name="moon" size={20} color="#6b7280" />
            <Text style={styles.preferenceTitle}>Quiet Hours</Text>
            <Switch
              value={preferences.quietHoursEnabled}
              onValueChange={(value) => updatePreference('quietHoursEnabled', value)}
              trackColor={{ false: '#e5e7eb', true: '#6b7280' }}
              thumbColor={preferences.quietHoursEnabled ? '#ffffff' : '#f3f4f6'}
            />
          </View>
          {preferences.quietHoursEnabled && (
            <View style={styles.preferenceDetail}>
              <Text style={styles.preferenceLabel}>
                {preferences.quietHoursStart} - {preferences.quietHoursEnd}
              </Text>
            </View>
          )}
        </View>
      </View>

      {/* Test Notifications */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Test Notifications</Text>
        <TouchableOpacity style={styles.testButton}>
          <Text style={styles.testButtonText}>🔔 Test Regime Alert</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.testButton}>
          <Text style={styles.testButtonText}>🎙️ Test Daily Digest</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.testButton}>
          <Text style={styles.testButtonText}>🎯 Test Mission Reminder</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { 
    flex: 1, 
    backgroundColor: '#f8f9fa', 
    padding: 16 
  },
  title: { 
    color: '#1f2937', 
    fontSize: 24, 
    fontWeight: '800', 
    marginBottom: 8,
    textAlign: 'center'
  },
  subtitle: { 
    color: '#6b7280', 
    fontSize: 16, 
    marginBottom: 24, 
    textAlign: 'center',
    lineHeight: 22
  },
  
  section: {
    marginBottom: 24
  },
  sectionTitle: {
    color: '#1f2937',
    fontSize: 18,
    fontWeight: '700',
    marginBottom: 12
  },
  
  // Notifications
  notificationCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2
  },
  unreadNotification: {
    borderLeftWidth: 4,
    borderLeftColor: '#3b82f6'
  },
  notificationHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start'
  },
  notificationIconContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#f3f4f6',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12
  },
  notificationContent: {
    flex: 1
  },
  notificationTitle: {
    color: '#1f2937',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4
  },
  unreadTitle: {
    fontWeight: '700'
  },
  notificationBody: {
    color: '#6b7280',
    fontSize: 14,
    lineHeight: 20,
    marginBottom: 8
  },
  notificationTime: {
    color: '#9ca3af',
    fontSize: 12
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#3b82f6',
    marginTop: 4
  },
  
  // Preferences
  preferenceCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2
  },
  preferenceHeader: {
    flexDirection: 'row',
    alignItems: 'center'
  },
  preferenceTitle: {
    color: '#1f2937',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 12,
    flex: 1
  },
  preferenceDetail: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#f3f4f6'
  },
  preferenceLabel: {
    color: '#6b7280',
    fontSize: 14
  },
  
  // Test Buttons
  testButton: {
    backgroundColor: '#3b82f6',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 8
  },
  testButtonText: {
    color: '#ffffff',
    fontWeight: '600',
    fontSize: 14
  }
});
