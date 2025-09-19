import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useQuery, useMutation } from '@apollo/client';
import { gql } from '@apollo/client';
import Icon from 'react-native-vector-icons/Feather';

// GraphQL Queries
const GET_NOTIFICATIONS = gql`
  query GetNotifications {
    notifications {
      id
      title
      message
      type
      isRead
      createdAt
      data
    }
  }
`;

const GET_NOTIFICATION_SETTINGS = gql`
  query GetNotificationSettings {
    notificationSettings {
      priceAlerts
      orderUpdates
      newsUpdates
      systemUpdates
    }
  }
`;

// GraphQL Mutations
const MARK_NOTIFICATION_READ = gql`
  mutation MarkNotificationRead($notificationId: String!) {
    markNotificationRead(notificationId: $notificationId) {
      success
      message
    }
  }
`;

const MARK_ALL_NOTIFICATIONS_READ = gql`
  mutation MarkAllNotificationsRead {
    markAllNotificationsRead {
      success
      message
    }
  }
`;

const UPDATE_NOTIFICATION_SETTINGS = gql`
  mutation UpdateNotificationSettings($settings: NotificationSettingsInput!) {
    updateNotificationSettings(settings: $settings) {
      success
      message
      settings {
        priceAlerts
        orderUpdates
        newsUpdates
        systemUpdates
      }
    }
  }
`;

const NotificationsScreen = ({ navigateTo }: { navigateTo?: (screen: string) => void }) => {
  const [refreshing, setRefreshing] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  // Queries
  const { 
    data: notificationsData, 
    loading: notificationsLoading, 
    refetch: refetchNotifications 
  } = useQuery(GET_NOTIFICATIONS, { errorPolicy: 'all' });

  const { 
    data: settingsData, 
    loading: settingsLoading,
    refetch: refetchSettings 
  } = useQuery(GET_NOTIFICATION_SETTINGS, { errorPolicy: 'all' });

  // Mutations
  const [markNotificationRead] = useMutation(MARK_NOTIFICATION_READ, {
    onCompleted: (data) => {
      if (data.markNotificationRead.success) {
        refetchNotifications();
      }
    },
    onError: (error) => {
      Alert.alert('Error', error.message);
    }
  });

  const [markAllNotificationsRead] = useMutation(MARK_ALL_NOTIFICATIONS_READ, {
    onCompleted: (data) => {
      if (data.markAllNotificationsRead.success) {
        refetchNotifications();
        Alert.alert('Success', 'All notifications marked as read');
      }
    },
    onError: (error) => {
      Alert.alert('Error', error.message);
    }
  });

  const [updateNotificationSettings] = useMutation(UPDATE_NOTIFICATION_SETTINGS, {
    onCompleted: (data) => {
      if (data.updateNotificationSettings.success) {
        refetchSettings();
        Alert.alert('Success', 'Notification settings updated');
      }
    },
    onError: (error) => {
      Alert.alert('Error', error.message);
    }
  });

  const handleRefresh = async () => {
    setRefreshing(true);
    await Promise.all([refetchNotifications(), refetchSettings()]);
    setRefreshing(false);
  };

  const handleMarkAsRead = (notificationId: string) => {
    markNotificationRead({ variables: { notificationId } });
  };

  const handleMarkAllAsRead = () => {
    Alert.alert(
      'Mark All as Read',
      'Are you sure you want to mark all notifications as read?',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Mark All', onPress: () => markAllNotificationsRead() }
      ]
    );
  };

  const handleToggleSetting = (setting: string) => {
    const currentSettings = settingsData?.notificationSettings || {};
    const newValue = !currentSettings[setting];
    
    updateNotificationSettings({
      variables: {
        settings: {
          ...currentSettings,
          [setting]: newValue
        }
      }
    });
  };

  const getNotificationIcon = (type: string) => {
    switch (type) {
      case 'price_alert':
        return 'trending-up';
      case 'order_filled':
        return 'check-circle';
      case 'order_cancelled':
        return 'x-circle';
      case 'news_update':
        return 'newspaper';
      case 'system_update':
        return 'settings';
      default:
        return 'bell';
    }
  };

  const getNotificationColor = (type: string) => {
    switch (type) {
      case 'price_alert':
        return '#FF9500';
      case 'order_filled':
        return '#34C759';
      case 'order_cancelled':
        return '#FF3B30';
      case 'news_update':
        return '#007AFF';
      case 'system_update':
        return '#8E8E93';
      default:
        return '#007AFF';
    }
  };

  const renderNotification = (notification: any) => (
    <TouchableOpacity
      key={notification.id}
      style={[
        styles.notificationCard,
        !notification.isRead && styles.unreadNotification
      ]}
      onPress={() => handleMarkAsRead(notification.id)}
    >
      <View style={styles.notificationHeader}>
        <View style={[
          styles.notificationIcon,
          { backgroundColor: getNotificationColor(notification.type) + '20' }
        ]}>
          <Icon 
            name={getNotificationIcon(notification.type)} 
            size={20} 
            color={getNotificationColor(notification.type)} 
          />
        </View>
        <View style={styles.notificationContent}>
          <Text style={[
            styles.notificationTitle,
            !notification.isRead && styles.unreadText
          ]}>
            {notification.title}
          </Text>
          <Text style={styles.notificationMessage}>
            {notification.message}
          </Text>
          <Text style={styles.notificationTime}>
            {new Date(notification.createdAt).toLocaleString()}
          </Text>
        </View>
        {!notification.isRead && (
          <View style={styles.unreadDot} />
        )}
      </View>
    </TouchableOpacity>
  );

  const renderSettings = () => {
    if (settingsLoading) {
      return (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#007AFF" />
          <Text style={styles.loadingText}>Loading settings...</Text>
        </View>
      );
    }

    const settings = settingsData?.notificationSettings || {};

    return (
      <View style={styles.settingsContainer}>
        <Text style={styles.settingsTitle}>Notification Preferences</Text>
        
        {[
          { key: 'priceAlerts', label: 'Price Alerts', description: 'Get notified when stocks reach your target prices' },
          { key: 'orderUpdates', label: 'Order Updates', description: 'Receive updates about your buy/sell orders' },
          { key: 'newsUpdates', label: 'News Updates', description: 'Stay informed with market news and analysis' },
          { key: 'systemUpdates', label: 'System Updates', description: 'Important app updates and maintenance notices' },
        ].map((setting) => (
          <TouchableOpacity
            key={setting.key}
            style={styles.settingRow}
            onPress={() => handleToggleSetting(setting.key)}
          >
            <View style={styles.settingInfo}>
              <Text style={styles.settingLabel}>{setting.label}</Text>
              <Text style={styles.settingDescription}>{setting.description}</Text>
            </View>
            <View style={[
              styles.toggle,
              settings[setting.key] && styles.toggleActive
            ]}>
              <View style={[
                styles.toggleThumb,
                settings[setting.key] && styles.toggleThumbActive
              ]} />
            </View>
          </TouchableOpacity>
        ))}
      </View>
    );
  };

  const unreadCount = notificationsData?.notifications?.filter(n => !n.isRead).length || 0;

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigateTo?.('profile')} style={styles.backButton}>
          <Icon name="arrow-left" size={24} color="#007AFF" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Notifications</Text>
        <View style={styles.headerActions}>
          {unreadCount > 0 && (
            <TouchableOpacity onPress={handleMarkAllAsRead} style={styles.markAllButton}>
              <Text style={styles.markAllText}>Mark All</Text>
            </TouchableOpacity>
          )}
          <TouchableOpacity 
            onPress={() => setShowSettings(!showSettings)} 
            style={styles.settingsButton}
          >
            <Icon name="settings" size={24} color="#007AFF" />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView 
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={handleRefresh} />
        }
        showsVerticalScrollIndicator={false}
      >
        {showSettings ? (
          renderSettings()
        ) : (
          <>
            {/* Notifications Count */}
            <View style={styles.countContainer}>
              <Text style={styles.countText}>
                {unreadCount > 0 ? `${unreadCount} unread` : 'All caught up!'}
              </Text>
            </View>

            {/* Notifications List */}
            {notificationsLoading ? (
              <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#007AFF" />
                <Text style={styles.loadingText}>Loading notifications...</Text>
              </View>
            ) : notificationsData?.notifications?.length > 0 ? (
              notificationsData.notifications.map(renderNotification)
            ) : (
              <View style={styles.emptyState}>
                <Icon name="bell" size={48} color="#C7C7CC" />
                <Text style={styles.emptyTitle}>No Notifications</Text>
                <Text style={styles.emptySubtitle}>You're all caught up! New notifications will appear here.</Text>
              </View>
            )}
          </>
        )}
      </ScrollView>
    </View>
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
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000000',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  markAllButton: {
    marginRight: 16,
  },
  markAllText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#007AFF',
  },
  settingsButton: {
    padding: 8,
  },
  content: {
    flex: 1,
  },
  countContainer: {
    padding: 20,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  countText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#8E8E93',
  },
  notificationCard: {
    backgroundColor: '#FFFFFF',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  unreadNotification: {
    backgroundColor: '#F0F8FF',
  },
  notificationHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  notificationIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  notificationContent: {
    flex: 1,
  },
  notificationTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000000',
    marginBottom: 4,
  },
  unreadText: {
    fontWeight: '700',
  },
  notificationMessage: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
    marginBottom: 8,
  },
  notificationTime: {
    fontSize: 12,
    color: '#8E8E93',
  },
  unreadDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#007AFF',
    marginTop: 4,
  },
  loadingContainer: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  loadingText: {
    fontSize: 16,
    color: '#8E8E93',
    marginTop: 12,
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 60,
    paddingHorizontal: 40,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#000000',
    marginTop: 16,
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#8E8E93',
    marginTop: 8,
    textAlign: 'center',
    lineHeight: 20,
  },
  settingsContainer: {
    padding: 20,
  },
  settingsTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#000000',
    marginBottom: 24,
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  settingInfo: {
    flex: 1,
    marginRight: 16,
  },
  settingLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#000000',
    marginBottom: 4,
  },
  settingDescription: {
    fontSize: 14,
    color: '#8E8E93',
    lineHeight: 20,
  },
  toggle: {
    width: 50,
    height: 30,
    borderRadius: 15,
    backgroundColor: '#E5E5EA',
    justifyContent: 'center',
    paddingHorizontal: 2,
  },
  toggleActive: {
    backgroundColor: '#007AFF',
  },
  toggleThumb: {
    width: 26,
    height: 26,
    borderRadius: 13,
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 2,
  },
  toggleThumbActive: {
    transform: [{ translateX: 20 }],
  },
});

export default NotificationsScreen;